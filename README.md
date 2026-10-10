# nonameskill：一句话，让 AI 出一条 1 分钟科技短视频

一个 [Agent Skill](https://agentskills.io)：装好后，跟你的 AI 编程助手（Claude Code 等支持 skills 的 agent）说一句「按那套流程做一期」，它就照着 `SKILL.md` 一步步走：

选热点 → 选题诊断 → 核实官方来源 → 抓官方截图 → 按「七条爆款规律」写分镜 → 去 AI 味 → 配音并逐段听写自检 → 代码渲染画面 → 生成封面 → 抽帧检查 → **交付样片，停在发布前**

画面全部由代码逐帧绘制（不用视频生成模型），口播是中文，成片 1080×1920 竖屏、约 1 分钟。

## 安装

```bash
# 1. 装这个 skill（任选一种）
npx skills add ForNoonee/nonameskill
#    或手动：git clone 后把整个文件夹复制到 ~/.claude/skills/nonameskill

# 2. 装渲染引擎（另一个开源 skill，MIT）
npx skills add alchaincyf/huashu-art-motion

# 3. 装 Python 依赖（Python 3.10+）
pip install -r ~/.claude/skills/nonameskill/requirements.txt

# 4. 自检：缺什么会逐项提示
python ~/.claude/skills/nonameskill/scripts/doctor.py
```

另外需要：**ffmpeg**、**Google Chrome**（渲染引擎调用系统 Chrome），以及一个 **Gemini API key**（[Google AI Studio](https://aistudio.google.com/api-keys) 免费申请）。key 请自己写进 `~/.config/gemini/api_key`，或设环境变量 `GEMINI_API_KEY`。**不要把 key 发给 AI，也不要提交进仓库。**

## 用法

在任意项目里跟 agent 说：

- 「nonameskill，选一期最新的 AI 热点做个样片」
- 「按那套流程，把这条新闻做成 1 分钟视频：<链接>」

成片放在当前目录的 `noname-videos/<slug>/out/` 下（可用 `NONAME_WORKSPACE` 改）。

## 可选配置

| 环境变量 | 作用 |
| --- | --- |
| `NONAME_WORKSPACE` | 成片工作区，默认 `./noname-videos` |
| `GEMINI_API_KEY` / `GEMINI_API_KEYS` | Gemini key（多个用逗号分隔，会轮流用）；也可放在 `~/.config/gemini/api_key`、`api_key2`…… |
| `GEMINI_TTS_MODELS` | 固定配音模型，例如 `gemini-3.8-flash-lite-tts` |
| `HUASHU_ENGINE` | 渲染引擎目录（不在默认 skill 目录时设置） |
| `NONAME_FONT` | 字幕中文字体文件（找不到系统字体时设置） |
| `NONAME_MUSIC_DIR` | 背景音乐文件夹；不设就不加 BGM。请只放你有授权的曲子 |
| `VOICE=edge` | 改用 edge-tts 备用配音（需 `pip install edge-tts`） |

封面：装了 [Codex CLI](https://github.com/openai/codex) 会自动生成；没装就输出提示词，用任意图像工具出图。想统一风格，可以在 `templates/` 放一张**你自己有版权的** `ref_cover.jpg`，每期会自动带上作为参考。

搭配使用效果更好（可选，没装也能跑）：[dbskill](https://github.com/dontbesilent2025/dbskill)（`dbs-content` 选题诊断、`dbs-ai-check` AI 味检测）、`humanizer-zh`（中文去 AI 味改写）。

## 目录

```
SKILL.md                 agent 读的流程说明
scripts/
  doctor.py              环境自检
  candidates.py          aihot 热点榜 + 已做标记；--story N 看事件详情
  new_episode.py         建一期目录、登记选题
  fetch_images.py        抓官方/报道配图，出带标签的拼图
  deai_lint.py           扫口播里的 AI 味
  build.py               配音 + 渲染 + 字幕 + 拼接
  tts_gemini.py          Gemini TTS（Charon，多 key 轮询、模型轮换、限速自动等待）
  asr_check.py           配音逐段听写，对照原稿
  cover.py               生成封面
  finish.py              叠封面、抽帧拼图、听写报告
templates/               分镜模板、封面提示词模板
references/deai_rules.md 去 AI 味规则
examples/                两份成品分镜，参考写法
```

## 注意

- 热点数据来自 [aihot.news](https://aihot.news) 的官方 Agent API：个人使用免费，**商用需向其取得书面授权**。
- Gemini 免费档按「每个 key × 每个模型」限额，一期 7~8 段口播会用掉 7~8 次调用。
- 抓来的新闻配图、官方截图版权归原作者，发布时请标明图源并自行确认可用。
- 这个 skill 只做到样片为止，不会替你发布到任何平台。

## 写这个 skill 时学到的三件事

1. 开头两行简介决定 AI 用不用它，要写你平时怎么叫它（「按那套流程做一期」）。
2. 步骤里别光写「必须」，把原因和吃过的亏写上，比如「对着标签选图，不要按排列位置猜编号（这样放错过图）」。
3. 第一版肯定不好用：「七条爆款规律」一开始写成了固定句式，结果每期都一个腔调，后来才改成「七条是目的，不是句式」。

## 许可证

MIT，见 [LICENSE](LICENSE)。渲染引擎 huashu-art-motion、dbskill 等按各自的许可证使用，不包含在本仓库内。
