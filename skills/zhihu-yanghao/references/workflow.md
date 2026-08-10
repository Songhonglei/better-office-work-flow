# 工作流与脚本调用（zhihu-yanghao）

## 运行环境要求
- 命令前缀：`ego-browser nodejs`（Bash 工具必须加 `dangerouslyDisableSandbox: true`，且 WorkBuddy 安全中心「沙箱安全」开关临时关闭）。否则 ego-browser 连不上（报 `Failed to connect to ego_cli bootstrap`）。
- 所有脚本在 `scripts/` 下，参数通过环境变量传入。脚本内部用字符串拼接组装 js 代码，避免 `${}` 被外壳展开。

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

## 模式 A：每日养号完整一轮
1. 闲逛热榜找选题：
```
KW='历史,神话,唐僧,西游记' ego-browser nodejs < scripts/pick_question.js
```
   从 KEYWORD_HITS / ALL_TITLES 选一个中热度、未答过的问题，记下 qid。
2. 验证未答过并点赞前 5（脚本内含「已答过跳过 + 已赞跳过 + 差值自校正」）：
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
