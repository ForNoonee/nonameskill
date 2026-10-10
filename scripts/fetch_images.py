"""抓配图 + 出带标签的拼图：python fetch_images.py <期目录或slug> <网址> [<网址> ...] [--max-per-page 6]

网址可以是报道/官网页面（取 og:image、twitter:image 和正文里的大图），也可以直接是图片地址。
结果存到 <期目录>/raw/fetch/imgN.*，拼图 raw/fetch/_sheet.jpg：每张图左上角印「文件名 来源站 尺寸」，
选图时对着标签选，不要按排列位置猜编号。去掉 logo/图标/头像和重复图（感知哈希）。"""
import argparse
import re
import sys
import urllib.request
from io import BytesIO
from pathlib import Path
from urllib.parse import urljoin, urlparse

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import episode_dir  # noqa: E402

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150 Safari/537.36"}
SKIP = re.compile(r"logo|icon|avatar|sprite|favicon|blank|placeholder|1x1|pixel|badge|emoji", re.I)

ap = argparse.ArgumentParser()
ap.add_argument("episode")
ap.add_argument("urls", nargs="+")
ap.add_argument("--max-per-page", type=int, default=6)
a = ap.parse_args()
out = episode_dir(a.episode) / "raw" / "fetch"
out.mkdir(parents=True, exist_ok=True)


def get(u, limit=8_000_000, referer=None):
    h = dict(UA)
    if referer:
        h["Referer"] = referer
    with urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=25) as r:
        return r.read(limit), r.headers.get("Content-Type", "")


def ahash(im):
    g = im.convert("L").resize((8, 8))
    px = list(g.getdata()); avg = sum(px) / 64
    return sum(1 << i for i, v in enumerate(px) if v > avg)


got = []


def save(img_url, credit, referer=None):
    if SKIP.search(img_url) or img_url.lower().endswith(".svg"):
        return
    try:
        data, _ = get(img_url, referer=referer)
        im = Image.open(BytesIO(data)); im.load()
    except Exception:
        return
    if im.width < 400 or im.height < 200 or len(data) < 15_000:
        return
    h = ahash(im)
    if any(bin(h ^ g["hash"]).count("1") <= 10 for g in got):
        return
    ext = {"PNG": ".png", "JPEG": ".jpg", "WEBP": ".webp", "GIF": ".gif"}.get(im.format, ".png")
    f = out / f"img{len(got)}{ext}"
    f.write_bytes(data)
    got.append({"file": f.name, "credit": credit, "src": img_url, "hash": h, "size": im.size})


for u in a.urls:
    site = urlparse(u).netloc
    try:
        data, ctype = get(u, 2_000_000)
    except Exception as e:
        print(f"打不开 {u}：{e}")
        continue
    if ctype.startswith("image/"):
        save(u, site)
        continue
    html = data.decode("utf-8", "ignore")
    cands = []
    for m in re.finditer(r'<meta[^>]+(?:property|name)=["\'](?:og:image|twitter:image)["\'][^>]*>', html, re.I):
        c = re.search(r'content=["\']([^"\']+)', m.group(0))
        if c:
            cands.append(c.group(1))
    for m in re.finditer(r'<img[^>]+(?:data-original|data-src|src)=["\']([^"\']+)["\']', html, re.I):
        cands.append(m.group(1))
    n0 = len(got)
    for c in dict.fromkeys(urljoin(u, c) for c in cands):
        if len(got) - n0 >= a.max_per_page:
            break
        save(c, site, referer=u)
    print(f"{site}: {len(got) - n0} 张")

W, tiles = 480, []
for g in got:
    im = Image.open(out / g["file"]).convert("RGB")
    t = im.resize((W, max(1, int(W * im.height / im.width))))
    d = ImageDraw.Draw(t)
    label = f"{g['file']}  {g['credit']}  {g['size'][0]}x{g['size'][1]}"
    d.rectangle((0, 0, 8 + 7 * len(label), 22), fill="black"); d.text((4, 5), label, fill="yellow")
    tiles.append(t); print(label, g["src"])
if tiles:
    cols = 3; rows = (len(tiles) + cols - 1) // cols; H = max(t.height for t in tiles)
    sheet = Image.new("RGB", (W * cols, H * rows), "white")
    for k, t in enumerate(tiles):
        sheet.paste(t, ((k % cols) * W, (k // cols) * H))
    sheet.save(out / "_sheet.jpg", quality=85)
    print("拼图", out / "_sheet.jpg")
else:
    print("一张图也没抓到：官网图常由脚本加载，用浏览器打开页面截图，存成 raw/<名字>.jpg")
