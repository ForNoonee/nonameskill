"""列出 aihot 最新热点，并标出本工作区做过的选题。

  python candidates.py              # 热点榜前 20 条：时间、来源数、是否做过、标题、原文链接
  python candidates.py --story 3    # 看第 3 条的事件摘要和相关报道链接（核实时用）
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import aihot  # noqa: E402
from common import workspace  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--story", type=int, help="展开第 N 条（从 1 数）的事件详情")
ap.add_argument("-n", type=int, default=20)
a = ap.parse_args()

items = aihot.hot_topics()[: a.n]
done = {}
reg = workspace() / "done.tsv"
if reg.exists():
    for ln in reg.read_text(encoding="utf-8").splitlines():
        if ln.strip():
            title, slug = (ln.split("\t") + [""])[:2]
            done[title] = slug

if a.story:
    h = items[a.story - 1]
    print("=====", h["title"], "| 来源", h.get("sourceCount", 0), "|", "、".join(h.get("sourceNames", [])[:8]))
    s = aihot.story(h)
    if not s:
        print("（这条没有事件聚合，只有原文）", (h.get("links") or {}).get("original", ""))
        sys.exit(0)
    print(s.get("digest") or "")
    for r in (s.get("reports") or [])[:15]:
        print("  -", (r.get("title") or "")[:80], (r.get("links") or {}).get("original", ""))
    sys.exit(0)

for i, h in enumerate(items, 1):
    st = f"[样片:{done[h['title']]}]" if h["title"] in done else "[未做]"
    print(f"{i:>2}. {h.get('latestAt', '')[:16]}  源{h.get('sourceCount', 0):>2}  {st:14} {h['title']}")
    print(f"        原文 {(h.get('links') or {}).get('original', '')}")
print(f"\n工作区：{workspace()}（做过的选题记在 done.tsv）")
