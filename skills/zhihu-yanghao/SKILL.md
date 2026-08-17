---
name: zhihu-yanghao
description: This skill provides the full Zhihu account-nurturing (养号) workflow for a Zhihu account via ego-browser — user-configurable topic pool, three-shift (morning/noon/evening) schedule where each shift writes+publishes+verifies one answer and runs like engagement, plus optional collect/follow/comment interactions driven by config. Use it when the user asks to 知乎养号 / 养知乎号 / 发知乎回答 / 知乎点赞互动 / 知乎浏览 / 三班养号, or wants a portable, risk-controlled, topic-configurable Zhihu growth routine on any machine where ego-browser is installed.
agent_created: true
version: 1.2.0
metadata:
  openclaw:
    requires:
      env:
        - SHIFT
        - CONFIG
        - QID
        - CONTENT
        - CONTENT_FILE
        - KW
        - LIMIT
---

# 知乎养号（zhihu-yanghao）v1.2.0

一套依赖 ego-browser 的知乎养号全流程，支持 **用户可配置话题池 + 早/中/晚三班节奏**：

- **选题**：全局 `topic_pool`，三班按「日序号 + 班次偏移」自动轮转取关键词（见 references/topic-strategy.md）。
- **每日每班 1 回答**：写 / 发布 / 折叠验证（你已选择三班各写 1 回答 = 3 回答/天，属自定义高风险，见下方⚠️）。
- **点赞互动**：前 10 个回答里随机选 3–5 个点赞（自然化，避免每次固定点赞前 N 被风控标记），三班各自独立会话。
- **可选互动**：收藏 / 关注问题 / 评论，按 `config.json` 每班 `interactions` 用户自定义。

可在任意装了 ego-browser 的机器上独立运行，不依赖本工作区记忆。

## 何时使用
- 用户说「知乎养号」「养知乎号」「今天养号」「发知乎回答」「知乎点赞 / 互动 / 浏览」「三班养号」「按话题养号」。
- 用户要在新机器上跑一套**话题可配置、带三班节奏**的知乎增长 routine。

## 前置依赖（必须）
1. 已安装 ego-browser（ego lite 浏览器 + CLI）。知乎账号在 ego-browser 中已登录（继承系统登录态，无需单独登录）。
2. ⚠️ **沙箱必须关闭**：ego-browser 的 Mach port IPC 会被 WorkBuddy 沙箱拦截。运行所有 `ego-browser nodejs` 命令时：
   - Bash 工具加 `dangerouslyDisableSandbox: true`；
   - 并在 WorkBuddy 安全中心临时关闭「沙箱安全」顶部开关（用完开回），否则报 `Failed to connect to ego_cli bootstrap`。
3. **配置话题与班次**（用户自定义）：复制 `config.example.json` 为 `config.json`，按你的账号/话题/互动修改（详见 references/workflow.md 的「配置 config.json」）。

## ⚠️ 三班各写 1 回答（自定义高风险，你必须知道）
你选择「三班各写 1 回答」= **3 回答/天**，超出 skill 默认保守的「1 回答/天」红线。实现上每班是**独立会话、间隔数小时**，满足「单次任务 ≤ 1 回答」「1 分钟内不连发」，但**日总量更高**：
- 7/27 限流根因是「1 分钟内连发 + 秒赞」，不是日总量；但日总量过高仍会增加画像风险。
- **若账号再次被限流**：先把 `config.json` 的三班 `answer` 改回仅 `morning: true`、其余 `false`（降回 1 回答/天），等风控释放。
- 评论（`comment`）默认关闭——知乎评论触发审核敏感，最易翻车，未验证前不要开。

## 风控红线（最高优先级，必读）
加载并严格遵守 references/risk-control.md。7/27 因连发 / 秒赞被临时限制 7 天，以下为硬约束：
- 🚫 1 分钟内连发 > 1 条创作内容（回答）；**单班任务 ≤ 1 回答**（三班 = 3 个独立任务）。
- 🚫 点赞 / 评论间隔 < 30 秒（知乎）；< 8 秒绝对禁止（全局）。
- 🚫 单任务操作密度 > 15 次 / 20 分钟。
- ⚠️ 任务前后各闲逛 3–5 分钟（热榜 / 推荐 / 关注）混入自然流量；发布前模拟阅读 5 分钟 + 发布前等 60 秒。
- ⚠️ 三班跨任务间隔 ≥ 2 小时（早 7:50 / 午 12:30 / 晚 20:00 天然满足）。

