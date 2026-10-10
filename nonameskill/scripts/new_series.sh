#!/bin/zsh
# 建一期新片的目录：zsh new_series.sh <slug> "<aihot 标题，照 candidates.py 原样复制>"
#   → series/<slug>/{raw/fetch,eps,publish,out} + 构建脚本 + huashu 引擎链接 + 封面风格参考图，
#     并把标题登记进 done.tsv（candidates.py 据此标「样片」，下次不会重复选）。
set -e
ROOT=${NONAME_ROOT:-$PWD};   # 项目根目录：环境变量 NONAME_ROOT，默认当前目录
 SK=$ROOT/.claude/skills/nonameskill
[[ -z $1 || -z $2 ]] && { echo '用法: new_series.sh <slug> "<aihot 标题>"'; exit 1; }
D=$ROOT/series/$1
[ -e $D ] && { echo "已存在: $D"; exit 1; }
# build_huashu.py 借用这两个旧系列的东西（排版工具、huashu 引擎），先检查，免得目录建一半
for dep in $ROOT/series/tesla_2008/build_ep1.py $ROOT/series/tesla_history/huashu_scripts/engine/render.py $ROOT/make_audio_gemini.py; do
  [ -e $dep ] || { echo "缺依赖: $dep"; exit 1; }
done
mkdir -p $D/raw/fetch $D/eps $D/publish $D/out
cp $SK/template/build_huashu.py $D/
cp $SK/template/eps/__init__.py $D/eps/
cp $SK/template/ep01_template.py $D/eps/ep01.py
cp $SK/template/cover_prompt.txt $D/publish/prompt.txt
if [ -f $SK/template/ref_cover.jpg ]; then cp $SK/template/ref_cover.jpg $D/publish/; else echo "提示：template/ 下没有 ref_cover.jpg（封面风格参考图），封面会不带参考图生成；想统一风格就自己放一张"; fi
ln -s ../tesla_history/huashu_scripts $D/huashu_scripts
grep -qF "$2	" $SK/done.tsv 2>/dev/null || printf '%s\t%s\t%s\n' "$2" "$1" "$(date +%F)" >> $SK/done.tsv
echo "OK $D（已登记 done.tsv）"
