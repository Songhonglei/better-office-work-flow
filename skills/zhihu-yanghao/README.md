# zhihu-yanghao

一套依赖 ego-browser 的知乎养号（account-nurturing）全流程 skill：**垂直领域收敛 + 三班节奏（早/午/晚）+ 深度版回答 + 想法发布 + 创作影响力规范**，内嵌 7/27 风控事故后总结的红线与陷阱。可在任意装了 ego-browser 的机器上独立运行，不依赖任何工作区记忆。

## 功能总览（v1.3.3）

- **三班编排**：早 07:50 / 午 12:30 / 晚 20:00，每班独立会话跑完「轮转选题 → 随机点赞 → 写回答 → 发布 → 折叠验证 → 可选收藏/关注/评论」。
- **垂直度收敛**：`vertical_focus` 只养 2 个领域（默认「趣味历史」+「人文心理」），每篇埋 2-3 个领域关键词帮算法点亮创作垂直度。
- **深度版回答**：每周 1 篇 800–1200 字（用户邀请 `invite` / 随机 `random` / 两者 `auto`），硬性要求 = 可核查硬料 + 对比结构 + 可操作结论。
- **想法发布**：`post_moment.js` 全自动发想法/动态（默认 dryRun 只填不发），冲关注者亲密度。
- **影响力规范**：每篇必带反直觉 hook + 可操作清单 + 引导互动（收藏/评论权重高于赞同）。
- **自然化互动**：前 10 候选随机选 3–5 个点赞（不固定前 N）、已答/已赞自动跳过、差值自校正。

## 前置依赖

- 已安装 ego-browser（ego lite 浏览器 + CLI），知乎账号已登录（ego-browser 继承系统登录态）。
- ⚠️ 运行 `ego-browser nodejs` 需关闭 WorkBuddy 沙箱（详见 SKILL.md「前置依赖」）。
- （可选）zhihu-cli + 知乎开放平台 Access Secret，用于热榜扫描与发布结果权威校验。

## 安装

- 方式一：拷贝本目录到 `~/.workbuddy/skills/zhihu-yanghao/`（用户级，跨项目可用）。
- 方式二：从 clawhub / skillhub 一键安装。
- 方式三：clone 本仓库，取 `skills/zhihu-yanghao/` 子目录。

## 快速使用（推荐：三班编排）

```bash
# 1) 配置：复制模板并按你的账号/话题/班次修改（config.json 不入库）
cp config.example.json config.json

# 2) 写参数文件（ego-browser 不透传 shell env，参数文件是可靠路径）
cat > /tmp/zhihu_shift_params.json <<'EOF'
{ "shift": "morning", "configPath": "/abs/path/config.json" }
EOF

# 3) 跑一个班（自动轮转选题 + 点赞 + 写/发布/验证 1 回答）
ego-browser nodejs < scripts/run_shift.js
```

发想法（默认 dryRun 只填不发，实发须显式 `"dryRun": false`）：

```bash
echo '想法正文（50-150 字）' > /tmp/moment.txt
cat > /tmp/zhihu_moment_params.json <<'EOF'
{ "contentFile": "/tmp/moment.txt", "dryRun": true }
EOF
ego-browser nodejs < scripts/post_moment.js
```

## 目录结构

- `SKILL.md` — 主流程、触发条件、创作分四件套规范
- `config.json` / `config.example.json` — 账号、垂直领域、话题池、班次、深度版/想法/影响力配置
- `references/risk-control.md` — 风控红线（必读）
- `references/selectors.md` — DOM 选择器 + ego-browser API 速查
- `references/topic-strategy.md` — 垂直收敛、话题池轮转、深度版与影响力写作规范
- `references/workflow.md` — 配置说明、脚本调用、参数文件 schema
- `scripts/` — run_shift.js（三班编排）/ post_moment.js（发想法）/ like_top5.js / write_answer.js / verify_via_cli.js（折叠验证）/ pick_question.js

## License

MIT — Evan Song
