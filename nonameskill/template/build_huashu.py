"""nonameskill 构建（huashu-art-motion 引擎）：口播 → 逐句时间 → 按语法渲片段（y5/y2/y1/t3）→ 拼接 + 字幕 + 配乐。
用法：../../.venv/bin/python build_huashu.py ep01 [--plan] [--only A,B] [--skip-render]；分镜在 eps/epNN.py
配音：Gemini 3.8 Flash TTS · Charon（2026-10-10 用户定，一律用它）。没有 key / 连不上就报错停下，不会悄悄换成云健；
VOICE=edge 只在用户同意后手动退回云健。--plan 会写 work/<ep>/voice.json，给 asr_check.py 听写自检用。
"""
import asyncio, hashlib, json, os, re, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw

HERE = Path(__file__).parent
RAW, WORK, OUT = HERE / "raw", HERE / "work", HERE / "out"
SPECS, CLIPS = WORK / "specs", WORK / "clips"
ENGINE = HERE / "huashu_scripts" / "engine" / "render.py"
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent.parent / "auto")); sys.path.insert(0, str(HERE.parent / "tesla_2008"))
sys.path.append(str(HERE.parent.parent))   # make_audio_gemini.py 在 sunbin 根目录；放最后，免得根目录的脚本盖住别的模块
import bgm  # noqa: E402
import musiclib  # noqa: E402
import build_ep1 as B  # noqa: E402  (排版工具、ffmpeg 封装；来自 series/tesla_2008/build_ep1.py)
for d in (WORK, OUT, SPECS, CLIPS):
    d.mkdir(parents=True, exist_ok=True)

W, H, FPS, SAFE_BOTTOM = 1080, 1920, 30, 520
GAP, LEAD = 0.45, 0.30
RATE = B.RATE
PY = str(HERE.parent.parent / ".venv" / "bin" / "python")
R = lambda k: str(RAW / f"{k}.jpg")

import importlib
EP = next((a for a in sys.argv[1:] if re.fullmatch(r"ep\d+[a-z]?", a)), "ep01")
M = importlib.import_module(f"eps.{EP}")
SEGS = M.SEGS
if True:
    WORK = HERE / "work" / EP; SPECS, CLIPS = WORK / "specs", WORK / "clips"
    for d in (WORK, SPECS, CLIPS):
        d.mkdir(parents=True, exist_ok=True)
    GAP, RATE = 0.32, "+18%"   # beat 间停顿；RATE 只对 VOICE=edge 生效

VOICE_ENGINE = os.environ.get("VOICE", "gemini")
if VOICE_ENGINE not in ("gemini", "edge"):
    raise SystemExit(f"VOICE={VOICE_ENGINE} 不认识：默认 gemini（Charon），只有用户同意时才用 VOICE=edge（云健）")


async def tts(key, text):
    """按文字哈希缓存：改稿后只重做改动的那段（以前 ep01 的缓存名不带哈希，改稿会继续用旧音频）。"""
    tag = hashlib.md5(text.encode()).hexdigest()[:6]
    if VOICE_ENGINE == "gemini":
        import make_audio_gemini as G
        p = WORK / f"{key}_charon_{tag}.mp3"
        if not p.exists():
            print(f"  Charon 配音 {key}", flush=True)
            G.tts_mp3(text, p, voice="Charon")   # key 轮询、模型按额度轮换（见 make_audio_gemini.py）
            p.with_suffix(".json").write_text(json.dumps(dict(model=G.last_model)), encoding="utf-8")
            print(f"    用的模型：{G.last_model}", flush=True)
        return p
    import edge_tts
    print(f"  ⚠️ {key} 用的是云健（VOICE=edge），不是 Charon", flush=True)
    p = WORK / f"{key}_edge{RATE.strip('+%')}_{tag}.mp3"
    if not p.exists():
        await edge_tts.Communicate(text, B.VOICE, rate=RATE).save(str(p))
    return p


def frac(text, sub):
    if not sub:
        return 0.0
    i = text.find(sub)
    return 0.0 if i < 0 else i / max(1, len(text))


