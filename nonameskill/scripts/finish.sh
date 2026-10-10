#!/bin/zsh
# 收尾：zsh finish.sh <slug> [ep01]  → 封面叠到片头 0.5 秒（out/<ep>_huashu_cover.mp4）+ 12 帧抽帧拼图 + 配音听写报告
# 第二个参数写定稿的分镜名（去 AI 味后另存为 ep01b 时就写 ep01b）。
ROOT=${NONAME_ROOT:-$PWD};   # 项目根目录：环境变量 NONAME_ROOT，默认当前目录
 D=$ROOT/series/$1; EP=${2:-ep01}; PY=$ROOT/.venv/bin/python
F=$($PY -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())")
cd $D || exit 1
$PY -c "from PIL import Image;Image.open('publish/cover.png').convert('RGB').resize((1080,1920),Image.LANCZOS).save('publish/cover_1080x1920.jpg',quality=95)" || exit 1
$F -y -loglevel error -i out/${EP}_huashu.mp4 -loop 1 -i publish/cover_1080x1920.jpg -filter_complex "[0:v][1:v]overlay=0:0:enable='lt(t,0.5)':shortest=1,format=yuv420p[v]" -map "[v]" -map 0:a -c:v libx264 -crf 18 -c:a copy -movflags +faststart out/${EP}_huashu_cover.mp4 || exit 1
DUR=$($F -i out/${EP}_huashu_cover.mp4 2>&1 | grep -o "Duration: [0-9:.]*" | awk -F'[:.]' '{print $2*3600+$3*60+$4}')
mkdir -p out/check; ins=()
for i in $(seq 0 11); do t=$(( i == 0 ? 0 : (DUR * i / 12) )); [ $i -eq 0 ] && t=0.2
  $F -loglevel error -y -ss $t -i out/${EP}_huashu_cover.mp4 -frames:v 1 -vf "scale=240:-1,drawtext=text='${t}s':x=6:y=6:fontsize=22:fontcolor=red:box=1:boxcolor=white" out/check/f_$i.jpg 2>/dev/null \
  || $F -loglevel error -y -ss $t -i out/${EP}_huashu_cover.mp4 -frames:v 1 -vf scale=240:-1 out/check/f_$i.jpg
  ins+=(-i out/check/f_$i.jpg); done
$F -loglevel error -y $ins -filter_complex "[0][1][2][3][4][5]hstack=6[a];[6][7][8][9][10][11]hstack=6[b];[a][b]vstack" out/check/${EP}_grid.jpg
echo "成片 $D/out/${EP}_huashu_cover.mp4  时长 ${DUR}s"
echo "抽帧 $D/out/check/${EP}_grid.jpg"
echo "--- Charon 配音听写（err>0.25 要人工听/改稿；只含当前分镜的句子）---"
$PY $ROOT/.claude/skills/nonameskill/scripts/asr_check.py $D $EP || true
