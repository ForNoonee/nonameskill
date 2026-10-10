#!/bin/zsh
# Codex 生成封面：zsh cover.sh <slug>   读 series/<slug>/publish/prompt.txt + ref_cover.jpg → publish/cover.png
# 2026-10-10 修：加 -s workspace-write（以前沙箱只读，图只落在 ~/.codex/generated_images/）；
# 旧 cover.png 先挪成 cover_prev.png，这次没生成出来就报失败，不会拿旧图冒充新图。
D=${NONAME_ROOT:-$PWD}/series/$1/publish; cd $D || exit 1
if grep -q '<[^<>]*>' prompt.txt; then echo "prompt.txt 还有没填的尖括号："; grep -n '<[^<>]*>' prompt.txt; exit 1; fi
[ -f cover.png ] && mv -f cover.png cover_prev.png
mark=$(mktemp)
REF=(); [ -f ref_cover.jpg ] && REF=(-i ref_cover.jpg)   # 风格参考图可选
codex exec --skip-git-repo-check -s workspace-write -C $D $REF - < prompt.txt > codex.log 2>&1
if [ ! -f cover.png ]; then   # 兜底：取这次运行之后 Codex 新生成的最新一张
  for f in $HOME/.codex/generated_images/**/*.png(N.om); do
    [[ $f -nt $mark ]] && { cp "$f" cover.png; echo "（从 $f 拷回）"; }
    break
  done
fi
rm -f $mark
[ -f cover.png ] && echo "OK $D/cover.png（读图逐字核对）" || { echo "封面失败，看 $D/codex.log；上一版在 cover_prev.png"; tail -5 codex.log; exit 1; }
