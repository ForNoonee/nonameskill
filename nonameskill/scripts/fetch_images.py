"""抓报道页的配图 + 出带文件名的拼图：python fetch_images.py <slug> <报道URL> [<URL>...]
→ series/<slug>/raw/fetch/imgN.* ，拼图 raw/fetch/_sheet.jpg（每张图左上角印文件名和来源站，防止编号看错——2026-10-10 踩过两次）。"""
import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw
ROOT = Path(os.environ.get("NONAME_ROOT", Path.cwd()))   # 项目根目录：环境变量 NONAME_ROOT，默认当前目录
sys.path.insert(0, str(ROOT / "auto"))
import pipeline as P
slug, urls = sys.argv[1], sys.argv[2:]
out = ROOT / "series" / slug / "raw" / "fetch"; out.mkdir(parents=True, exist_ok=True)
got = P.fetch_images([{"url": u, "credit": u.split("/")[2], "page": True} for u in urls], out, max_n=len(urls))
W = 480; tiles = []
for g in got:
    im = Image.open(out / g["file"]).convert("RGB")
    t = im.resize((W, int(W * im.height / im.width)))
    d = ImageDraw.Draw(t); label = f"{g['file']}  {g['credit']}  {im.width}x{im.height}"
    d.rectangle((0, 0, 8 + 7 * len(label), 22), fill="black"); d.text((4, 5), label, fill="yellow")
    tiles.append(t); print(label, g["src"])
if tiles:
    H = max(t.height for t in tiles); cols = 3; rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (W * cols, H * rows), "white")
    for k, t in enumerate(tiles):
        sheet.paste(t, ((k % cols) * W, (k // cols) * H))
    sheet.save(out / "_sheet.jpg"); print("拼图", out / "_sheet.jpg")
