# nonameskill：一句话，让 AI 出一条 1 分钟科技短视频

一个 [Agent Skill](https://agentskills.io)（Claude Code 里用，格式是开放标准）。
跟 AI 说一句「按那套流程做一期」，它就照着 `SKILL.md` 一步步走：

选热点 → 选题诊断 → 核实官方来源 → 抓官方截图 → 按「七条爆款规律」写分镜 → 去 AI 味 → 配音并逐段听写自检 → 代码渲染画面 → 生成封面 → 抽帧检查 → 交样片

最后一步写死了：**只出样片，不发布**，等人看过点头。

> 视频号「全球科技.」/ 公众号「硅谷趣闻」那期《一句话，让AI出视频：全流程公开》就是它做的，分镜和封面提示词都在 `examples/skill_intro/`。

## 目录

```
nonameskill/                 ← 整个文件夹就是 skill，放进 skills 目录即可
├── SKILL.md                 流程说明（AI 读的就是它）
├── references/deai_rules.md 去 AI 味规则：新闻腔、套话、模板句……
├── scripts/                 7 个小脚本：找候选、建目录、抓图、去AI味扫描、听写自检、封面、收尾抽帧
└── template/                分镜模板、构建脚本、封面提示词模板
examples/skill_intro/        这期视频的分镜 ep01b.py、配图脚本、封面提示词和封面
extras/make_audio_gemini.py  Gemini TTS 配音封装（Charon 声音，多 key 轮询、模型轮换、429 自动等待）
```

## 怎么装

```bash
# 个人用（所有项目都能用）
cp -r nonameskill ~/.claude/skills/
# 或只给某个项目用
cp -r nonameskill <你的项目>/.claude/skills/
```

脚本里的项目根目录用环境变量 `NONAME_ROOT`，不设就用当前目录。

## 先说清楚：哪些能直接用，哪些要自己补

这份 skill 是从作者自己的视频项目里拿出来的，**流程和规则是完整的，脚本是参考实现**：

- 能直接用的：
  - `SKILL.md` 里的流程，`references/deai_rules.md` 里的去 AI 味规则
  - `scripts/deai_lint.py`：扫口播稿里的 AI 味
  - `extras/make_audio_gemini.py`：Gemini 配音
  - `scripts/cover.sh`：需要先装 Codex CLI
- 要自己补的（作者项目里的其他模块，没放进来）：
  - 渲染引擎 `huashu_scripts`
  - 排版工具 `build_ep1.py`
  - 热点抓取 `auto/pipeline.py`（读 aihot.news 的 API；个人使用免费，商用要书面授权）
  - 配乐 `bgm` / `musiclib`
  - 听写比对用的 `clone_voice._cer`
  - 不用这些也能照着 `SKILL.md` 走，换成你自己的渲染、配音工具就行。
- 流程里调用的别家 skill，要另外装：dbskill（`dbs-content`、`dbs-ai-check`）、`humanizer-zh`、`guoshen`。
- Gemini API key 自己申请，放在 `~/.config/gemini/api_key`。**不要把 key 提交进仓库。**
- 封面风格参考图没放进来（原图是别人的版权素材）。想统一风格，就在 `template/` 放一张自己的 `ref_cover.jpg`。

## 写这个 skill 时学到的三件事

1. 开头两行简介决定 AI 用不用它，要写你平时怎么叫它（「按那套流程做一期」）。
2. 步骤里别光写「必须」，把原因和吃过的亏写上，比如「不能靠排列位置猜编号（2026-10-10 因此连续两次放错图）」。
3. 第一版肯定不好用，头一天就改了好几轮。

## 许可证

MIT，见 [LICENSE](LICENSE)。流程里调用的别家 skill（dbskill、humanizer-zh、guoshen）和渲染引擎按它们各自的许可证使用，不包含在本仓库内。
