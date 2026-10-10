"""构建一期：口播配音 → 逐段时间 → 按语法渲动画段（huashu-art-motion 引擎）→ 拼接 + 字幕 + 背景音乐。

  python build.py <期目录或slug> ep01 --plan          只生成配音、算时长、写 work/ep01/voice.json（给 asr_check 用）
  python build.py <期目录或slug> ep01                 全片渲染 → out/ep01.mp4
  python build.py <期目录或slug> ep01 --only C        只重渲 C 段（改了配图时）
  python build.py <期目录或slug> ep01 --skip-render   不渲染，只用已有片段重新拼接

配音默认 Gemini TTS · Charon（scripts/tts_gemini.py）；VOICE=edge 改用 edge-tts（需 pip install edge-tts）。
分镜写在 <期目录>/eps/<ep>.py 的 SEGS 里，格式见 templates/ep01_template.py。
"""
import asyncio
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

ONLY_RAW = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
ONLY = ONLY_RAW.split(",") if ONLY_RAW else None
args = [x for i, x in enumerate(sys.argv[1:], 1) if not x.startswith("--") and not (ONLY_RAW and sys.argv[i - 1] == "--only")]
if not args:
    sys.exit(__doc__)
HERE = C.episode_dir(args[0])
EP = next((x for x in args[1:] if re.fullmatch(r"ep\d+[a-z]?", x)), "ep01")

RAW, OUT = HERE / "raw", HERE / "out"
WORK = HERE / "work" / EP
SPECS, CLIPS = WORK / "specs", WORK / "clips"
for d in (WORK, OUT, SPECS, CLIPS):
    d.mkdir(parents=True, exist_ok=True)

W, H, FPS, SAFE_BOTTOM = 1080, 1920, 30, 520
GAP, LEAD = 0.32, 0.30
VOICE_ENGINE = os.environ.get("VOICE", "gemini")
if VOICE_ENGINE not in ("gemini", "edge"):
    sys.exit(f"VOICE={VOICE_ENGINE} 不认识：默认 gemini（Charon），备用 edge")

sys.path.insert(0, str(HERE))
spec = importlib.util.spec_from_file_location(f"eps.{EP}", HERE / "eps" / f"{EP}.py")
if not spec or not (HERE / "eps" / f"{EP}.py").exists():
    sys.exit(f"没有分镜文件 {HERE / 'eps' / (EP + '.py')}")
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)
SEGS = M.SEGS


async def tts(key, text):
    """按文字哈希缓存：改稿后只重做改动的段。"""
    tag = hashlib.md5(text.encode()).hexdigest()[:6]
    if VOICE_ENGINE == "gemini":
        import tts_gemini as G
        p = WORK / f"{key}_charon_{tag}.mp3"
        if not p.exists():
            print(f"  配音 {key}", flush=True)
            G.tts_mp3(text, p, voice="Charon")
            p.with_suffix(".json").write_text(json.dumps(dict(model=G.last_model)), encoding="utf-8")
            print(f"    模型：{G.last_model}", flush=True)
        return p
    import edge_tts
    p = WORK / f"{key}_edge_{tag}.mp3"
    if not p.exists():
        await edge_tts.Communicate(text, "zh-CN-YunjianNeural", rate="+18%").save(str(p))
    return p


def frac(text, sub):
    if not sub:
        return 0.0
    i = text.find(sub)
    return 0.0 if i < 0 else i / max(1, len(text))


