"""本期配图：全部用代码画（HTML → Chrome 截图），内容取自用户自己的 nonameskill 文件和官方原文。
用法：../../.venv/bin/python make_cards.py   → raw/skill_md.jpg tree.jpg desc_compare.jpg why_line.jpg
"""
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE = Path(__file__).parent
RAW = HERE / "raw"
W, H = 1280, 860

BASE = """<html><head><meta charset="utf-8"><style>
*{margin:0;padding:0;box-sizing:border-box}
body{width:%dpx;height:%dpx;background:#1d1b19;color:#ece6dc;font-family:"PingFang SC","Hiragino Sans GB",sans-serif;
  display:flex;flex-direction:column;overflow:hidden}
.bar{height:64px;background:#2a2724;display:flex;align-items:center;padding:0 28px;gap:12px;font-size:26px;color:#a59d92}
.dot{width:16px;height:16px;border-radius:50%%}
.file{margin-left:18px;font-family:Menlo,monospace;color:#ece6dc}
.body{flex:1;padding:36px 44px;font-size:36px;line-height:1.55}
.mono{font-family:Menlo,"PingFang SC",monospace}
.ln{display:flex;gap:26px}
.no{width:44px;text-align:right;color:#6b645b;font-family:Menlo,monospace;flex:none}
.hl{background:rgba(232,131,58,.18);border-left:6px solid #e8833a;margin-left:-44px;padding-left:38px}
.key{color:#e8a35f}.dim{color:#8c847a}.or{color:#f0954a;font-weight:700}
.foot{position:absolute;bottom:22px;right:34px;font-size:22px;color:#8c847a}
</style></head><body>%s</body></html>"""

BAR = ('<div class="bar"><span class="dot" style="background:#e0605a"></span><span class="dot" style="background:#e3b341"></span>'
       '<span class="dot" style="background:#5bbf61"></span><span class="file">%s</span></div>')


def ln(no, html, hl=False):
    return f'<div class="ln{" hl" if hl else ""}"><span class="no">{no}</span><span>{html}</span></div>'


CARDS = {
    # A 段：nonameskill 的开头两行（name + description），大字少行，手机上要看得清
    "skill_md": BAR % "nonameskill / SKILL.md" + '<div class="body mono" style="font-size:54px;line-height:1.5;padding-top:30px">' + "".join([
        ln(1, '<span class="dim">---</span>'),
        ln(2, '<span class="key">name:</span> nonameskill', True),
        ln(3, '<span class="key">description:</span><br>1 分钟 AI/科技爆款短视频<br>固定工作流……用户说<br>「<span class="or">按那套流程做一期</span>」…时使用。', True),
        ln(4, '<span class="dim">---</span>'),
    ]) + '</div><div class="foot" style="font-size:28px">我的 Skill 文件（节选）</div>',

    # C 段：文件夹结构
    "tree": BAR % "nonameskill/" + '<div class="body mono" style="font-size:58px;line-height:1.6;padding-top:36px">'
    '<div><span class="or">nonameskill/</span></div>'
    '<div>├ <b>SKILL.md</b>　<span class="key">139 行</span></div>'
    '<div>├ scripts/　<span class="key">7 个脚本</span></div>'
    '<div>├ references/</div>'
    '<div>└ template/</div>'
    '</div>',

    # E 段：简介写法对比
    "desc_compare": BAR % "description 怎么写" + '<div class="body" style="font-size:52px;padding-top:30px;line-height:1.4">'
    '<div style="color:#e0605a;font-size:44px;font-weight:700">✗ AI 想不起来用</div>'
    '<div style="margin:10px 0 34px;padding:20px 28px;background:#2a2724;border-radius:12px">帮我处理工作。</div>'
    '<div style="color:#5bbf61;font-size:44px;font-weight:700">✓ 写你平时怎么叫它</div>'
    '<div style="margin:10px 0 30px;padding:20px 28px;background:#2a2724;border-radius:12px">……用户说「<span class="or">按那套流程做一期</span>」…时使用。</div>'
    '<div style="font-size:34px;color:#a59d92">官方：简介写得“强势”点，Claude 容易漏用（skill-creator）</div>'
    '</div>',

    # F 段：我文件里真实的一句 + 官方「讲为什么」
    "why_line": BAR % "nonameskill / SKILL.md · 第 2 步" + '<div class="body" style="font-size:54px;padding-top:36px;line-height:1.5">'
    '<div class="ln hl" style="margin-left:0;padding:22px 30px">'
    '<span>不能靠排列位置猜编号<br><span class="or">（2026-10-10 因此连续两次放错图）</span></span></div>'
    '<div style="margin-top:36px;font-size:36px;color:#a59d92;line-height:1.45">官方 skill-creator：<br>'
    '<span style="color:#ece6dc">“explain to the model why things are important in lieu of heavy-handed musty MUSTs”</span></div>'
    '</div>',
}

HEIGHT = dict(skill_md=640, tree=640, desc_compare=690, why_line=640)   # 按内容裁高，别留大片空底


def main():
    RAW.mkdir(exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome")
        pg = b.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        for name, html in CARDS.items():
            h = HEIGHT.get(name, H)
            pg.set_viewport_size({"width": W, "height": h})
            pg.set_content(BASE % (W, h, html))
            pg.wait_for_timeout(200)
            out = RAW / f"{name}.jpg"
            pg.screenshot(path=str(out), type="jpeg", quality=92)
            print("OK", out)
        b.close()


if __name__ == "__main__":
    main()
