"""列出 aihot 最新热点 + 是否做过：在 sunbin 根目录跑 .venv/bin/python .claude/skills/nonameskill/scripts/candidates.py
状态：[样片:slug] 本流程做过（done.tsv，new_series.sh 自动登记）；[published] 快讯线已发；[error]/[low_hook] 快讯线没做成，也可以选。"""
import os
import json, sys
from pathlib import Path
ROOT = Path(os.environ.get("NONAME_ROOT", Path.cwd()))   # 项目根目录：环境变量 NONAME_ROOT，默认当前目录
sys.path.insert(0, str(ROOT / "auto"))
import pipeline as P
done = json.loads((ROOT / "auto" / "state.json").read_text(encoding="utf-8")).get("done", {})
done_titles = {v.get("title", ""): v.get("status") for v in done.values()}
tsv = ROOT / ".claude" / "skills" / "nonameskill" / "done.tsv"   # 本工作流做过的（手动线不进 state.json）
if tsv.exists():
    for ln in tsv.read_text(encoding="utf-8").splitlines():
        if ln.strip():
            done_titles[ln.split("\t")[0]] = "样片:" + ln.split("\t")[1]
series = [p.name for p in (ROOT / "series").iterdir() if p.is_dir()]
for h in P.api_get("/hot-topics")["items"][:20]:
    st = done_titles.get(h["title"], "")
    print(f"{h.get('latestAt','')[:16]}  源{h.get('sourceCount',0):>2}  {('['+st+']') if st else '[未做]':12} {h['title']}")
    print(f"        原文 {h['links'].get('original','')}")
print("\n已有 series 目录：", ", ".join(sorted(series)))