def plan():
    left = [b["k"] for s in SEGS for b in s["beats"] if re.search(r"<[^<>]+>", b["t"])]
    if left or re.search(r"<[^<>]+>", getattr(M, "TITLE", "")):
        raise SystemExit(f"分镜里还有没填的 <占位>：{left or 'TITLE'}")
    t = 0.0
    for s in SEGS:
        cur = LEAD
        for b in s["beats"]:
            bad = [a for a, _ in b["cues"] if a and a not in b["t"]]
            if bad:
                raise SystemExit(f"{b['k']} 的锚点不在口播里：{bad}")
            b["mp3"] = asyncio.run(tts(b["k"], b["t"]))
            b["dur"] = B.dur(b["mp3"])
            b["start"] = cur
            cur += b["dur"] + GAP
        s["dur"] = round(cur + 0.3, 2)
        s["t0"] = t
        t += s["dur"]
    for s in SEGS:
        for b in s["beats"]:
            side = Path(b["mp3"]).with_suffix(".json")
            b["model"] = json.loads(side.read_text(encoding="utf-8")).get("model") if side.exists() else VOICE_ENGINE
    used = {}
    for s in SEGS:
        for b in s["beats"]:
            used.setdefault(b["model"], []).append(b["k"])
    print("配音模型：", "；".join(f"{m} → {','.join(ks)}" for m, ks in used.items()), flush=True)
    if len(used) > 1:
        print("⚠️ 这一期混用了不同的配音模型，声音可能前后不一致。可以删掉少数那几段的 mp3，"
              "等额度恢复后用 GEMINI_TTS_MODELS=<模型> 固定一个模型重配。", flush=True)
    # 只记当前分镜的句子（改稿删掉的不会留在听写报告里）
    (WORK / "voice.json").write_text(json.dumps([dict(k=b["k"], t=b["t"], mp3=str(b["mp3"]), model=b["model"]) for s in SEGS for b in s["beats"]],
                                                ensure_ascii=False, indent=1), encoding="utf-8")
    return t


def make_spec(s):
    cues = []
    for b in s["beats"]:
        for anchor, c in b["cues"]:
            q = dict(c)
            at = b["start"] + 0.25 + b["dur"] * frac(b["t"], anchor) - (0.12 if anchor else -0.05)
            q["at"] = round(max(0.0, at), 2)
            cues.append(q)
    cues.sort(key=lambda q: q["at"])
    if s["g"] == "y1_kurzgesagt":  # 钻进去之后的 point 要等转场落定
        enter = next((q for q in cues if q["kind"] == "enter"), None)
        if enter:
            tmin = enter["at"] + enter.get("dur", 1.6) + 0.1
            for q in cues:
                if q["kind"] == "point" and q["at"] > enter["at"] and q["at"] < tmin:
                    q["at"] = round(tmin, 2); tmin += 0.9
    spec = dict(grammar=s["g"], duration=s["dur"], fps=FPS, width=W, height=H, safe=dict(top=420 if s['g'] == 'y1_kurzgesagt' else 0, bottom=SAFE_BOTTOM), cues=cues)
    if s.get("data"):
        spec["data"] = s["data"]
    p = SPECS / f"{s['id']}.json"
    p.write_text(json.dumps(spec, ensure_ascii=False, indent=1))
    return p


def render(s, spec):
    out = CLIPS / f"{s['id']}.mp4"
    r = subprocess.run([PY, str(ENGINE), "--spec", str(spec), "--out", str(out)], capture_output=True, text=True, cwd=ENGINE.parent)
    log = (r.stdout + r.stderr)
    (WORK / f"render_{s['id']}.log").write_text(log)
    bad = [l for l in log.splitlines() if ("[page" in l and "404" not in l) or "拒绝" in l or "Error" in l]
    if not out.exists():
        raise RuntimeError(f"{s['id']} 渲染失败\n{log[-1500:]}")
    if bad:
        print(f"  {s['id']} 警告:", *bad[:4], sep="\n    ")
    return out


def sub_png(path, text):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    f = B.font(B.FONT_B, 54)
    lines = B.wrap(d, text, f, 900)
    h = int(len(lines) * 54 * 1.3) + 40
    y0 = 1490
    d.rounded_rectangle((70, y0 - 20, 1010, y0 - 20 + h), 24, fill=(0, 0, 0, 165))
    B.text_block(d, (W / 2, y0), text, f, (245, 238, 226, 255), 900, spacing=1.3, anchor_center=True, shadow=False)
    im.save(path)


