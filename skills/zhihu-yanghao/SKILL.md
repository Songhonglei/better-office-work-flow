---
name: zhihu-yanghao
description: This skill provides the full Zhihu account-nurturing (养号) workflow for a Zhihu account via ego-browser — topic selection (three-line model), daily answer writing/publishing with fold verification, and like engagement with count-delta self-correction. Use it when the user asks to 养知乎号 / 知乎养号 / 发知乎回答 / 知乎点赞互动 / 知乎浏览, or wants a portable, risk-controlled Zhihu growth routine on any machine where ego-browser is installed.
agent_created: true
version: 1.0.0
metadata:
  openclaw:
    requires:
      env:
        - QID
        - AID
        - CONTENT
        - CONTENT_FILE
        - KW
        - LIMIT
---

# 知乎养号（zhihu-yanghao）

一套依赖 ego-browser 的知乎养号全流程：选题 → 每日 1 回答（写 / 发布 / 折叠验证）→ 点赞互动（计数差值自校正），并内嵌 7/27 风控事故后总结的红线与陷阱。可在任意装了 ego-browser 的机器上独立运行，不依赖本工作区记忆。

## 何时使用
- 用户说「知乎养号」「养知乎号」「今天养号」「发知乎回答」「知乎点赞 / 互动 / 浏览」。
- 用户要在新机器上跑一套可控风险的知乎增长 routine。

## 前置依赖（必须）
1. 已安装 ego-browser（ego lite 浏览器 + CLI）。知乎账号在 ego-browser 中已登录（ego-browser 继承系统登录态，无需单独登录）。
2. ⚠️ **沙箱必须关闭**：ego-browser 的 Mach port IPC 会被 WorkBuddy 沙箱拦截。运行所有 `ego-browser nodejs` 命令时：
   - Bash 工具加 `dangerouslyDisableSandbox: true`；
   - 并在 WorkBuddy 安全中心临时关闭「沙箱安全」顶部开关（用完开回），否则报 `Failed to connect to ego_cli bootstrap`。
3. 配置账号（在其他机器上替换为你自己的）：
   - `ZHIHU_ACCOUNT`：知乎账号 ID（用于主页验证，如 `kong-you-77`）。
   - 心智定位 / 三线模型见 references/topic-strategy.md，按账号人设调整。

## 风控红线（最高优先级，必读）
加载并严格遵守 references/risk-control.md。7/27 因连发 / 秒赞被临时限制 7 天，以下为硬约束：
- 🚫 1 分钟内连发 > 1 条创作内容（回答）；单次任务 ≤ 1 回答。
- 🚫 点赞 / 评论间隔 < 30 秒（知乎）；< 8 秒绝对禁止（全局）。
- 🚫 单任务操作密度 > 15 次 / 20 分钟。
- ⚠️ 任务前后各闲逛 3–5 分钟（热榜 / 推荐 / 关注）混入自然流量；发布前模拟阅读 5 分钟 + 发布前等 60 秒。

## 两种运行模式
### 模式 A：每日养号（内容 + 互动，推荐）
完整一轮：闲逛热榜 → 按选题策略选 1 个未答过问题 → 模拟阅读前 5 赞（~90s）→ 点赞前 5（间隔 35–80s）→ 写 1 回答（250–800 字，直接 UTF-8，勿用 String.raw）→ 等 60s → 发布 → 验证未折叠。

### 模式 B：纯互动（只点赞 / 浏览，不写回答）
热榜或指定问题 → 点赞前 5（差值自校正）→ 离开。用于养号早期或补互动。

## 执行步骤（依赖 ego-browser）
所有命令用 `ego-browser nodejs`（带 `dangerouslyDisableSandbox: true`），读取 scripts/ 下的脚本并执行（详见 references/workflow.md）：
- `scripts/like_top5.js`：对指定问题点赞前 5（env: `QID`）。含「已答过跳过 + 已赞跳过 + 差值自校正」。
- `scripts/write_answer.js`：写回答 + 发布（env: `QID` + `CONTENT_FILE` 或 `CONTENT`）。
- `scripts/verify_fold.js`：按 `aid` 验证回答是否折叠（env: `AID`，可选 `QID`）。
- `scripts/pick_question.js`：扫热榜，按关键词过滤 + 输出候选 qid（env: `KW`、`LIMIT`）。

DOM 选择器、按钮点击要点见 references/selectors.md。

## 关键陷阱（务必先看）
- 🚫 **永远不要对中文用 `String.raw`**（8/4 乱码事故）：`fillInput` 直接传 UTF-8 字符串。
- ✅ 点赞按钮 `button.VoteButton:not(.VoteButton--down)`，知乎非 React controlled，`.click()` 即可；但「已赞同」再点会取消，需差值自校正（脚本已实现）。
- ✅ 「写回答」按钮文本前有零宽字符 `\u200b`，用 `.includes('写回答')`；「发布回答」按钮用 `innerText.trim() === '发布回答'` 的 js click 才稳。
- 🚫 **发布卡「发布中…」disabled 即停**：不要重复点 / 重试（会在云端累积卡死草稿）。等待账号风控释放或手动在浏览器发布。验证发布成功唯一可靠方式：去 `https://www.zhihu.com/people/<账号>/answers` 干净主页查，或用 `verify_fold.js` 调 `/api/v4/answers/{aid}` 看 `is_collapsed`。
- ✅ 折叠验证以 API `is_collapsed` / 回答页「编辑回答」按钮为准，不要信页面摘要（默认只显示末尾段）。

## 验证发布成功
1. 发布后 URL 跳转 `/question/{qid}/answer/{aid}`。
2. 调 `verify_fold.js`（env `AID`）→ `is_collapsed=false` 且回答页有「编辑回答」按钮 → 未折叠 ✅。

## 文件产出建议
- 日报：`output/zhihu/YYYY-MM-DD-{type}.md`（type: product / emotion / history / social）。
- 任务空间用完 `completeTaskSpace(name, { keep: false })` 关闭。

## 参考资料
- references/risk-control.md — 风控红线与全局原则（必读）
- references/selectors.md — DOM 选择器 + ego-browser API 速查
- references/topic-strategy.md — 三线模型、心智定位、选题与轮换
- references/workflow.md — 脚本调用方式、env 变量、示例命令
