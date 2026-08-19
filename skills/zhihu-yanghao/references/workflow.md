# 工作流与脚本调用（zhihu-yanghao v1.1.0）

## 运行环境要求
- 命令前缀：`ego-browser nodejs`（Bash 工具必须加 `dangerouslyDisableSandbox: true`，且 WorkBuddy 安全中心「沙箱安全」开关临时关闭）。否则 ego-browser 连不上（报 `Failed to connect to ego_cli bootstrap`）。
- 所有脚本在 `scripts/` 下，参数通过环境变量传入。脚本内部用字符串拼接组装 js 代码，避免 `${}` 被外壳展开。

## 配置 config.json（用户自定义话题与班次）
1. 复制模板：`cp config.example.json config.json`（config.json 不纳入版本库，按你账号改）。
2. 关键字段：
   - `account`：知乎账号 ID（如 `kong-you-77`），用于日报/主页验证。
   - `topic_pool`：全局话题池（数组）。三班按「日序号 + 班次偏移」轮转取关键词，用户随时改这里即换话题。
   - `answer_style`：回答字数区间与视角提示（LLM 写回答时参考）。
   - `shifts`：三个班次，每班含：
     - `enabled`：是否启用该班。
     - `time`：建议触发时间（自动化调度用）。
     - `answer`：该班是否写 1 回答。
     - `interactions`：`{ like, collect, follow, comment }` 数量/开关——**收藏/关注/评论是否做、做多少，全由你在这里配**（comment 默认 false，实验性）。
3. 改完保存即可，run_shift.js 下次运行自动读最新配置。

## 两种调用方式
方式一（推荐，文件直读）：把脚本内容喂给 ego-browser：
```
QID=2021300214389043782 ego-browser nodejs < scripts/like_top5.js
```
方式二（heredoc，最稳）：打开脚本文件，把其内容粘贴进 `ego-browser nodejs <<'EOF' ... EOF'`：
```
QID=2021300214389043782 ego-browser nodejs <<'EOF'
<此处粘贴 scripts/like_top5.js 的全文>
EOF
```

## 推荐：三班编排（run_shift.js）
一个命令跑完一个班的全部动作，配置全在 config.json：
```
# 早班：按 config 轮转话题 + 写1回答 + 仅点赞（依 config.interactions）
CONFIG=/绝对路径/config.json SHIFT=morning ego-browser nodejs < scripts/run_shift.js

# 午班：写1回答 + 点赞 + 收藏 + 关注（依 config.interactions）
CONFIG=/绝对路径/config.json SHIFT=noon ego-browser nodejs < scripts/run_shift.js

# 晚班：指定 QID 覆盖自动选题（适合你想手动定点某问题）
SHIFT=evening QID=2021300214389043782 CONTENT_FILE=/tmp/answer.txt ego-browser nodejs < scripts/run_shift.js
```
> ⚠️ **环境变量注意（重要）**：部分 ego-browser 构建的 `nodejs` 子命令**不继承 shell 环境变量**（`CONFIG`/`SHIFT` 会被丢弃，且 `cwd` 锁死为 `/`），上面的 `CONFIG=... SHIFT=... ego-browser nodejs < script` 会跑不起来、脚本内相对路径也找不到。可靠写法见 SKILL.md「运行模式」：用 heredoc 在脚本内 `process.env.X=...` 注入、用绝对路径 `eval` 主脚本。

`run_shift.js` env 变量：
- `CONFIG`：配置文件路径（默认 `../config.json`，找不到回退 `../config.example.json`）。
- `SHIFT`：`morning` / `noon` / `evening`（必填）。
- `QID`：指定问题 qid（可选，跳过自动选题）。
- `CONTENT` / `CONTENT_FILE`：回答正文（`answer=true` 时必填其一；CONTENT_FILE 优先）。
- `KW`：覆盖轮转关键词（可选，逗号分隔）。
- `LIMIT`：热榜扫描条数（默认 25）。
- `COMMENT_TEXT`：评论内容（`interactions.comment=true` 时可选）。

脚本流程：读配置 → 轮转取关键词 → 选未答过问题（或 QID 覆盖）→ 前10随机3-5赞（差值自校正）→ 写/发布/验证1回答 → 按 interactions 做可选收藏/关注/评论。已内置「已答过跳过 + 已赞跳过 + 发布卡死即停」。

## 模式 A：每日养号完整一轮（旧版单脚本，仍可用）
1. 闲逛热榜找选题：
```
KW='历史,神话,唐僧,西游记' ego-browser nodejs < scripts/pick_question.js
```
   从 KEYWORD_HITS / ALL_TITLES 选一个中热度、未答过的问题，记下 qid。
2. 验证未答过并前10随机点赞3-5（脚本内含「已答过跳过 + 已赞跳过 + 差值自校正」）：
```
QID=<qid> ego-browser nodejs < scripts/like_top5.js
```
3. 写回答（正文写到文件，再用 CONTENT_FILE 传入；或短回答用 CONTENT 环境变量）：
```
QID=<qid> CONTENT_FILE=/tmp/zhihu-answer.txt ego-browser nodejs < scripts/write_answer.js
```
   脚本会：打开编辑器 → fillInput 正文 → 等 60s → 点「发布回答」→ 输出 aid。
4. 验证未折叠：
```
AID=<上一步输出的aid> QID=<qid> ego-browser nodejs < scripts/verify_fold.js
```
   看到 `is_collapsed=false` 且 `hasEdit:true` 即成功。

## 模式 B：纯互动（只点赞）
```
QID=<qid> ego-browser nodejs < scripts/like_top5.js
```

## 写回答正文怎么给
- 长回答：先把正文写进文件（如 `/tmp/zhihu-answer.txt`，用空行分段），再 `CONTENT_FILE=/tmp/zhihu-answer.txt`。
- 短回答：直接 `CONTENT='你的回答正文'`。
- 若你的 ego-browser 构建不支持 `require('fs')`，改为把正文直接嵌进 heredoc 的 JS 字符串（同 write_answer.js 主体，仅把 content 来源改成字面量）。

## 风控提醒（详见 references/risk-control.md）
- 点赞间隔脚本已内置 35–80s 随机；不要人为加速。
- 发布卡「发布中…」立刻停，不要重试（详见风控文档）。
- 任务前后自己加 3–5 分钟闲逛（开热榜 / 推荐页 wait 即可）。
