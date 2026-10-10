"""Skill 小白入门 + 介绍用户自己的 nonameskill · v2 去 AI 味版（2026-10-10）：针对 dbs-ai-check 的跨期模板句（「回到…」「我也说不准」）和后半段连串祈使句重写，事实与配图同 ep01。
事实（逐条写来源，后面改稿只许用这里的事实）：
- Anthropic 2025-10-16 推出 Skills（Claude 应用、API、Claude Code）—— claude.com/blog/skills（官方）
- 2025-12-18 把 Agent Skills 作为开放标准发布，规范在 agentskills.io —— 同页官方更新说明；agentskills.io「originally developed by Anthropic, released as an open standard」
- 支持的工具含 Claude Code、ChatGPT & Codex、Cursor、Gemini CLI、GitHub Copilot、VS Code、Junie、TRAE、Kiro 等 —— agentskills.io 官方客户端列表
- 一个 Skill = 一个文件夹 + 一份 SKILL.md，至少有 name 和 description，可带 scripts/references/assets —— agentskills.io
- 渐进加载：启动时只读每个 Skill 的名字和简介；任务对上简介才读整份 SKILL.md；脚本/参考文件用到才打开 —— agentskills.io「How do Agent Skills work?」
- 「Claude has a tendency to "undertrigger" skills … make the skill descriptions a little bit "pushy"」—— Anthropic skill-creator SKILL.md 原文（github.com/anthropics/skills）
- 「explain to the model why things are important in lieu of heavy-handed musty MUSTs」—— 同上
- 用户的 nonameskill：SKILL.md 139 行、scripts/ 7 个脚本、references/ 去 AI 味规则、template/ 模板；硬规矩「只出样片，不发布」「停在发布前」；
  第 2 步写着「不能靠排列位置猜编号（2026-10-10 因此连续两次放错图）」；10-10 当天改过多轮（换 Charon、删模板句、改封面脚本等，见 memory）—— 本机文件
- 本机 ~/.claude/skills 48 个 + 项目 4 个 ≈ 五十来个 —— 本机目录
- 本期是用户贴文章 +「帮我做一期」，由 nonameskill 带着做的 —— 本会话
- 「说到第三遍就写成 Skill」是原文作者的经验说法，口播里当建议讲，不当事实
截图/图片来源：全部用代码画（make_cards.py），内容取自 nonameskill 本机文件和 skill-creator 官方原文；没有用网上配图。"""
from eps import R

TITLE = "一个文件，让AI记住你的活：Skill 小白入门"
BGM = dict(seed=66, bpm=118)

SEGS = [
 # ① 最好的画面先上：这条片子本身就是 Skill 做的；② 疑点「开头那两行」在 E 段兑现
 dict(id="A", g="y2_vox", beats=[
  dict(k="n01", t="这条视频，我就丢给AI一篇文章，说了句“帮我做一期”，它照着一个文件，从找图做到配音。", cues=[
   (None, dict(kind="image", image=R("skill_md"), text="我的 Skill：nonameskill（节选）")),
   ("帮我做一期", dict(kind="point", text="我只说了一句：帮我做一期")),
  ]),
  dict(k="n02", t="这种文件谁都能写，可不少人写完，AI压根不用，毛病就在开头两行。", cues=[
   ("开头两行", dict(kind="point", text="毛病在开头两行")),
  ])]),
 # 是什么、谁做的、谁能用
 dict(id="B", g="y5_kinetic_type", beats=[
  dict(k="n03", t="它叫Skill，Claude去年推出，后来成了通用格式，别家AI也认。", cues=[
   (None, dict(kind="title", text="它叫 Skill", sub="去年推出 · 已成通用格式", data=dict(label="Claude", key="Skill"))),
  ])]),
 # ③ 大白话讲结构，拿我的 nonameskill 当实物
 dict(id="C", g="y2_vox", beats=[
  dict(k="n04", t="说穿了就是个文件夹，放一份说明：开头两行写它叫啥、啥时候用，下面写步骤。", cues=[
   (None, dict(kind="image", image=R("tree"), text="我的 nonameskill 目录")),
   ("开头两行", dict(kind="point", text="名字 + 什么时候用")),
  ]),
  dict(k="n05", t="我这份一百三十多行，带7个脚本，最后一步写死：停在发布前，等我点头。", cues=[
   ("7个脚本", dict(kind="point", text="139 行 + 7 个脚本")),
   ("停在发布前", dict(kind="point", text="不自己发，等我点头")),
  ])]),
 # 中段续命：机制本身就是新信息
 dict(id="D", g="y5_kinetic_type", beats=[
  dict(k="n06", t="AI平时只看每份说明那两行，对上了才往下翻，所以装五十来个也不挤。", cues=[
   (None, dict(kind="title", text="先看简介", sub="对上了，才读全文", data=dict(label="Agent Skills", key="简介"))),
  ])]),
 # 兑现 A 段的疑点：用词「那两行」对上
 dict(id="E", g="y2_vox", beats=[
  dict(k="n07", t="那两行只写“帮我处理工作”，它多半想不起来用。我写的是平时怎么叫它：“按那套流程做一期”。", cues=[
   (None, dict(kind="image", image=R("desc_compare"), text="简介写法对比 · 官方原文出自 Anthropic skill-creator")),
   ("帮我处理工作", dict(kind="point", text="太泛：AI 想不起来用")),
   ("按那套流程", dict(kind="point", text="简介里写你平时的说法")),
  ])]),
 # ⑥ 站队的判断：别光写「必须」
 dict(id="F", g="y2_vox", beats=[
  dict(k="n08", t="步骤里也没光写“必须”。比如别按位置猜图，后面跟着原因：上回因为这个，连放错两次。", cues=[
   (None, dict(kind="image", image=R("why_line"), text="我的 SKILL.md 第 2 步 · 官方原文出自 skill-creator")),
   ("跟着原因", dict(kind="point", text="官方：讲清为什么")),
   ("连放错两次", dict(kind="point", text="规矩 + 吃过的亏")),
  ])]),
 # ④ 全片唯一大字数字；⑤ 收尾：真实的不确定 + 建议 + 转发对象
 dict(id="H", g="y5_kinetic_type", beats=[
  dict(k="n09", t="同一段话跟AI说到第三遍，就值得写下来。先挑一件每周都做的活，写个十几行试试。头一版多半不好使，我这份也改了好几轮。转给天天给AI贴提示词的同事。", cues=[
   (None, dict(kind="title", text="说到第 3 遍", sub="就把它写成 Skill", data=dict(key="3"))),
  ])]),
]
