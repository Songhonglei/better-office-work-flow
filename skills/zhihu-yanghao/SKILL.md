---
name: zhihu-yanghao
description: This skill provides the full Zhihu account-nurturing (养号) workflow for a Zhihu account via ego-browser — user-configurable topic pool with vertical focus (创作垂直度), three-shift (morning/noon/evening) schedule where each shift writes+publishes+verifies one answer and runs like engagement, weekly deep-dive answers (深度版, user-invited or random), moments/想法 posting for follower intimacy, content-influence requirements (hook + actionable + CTA + comment reply), plus optional collect/follow/comment interactions driven by config. Use it when the user asks to 知乎养号 / 养知乎号 / 发知乎回答 / 知乎点赞互动 / 知乎浏览 / 三班养号 / 写深度版 / 发想法 / 提升创作分, or wants a portable, risk-controlled, topic-configurable Zhihu growth routine on any machine where ego-browser is installed.
agent_created: true
---

# 知乎养号（zhihu-yanghao）v1.3.4

一套依赖 ego-browser 的知乎养号全流程，支持 **垂直领域收敛 + 用户可配置话题池 + 早/中/晚三班节奏 + 深度版回答 + 想法发布 + 影响力规范**：

- **垂直收敛**：账号只养 2 个领域（当前「趣味历史」+「人文心理」），刻意埋关键词帮算法点亮创作垂直度。
- **选题**：全局 `topic_pool`，三班按「日序号 + 班次偏移」自动轮转取关键词（见 references/topic-strategy.md）。
- **每日每班 1 回答**：写 / 发布 / 折叠验证（你已选择三班各写 1 回答 = 3 回答/天，属自定义高风险，见下方⚠️）。
- **深度版**：每周 1 篇 800–1200 字深度回答（用户邀请 or 自动随机），冲内容优质分。
- **想法**：每周若干条短动态，冲关注者亲密度。
- **影响力规范**：每篇回答必须带反直觉 hook + 可操作清单 + 引导互动，并在 24h 内回评论。
- **点赞互动**：前 10 个回答里随机选 3–5 个点赞（自然化，避免每次固定点赞前 N 被风控标记），三班各自独立会话。
- **可选互动**：收藏 / 关注问题 / 评论，按 `config.json` 每班 `interactions` 用户自定义。

可在任意装了 ego-browser 的机器上独立运行，不依赖本工作区记忆。

## 何时使用
- 用户说「知乎养号」「养知乎号」「今天养号」「发知乎回答」「知乎点赞 / 互动 / 浏览」「三班养号」「按话题养号」。
- 用户说「写深度版 / 这篇写深一点」「发个想法 / 发动态」「提升创作分 / 创作分复盘」「点亮垂直度」。
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
> ⚠️ **环境变量注意（本机实测关键）**：部分 ego-browser 构建的 `nodejs` 子命令**不继承 shell 环境变量**（`CONFIG`/`SHIFT` 会被丢弃，且进程 `cwd` 锁死为 `/`）。因此 `CONFIG=... SHIFT=... ego-browser nodejs < script` 在本机跑不起来。可靠写法见下方 heredoc。

```bash
ego-browser nodejs <<'EOF'
const fs = require('fs');
process.env.CONFIG = '/Users/songhonglei/.workbuddy/skills/zhihu-yanghao/config.json';
process.env.SHIFT = 'morning';
const keep = setInterval(function () {}, 1000);
const src = fs.readFileSync('/Users/songhonglei/.workbuddy/skills/zhihu-yanghao/scripts/run_shift.js', 'utf8');
Promise.resolve(eval(src)).then(
  function () { clearInterval(keep); cliLog('=== SHIFT_DONE_OK ==='); },
  function (e) { clearInterval(keep); cliLog('=== SHIFT_ERROR: ' + (e && e.message) + ' ==='); }
);
EOF
```