## 运行模式（推荐：三班编排）
用 `scripts/run_shift.js` 一把跑完一个班的「选题(可轮转) → 点赞 → 写回答 → 验证 → 可选收藏/关注/评论」，配置全在 `config.json`：
```
# 早班（按 config 轮转话题 + 写1回答 + 仅点赞）
CONFIG=/path/config.json SHIFT=morning ego-browser nodejs < scripts/run_shift.js

# 午班（写1回答 + 点赞 + 收藏 + 关注，依 config.interactions）
CONFIG=/path/config.json SHIFT=noon ego-browser nodejs < scripts/run_shift.js

# 指定问题覆盖（跳过自动选题）
SHIFT=evening QID=2021300214389043782 CONTENT_FILE=/tmp/answer.txt ego-browser nodejs < scripts/run_shift.js
```
脚本内部已含「已答过跳过 + 已赞跳过 + 随机选赞（前10随机3-5） + 发布卡死即停」。详细 env 与配置见 references/workflow.md。

### 旧版单脚本（仍可用，按需）
- `scripts/like_top5.js`：对指定问题在前 10 个回答里随机选 3–5 个点赞（env: `QID`，可选 `POOL`/`LIKE_MIN`/`LIKE_MAX` 覆盖默认）。
- `scripts/write_answer.js`：写回答 + 发布（env: `QID` + `CONTENT_FILE`/`CONTENT`）。
- `scripts/verify_fold.js`：按 `aid` 验证折叠（env: `AID`，可选 `QID`）。
- `scripts/pick_question.js`：扫热榜按关键词过滤输出候选 qid（env: `KW`、`LIMIT`）。

DOM 选择器、按钮点击要点见 references/selectors.md。

## 关键陷阱（务必先看）
- 🚫 **永远不要对中文用 `String.raw`**（8/4 乱码事故）：`fillInput` 直接传 UTF-8 字符串。
- ✅ **点赞按钮（8/11 实测修正）**：旧 `button.VoteButton:not(.VoteButton--down)` / `button.VoteButton--up` 在新版知乎**已失效**；改用 `button[aria-label*="赞同"]`，aria-label 形如 `"已赞同 1020 "` / `"赞同 307"`（**含尾空格必须 trim**），已赞判定用 `classList.contains('is-active')`（class 含 `VoteButton is-active`）。
- ⚠️ **点赞按钮 innerText 含前导零宽字符 `\u200b`**（实测为 `"\u200b 已赞同 87"`），**不能用 `===` / `startsWith('赞同')` 精确匹配**；一律用 aria-label + trim（8/12 实测：innerText 精确匹配命中 0，aria-label 精确匹配命中）。
- ✅ 「写回答」按钮文本前有零宽字符 `\u200b`，用 `.includes('写回答')`；「发布回答」按钮用 `innerText.trim() === '发布回答'` 的 js click 才稳。
- 🚫 **发布卡「发布中…」disabled 即停**：不要重复点 / 重试（会在云端累积卡死草稿）。等待账号风控释放或手动在浏览器发布。验证发布成功唯一可靠方式：去 `https://www.zhihu.com/people/<账号>/answers` 干净主页查，或用 `verify_fold.js` 调 `/api/v4/answers/{aid}` 看 `is_collapsed`。
- ✅ 折叠验证以 API `is_collapsed` / 回答页「编辑回答」按钮为准，不要信页面摘要（默认只显示末尾段）。

## 验证发布成功
1. 发布后 URL 跳转 `/question/{qid}/answer/{aid}`。
2. `run_shift.js` 会自动调 `/api/v4/answers/{aid}` 看 `is_collapsed`；或单独跑 `verify_fold.js`（env `AID`）。

## 文件产出建议
- 日报：`output/zhihu/YYYY-MM-DD-{shift}.md`（shift: morning / noon / evening）。
- 任务空间用完 `completeTaskSpace(name, { keep: false })` 关闭。

## 参考资料
- references/risk-control.md — 风控红线与全局原则（必读）
- references/selectors.md — DOM 选择器 + ego-browser API 速查
- references/topic-strategy.md — 全局话题池、心智定位、三班轮转
- references/workflow.md — config.json 配置、脚本调用方式、env 变量、示例命令
