"""用 Gemini TTS 生成配音（默认声音 Charon，2026-10-10 起替代云健）。

key：环境变量 GEMINI_API_KEYS（逗号分隔）/ GEMINI_API_KEY，再加 ~/.config/gemini/api_key、api_key2、api_key3……（每行一个）。
多个 key 轮流用；模型按 MODELS 的顺序，当天额度在所有 key 上都用完才换下一个模型（2026-10-10 用户定：key 轮询、模型轮换）。
同一期视频尽量不混模型，声音才一致：要固定模型就设 GEMINI_TTS_MODELS=gemini-3.8-flash-lite-tts。
哪个 key + 模型今天用完了，记在 ~/.config/gemini/tts_quota.json（只记 key 的哈希前 8 位，不存 key）。

用法：
  python make_audio_gemini.py "要读的文字" [--voice Charon] [--style "像科技新闻主播，干脆有力"] [--out out.wav]
  python make_audio_gemini.py --file 稿子.txt --mp3            # 另存 loudnorm 到 -16 LUFS 的 mp3
  python make_audio_gemini.py "文字" --voices Charon,Orus,Algenib,Sadaltager --out gemini_try/
  python make_audio_gemini.py --list-voices zh                  # 列出扩展声音库里的中文声音
"""
import argparse, base64, hashlib, io, json, os, re, subprocess, time, urllib.error, urllib.request, wave
from pathlib import Path

API = "https://generativelanguage.googleapis.com/v1beta"
MODEL = "gemini-3.8-flash-tts"
# 优先级顺序（2026-10-10 用户定；用户说的「3.6」没有这个 TTS 模型，API 里有的是 3.1 Flash TTS Preview）
MODELS = ["gemini-3.8-flash-tts", "gemini-3.8-flash-lite-tts", "gemini-3.1-flash-tts-preview"]
NO_STYLE = {"gemini-3.1-flash-tts-preview"}   # 不支持语气提示（speech_metadata），带了会报 400
STYLE = "中文科技新闻口播，男声，语速稍快，干脆有力，句尾不拖腔"
KEY_DIR = Path.home() / ".config/gemini"
STATE = KEY_DIR / "tts_quota.json"
last_model = None   # 最近一次成功用的模型，调用方可以读来记录


def api_keys():
    keys = [k.strip() for k in os.environ.get("GEMINI_API_KEYS", "").split(",")]
    keys.append(os.environ.get("GEMINI_API_KEY", "").strip())
    for f in sorted(KEY_DIR.glob("api_key*")):
        if re.fullmatch(r"api_key\d*", f.name) and f.is_file():
            keys += [ln.strip() for ln in f.read_text(encoding="utf-8").splitlines() if not ln.strip().startswith("#")]
    keys = list(dict.fromkeys(k for k in keys if k))
    if not keys:
        raise SystemExit("没有 Gemini key：请写进 ~/.config/gemini/api_key（多个 key 用 api_key2、api_key3）")
    return keys


def api_key():
    return api_keys()[0]


def _kid(key):
    return hashlib.sha256(key.encode()).hexdigest()[:8]


def _load_state():
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_state(st):
    try:
        STATE.write_text(json.dumps(st, indent=1), encoding="utf-8")
        STATE.chmod(0o600)
    except Exception:
        pass


def _retry_after(msg):
    """从「Please retry in 4h53m11s」里取等待秒数，取不到按 1 小时。"""
    m = re.search(r"retry in (?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?", msg)
    sec = m and (int(m.group(1) or 0) * 3600 + int(m.group(2) or 0) * 60 + int(m.group(3) or 0))
    return sec or 3600


class RateLimited(Exception):
    pass


class ApiError(Exception):
    def __init__(self, code, msg):
        super().__init__(f"HTTP {code}: {msg}")
        self.code = code


