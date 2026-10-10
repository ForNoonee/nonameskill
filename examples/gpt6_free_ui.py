"""示例分镜（GPT-6 全员开放那期，去 AI 味后的定稿）。图片文件不随 skill 分发，只用来参考写法。
GPT-6 全员开放 · v2 去 AI 味版（2026-10-10）：针对 dbs-ai-check 的 6 处（开头三件套/三连排比/零信息转场/规则式收尾/拔高/曲线太顺）重写，事实与配图同 ep01。
事实：OpenAI 公告（10/7 付费 Plus/Pro/Business/Enterprise 用 GPT-6 Sol；10/8 Free/Go 用 GPT-6 Luna；Intelligent UI 例子：储蓄计算器、AA 分账、游戏；
联网问题 GPT-6 Instant 比 5.6 Instant 平均早 44% 开始回答；可在网页设置「Layout and visuals」关闭；旧版桌面 App 不支持；免费额度未公布），
经 Search Engine Journal / Business Today / gHacks / TechAIWire 转述一致。截图为 OpenAI 官方示例（经媒体转载）。"""
from eps import R

TITLE = "GPT-6 全员开放：ChatGPT 开始直接给你做工具"
BGM = dict(seed=66, bpm=118)
CR = "图源 OpenAI（经 Business Today）"

SEGS = [
 # 开头：一个例子说细（不再三连排比）；悬念换成具体疑点，不说“最后说”
 dict(id="A", g="y2_vox", beats=[
  dict(k="n01", t="几个人吃饭要AA，你问ChatGPT，它现在不列算式了，直接做一张分账表让你填。免费用户也能用，只是用的不是同一个GPT-6。", cues=[
   (None, dict(kind="image", image=R("ui_bill"), text="ChatGPT 直接生成的 AA 分账工具 · " + CR)),
   ("分账表", dict(kind="point", text="不列算式，直接给分账表")),
   ("不是同一个", dict(kind="point", text="免费版 ≠ 付费版")),
  ])]),
 dict(id="B", g="y5_kinetic_type", beats=[
  dict(k="n02", t="10月7号付费用户先上，8号轮到免费用户，这回是全员开放。", cues=[
   (None, dict(kind="title", text="GPT-6 全员开放", sub="免费用户 10 月 8 日跟进", data=dict(label="ChatGPT", key="全员"))),
  ])]),
 dict(id="C", g="y2_vox", beats=[
  dict(k="n03", t="OpenAI管这个叫智能界面：回答里可以有按钮、表单、图表，用不用，它自己判断。", cues=[
   (None, dict(kind="image", image=R("hero"), text="GPT-6 with Intelligent UI · 图源 OpenAI（经 Gadget Pilipinas）")),
   ("按钮", dict(kind="point", text="按钮 · 表单 · 图表")),
   ("自己判断", dict(kind="point", text="用不用，模型自己定")),
  ])]),
 # 其余例子一句带过，长短错开
 dict(id="D", g="y2_vox", beats=[
  dict(k="n04", t="问自行车怎么变速，它画一张拆解图，点哪儿讲哪儿。问存钱，就给你个计算器。", cues=[
   (None, dict(kind="image", image=R("ui_bike"), text="可点开的自行车拆解图 · " + CR)),
   ("拆解图", dict(kind="point", text="问原理 → 可点的拆解图")),
   ("计算器", dict(kind="point", text="问存钱 → 储蓄计算器")),
  ])]),
 # 转场句自己带信息
 dict(id="E", g="y5_kinetic_type", beats=[
  dict(k="n05", t="速度也变了。要联网查的问题，平均早44%开始回答，边想边说。", cues=[
   (None, dict(kind="title", text="快 44%", sub="联网问题开始回答更快（官方数据）", data=dict(label="GPT-6", key="44%"))),
  ])]),
 # 反差落到具体对比，不拔高
 dict(id="F", g="y5_kinetic_type", beats=[
  dict(k="n06", t="以前算个账、分个账，得专门下个App。现在它在聊天里现做一个。OpenAI的说法是，让软件来适应人。", cues=[
   (None, dict(kind="title", text="少下几个App", sub="让软件适应人（OpenAI）", data=dict(label="OpenAI", key="App"))),
  ])]),
 # 兑现开头的疑点
 dict(id="G", g="y2_vox", beats=[
  dict(k="n07", t="回到那个不同：免费用户拿到的是轻量版，叫Luna；付费的是完整版，叫Sol。免费能用多少次，官方没说。", cues=[
   (None, dict(kind="image", image=R("ui_roast"), text="周日烤羊肉聚餐方案 · 图源 OpenAI（经 Digit）")),
   ("轻量版", dict(kind="point", text="免费：GPT-6 Luna（轻量版）")),
   ("完整版", dict(kind="point", text="付费：GPT-6 Sol")),
   ("多少次", dict(kind="point", text="免费额度：官方未公布")),
  ]),
  dict(k="n08", t="嫌这些界面花哨，网页版设置里能关。", cues=[
   ("设置", dict(kind="point", text="网页设置 · Layout and visuals 可关")),
  ])]),
 # 收尾：留一处真实的不确定，不做规则式总结
 dict(id="H", g="y5_kinetic_type", beats=[
  dict(k="n09", t="免费版到底够不够用，我也说不准。算账、分账这种小事，先拿它试试；写代码，还是付费版稳。转给身边还只拿它聊天的人。", cues=[
   (None, dict(kind="title", text="先拿小事试试", sub="免费额度官方未公布", data=dict(key="小事"))),
  ])]),
]
