"""<题目>（<日期>，nonameskill 七条规律）。
事实（逐条写来源，后面改稿只许用这里的事实）：
- …… —— 来源
截图/图片来源：……
范例：series/gpt6_ui/eps/ep01b.py（去 AI 味后的定稿）。尖括号里写的是这一段要达到的目的，不是要照抄的句子；
「最后说」「但这还不是全部」「现在说那个坑」「所以记住」这类固定句式不要用，deai_lint 会标成模板句。"""
from eps import R

TITLE = "<主标题：先让人看到对自己有什么用，反差只是手段>"
BGM = dict(seed=66, bpm=118)
CR = "图源 <官方>（经 <媒体>）"

# 每段 g 只用这四种语法：y2_vox（图片 + 便签 point）、y5_kinetic_type（黄底大字 title）、t3_finance_chart（柱状图）、y1_kurzgesagt（少用）。
# cue 的锚点（元组第一个元素）必须原样出现在本句口播 t 里；None = 本句一开始。占位没填完，build_huashu.py 会拒绝运行。
SEGS = [
 # ① 最好的画面先上：一个具体例子说细（不要三连排比）；② 埋一个具体的疑点，在 G 段兑现
 dict(id="A", g="y2_vox", beats=[
  dict(k="n01", t="<一个生活场景 + 它现在怎么帮你，说细>。<一个具体的疑点，比如「免费也能用，只是用的不是同一个版本」>。", cues=[
   (None, dict(kind="image", image=R("<最抓眼的图>"), text="<图说> · " + CR)),
   ("<锚点>", dict(kind="point", text="<便签短句>")),
  ])]),
 # 标题兑现：谁、什么时候、对谁开放
 dict(id="B", g="y5_kinetic_type", beats=[
  dict(k="n02", t="<是什么事：谁、什么时候、对谁开放>。", cues=[
   (None, dict(kind="title", text="<大字≤8字>", sub="<小字>", data=dict(label="<品牌>", key="<大字里要高亮的词>"))),
  ])]),
 # ③ 它到底是什么，说成大白话（功能名说中文，画面上可以留英文）
 dict(id="C", g="y2_vox", beats=[
  dict(k="n03", t="<一句话说清它是什么、谁来决定用不用>。", cues=[
   (None, dict(kind="image", image=R("<图>"), text="<图说> · " + CR)),
   ("<锚点>", dict(kind="point", text="<要点>")),
  ])]),
 # ③ 其余例子一句带过，和 A 段长短错开
 dict(id="D", g="y2_vox", beats=[
  dict(k="n04", t="<例子2，稍细>。<例子3，一句话>。", cues=[
   (None, dict(kind="image", image=R("<图>"), text="<图说> · " + CR)),
   ("<锚点>", dict(kind="point", text="<场景 → 结果>")),
  ])]),
 # 中段续命：转场句本身带新信息（如「速度也变了」）；④ 全片只留这一个最炸的数字做大字卡
 dict(id="E", g="y5_kinetic_type", beats=[
  dict(k="n05", t="<带信息的转场>。<一个数字，换成人话>。", cues=[
   (None, dict(kind="title", text="<数字>", sub="<口径，标官方数据>", data=dict(label="<品牌>", key="<数字>"))),
  ])]),
 # ⑥ 反差落到具体对比（以前要……，现在……），观点说成观点，不拔高
 dict(id="F", g="y5_kinetic_type", beats=[
  dict(k="n06", t="<以前怎样>。<现在怎样>。<官方原话或一句观点>。", cues=[
   (None, dict(kind="title", text="<对比结论≤8字>", sub="<依据>", data=dict(label="<品牌>", key="<词>"))),
  ])]),
 # 兑现 A 段的疑点，用词和 A 段对上
 dict(id="G", g="y2_vox", beats=[
  dict(k="n07", t="<回到 A 段那个疑点，给出答案；官方没说的就直说没说>。", cues=[
   (None, dict(kind="image", image=R("<图>"), text="<图说> · " + CR)),
   ("<锚点>", dict(kind="point", text="<便签>")),
  ])]),
 # ⑤ 收尾：留一处真实的不确定 + 可照做的建议 + 转发给具体的人（每期换对象和理由）
 dict(id="H", g="y5_kinetic_type", beats=[
  dict(k="n08", t="<一处真实的不确定>。<什么情况先试什么>。转给<具体的人>。", cues=[
   (None, dict(kind="title", text="<可转述的建议≤8字>", sub="<一句话补充>", data=dict(key="<词>"))),
  ])]),
]