def call(method, path, body=None, key=None, strict=True):
    req = urllib.request.Request(f"{API}/{path}", method=method,
                                 data=json.dumps(body).encode() if body else None,
                                 headers={"x-goog-api-key": key or api_key(), "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        msg = e.read().decode('utf-8', 'ignore')[:800]
        if e.code == 429:
            raise RateLimited(msg)
        if not strict:
            raise ApiError(e.code, msg)
        raise SystemExit(f"HTTP {e.code}: {msg}")


def tts(text, voice="Charon", style=STYLE, model=None, retries=8):
    """返回 wav 字节（24kHz 单声道 16bit）。model=None 时按 MODELS（或环境变量 GEMINI_TTS_MODELS）轮换。
    免费档每个 key、每个模型每分钟 3 次、每天 10 次（2026-10-10 实测）：
    多个 key 轮流用；某个 key 的日额度用完就换下一个 key，这个模型在所有 key 上都用完才换下一个模型；
    所有 key 都只是分钟限速时，等一会儿再试。"""
    global last_model
    keys = api_keys()
    env = [m.strip() for m in os.environ.get("GEMINI_TTS_MODELS", "").split(",") if m.strip()]
    models = [model] if model else (env or MODELS)
    st, why = _load_state(), []
    for m in models:
        bad_keys, reason = set(), "每分钟限速，重试多次仍不行"
        for i in range(retries):
            now, rr = time.time(), st.get("_rr", 0)
            live = [k for k in (keys[(rr + j) % len(keys)] for j in range(len(keys)))
                    if st.get(f"{_kid(k)}|{m}", 0) <= now and k not in bad_keys]
            if not live:
                reason = "所有 key 今天的额度都用完或不可用"
                break
            busy = False
            for k in live:
                try:
                    data = _tts_once(text, voice, "" if m in NO_STYLE else style, m, k)
                except RateLimited as e:
                    if "per day" in str(e):
                        st[f"{_kid(k)}|{m}"] = now + _retry_after(str(e)); _save_state(st)
                        print(f"Gemini {m} 在 key#{_kid(k)} 上今天的额度用完，换下一个", flush=True)
                    else:
                        busy = True
                    continue
                except ApiError as e:
                    if e.code in (401, 403):   # key 无效或没权限：这次运行里跳过这个 key
                        bad_keys.add(k); print(f"Gemini key#{_kid(k)} 不可用（HTTP {e.code}），跳过", flush=True)
                        continue
                    reason = str(e)[:160]   # 400/404 等：这个模型不行，换下一个模型
                    print(f"Gemini {m} 出错，换下一个模型：{reason}", flush=True)
                    break
                st["_rr"] = rr + 1; _save_state(st)
                last_model = m
                return data
            else:
                if busy:
                    wait = 25 + 5 * i
                    print(f"Gemini {m} 每分钟限速，{wait} 秒后重试（{i + 1}/{retries}）", flush=True)
                    time.sleep(wait)
                continue
            break   # 模型出错，换下一个模型
        why.append(f"{m}: {reason}")
    raise SystemExit("Gemini 配音失败：" + "；".join(why))


def _tts_once(text, voice, style, model, key=None):
    content = {"type": "text", "text": text}
    if style:
        content["annotations"] = [{"type": "speech_metadata", "style": style}]
    r = call("POST", "interactions", {
        "model": model,
        "input": [{"type": "user_input", "content": [content]}],
        "response_format": {"type": "audio"},
        "generation_config": {"speech_config": [{"voice": voice}]},
    }, key=key, strict=False)
    audio = [c for s in r.get("steps", []) if s.get("type") == "model_output"
             for c in s.get("content", []) if c.get("type") == "audio"]
    if not audio:
        raise SystemExit("返回里没有音频：" + json.dumps(r, ensure_ascii=False)[:800])
    data = base64.b64decode(audio[-1]["data"])
    if data[:4] != b"RIFF":   # 3.1 Flash TTS Preview 返回不带文件头的 PCM（24kHz 单声道 16bit），补成 wav
        mime = str(audio[-1].get("mime_type") or audio[-1].get("mimeType") or "")
        rate = int((re.search(r"rate=(\d+)", mime) or [0, 24000])[1])
        buf = io.BytesIO()
        with wave.open(buf, "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate); w.writeframes(data)
        data = buf.getvalue()
    return data


def tts_mp3(text, mp3, voice="Charon", style=STYLE, model=None):
    """出片用：生成配音 → 切掉首尾静音 → 写 mp3（2026-10-10 起默认 Charon，替代云健）。"""
    import imageio_ffmpeg
    mp3 = Path(mp3)
    wav = mp3.with_suffix(".gemini.wav")
    wav.write_bytes(tts(text, voice, style, model))
    trim = "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse"
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-i", str(wav), "-af", trim,
                    "-ar", "24000", "-b:a", "128k", str(mp3)], check=True)
    wav.unlink(missing_ok=True)
    return mp3


def to_mp3(wav, mp3):
    import imageio_ffmpeg
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-i", str(wav),
                    "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", "44100", "-b:a", "128k", str(mp3)], check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("text", nargs="?")
    ap.add_argument("--file")
    ap.add_argument("--voice", default="Charon")
    ap.add_argument("--voices", help="逗号分隔，一次出多个声音对比")
    ap.add_argument("--style", default=STYLE, help='整段语气；传 "" 不加')
    ap.add_argument("--model", default=None, help="不填就按 MODELS 轮换")
    ap.add_argument("--out", default="gemini_tts.wav", help="单个声音为文件名，多个声音为目录")
    ap.add_argument("--mp3", action="store_true", help="另存 loudnorm 后的 mp3")
    ap.add_argument("--list-voices", metavar="LANG", help="列出扩展声音库，按语言过滤，如 zh")
    a = ap.parse_args()

    if a.list_voices is not None:
        voices = call("GET", "voices").get("voices", [])
        for v in voices:
            if a.list_voices.lower() in json.dumps(v, ensure_ascii=False).lower():
                print(json.dumps(v, ensure_ascii=False))
        return

    text = Path(a.file).read_text(encoding="utf-8").strip() if a.file else a.text
    if not text:
        raise SystemExit("没有要读的文字")
    voices = a.voices.split(",") if a.voices else [a.voice]
    out = Path(a.out)
    for v in voices:
        wav = out / f"{v}.wav" if len(voices) > 1 else out
        wav.parent.mkdir(parents=True, exist_ok=True)
        wav.write_bytes(tts(text, v, a.style, a.model))
        print("写出", wav)
        if a.mp3:
            to_mp3(wav, wav.with_suffix(".mp3"))
            print("写出", wav.with_suffix(".mp3"))


if __name__ == "__main__":
    main()
