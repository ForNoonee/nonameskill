"""收尾：python finish.py <期目录或slug> [ep01]

1. 把 publish/cover.png 叠在片头 0.5 秒 → out/<ep>_cover.mp4（平台默认取首帧当封面）
2. 均匀抽 12 帧拼成 out/check/<ep>_grid.jpg，每帧标时间，供逐帧检查
3. 跑一遍配音听写自检（asr_check.py）"""
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

if len(sys.argv) < 2:
    sys.exit(__doc__)
D = C.episode_dir(sys.argv[1]); EP = sys.argv[2] if len(sys.argv) > 2 else "ep01"
src, cover = D / "out" / f"{EP}.mp4", D / "publish" / "cover.png"
if not src.exists():
    sys.exit(f"没有成片 {src}：先跑 build.py")
final = D / "out" / f"{EP}_cover.mp4"
if cover.exists():
    jpg = D / "publish" / "cover_1080x1920.jpg"
    Image.open(cover).convert("RGB").resize((1080, 1920), Image.LANCZOS).save(jpg, quality=95)
    C.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-loop", "1", "-i", str(jpg), "-filter_complex",
           "[0:v][1:v]overlay=0:0:enable='lt(t,0.5)':shortest=1,format=yuv420p[v]", "-map", "[v]", "-map", "0:a",
           "-c:v", "libx264", "-crf", "18", "-c:a", "copy", "-movflags", "+faststart", str(final)])
else:
    print("没有 publish/cover.png，先不叠封面")
    final = src
dur = C.duration(final)
chk = D / "out" / "check"; chk.mkdir(parents=True, exist_ok=True)
tiles = []
for i in range(12):
    t = 0.2 if i == 0 else dur * i / 12
    f = chk / f"f_{i}.jpg"
    C.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{t:.2f}", "-i", str(final), "-frames:v", "1", "-vf", "scale=240:-1", str(f)])
    im = Image.open(f).convert("RGB"); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 64, 22), fill="white"); d.text((5, 5), f"{t:.1f}s", fill="red")
    tiles.append(im)
w, h = tiles[0].size
grid = Image.new("RGB", (w * 6, h * 2), "white")
for k, im in enumerate(tiles):
    grid.paste(im, ((k % 6) * w, (k // 6) * h))
grid.save(chk / f"{EP}_grid.jpg", quality=88)
print(f"成片 {final}  时长 {dur:.1f}s")
print(f"抽帧 {chk / (EP + '_grid.jpg')}")
print("--- 配音听写（err>0.25 要人工听/改稿）---", flush=True)
subprocess.run([sys.executable, str(Path(__file__).with_name("asr_check.py")), str(D), EP])
