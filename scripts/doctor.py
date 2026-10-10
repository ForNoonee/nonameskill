"""环境自检：python doctor.py —— 第一次用这个 skill 前先跑，缺什么就照提示装。只检查，不安装、不打印任何 key。"""
import importlib.util
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

ok = True


def check(name, good, fix, required=True):
    global ok
    print(("✅ " if good else ("❌ " if required else "⚪ ")) + name + ("" if good else f"  → {fix}"))
    if required and not good:
        ok = False


print(f"Python {sys.version.split()[0]}")
check("Python ≥ 3.10", sys.version_info >= (3, 10), "换用 Python 3.10 以上")
for mod, pkg in [("PIL", "pillow"), ("numpy", "numpy"), ("playwright", "playwright"), ("faster_whisper", "faster-whisper"), ("pypinyin", "pypinyin")]:
    check(f"Python 包 {pkg}", importlib.util.find_spec(mod) is not None, f"pip install {pkg}（或 pip install -r requirements.txt）")
check("可选：edge-tts（只在 VOICE=edge 时用）", importlib.util.find_spec("edge_tts") is not None, "pip install edge-tts", required=False)
has_ff = bool(shutil.which("ffmpeg")) or importlib.util.find_spec("imageio_ffmpeg") is not None
check("ffmpeg", has_ff, "brew install ffmpeg / apt install ffmpeg / pip install imageio-ffmpeg")
chrome = any(Path(p).exists() for p in ("/Applications/Google Chrome.app", "/usr/bin/google-chrome", "/usr/bin/google-chrome-stable",
                                         "C:/Program Files/Google/Chrome/Application/chrome.exe")) or bool(shutil.which("google-chrome"))
check("Google Chrome（渲染引擎用系统 Chrome）", chrome, "安装 Google Chrome")
eng = None
try:
    eng = C.huashu_engine()
except SystemExit:
    pass
check(f"huashu-art-motion 渲染引擎{('：' + str(eng.parent)) if eng else ''}", bool(eng),
      "npx skills add alchaincyf/huashu-art-motion，或设置 HUASHU_ENGINE=<它的 scripts/engine 目录>")
font = None
try:
    font = C.cjk_font_path()
except SystemExit:
    pass
check(f"中文字体{('：' + font) if font else ''}", bool(font), "设置 NONAME_FONT=<中文字体文件路径>")
keyfiles = [p for p in (Path.home() / ".config" / "gemini").glob("api_key*") if p.is_file()] if (Path.home() / ".config" / "gemini").exists() else []
has_key = bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEYS") or keyfiles)
check(f"Gemini API key（找到 {len(keyfiles)} 个 key 文件）", has_key,
      "到 aistudio.google.com/api-keys 申请，自己写进 ~/.config/gemini/api_key（不要发给 AI）")
check("可选：Codex CLI（自动出封面）", bool(shutil.which("codex")), "不装也行：cover.py 会给出提示词，用别的工具出图", required=False)
check("可选：背景音乐 NONAME_MUSIC_DIR", bool(os.environ.get("NONAME_MUSIC_DIR")), "不设就不加 BGM；设成一个放 mp3 的文件夹（注意曲子授权）", required=False)
print(f"\n工作区：{C.workspace()}（可用 NONAME_WORKSPACE 改）")
print("全部就绪 ✅" if ok else "还有必需项没装好 ❌")
sys.exit(0 if ok else 1)