def subtitles():
    subs = []
    for s in SEGS:
        for b in s["beats"]:
            parts = [p for p in re.findall(r"[^。！？：；]+[。！？：；]?", b["t"]) if p.strip()]
            n = sum(len(p) for p in parts); acc = 0
            for p in parts:
                a = s["t0"] + b["start"] + 0.25 + b["dur"] * acc / n
                acc += len(p)
                e = s["t0"] + b["start"] + 0.25 + b["dur"] * acc / n
                subs.append((a, e + (0.2 if acc < n else 0.4), p.strip("：；")))
    return subs


def main():
    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1].split(",")
    total = plan()
    print("总时长", round(total, 1), "秒；", {s["id"]: s["dur"] for s in SEGS})
    if "--plan" in sys.argv:
        return
    for s in SEGS:
        spec = make_spec(s)
        if "--skip-render" in sys.argv or (only and s["id"] not in only):
            continue
        print("渲染", s["id"], s["g"], flush=True)
        render(s, spec)
    if only or "--no-mux" in sys.argv:
        return
    lst = WORK / "clips.txt"
    lst.write_text("".join(f"file 'clips/{s['id']}.mp4'\n" for s in SEGS))
    vid = WORK / "video_raw.mp4"
    B.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-vf", f"fps={FPS},format=yuv420p", "-c:v", "libx264", "-crf", "18", str(vid)])
    # 音频：每个 beat 按绝对时间摆放 + 配乐
    inputs = ["-i", str(vid)]; fa = ""; labels = ""; idx = 1
    for s in SEGS:
        for b in s["beats"]:
            ms = int((s["t0"] + b["start"] + 0.25) * 1000)
            inputs += ["-i", str(b["mp3"])]
            fa += f"[{idx}:a]adelay={ms}|{ms}[a{idx}];"; labels += f"[a{idx}]"; idx += 1
    bgm_info = musiclib.bed(WORK / "full.mp3", total + 0.5)
    if bgm_info is None:
        bg = bgm.make_bgm(WORK, total, **getattr(M, "BGM", dict(seed=11, bpm=118)))
        print("配乐：曲库为空，用合成配乐", flush=True)
    else:
        print("配乐：", bgm_info["track"], f"{bgm_info['total']:.1f}s", flush=True)
    inputs += ["-i", str(WORK / "full.mp3")]
    fa += f"{labels}amix=inputs={idx - 1}:normalize=0,apad[nar];[{idx}:a]volume=0.14,afade=t=in:d=0.5[mu];[nar][mu]amix=inputs=2:duration=longest:normalize=0,atrim=0:{total:.2f}[aout];"
    # 字幕：所有字幕图按时间串成一条图片序列（concat），只叠一次
    subs = subtitles(); blank = WORK / "sub_blank.png"
    Image.new("RGBA", (W, H), (0, 0, 0, 0)).save(blank)
    seq, t = [], 0.0
    for i, (a, e, txt) in enumerate(subs):
        p = WORK / f"sub_{i:02d}.png"; sub_png(p, txt)
        e = min(e, subs[i + 1][0]) if i + 1 < len(subs) else e
        if a > t:
            seq.append((blank, a - t))
        seq.append((p, max(0.04, e - max(a, t)))); t = max(e, t)
    seq.append((blank, max(0.1, total - t + 1)))
    sl = WORK / "subs.txt"
    sl.write_text("".join(f"file '{p.name}'\nduration {d:.3f}\n" for p, d in seq) + f"file '{blank.name}'\n")
    inputs += ["-f", "concat", "-safe", "0", "-i", str(sl)]
    fv = f"[{idx + 1}:v]fps={FPS},format=rgba[sb];[0:v][sb]overlay=0:0:eof_action=pass[vout]"; cur = "vout"
    raw = WORK / f"{EP}_hs_raw.mp4"
    B.run(["ffmpeg", "-y", *inputs, "-filter_complex", fa + fv, "-map", f"[{cur}]", "-map", "[aout]", "-t", f"{total:.2f}",
           "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", str(raw)])
    final = OUT / f"{EP}_huashu.mp4"
    B.run(["ffmpeg", "-y", "-i", str(raw), "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", str(final)])
    print("完成", final, round(B.dur(final), 1), "秒")


if __name__ == "__main__":
    main()