def plan():
    left = [b["k"] for s in SEGS for b in s["beats"] if re.search(r"<[^<>]+>", b["t"])]
    if left or re.search(r"<[^<>]+>", getattr(M, "TITLE", "")):
        sys.exit(f"分镜里还有没填的 <占位>：{left or 'TITLE'}")
    t = 0.0
    for s in SEGS:
        cur = LEAD
        for b in s["beats"]:
            bad = [x for x, _ in b["cues"] if x and x not in b["t"]]
            if bad:
                sys.exit(f"{b['k']} 的锚点不在口播里：{bad}")
            b["mp3"] = asyncio.run(tts(b["k"], b["t"]))
            b["dur"] = C.duration(b["mp3"])
            b["start"] = cur
            cur += b["dur"] + GAP
        s["dur"] = round(cur + 0.3, 2)
        s["t0"] = t
        t += s["dur"]
    used = {}
    for s in SEGS:
        for b in s["beats"]:
            side = Path(b["mp3"]).with_suffix(".json")
            b["model"] = json.loads(side.read_text(encoding="utf-8")).get("model") if side.exists() else VOICE_ENGINE
            used.setdefault(b["model"], []).append(b["k"])
    print("配音模型：", "；".join(f"{m} → {','.join(ks)}" for m, ks in used.items()), flush=True)
    if len(used) > 1:
        print("⚠️ 这一期混用了不同的配音模型，声音可能前后不一致：删掉少数那几段的 mp3，"
              "额度恢复后用 GEMINI_TTS_MODELS=<模型> 固定一个模型重配。", flush=True)
    (WORK / "voice.json").write_text(json.dumps([dict(k=b["k"], t=b["t"], mp3=str(b["mp3"]), model=b["model"])
                                                 for s in SEGS for b in s["beats"]], ensure_ascii=False, indent=1), encoding="utf-8")
    return t


def make_spec(s):
    cues = []
    for b in s["beats"]:
        for anchor, c in b["cues"]:
            q = dict(c)
            q["at"] = round(max(0.0, b["start"] + 0.25 + b["dur"] * frac(b["t"], anchor) - (0.12 if anchor else -0.05)), 2)
            cues.append(q)
    cues.sort(key=lambda q: q["at"])
    if s["g"] == "y1_kurzgesagt":   # 钻进去之后的 point 要等转场落定
        enter = next((q for q in cues if q["kind"] == "enter"), None)
        if enter:
            tmin = enter["at"] + enter.get("dur", 1.6) + 0.1
            for q in cues:
                if q["kind"] == "point" and enter["at"] < q["at"] < tmin:
                    q["at"] = round(tmin, 2); tmin += 0.9
    sp = dict(grammar=s["g"], duration=s["dur"], fps=FPS, width=W, height=H,
              safe=dict(top=420 if s["g"] == "y1_kurzgesagt" else 0, bottom=SAFE_BOTTOM), cues=cues)
    if s.get("data"):
        sp["data"] = s["data"]
    p = SPECS / f"{s['id']}.json"
    p.write_text(json.dumps(sp, ensure_ascii=False, indent=1))
    return p


def render(s, spec_path, engine):
    out = CLIPS / f"{s['id']}.mp4"
    r = subprocess.run([sys.executable, str(engine), "--spec", str(spec_path), "--out", str(out)],
                       capture_output=True, text=True, cwd=engine.parent, env=C.ffmpeg_env())
    log = r.stdout + r.stderr
    (WORK / f"render_{s['id']}.log").write_text(log)
    if not out.exists():
        raise RuntimeError(f"{s['id']} 渲染失败\n{log[-1500:]}")
    bad = [l for l in log.splitlines() if ("[page" in l and "404" not in l) or "Error" in l]
    if bad:
        print(f"  {s['id']} 警告:", *bad[:4], sep="\n    ")
    return out


def sub_png(path, text):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    f = C.font(54)
    lines = C.wrap(d, text, f, 900)
    h = int(len(lines) * 54 * 1.3) + 40
    y0 = 1490
    d.rounded_rectangle((70, y0 - 20, 1010, y0 - 20 + h), 24, fill=(0, 0, 0, 165))
    C.text_block(d, (W / 2, y0), text, f, (245, 238, 226, 255), 900, spacing=1.3, anchor_center=True)
    im.save(path)


def subtitles():
    subs = []
    for s in SEGS:
        for b in s["beats"]:
            parts = [p for p in re.findall(r"[^。！？：；]+[。！？：；]?", b["t"]) if p.strip()]
            n = sum(len(p) for p in parts); acc = 0
            for p in parts:
                a0 = s["t0"] + b["start"] + 0.25 + b["dur"] * acc / n
                acc += len(p)
                e = s["t0"] + b["start"] + 0.25 + b["dur"] * acc / n
                subs.append((a0, e + (0.2 if acc < n else 0.4), p.strip("：；")))
    return subs


