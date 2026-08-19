# zhihu-yanghao

一套依赖 ego-browser 的知乎养号（account-nurturing）全流程 skill：选题 → 每日 1 回答（写 / 发布 / 折叠验证）→ 点赞互动（计数差值自校正），内嵌风控红线与陷阱。可在任意装了 ego-browser 的机器上独立运行，不依赖任何工作区记忆。

## 前置依赖
- 已安装 ego-browser（ego lite 浏览器 + CLI），知乎账号已登录（ego-browser 继承系统登录态）。
- ⚠️ 运行 `ego-browser nodejs` 需关闭 WorkBuddy 沙箱（详见 SKILL.md「前置依赖」）。
- 知乎账号 ID（用于主页验证），替换为你自己的（如 `kong-you-77`）。

## 安装
- 方式一：拷贝本目录到 `~/.workbuddy/skills/zhihu-yanghao/`（用户级，跨项目可用）。
- 方式二：解压 `zhihu-yanghao.zip` 到技能目录。
- 方式三：从 clawhub / skillhub 一键安装。

## 快速使用
完整一轮（每日养号）：
1. `KW='历史,神话' ego-browser nodejs < scripts/pick_question.js` 扫热榜选问题
2. `QID=<qid> ego-browser nodejs < scripts/like_top5.js` 点赞前 5（含已答过/已赞跳过 + 差值自校正）
3. `QID=<qid> CONTENT_FILE=/tmp/answer.txt ego-browser nodejs < scripts/write_answer.js` 写回答并发布
4. `AID=<aid> QID=<qid> ego-browser nodejs < scripts/verify_fold.js` 验证未折叠

详见 `SKILL.md` 与 `references/`。

## 目录结构
- `SKILL.md` — 主流程与触发条件
- `references/risk-control.md` — 风控红线（必读）
- `references/selectors.md` — DOM 选择器 + ego-browser API 速查
- `references/topic-strategy.md` — 三线模型与选题策略
- `references/workflow.md` — 脚本调用方式、env 变量、示例命令
- `scripts/` — 四个可执行 ego-browser nodejs 脚本（like_top5 / write_answer / verify_fold / pick_question）

## License
MIT — Evan Song
