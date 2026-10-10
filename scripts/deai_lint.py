"""去 AI 味·口播/文案规则扫描（确定性，先跑它再按 humanizer-zh 改）：
  python deai_lint.py series/<slug>/eps/ep01.py     扫分镜里每句口播
  python deai_lint.py 文案.md                        扫任意文本（按行）
输出每条命中：位置、规则、原句。退出码 = 命中数（0 为干净）。规则说明见 ../references/deai_rules.md。"""
import importlib.util, re, sys
from pathlib import Path

# (规则名, 正则, 说明)
PHRASES = [
    ("新闻腔开头", r"^(?:近日|日前|据悉|重磅|刚刚宣布|正式宣布|正式发布|官宣)", "口播开头别用通稿腔，直接说对观众的事"),
    ("套话连接", r"值得一提的是|总而言之|综上所述|不难看出|众所周知|毫无疑问|让我们|接下来我们|首先.{0,20}其次", "删掉，直接说内容"),
    ("拔高词", r"里程碑|颠覆性?|革命性|新纪元|新时代的大门|赋能|全方位|极致|未来可期|彰显|标志着|划时代|重新定义", "换成具体做了什么/对谁有什么用"),
    ("空对比", r"不只是.{1,15}更是|不仅仅?是.{1,15}更是|与其说.{1,15}不如说", "直接说后半句的重点"),
    ("意味腔", r"这意味着|这标志|这无疑", "换成具体后果"),
    ("书面词", r"迄今|此外|然而|因此|于是乎|(?<![尤极])其(?![实他中余次])(?=[一-鿿]{1,3}(?:的|是|为|在))|该(?:公司|模型|功能|产品)|于(?=\d|[一二三四五六七八九十]+月)", "口播换口语：到现在/另外/但/所以/它"),
    ("模型自述", r"作为(?:一个|一名)?\s*(?:AI|人工智能|语言模型)|希望(?:对你|这)有(?:所)?帮助|以下是", "删"),
    ("模板句", r"最后(?:说|教你)|但这还不是(?:全部|最狠的)|还不是最狠的|所以记住|记住一句话|更关键的是|更反常的是|现在(?:说|教你)那(?:个|一)", "七条规律的固定句式，观众刷多了会认出来；同一规律换具体说法（见 deai_rules.md D 节）"),
    ("惊叹堆叠", r"[！!]{2,}|太.{1,4}了[！!].{0,10}太.{1,4}了", "一个感叹就够"),
]


def _nums(s):
    """数一句里的数字：型号里的（GPT-6、5.5 紧跟英文）不算；“10月7号”这类日期算一个。"""
    s = re.sub(r"\d{1,2}月\d{1,2}[日号]?", "D", s)
    s = re.sub(r"(?<=[A-Za-z\-\s])\d+(?:\.\d+)?(?![%\d])", "", s)
    return re.findall(r"\d+(?:\.\d+)?%?|D", s)


def sentences(text):
    return [s for s in re.findall(r"[^。！？；!?;]+[。！？；!?;]?", text) if s.strip()]


def check(text):
    hits = []
    for name, pat, tip in PHRASES:
        for m in re.finditer(pat, text):
            hits.append((name, m.group(0), tip))
    if len(_nums(text)) > 4:
        hits.append(("整段数字太多", text[:30] + "…", f"{len(_nums(text))} 个数字，一段口播≤4 个；只留最炸的一个讲成人话"))
    for s in sentences(text):
        core = re.sub(r"[，。！？；：、,.!?;: ]", "", s)
        n_cn = len(re.findall(r"[一-鿿]", core))
        longest = max((len(re.findall(r"[\u4e00-\u9fff]", c)) for c in re.split(r"[，、：,:]", s)), default=0)
        if longest > 16 or n_cn > 40:
            hits.append(("句子太长", s.strip(), f"最长分句 {longest} 字/整句 {n_cn} 字：口播分句≤16 字，用逗号断开"))
        nums = _nums(s)
        if len(nums) > 2:
            hits.append(("数字扎堆", s.strip(), f"{len(nums)} 个数字，一句≤2 个，其余放画面"))
        en = [w for w in re.findall(r"[A-Za-z][A-Za-z0-9.\-]*", s) if len(w) > 2]
        if len(en) > 2:
            hits.append(("英文太多", s.strip(), f"{en}：配音容易读不准、听着累，第二次起用「它」"))
    return hits


def check_all(texts):
    """跨句检查：同一开头连用 3 次（机械排比）、口头禅超量。"""
    hits, joined = [], "".join(texts)
    clauses = [c.strip() for c in re.split(r"[，。！？；]", joined) if len(c.strip()) >= 4]
    for i in range(len(clauses) - 2):
        a, b, c = (x[:2] for x in clauses[i:i + 3])
        if a == b == c:
            hits.append(("机械排比", "｜".join(clauses[i:i + 3]), "三个分句同一开头，合并或换说法（有意的排比最多一处）"))
    for w, cap in (("说白了", 1), ("其实", 1), ("真的", 1), ("直接", 2), ("最后", 2)):
        n = joined.count(w)
        if n > cap:
            hits.append(("口头禅超量", w, f"出现 {n} 次，上限 {cap}"))
    return hits


def load(path):
    p = Path(path)
    if p.suffix == ".py":
        sys.path.insert(0, str(p.parent.parent))   # series/<slug>，让 `from eps import R` 能用
        spec = importlib.util.spec_from_file_location("ep_under_lint", p)
        m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        return [(b["k"], b["t"]) for s in m.SEGS for b in s["beats"]]
    return [(f"L{i + 1}", ln) for i, ln in enumerate(p.read_text(encoding="utf-8").splitlines()) if ln.strip()]


if __name__ == "__main__":
    items = load(sys.argv[1])
    total = 0
    for key, text in items:
        for name, frag, tip in check(text):
            print(f"[{key}] {name}：{frag}  → {tip}"); total += 1
    for name, frag, tip in check_all([t for _, t in items]):
        print(f"[全稿] {name}：{frag}  → {tip}"); total += 1
    print(f"共 {total} 处" if total else "干净：没有命中规则（仍要通读一遍）")
    sys.exit(min(total, 99))
