"""Charon 配音听写自检：python asr_check.py <slug 或 series 目录> [ep01]
读 build_huashu.py 每次 --plan 写出的 work/<ep>/voice.json（只含当前分镜的句子，改稿删掉的不会出现），
用 faster-whisper 听写每段配音，按拼音和原稿比对；err>0.25 标 ⚠️，要人工听或改稿。退出码 = ⚠️ 段数。"""
import os
import json, subprocess, sys
from pathlib import Path

import numpy as np

ROOT = Path(os.environ.get("NONAME_ROOT", Path.cwd()))   # 项目根目录：环境变量 NONAME_ROOT，默认当前目录
sys.path.insert(0, str(ROOT / "auto"))
import clone_voice as C  # noqa: E402  借用它的 _cer：数字、英文名先统一成读法，再按拼音比（同音字不算错）
import imageio_ffmpeg  # noqa: E402

arg = sys.argv[1]
D = Path(arg) if "/" in arg else ROOT / "series" / arg
ep = sys.argv[2] if len(sys.argv) > 2 else "ep01"
vj = D / "work" / ep / "voice.json"
if not vj.exists():
    raise SystemExit(f"没有 {vj}：先跑 build_huashu.py {ep} --plan")

from faster_whisper import WhisperModel  # noqa: E402
asr = WhisperModel("small", device="cpu", compute_type="int8")
bad = 0
for v in json.loads(vj.read_text(encoding="utf-8")):
    pcm = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-v", "error", "-i", v["mp3"], "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    segs, _ = asr.transcribe(np.frombuffer(pcm, dtype=np.float32), language="zh", beam_size=1, initial_prompt="以下是普通话的句子。")
    hyp = "".join(s.text for s in segs)
    err = C._cer(v["t"], hyp)
    bad += err > 0.25
    print(("⚠️ " if err > 0.25 else "   ") + f"{err:.2f} [{v['k']}] {v.get('model', '')} {v['t']}\n        听写：{hyp}")
print(f"{bad} 段要人工听/改稿" if bad else "听写全部对得上")
sys.exit(min(bad, 99))
