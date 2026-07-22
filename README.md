# Better Office Work Flow

> AI Agent Skill Suite — 办公自动化技能套件，覆盖发票处理、邮件管理等高频办公场景。

## Skills

| Skill | Description |
|---|---|
| [invoice-auto-forward](./skills/invoice-auto-forward/) | 邮箱发票自动转发：IMAP 扫描 + PDF 解析 + SMTP 转发，支持抬头白名单与定时无人值守 |

## Quick Start

每个 skill 独立可用，详见各自目录下的 `SKILL.md`。

```bash
# 克隆本仓库
git clone https://github.com/Songhonglei/better-office-work-flow.git

# 将需要的 skill 复制到你的 agent skills 目录
cp -r skills/invoice-auto-forward ~/.workbuddy/skills/
# 或 ~/.claude/skills/ / ~/.cursor/skills/ 等
```

## Install via Agent Platforms

| Platform | Install |
|---|---|
| OpenClaw | `clawhub install invoice-auto-forward` |
| Claude Code | Manual: copy to `~/.claude/skills/` |
| Cursor | Manual: copy to `.cursor/skills/` |
| WorkBuddy | Manual: copy to `~/.workbuddy/skills/` |

## License

MIT (see [LICENSE](./LICENSE))

## Author

Evan Song · [github.com/Songhonglei](https://github.com/Songhonglei)
