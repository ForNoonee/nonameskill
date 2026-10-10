"""封面：python cover.py <期目录或slug>

读 publish/prompt.txt（四行字填好、尖括号全部替换掉）；publish/ref_cover.jpg 存在时一并作为风格参考图。
装了 Codex CLI（`codex`）就自动生成 publish/cover.png；没装就打印提示词，请用任何图像生成工具
按它出一张 1080×1920 的图，存成 publish/cover.png。生成后要读图逐字核对，错字就重来。
旧封面会先改名为 cover_prev.png，所以生成失败会直接报错，不会把旧图当成新图。"""
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import episode_dir  # noqa: E402

if len(sys.argv) < 2:
    sys.exit(__doc__)
P = episode_dir(sys.argv[1]) / "publish"
prompt = (P / "prompt.txt").read_text(encoding="utf-8")
left = re.findall(r"<[^<>]*>", prompt)
if left:
    sys.exit("prompt.txt 还有没填的尖括号：" + "、".join(left))
if (P / "cover.png").exists():
    (P / "cover.png").replace(P / "cover_prev.png")

if not shutil.which("codex") or "--no-codex" in sys.argv:
    print("没有 Codex CLI。请用任意图像生成工具，按下面的提示词出图，"
          f"存成 {P / 'cover.png'}：\n\n{prompt}")
    sys.exit(0)

mark = time.time()
with open(P / "prompt.txt", "rb") as fin, open(P / "codex.log", "w") as log:
    ref = ["-i", "ref_cover.jpg"] if (P / "ref_cover.jpg").exists() else []
    subprocess.run(["codex", "exec", "--skip-git-repo-check", "-s", "workspace-write", "-C", str(P), *ref, "-"],
                   stdin=fin, stdout=log, stderr=subprocess.STDOUT, cwd=P)
if not (P / "cover.png").exists():   # 兜底：沙箱没写进来时，图在 ~/.codex/generated_images/ 里，取这次之后最新的一张
    gen = sorted((p for p in (Path.home() / ".codex" / "generated_images").rglob("*.png") if p.stat().st_mtime > mark),
                 key=lambda p: p.stat().st_mtime)
    if gen:
        shutil.copy(gen[-1], P / "cover.png")
if (P / "cover.png").exists():
    print(f"OK {P / 'cover.png'}（读图逐字核对）")
else:
    sys.exit(f"封面没生成出来，看 {P / 'codex.log'}；上一版（如果有）在 cover_prev.png")
