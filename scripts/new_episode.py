"""建一期新片的目录并登记选题：python new_episode.py <slug> "<aihot 标题，照 candidates.py 原样复制>"

生成 <工作区>/<slug>/：
  eps/ep01.py        分镜（从模板复制）    raw/fetch/   抓来的配图
  publish/prompt.txt 封面提示词模板         out/         成片与抽帧
（templates/ 里放了自己的 ref_cover.jpg 的话，会一并复制，作为封面风格参考）
并把标题写进 <工作区>/done.tsv，下次 candidates.py 会标成「样片」。"""
import shutil
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import TEMPLATES, workspace  # noqa: E402

if len(sys.argv) < 3:
    sys.exit('用法：python new_episode.py <英文slug> "<选题标题>"')
slug, title = sys.argv[1], sys.argv[2]
if not slug.replace("_", "").replace("-", "").isalnum():
    sys.exit("slug 只用字母、数字、下划线、短横线")
ws = workspace()
d = ws / slug
if d.exists():
    sys.exit(f"已存在：{d}")
for sub in ("raw/fetch", "eps", "publish", "out"):
    (d / sub).mkdir(parents=True)
shutil.copy(TEMPLATES / "eps_init.py", d / "eps" / "__init__.py")
shutil.copy(TEMPLATES / "ep01_template.py", d / "eps" / "ep01.py")
shutil.copy(TEMPLATES / "cover_prompt.txt", d / "publish" / "prompt.txt")
if (TEMPLATES / "ref_cover.jpg").exists():   # 可选：你自己的封面风格参考图（不随 skill 分发）
    shutil.copy(TEMPLATES / "ref_cover.jpg", d / "publish" / "ref_cover.jpg")
reg = ws / "done.tsv"
lines = reg.read_text(encoding="utf-8").splitlines() if reg.exists() else []
if not any(ln.startswith(title + "\t") for ln in lines):
    with reg.open("a", encoding="utf-8") as f:
        f.write(f"{title}\t{slug}\t{date.today()}\n")
print(f"OK {d}（已登记 {reg}）")
