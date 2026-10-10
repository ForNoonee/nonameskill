"""示例分镜（Claude 文档/幻灯片/设计转正那期）。图片文件不随 skill 分发，只用来参考写法。
Claude 文档/幻灯片/设计转正、免费版可用 + Dashboards / Motion 测试（2026-10-10，nonameskill 七条规律）。
事实（逐条写来源，后面改稿只许用这里的事实）：
- 2026-10-08 发布，标题 "Build live dashboards and animate explainers with Claude" —— claude.com/blog/dashboards-and-motion（官方）
- Docs、Slides、Design 结束 beta，"available on every plan, including Free" —— 官方博客；claude.com/product/design 同说法；The Decoder 转述一致
- 9 月 16 日推出时 "All three are in beta on paid plans" —— claude.com/blog/cowork-is-now-claude（官方）
- 用户在 Claude 里做了超过 4500 万份文档、幻灯片和设计（"more than 45 million docs, decks, and designs"）—— 官方博客；The Decoder 转述一致
- 幻灯片：说要什么，Claude 起草；可直接改、在 Claude 里演示；导出 PowerPoint、PDF 保留格式；可转成 Google Slides 继续编辑；手机 App 可编辑 —— 官方博客 + cowork-is-now-claude
- Dashboards：付费计划 beta；连接数据平台或 CRM（Redshift、BigQuery、ClickHouse、Databricks、Snowflake、Salesforce）；数据变了看板跟着更新；点任意数字可看背后的查询 —— 官方博客
- Motion：仅 Team、Enterprise 计划 beta；Claude 写代码让文字、图表、形状、图片动起来；"doesn't use a video generation model"，没有生成画面、没有 AI 生成的人；可改任意文字、数字、时间点；导出 MP4；在输入框打 /motion 调出 —— 官方博客
- 用量上限、价格：官方未公布 —— 官方博客未提
截图/图片来源：claude.com 官方博客配图（看板、/motion 菜单）、claude.com/product/design 官方演示视频截帧、claude.com/features/artifacts 官方视频封面。"""
from eps import R

TITLE = "Claude 免费版也能做PPT了：一句话起初稿，导出格式不乱"
BGM = dict(seed=66, bpm=118)
CR = "图源 Claude 官网"

SEGS = [
 # ① 最好的画面先上：官方设计界面；② 疑点：刷屏的那个功能你多半用不上（G 段兑现）
 dict(id="A", g="y2_vox", beats=[
  dict(k="n01", t="要做个PPT、做张设计稿，跟Claude说一句，它先给你起一版，免费版就能用。倒是这次最抢眼的那个功能，你多半用不上。", cues=[
   (None, dict(kind="image", image=R("design_ui"), text="Claude 一句话起草的设计稿 · " + CR)),
   ("起一版", dict(kind="point", text="一句话 → 一版初稿")),
   ("用不上", dict(kind="point", text="最抢眼的那个，先卖个关子")),
  ])]),
 # 标题兑现：谁、什么时候、对谁开放
 dict(id="B", g="y5_kinetic_type", beats=[
  dict(k="n02", t="10月8号，文档、幻灯片、设计这三样转正了。上个月，它们还只在付费版里测试。", cues=[
   (None, dict(kind="title", text="免费版\n也能做PPT", sub="文档 · 幻灯片 · 设计\n10 月 8 日转正", data=dict(label="Claude", key="免费版"))),
  ])]),
 # ③ 怎么用：一个场景说细
 dict(id="C", g="y2_vox", beats=[
  dict(k="n03", t="比如明天要汇报，把材料丢给它，让它做成PPT。起完稿直接在上面改，改好导出PPT或PDF，格式不乱。", cues=[
   (None, dict(kind="image", image=R("deck_prompt"), text="「把发布资料做成汇报 PPT」· " + CR)),
   ("直接在上面改", dict(kind="point", text="在它的稿子上直接改")),
   ("格式不乱", dict(kind="point", text="导出 PowerPoint / PDF 保留格式")),
  ])]),
 # ③ 付费用户多的那一样，一句带过
 dict(id="E", g="y2_vox", beats=[
  dict(k="n05", t="付费用户还多一样：连上公司的数据库或客户系统，用大白话问，它就搭个数据看板。数据一变，图跟着变。", cues=[
   (None, dict(kind="image", image=R("dashboard"), text="Claude 搭的数据看板（测试版）· " + CR)),
   ("大白话", dict(kind="point", text="大白话提问 → 数据看板")),
   ("图跟着变", dict(kind="point", text="数据一变，看板自动更新")),
  ])]),
 # ⑥ 反差：刷屏的动画是代码画的，落到我们自己身上
 dict(id="F", g="y5_kinetic_type", beats=[
  dict(k="n06", t="最抢眼的是动画功能：报告、图表，一句话变成短动画。它没用视频模型，画面是Claude写代码做的。我们这条视频，也是代码画的。", cues=[
   (None, dict(kind="title", text="代码画的动画", sub="不用视频模型、没有 AI 生成的人（官方）", data=dict(label="Claude", key="代码"))),
  ])]),
 # 兑现 A 段的疑点
 dict(id="G", g="y2_vox", beats=[
  dict(k="n07", t="可它只开给团队版和企业版。个人用户，哪怕交了钱，目前也用不上。", cues=[
   (None, dict(kind="image", image=R("motion_menu"), text="输入 /motion 调出动画（团队版、企业版）· " + CR)),
   ("团队版和企业版", dict(kind="point", text="动画：只限团队版 / 企业版")),
  ])]),
 # ⑤ 收尾：真实的不确定（用量没公布）→ 由此推出的建议（别等交差前才第一次用）→ 转发对象
 dict(id="H", g="y5_kinetic_type", beats=[
  dict(k="n08", t="免费版能用多少次，官方没写。所以别等交差前一晚才第一次用，这周先拿份旧材料练练手。转给每次汇报前都在赶PPT的同事。", cues=[
   (None, dict(kind="title", text="拿旧材料练手", sub="免费版用量官方未公布", data=dict(key="练手"))),
  ])]),
]
