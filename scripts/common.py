"""nonameskill 公共工具：目录约定、ffmpeg、中文字体、文字排版、渲染引擎定位。

环境变量（都可选）：
  NONAME_WORKSPACE  成片工作区，默认 ./noname-videos（每期一个子目录）
  NONAME_FONT       字幕用的中文字体文件（.ttf/.ttc），默认按系统自动找
  HUASHU_ENGINE     huashu-art-motion 引擎目录（含 render.py），默认在常见 skill 安装位置里找
  NONAME_MUSIC_DIR  背景音乐文件夹（mp3/wav/m4a），不设就不加 BGM
"""
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATES = SKILL_DIR / "templates"


def workspace():
    return Path(os.environ.get("NONAME_WORKSPACE") or (Path.cwd() / "noname-videos")).expanduser().resolve()


def episode_dir(arg):
    """接受「期目录路径」或「工作区里的 slug」。"""
    p = Path(arg).expanduser()
    if p.is_dir():
        return p.resolve()
    q = workspace() / arg
    if q.is_dir():
        return q
    sys.exit(f"找不到这一期的目录：{arg}（也不在工作区 {workspace()} 里）")


# ---------- ffmpeg ----------
def ffmpeg():
    p = shutil.which("ffmpeg")
    if p:
        return p
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        sys.exit("找不到 ffmpeg：请安装（macOS: brew install ffmpeg；Ubuntu: apt install ffmpeg）或 pip install imageio-ffmpeg")


def ffmpeg_env():
    """渲染引擎直接调用 PATH 里的 `ffmpeg`；系统没装时，把 imageio-ffmpeg 的二进制以 `ffmpeg` 名字挂到临时 PATH 上。"""
    env = dict(os.environ)
    if shutil.which("ffmpeg"):
        return env
    exe = ffmpeg()
    shim = Path.home() / ".cache" / "nonameskill" / "bin"
    shim.mkdir(parents=True, exist_ok=True)
    link = shim / ("ffmpeg.exe" if os.name == "nt" else "ffmpeg")
    if not link.exists():
        try:
            link.symlink_to(exe)
        except OSError:
            shutil.copy2(exe, link)
    env["PATH"] = str(shim) + os.pathsep + env.get("PATH", "")
    return env


def run(cmd):
    cmd = [ffmpeg() if c == "ffmpeg" else c for c in cmd]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(" ".join(map(str, cmd))[:300] + "\n" + r.stderr[-1500:])
    return r


def duration(path):
    """媒体时长（秒）。不依赖 ffprobe（imageio-ffmpeg 不带它）。"""
    r = subprocess.run([ffmpeg(), "-i", str(path)], capture_output=True, text=True)
    m = re.search(r"Duration: (\d+):(\d+):(\d+(?:\.\d+)?)", r.stderr)
    if not m:
        raise RuntimeError(f"读不到时长：{path}")
    h, mi, s = m.groups()
    return int(h) * 3600 + int(mi) * 60 + float(s)


# ---------- 字体与排版 ----------
_FONTS = [
    "/System/Library/Fonts/STHeiti Medium.ttc", "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc", "/Library/Fonts/Arial Unicode.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", "/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "C:/Windows/Fonts/msyhbd.ttc", "C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simhei.ttf",
]


def cjk_font_path():
    for f in [os.environ.get("NONAME_FONT")] + _FONTS:
        if f and Path(f).exists():
            return f
    sys.exit("找不到中文字体：请设置环境变量 NONAME_FONT 指向一个 .ttf/.ttc 中文字体文件")


def font(size):
    from PIL import ImageFont
    return ImageFont.truetype(cjk_font_path(), size)


NO_LEAD = set("，。、：；！？）”’…—,.:;!?)")
_TOK = re.compile(r"[A-Za-z0-9][A-Za-z0-9'’\-\.,%$&/]*|\s+|.", re.S)


def wrap(draw, text, fnt, maxw):
    """按词元换行：英文单词/数字整体不拆、中文逐字；按总宽度均分行，标点不放行首。"""
    toks = list(_TOK.findall(text.strip()))
    total = draw.textlength("".join(toks), font=fnt)
    n = max(1, -(-int(total) // int(maxw)))
    lines = []
    for _ in range(6):
        target = total / n
        lines, cur = [], ""
        for i, t in enumerate(toks):
            nxt = toks[i + 1] if i + 1 < len(toks) else ""
            if cur and draw.textlength(cur + t, font=fnt) > maxw:
                lines.append(cur.rstrip())
                cur = t.lstrip()
            else:
                cur += t
            if len(lines) < n - 1 and draw.textlength(cur, font=fnt) >= target and nxt[:1] not in NO_LEAD and nxt.strip():
                lines.append(cur.rstrip())
                cur = ""
        if cur.strip():
            lines.append(cur.rstrip())
        if all(draw.textlength(l, font=fnt) <= maxw + 1 for l in lines):
            return lines
        n += 1
    return lines


def text_block(draw, xy, text, fnt, fill, maxw, spacing=1.25, anchor_center=False):
    x, y = xy
    for ln in wrap(draw, text, fnt, maxw):
        w = draw.textlength(ln, font=fnt)
        draw.text((x - w / 2 if anchor_center else x, y), ln, font=fnt, fill=fill)
        y += int(fnt.size * spacing)
    return y


# ---------- 渲染引擎 ----------
def huashu_engine():
    """返回 huashu-art-motion 的 render.py 路径。安装：npx skills add alchaincyf/huashu-art-motion"""
    cands = [os.environ.get("HUASHU_ENGINE")] + [str(Path(b).expanduser() / "huashu-art-motion" / "scripts" / "engine") for b in (
        "~/.claude/skills", "~/.agents/skills", "~/.codex/skills", str(Path.cwd() / ".claude" / "skills"),
        str(Path.cwd() / ".agents" / "skills"), str(SKILL_DIR.parent))]
    for c in cands:
        if c and (Path(c) / "render.py").exists():
            return Path(c) / "render.py"
    sys.exit("找不到 huashu-art-motion 渲染引擎：先安装 `npx skills add alchaincyf/huashu-art-motion`，"
             "或设置 HUASHU_ENGINE 指向它的 scripts/engine 目录")
