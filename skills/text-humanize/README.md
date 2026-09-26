# text-humanize

> 中英文去 AI 味检测 + 改写。自动识别语言**与体裁**，再套用对应的检测模式与改写规则。

## Features

- **双语自动识别** —— 中文、英文各一套模式目录；混排文本按语言块分别审计。
- **体裁闸门** —— 短文本 / 长文 / 文学三档。评论区该删破折号，散文该留破折号；跳过这一步就会给出互相打架的建议。
- **两道机械自检** —— 标点层（半角引号数与标点周边空格，纯中文文本应为 0）+ 抒情同位语结构计数（`X，Y 的 Z` 出现次数、最长连续句数、陈腐喻体与万能形容词词库命中）。先出数字，再谈文风。
- **六类中文信号** —— 结构 / 开头 / 正文 / 结尾 / 表面 / 修辞·抒情（R-CN1~R-CN6）。
- **五类英文信号** —— Structural / Opening / Body / Closing / Surface，附 HN、Reddit、Twitter/X、LinkedIn、Dev.to 平台规则。
- **两种模式** —— 只审计（报告 + 绿黄红判定），或审计 + 改写（左右对照，改动分「机械规范化」与「内容改动」两级）。

## 什么场景用它

| 场景 | 体裁判定 |
|---|---|
| HN / Reddit 回帖、即刻、微博、朋友圈、抖音评论区 | 短文本 |
| 公众号正文、知乎长答、博客、署名文章 | 长文 |
| 散文、美文、抒情段落、现代诗短句、小说叙事段落 | 文学 |

## Quick Start

```bash
# Install (clawhub)
clawhub install text-humanize

# Or clone the mono-repo; the skill lives in skills/text-humanize/
git clone https://github.com/Songhonglei/better-office-work-flow.git
```

## Usage

详细规则见 [SKILL.md](./SKILL.md)，信号目录见 [references/](./references/)。

触发示例：

- 「帮我检查一下这段有没有 AI 味」→ 审计模式
- 「把这篇改得像人写的」→ 审计 + 改写模式
- 「这段散文是不是太文艺腔了」→ 文学档 + R 类信号

## Install in your AI agent

| Agent | Install |
|---|---|
| WorkBuddy | 复制到 `~/.workbuddy/skills/` |
| Claude Code | 复制到 `~/.claude/skills/` |
| Cursor | 复制到 `.cursor/skills/` |
| OpenClaw | `clawhub install text-humanize` |

## License

MIT (see [LICENSE](./LICENSE))

## Author

Evan Song · [github.com/Songhonglei](https://github.com/Songhonglei)

## Changelog

See [CHANGELOG.md](./CHANGELOG.md) for the full version history.