def music_bed(total):
    """NONAME_MUSIC_DIR 里轮流取一首（最久没用的优先），循环铺满全片。没设就返回 None。"""
    d = os.environ.get("NONAME_MUSIC_DIR")
    if not d:
        return None
    tracks = sorted(p for p in Path(d).expanduser().iterdir() if p.suffix.lower() in (".mp3", ".wav", ".m4a", ".aac", ".flac"))
    if not tracks:
        return None
    use_f = C.workspace() / ".music_usage.json"
    use = json.loads(use_f.read_text()) if use_f.exists() else {}
    track = min(tracks, key=lambda p: use.get(p.name, 0))
    import time
    use[track.name] = time.time(); use_f.parent.mkdir(parents=True, exist_ok=True); use_f.write_text(json.dumps(use))
    bed = WORK / "bgm.mp3"
    C.run(["ffmpeg", "-y", "-stream_loop", "-1", "-i", str(track), "-t", f"{total + 0.5:.2f}",
           "-af", f"afade=t=out:st={max(0, total - 1.5):.2f}:d=1.5", str(bed)])
    print("配乐：", track.name, flush=True)
    return bed


def main():
    total = plan()
    print("总时长", round(total, 1), "秒；", {s["id"]: s["dur"] for s in SEGS})
    if "--plan" in sys.argv:
        return
    engine = C.huashu_engine()
    for s in SEGS:
        sp = make_spec(s)
        if "--skip-render" in sys.argv or (ONLY and s["id"] not in ONLY):
            continue
        print("渲染", s["id"], s["g"], flush=True)
        render(s, sp, engine)
    if ONLY:
        return
    lst = WORK / "clips.txt"
    lst.write_text("".join(f"file 'clips/{s['id']}.mp4'\n" for s in SEGS))
    vid = WORK / "video_raw.mp4"
    C.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-vf", f"fps={FPS},format=yuv420p", "-c:v", "libx264", "-crf", "18", str(vid)])
    inputs = ["-i", str(vid)]; fa = ""; labels = ""; idx = 1
    for s in SEGS:
        for b in s["beats"]:
            ms = int((s["t0"] + b["start"] + 0.25) * 1000)
            inputs += ["-i", str(b["mp3"])]
            fa += f"[{idx}:a]adelay={ms}|{ms}[a{idx}];"; labels += f"[a{idx}]"; idx += 1
    bed = music_bed(total)
    if bed:
        inputs += ["-i", str(bed)]
        fa += (f"{labels}amix=inputs={idx - 1}:normalize=0,apad[nar];[{idx}:a]volume=0.14,afade=t=in:d=0.5[mu];"
               f"[nar][mu]amix=inputs=2:duration=longest:normalize=0,atrim=0:{total:.2f}[aout];")
        sub_idx = idx + 1
    else:
        fa += f"{labels}amix=inputs={idx - 1}:normalize=0,apad,atrim=0:{total:.2f}[aout];"
        sub_idx = idx
    subs = subtitles(); blank = WORK / "sub_blank.png"
    Image.new("RGBA", (W, H), (0, 0, 0, 0)).save(blank)
    seq, t = [], 0.0
    for i, (a0, e, txt) in enumerate(subs):
        p = WORK / f"sub_{i:02d}.png"; sub_png(p, txt)
        e = min(e, subs[i + 1][0]) if i + 1 < len(subs) else e
        if a0 > t:
            seq.append((blank, a0 - t))
        seq.append((p, max(0.04, e - max(a0, t)))); t = max(e, t)
    seq.append((blank, max(0.1, total - t + 1)))
    sl = WORK / "subs.txt"
    sl.write_text("".join(f"file '{p.name}'\nduration {d:.3f}\n" for p, d in seq) + f"file '{blank.name}'\n")
    inputs += ["-f", "concat", "-safe", "0", "-i", str(sl)]
    fv = f"[{sub_idx}:v]fps={FPS},format=rgba[sb];[0:v][sb]overlay=0:0:eof_action=pass[vout]"
    raw = WORK / f"{EP}_raw.mp4"
    C.run(["ffmpeg", "-y", *inputs, "-filter_complex", fa + fv, "-map", "[vout]", "-map", "[aout]", "-t", f"{total:.2f}",
           "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", str(raw)])
    final = OUT / f"{EP}.mp4"
    C.run(["ffmpeg", "-y", "-i", str(raw), "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", str(final)])
    print("完成", final, round(C.duration(final), 1), "秒")


if __name__ == "__main__":
    main()
