"""Gemini TTS 配音（默认声音 Charon），带多 key 轮询、多模型轮换。

key（不要写进代码或聊天）：环境变量 GEMINI_API_KEYS（逗号分隔）或 GEMINI_API_KEY，
  或文件 ~/.config/gemini/api_key、api_key2、api_key3……（每行一个）。
模型：按 MODELS 顺序；一个模型在所有 key 上当天额度用完，才换下一个。要固定模型就设
  GEMINI_TTS_MODELS=gemini-3.8-flash-lite-tts（同一期只用一个模型，声音才一致）。
额度记录：~/.config/nonameskill/tts_quota.json（只记 key 哈希的前 8 位，不存 key）。

命令行试听：python tts_gemini.py "要读的文字" out.mp3
"""
import base64
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
import wave
from pathlib import Path

API = "https://generativelanguage.googleapis.com/v1beta"
MODELS = ["gemini-3.8-flash-tts", "gemini-3.8-flash-lite-tts", "gemini-3.1-flash-tts-preview"]
NO_STYLE = {"gemini-3.1-flash-tts-preview"}   # 不支持语气提示（speech_metadata），带了会 400
STYLE = "中文科技新闻口播，男声，语速稍快，干脆有力，句尾不拖腔"
KEY_DIR = Path.home() / ".config" / "gemini"
STATE = Path.home() / ".config" / "nonameskill" / "tts_quota.json"
last_model = None


def api_keys():
    keys = [k.strip() for k in os.environ.get("GEMINI_API_KEYS", "").split(",")]
    keys.append(os.environ.get("GEMINI_API_KEY", "").strip())
    for f in sorted(KEY_DIR.glob("api_key*")):
        if re.fullmatch(r"api_key\d*", f.name) and f.is_file():
            keys += [ln.strip() for ln in f.read_text(encoding="utf-8").splitlines() if not ln.strip().startswith("#")]
    keys = list(dict.fromkeys(k for k in keys if k))
    if not keys:
        sys.exit("没有 Gemini API key：设置环境变量 GEMINI_API_KEY，或把 key 写进 ~/.config/gemini/api_key")
    return keys


def _kid(key):
    return hashlib.sha256(key.encode()).hexdigest()[:8]


def _load():
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save(st):
    try:
        STATE.parent.mkdir(parents=True, exist_ok=True)
        STATE.write_text(json.dumps(st, indent=1), encoding="utf-8")
    except Exception:
        pass


def _retry_after(msg):
    m = re.search(r"retry in (?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?", msg)
    sec = m and (int(m.group(1) or 0) * 3600 + int(m.group(2) or 0) * 60 + int(m.group(3) or 0))
    return sec or 3600


class RateLimited(Exception):
    pass


class ApiError(Exception):
    def __init__(self, code, msg):
        super().__init__(f"HTTP {code}: {msg}")
        self.code = code


def _call(body, key):
    req = urllib.request.Request(f"{API}/interactions", method="POST", data=json.dumps(body).encode(),
                                 headers={"x-goog-api-key": key, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        msg = e.read().decode("utf-8", "ignore")[:800]
        if e.code == 429:
            raise RateLimited(msg)
        raise ApiError(e.code, msg)


def _tts_once(text, voice, style, model, key):
    content = {"type": "text", "text": text}
    if style:
        content["annotations"] = [{"type": "speech_metadata", "style": style}]
    r = _call({"model": model, "input": [{"type": "user_input", "content": [content]}],
               "response_format": {"type": "audio"}, "generation_config": {"speech_config": [{"voice": voice}]}}, key)
    audio = [c for s in r.get("steps", []) if s.get("type") == "model_output"
             for c in s.get("content", []) if c.get("type") == "audio"]
    if not audio:
        raise ApiError(0, "返回里没有音频：" + json.dumps(r, ensure_ascii=False)[:300])
    data = base64.b64decode(audio[-1]["data"])
    if data[:4] != b"RIFF":   # 有的模型返回不带文件头的 PCM（24kHz 单声道 16bit），补成 wav
        mime = str(audio[-1].get("mime_type") or audio[-1].get("mimeType") or "")
        rate = int((re.search(r"rate=(\d+)", mime) or [0, 24000])[1])
        buf = io.BytesIO()
        with wave.open(buf, "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate); w.writeframes(data)
        data = buf.getvalue()
    return data


def tts(text, voice="Charon", style=STYLE, model=None, retries=8):
    """返回 wav 字节。免费档按 key × 模型分别限额（每分钟、每天）：分钟限速就等，日额度用完就换 key / 换模型。"""
    global last_model
    keys = api_keys()
    env = [m.strip() for m in os.environ.get("GEMINI_TTS_MODELS", "").split(",") if m.strip()]
    models = [model] if model else (env or MODELS)
    st, why = _load(), []
    for m in models:
        bad, reason = set(), "每分钟限速，重试多次仍不行"
        for i in range(retries):
            now, rr = time.time(), st.get("_rr", 0)
            live = [k for k in (keys[(rr + j) % len(keys)] for j in range(len(keys)))
                    if st.get(f"{_kid(k)}|{m}", 0) <= now and k not in bad]
            if not live:
                reason = "所有 key 今天的额度都用完或不可用"
                break
            busy = False
            for k in live:
                try:
                    data = _tts_once(text, voice, "" if m in NO_STYLE else style, m, k)
                except RateLimited as e:
                    if "per day" in str(e):
                        st[f"{_kid(k)}|{m}"] = now + _retry_after(str(e)); _save(st)
                        print(f"Gemini {m} 在 key#{_kid(k)} 上今天的额度用完，换下一个", flush=True)
                    else:
                        busy = True
                    continue
                except ApiError as e:
                    if e.code in (401, 403):
                        bad.add(k); print(f"Gemini key#{_kid(k)} 不可用（HTTP {e.code}），跳过", flush=True)
                        continue
                    reason = str(e)[:160]
                    print(f"Gemini {m} 出错，换下一个模型：{reason}", flush=True)
                    break
                st["_rr"] = rr + 1; _save(st)
                last_model = m
                return data
            else:
                if busy:
                    wait = 25 + 5 * i
                    print(f"Gemini {m} 每分钟限速，{wait} 秒后重试（{i + 1}/{retries}）", flush=True)
                    time.sleep(wait)
                continue
            break
        why.append(f"{m}: {reason}")
    raise SystemExit("Gemini 配音失败：" + "；".join(why))


def tts_mp3(text, mp3, voice="Charon", style=STYLE, model=None):
    """生成配音 → 切掉首尾静音 → 写 mp3。"""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from common import ffmpeg
    mp3 = Path(mp3)
    wav = mp3.with_suffix(".gemini.wav")
    wav.write_bytes(tts(text, voice, style, model))
    trim = ("silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
            "silenceremove=start_periods=1:start_threshold=-45dB,areverse")
    subprocess.run([ffmpeg(), "-y", "-loglevel", "error", "-i", str(wav), "-af", trim, "-ar", "24000", "-b:a", "128k", str(mp3)], check=True)
    wav.unlink(missing_ok=True)
    return mp3


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit('用法：python tts_gemini.py "要读的文字" out.mp3')
    print(tts_mp3(sys.argv[1], sys.argv[2]), "模型：", last_model)