> ⚠️ **上面这个启动器有三条硬约束，改动前先看（2026-09-05 实测踩坑）**：
> ① **heredoc 里不能出现顶层 `await`**——`require` 与顶层 `await` 同时存在会触发 node 模块格式自动探测冲突，直接报 `ReferenceError: Cannot determine intended module format`。这不是本机环境问题，**所有机器都一样**。
> ② **`eval(src)` 返回的 Promise 必须有人接管**（上面的 `.then`）。脚本主体是 `(async () => {...})()`，若写成 `(function(){ eval(src); })()`，运行时会认为同步代码已跑完并结束会话，异步流程被丢弃——症状是「跑了三四分钟、零输出、什么都没做」。
> ③ `setInterval` 保活，防止进程在等待浏览器 I/O 时提前退出。
> 备选：确实需要顶层 await 时改用 `import fs from 'node:fs'`（ESM 模式），但 eval 进来的脚本内部若有 `require` 会挂。
> 📌 另注：`cliLog` 输出走 **stderr**，且**延迟到进程结束才 flush**；后台运行时中途看不到日志是正常现象，不要误判为卡死。

三班只需改 `process.env.SHIFT` 为 `noon` / `evening`；指定问题覆盖时额外 `process.env.QID = '...'` + `process.env.CONTENT_FILE = '/tmp/answer.txt'`。

> 📌 **本机保留修正（勿在下次 GitHub 更新时回退）**：① 点赞选择器用 `button[aria-label*=赞同]`（新版知乎 `VoteButton` 已失效）；② 写回答用 `ClipboardEvent` 粘贴注入（Draft.js 不认 `fillInput`）；③ 上方 heredoc 注入 env + `.then` 接管 Promise（覆盖 `CONFIG=...` 写法与裸 `eval` 写法）；④ 关注问题按钮按 `FollowButton` class 匹配（页面文案是「关注」/「已关注」，**从不存在**「关注问题」四个字，旧写法永远返回 `no_button`）。前三条是本机 8/11–8/16 实测结论，第 ④ 条为 9/5 实测。脚本内部已含「已答过跳过 + 已赞跳过 + 随机选赞（前10随机3-5） + 发布卡死即停 + is_collapsed 验证带 retry(3-5次/10-15s)」。详细 env 与配置见 references/workflow.md。

## 创作分提升四件套（v1.3.0）
针对知乎创作分六维体系（创作活跃度 / 创作垂直度 / 内容优质分 / 创作影响力 / 关注者亲密度 / 社区成就分）的定向优化，全部由 `config.json` 驱动：

### 1. 垂直度收敛（`vertical_focus`）
账号只养 **2 个领域**，不再横跨多领域。当前锁定 **「趣味历史」+「人文心理」**（见 `config.vertical_focus.primary`）。
- 每篇回答**刻意自然融入 2–3 个本领域关键词**（见 `keyword_hints`），帮算法识别并点亮创作垂直度。
- `topic_pool` 按历史类 / 人文类**交替排列**，保证轮转取到的 3 个关键词横跨两个领域，既集中又不单一。
- 🚫 不在垂直领域外的话题下写回答（产品 / 财务 / 职场 / 社会热点一律不写），否则垂直度永远点不亮。

### 2. 深度版回答（`deep_answer`，每周 1 篇）
内容优质分是**周更**维度，靠"被算法识别为优质内容"涨分，标准回答（250–800 字）拉不动。每周至少 1 篇深度版：
- **触发方式**（`config.deep_answer.mode`）：
  - `auto`（默认）：用户说「深度版 / 写深一点」即 **invite 触发**；否则每周**随机挑 1 班**自动走深度版。
  - `invite`：仅用户显式邀请时写。
  - `random`：仅按周自动随机，不接受指定。
- **字数**：800–1200 字（普通回答是 250–800）。
- **硬性三项要求**（`config.deep_answer.requirements`）：① 1 处可核查的史料原文 / 数据 / 案例；② 1 组对比结构（分层或表格化）；③ 1 段可操作的判断框架或结论。
- 深度版同样走 `run_shift.js` 发布流程，只是正文按深度规范生成，**流程无差别**。

