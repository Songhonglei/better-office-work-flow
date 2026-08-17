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
     - `interactions`：`{ like, collect, follow, comment }`——`like` 为点赞配置：**整数 `5`（固定 5 个）或对象 `{"pool":10,"min":3,"max":5}`（前 10 个候选随机选 3–5，推荐自然化）**；`collect`/`follow`/`comment` 为开关（comment 默认 false，实验性）。
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
一个命令跑完一个班的全部动作，配置全在 config.json。本环境用**参数文件**方式（ego-browser 不透传 env）：
```
# 1) 写参数文件（shift/qid/contentFile/configPath 等），见下方 schema
cat > /tmp/zhihu_shift_params.json <<'EOF'
{ "shift": "morning", "qid": "2070982459156424668",
  "contentFile": "/abs/answer.txt",
  "configPath": "/abs/config.json" }
EOF

# 2) 跑（不带 env，脚本自动读参数文件）
ego-browser nodejs < scripts/run_shift.js
```
env 写法（其他机器若透传 env 可用）：`SHIFT=morning CONFIG=/abs/config.json ego-browser nodejs < scripts/run_shift.js`。
`run_shift.js` 参数（**env 优先，回退参数文件**）：
- **env 方式**（部分 ego-browser 构建不透传 shell env，见下）：`CONFIG` / `SHIFT` / `QID` / `CONTENT` / `CONTENT_FILE` / `KW` / `LIMIT` / `COMMENT_TEXT`。
- **参数文件方式（推荐，env 不可用时）**：把下列 JSON 写到 `/tmp/zhihu_shift_params.json`，再 `ego-browser nodejs < scripts/run_shift.js`（不传 env）：
  ```json
  {
    "shift": "morning|noon|evening",
    "qid": "2070982459156424668",
    "contentFile": "/abs/answer.txt",
    "configPath": "/abs/config.json",
    "kw": "历史,神话",
    "limit": 25,
    "commentText": "评论内容"
  }
  ```

> ⚠️ **本机实测（macOS / ego-browser nodejs）不向运行时透传 shell 环境变量**——`process.env.*` 全为 `UNDEF`，故 heredoc/env 内联写法在本环境会失败。统一用「参数文件 `/tmp/zhihu_shift_params.json` + 不带 env 的 `ego-browser nodejs < scripts/run_shift.js`」最稳。脚本已同时兼容 env（其他机器若透传仍可用）。

脚本流程：读配置 → 轮转取关键词 → 选未答过问题（或 QID 覆盖）→ 前10随机选3-5点赞（自然化）→ 写/发布/验证1回答 → 按 interactions 做可选收藏/关注/评论。已内置「已答过跳过 + 已赞跳过 + 随机选赞 + 发布卡死即停」。

## 模式 A：每日养号完整一轮（旧版单脚本，仍可用）
1. 闲逛热榜找选题：
```
KW='历史,神话,唐僧,西游记' ego-browser nodejs < scripts/pick_question.js
```
   从 KEYWORD_HITS / ALL_TITLES 选一个中热度、未答过的问题，记下 qid。
2. 验证未答过并点赞（前10随机选3-5，脚本内含「已答过跳过 + 已赞跳过 + 随机选赞」）：
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
