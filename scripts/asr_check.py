"""配音听写自检：python asr_check.py <期目录或slug> [ep01]

读 build.py --plan 写出的 work/<ep>/voice.json（只含当前分镜的句子），用 faster-whisper 听写每段配音，
数字和英文名先统一成读法，再按拼音和原稿比对（同音字不算错）。err>0.25 标 ⚠️，要人工听或改稿。
第一次运行会下载 whisper small 模型（约 460MB）。退出码 = ⚠️ 段数。"""
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import episode_dir, ffmpeg  # noqa: E402

DIG = "零一二三四五六七八九"
# 英文名的中文读法（只用于比对，原稿不变）；常见的先放几个，按需补充
PRON = {"Claude": "克劳德", "OpenAI": "欧鹏AI", "ChatGPT": "恰特GPT", "Gemini": "杰米尼", "AI": "A I", "App": "A P P"}


def _int_zh(n):
    if n == 0:
        return "零"
    out, units = "", ["", "十", "百", "千"]
    for big, name in ((10 ** 8, "亿"), (10 ** 4, "万")):
        if n >= big:
            out += _int_zh(n // big) + name
            n %= big
            if 0 < n < big // 10:
                out += "零"
    s = str(n) if n else ""
    for i, ch in enumerate(s):
        d, u = int(ch), units[len(s) - 1 - i]
        if d:
            out += DIG[d] + u
        elif not out.endswith("零") and i < len(s) - 1 and int(s[i + 1:] or 0):
            out += "零"
    return out[1:] if out.startswith("一十") else out


def _num(m):
    s = m.group(0)
    if "." in s:
        a, b = s.split(".", 1)
        b = b.rstrip("0")
        return _int_zh(int(a)) + ("点" + "".join(DIG[int(c)] for c in b) if b else "")
    return _int_zh(int(s))


def normalize(t):
    for en, zh in PRON.items():
        t = re.sub(rf"(?<![A-Za-z]){en}(?![A-Za-z])", zh, t)
    t = re.sub(r"(\d{4})(?=年)", lambda m: "".join(DIG[int(c)] for c in m.group(1)), t)
    t = re.sub(r"(\d+(?:\.\d+)?)%", lambda m: "百分之" + _num(re.match(r".+", m.group(1))), t)
    return re.sub(r"\d+(?:\.\d+)?", _num, t)


def _py(s):
    from pypinyin import lazy_pinyin
    return "".join(lazy_pinyin(re.sub(r"[^\w]", "", normalize(s)).lower()))


def cer(ref, hyp):
    r, h = _py(ref), _py(hyp)
    d = list(range(len(h) + 1))
    for i, rc in enumerate(r, 1):
        prev, d[0] = d[0], i
        for j, hc in enumerate(h, 1):
            prev, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, prev + (rc != hc))
    return d[len(h)] / max(1, len(r))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    D = episode_dir(sys.argv[1]); ep = sys.argv[2] if len(sys.argv) > 2 else "ep01"
    vj = D / "work" / ep / "voice.json"
    if not vj.exists():
        sys.exit(f"没有 {vj}：先跑 build.py {D.name} {ep} --plan")
    from faster_whisper import WhisperModel
    asr = WhisperModel("small", device="cpu", compute_type="int8")
    bad = 0
    for v in json.loads(vj.read_text(encoding="utf-8")):
        pcm = subprocess.run([ffmpeg(), "-v", "error", "-i", v["mp3"], "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
                             capture_output=True, check=True).stdout
        segs, _ = asr.transcribe(np.frombuffer(pcm, dtype=np.float32), language="zh", beam_size=1, initial_prompt="以下是普通话的句子。")
        hyp = "".join(s.text for s in segs)
        err = cer(v["t"], hyp)
        bad += err > 0.25
        print(("⚠️ " if err > 0.25 else "   ") + f"{err:.2f} [{v['k']}] {v.get('model', '')} {v['t']}\n        听写：{hyp}")
    print(f"{bad} 段要人工听/改稿" if bad else "听写全部对得上")
    sys.exit(min(bad, 99))