### 3. 想法 / 动态（`moments`）
关注者亲密度是**月更**维度，且是提升性价比最高的一项——想法（知乎动态）短、频、轻，不需要深度。
- 频率：`config.moments.per_week`（默认 4 条 / 周），长度 50–150 字。
- 内容方向见 `config.moments.topics`（读史笔记 / 历史冷知识 / 生活心理观察 / 读书摘录+点评）。
- **已自动化**：`scripts/post_moment.js`（2026-08-31 实测选择器 + dryRun 验证通过）：
  ```
  echo '{"contentFile":"/abs/moment.txt","dryRun":true}' > /tmp/zhihu_moment_params.json
  ego-browser nodejs < scripts/post_moment.js
  ```
  建议新机器首次跑先带 `dryRun: true`（只填不发布），确认无异常再写 `"dryRun": false` 实发。
  ⚠️ **默认 fail-safe**：不设置 `dryRun` 时一律只填不发布，实发必须显式写 `"dryRun": false`。

### 4. 创作影响力要求（`influence`）
影响力 ≠ 点赞数。**收藏、评论、分享的权重高于赞同**——自动点赞只贡献赞同，必须靠内容质量拉动收藏与评论。每篇回答必须满足：
- **hook**：开头或中段抛 1 个反直觉 / 反常识观点，让人产生想反驳或补充的冲动（拉评论）。
- **actionable**：至少 1 个可操作清单 / 判断框架 / 步骤（如「判断 X 的 3 步法」）（拉收藏）。
- **cta**：结尾 1 句轻量引导互动，不硬求赞、不套路。
- **评论回复**：发布后 24h 内回复全部评论（`config.influence.comment_reply`），互动率直接影响影响力分。**由 agent 执行（无脚本）**：agent 应在下一次养号任务开始时，先用 CLI 查上一班回答的评论并回复，或提醒用户手动回复。

> **配置分工（重要，勿误解）**：`vertical_focus` / `deep_answer` / `influence` 三个配置块是**给 agent 的写作规范**——`vertical_focus`/`influence` 不被脚本读取；`deep_answer.min_words/max_words` 在参数文件写 `"deep": true` 时被 `run_shift.js` 用于字数护栏；各班 `shifts.*.interactions` 被 `run_shift.js` 读取执行。
> **字数护栏（v1.3.3）**：`run_shift.js` 发布前校验 contentFile 字符数——标准区间 `answer_style.min/max_words`（250–800）、深度版（参数 `"deep": true`）区间 `deep_answer.min/max_words`（800–1200）。**超区间输出 `ANSWER_SKIPPED: WORD_COUNT_EXCEEDED` 并跳过发布**（点赞/互动照常收尾），压缩或扩写正文后重跑即可（已赞自动跳过）。

### 旧版单脚本（仍可用，按需）
- `scripts/like_top5.js`：对指定问题在前 10 个回答里随机选 3–5 个点赞（env: `QID`，可选 `POOL`/`LIKE_MIN`/`LIKE_MAX` 覆盖默认）。
- `scripts/write_answer.js`：写回答 + 发布（env: `QID` + `CONTENT_FILE`/`CONTENT`）。
- `scripts/verify_via_cli.js`：折叠状态权威验证（参数文件 `/tmp/zhihu_verify_params.json`：`aid`/`type`，或 env `AID`/`TYPE`）。自动定位 zhihu-cli（PATH → macOS 默认路径），Summary 非空=未折叠。**替代已删除的 verify_fold.js**（其 serverFetch API 8/26 起恒 403）。
- `scripts/pick_question.js`：扫热榜按关键词过滤输出候选 qid（env: `KW`、`LIMIT`）。⚠️ 本机 env 不透传，需把 `kwRaw` 改成硬编码或复制到 /tmp 修改后运行。
- `scripts/post_moment.js`：发想法 / 动态（参数文件 `/tmp/zhihu_moment_params.json`，支持 `dryRun`）。
- `scripts/edit_answer.js`：修改已发布回答（参数文件 `/tmp/zhihu_edit_params.json`：`aid`/`qid`/`contentFile`/`stripMarkdown`/`dryRun`）。⚠️ 已知限制：内容替换可行，但「提交修改」点击可能不生效（脚本会安全停止并提示人工确认）。

