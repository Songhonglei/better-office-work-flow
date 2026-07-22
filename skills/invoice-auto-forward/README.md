# invoice-auto-forward

> 自动扫描邮箱发票邮件，解析 PDF 发票并按模板转发给指定收件人（财务/行政），支持抬头白名单过滤与定时无人值守运行。

## Features

- **全自动发票转发**：IMAP 扫描 + PDF 解析 + SMTP 转发，一次配置永久运行
- **智能去重**：按 Message-ID + 发票号双重去重，重复执行不重复转发
- **抬头白名单**：可按购买方抬头过滤，只转发匹配的发票
- **干跑预览**：`scan` 模式预览将发送清单，确认后再 `run`
- **定时无人值守**：支持 crontab / agent automation 定时执行
- **多邮箱支持**：默认 QQ 邮箱，兼容 163 等支持 IMAP 的邮箱

## Quick Start

```bash
# Install (clawhub)
clawhub install invoice-auto-forward

# Or clone directly
git clone https://github.com/Songhonglei/better-office-work-flow.git
```

## Usage

详细使用方法见 [SKILL.md](./SKILL.md)。

## Install in your AI agent

| Agent | Install |
|---|---|
| OpenClaw | `clawhub install invoice-auto-forward` |
| Claude Code | Manual: copy to `~/.claude/skills/` |
| Cursor | Manual: copy to `.cursor/skills/` |

## License

MIT (see [LICENSE](../../LICENSE))

## Author

Evan Song · [github.com/Songhonglei](https://github.com/Songhonglei)

## Changelog

See [CHANGELOG.md](./CHANGELOG.md) for the full version history.