DOM 选择器、按钮点击要点见 references/selectors.md。

## 关键陷阱（务必先看）
- 🚫 **生成回答禁止输出 Markdown**（9/1）：编辑器不渲染，`**` / `- ` 按字面残留。纯文本排版用「1.」「· 」、破折号强调。
- 🚫 **永远不要对中文用 `String.raw`**（8/4 乱码事故）：`fillInput` 直接传 UTF-8 字符串。
- ✅ **点赞按钮（8/11 实测修正）**：旧 `button.VoteButton:not(.VoteButton--down)` / `button.VoteButton--up` 在新版知乎**已失效**；改用 `button[aria-label*="赞同"]`，aria-label 形如 `"已赞同 1020 "` / `"赞同 307"`（**含尾空格必须 trim**），已赞判定用 `classList.contains('is-active')`（class 含 `VoteButton is-active`）。
- ⚠️ **点赞按钮 innerText 含前导零宽字符 `\u200b`**（实测为 `"\u200b 已赞同 87"`），**不能用 `===` / `startsWith('赞同')` 精确匹配**；一律用 aria-label + trim（8/12 实测：innerText 精确匹配命中 0，aria-label 精确匹配命中）。
- ✅ 「写回答」按钮文本前有零宽字符 `\u200b`，用 `.includes('写回答')`；「发布回答」按钮用 `innerText.trim() === '发布回答'` 的 js click 才稳。
- 🚫 **发布卡「发布中…」disabled 即停**：不要重复点 / 重试（会在云端累积卡死草稿）。等待账号风控释放或手动在浏览器发布。
- ⚠️ **验证发布/修改成功一律用官方 CLI**：`zhihu-cli me contents --type answer --limit 3`（摘要完整=未折叠；想法用 `--type pin`）。`serverFetch('/api/v4/answers/{aid}')` 自 8/26 起持续 403 已失效——v1.3.3 起 `run_shift.js` 已**移除** API 验证死路，改用 `scripts/verify_via_cli.js`；页面摘要/浏览器侧信号均有假阴性。

## 验证发布成功
1. 发布后 URL 跳转 `/question/{qid}/answer/{aid}`。
2. **权威校验**：`echo '{"aid":"<aid>","type":"answer"}' > /tmp/zhihu_verify_params.json && ego-browser nodejs < scripts/verify_via_cli.js` —— 输出 `VERIFY_RESULT: OK_NOT_COLLAPSED` 即成功（折叠则 `COLLAPSED`；`NOT_FOUND_YET` 是索引滞后，等 1–2 分钟重跑）。等价手工命令：`zhihu-cli me contents --type answer --limit 3` 看最新一条摘要是否完整。

## 部署注意（本机 macOS 实测）
- ego-browser 可能不在 shell PATH：用绝对路径 `~/.local/bin/ego-browser`。
- zhihu-cli 通常不在 PATH：真实路径 `~/Library/Application Support/zhihu-cli/current/zhihu-cli`（verify_via_cli.js 已内置此回退）。

## 文件产出建议
- 日报：`output/zhihu/YYYY-MM-DD-{shift}.md`（shift: morning / noon / evening）。
- 任务空间用完 `completeTaskSpace(name, { keep: false })` 关闭。

## 参考资料
- references/risk-control.md — 风控红线与全局原则（必读）
- references/selectors.md — DOM 选择器 + ego-browser API 速查
- references/topic-strategy.md — 全局话题池、心智定位、三班轮转
- references/workflow.md — config.json 配置、脚本调用方式、env 变量、示例命令

## 版本变更
- **v1.3.4（2026-09-05）**：补齐两个「写了但从未真正生效」的实测修复（均经同一页面对照实证验证）：
  1. **关注问题按钮选择器**（`run_shift.js`）：旧写法按 innerText 匹配 `"关注问题"`，但知乎页面上该控件文案只有「关注」/「已关注」（class `FollowButton`），字符串 `"关注问题"` 从未出现过，故永远返回 `no_button`。改为**先按 `FollowButton` class 匹配、回退按文案精确匹配**；命中「已关注」判为 `already`，避免误点成取消关注。实证：同一页面旧写法 `no_button` → 新写法 `already`。
  2. **启动器必须接管 Promise**（`SKILL.md` 运行模式）：原示例 `(function(){ eval(src); })()` 中，`(async () => {...})()` 返回的 Promise 无人接管，运行时判定同步代码已跑完即结束会话，异步流程被整体丢弃——症状是「跑了三四分钟、零输出、什么都没做」。改为 `Promise.resolve(eval(src)).then(ok, err)` + `setInterval` 保活，并固化三条硬约束：heredoc 内禁用顶层 await（`require` 与顶层 await 并存会触发 node 模块格式自动探测冲突，报 `Cannot determine intended module format`，**非本机特例，所有机器同理**）、Promise 必须有人接管、保活定时器。另补充 `cliLog` 走 stderr 且延迟到进程结束才 flush 的提示（避免后台运行时误判卡死）。
- **v1.3.3（2026-09-05）**：健康度清理与护栏增强（核心行为不变，删死路 + 护栏 + 文档同步）：
  1. **移除 API_VERIFY 403 死路**：`run_shift.js` 不再对恒 403 的 serverFetch API 做 5 次重试（每班白耗约 60s + 报错噪音）。
  2. **新增 `scripts/verify_via_cli.js`**：折叠权威验证脚本化（自动定位 zhihu-cli，含 macOS 默认路径回退），实测通过。
  3. **删除 `scripts/verify_fold.js`**：整个脚本建立在已失效 API 上。
  4. **字数护栏**：发布前按 config 区间校验字数，超限跳过发布（`ANSWER_SKIPPED: WORD_COUNT_EXCEEDED`）。
  5. **references/ 文档全量同步** v1.3.2/v1.3.3 变更。
- **v1.3.2（2026-09-05）**：在 v1.3.1 基础上合入本机（macOS + 特定 ego-browser 构建）实测必需的三处兼容性修正，避免纯覆盖 v1.3.1 后在本机养号失败：
  1. **点赞选择器**：`button.VoteButton:not(.VoteButton--down)`（v1.3.1，已失效）→ `button[aria-label*=赞同]`（无引号写法，规避 `js()` 二次求值引号错配）。影响 `run_shift.js`。
  2. **写回答注入**：`fillInput('.public-DraftEditor-content')`（v1.3.1，Draft.js 不认）→ `ClipboardEvent` 粘贴注入。影响 `run_shift.js` + `write_answer.js`。
  3. **想法正文注入**：`post_moment.js` 同 `fillInput` 坑，一并改为 `ClipboardEvent` 粘贴注入。
  4. **运行示例**：v1.3.1 的 `CONFIG=... SHIFT=... ego-browser nodejs < script` 在本机不继承 shell 环境变量（cwd 锁死 `/`、CONFIG/SHIFT 被丢弃），改为 heredoc 内联 `process.env.X` + `fs.readFileSync` + `eval(主脚本)` 的可靠写法（见「运行模式」）。
  - 注：以上修正仅针对本机环境；在其他正常继承 env 的机器上，`CONFIG=...` 前缀写法仍可工作。个人 `config.json` 不上传，请复制 `config.example.json` 自建。
