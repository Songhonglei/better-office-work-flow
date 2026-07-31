# xhs-image-note-release

> 通过 ego-browser 自动化发布小红书图文笔记，核心解决 closed Shadow DOM 发布按钮无法点击的问题。

## Features

- 全自动 9 步流程：打开创作平台 → 上传图片 → 填标题/正文 → 发布 → 清理
- CDP 批量上传图片（绕过 uploadFile 逗号分隔不生效的坑）
- **穿透 closed Shadow DOM 点击发布按钮**（`_onPublish()` 方法调用）
- 附带一键发布脚本，改 4 个参数即可复用
- 完整技术文档含 5 种失败方案对比表

## Dependencies

| 依赖 | 类型 | 安装方式 |
|------|------|----------|
| **ego-browser** (ego-lite) | CLI 工具 + Skill | `bash ~/.workbuddy/skills/ego-browser/scripts/install.sh` |
| **小红书账号** | 平台账号 | 在 ego-lite 中手动登录 creator.xiaohongshu.com |
| **WorkBuddy 沙箱关闭** | 环境配置 | WorkBuddy 设置 → 关闭沙箱 |

> 详见 [SKILL.md](./SKILL.md) 的 Dependencies 章节。

## Quick Start

```bash
# 从本仓库安装
git clone https://github.com/Songhonglei/better-office-work-flow.git
cp -r better-office-work-flow/skills/xhs-image-note-release ~/.workbuddy/skills/
```

## Usage

详细使用方法见 [SKILL.md](./SKILL.md)。

## Install in your AI agent

| Agent | Install |
|---|---|
| OpenClaw | `clawhub install xhs-image-note-release` |
| Claude Code | Manual: copy to `~/.claude/skills/` |
| Cursor | Manual: copy to `.cursor/skills/` |
| WorkBuddy | Manual: copy to `~/.workbuddy/skills/` |

## License

MIT (see repo [LICENSE](../../LICENSE))

## Author

Evan Song · [github.com/Songhonglei](https://github.com/Songhonglei)

## Changelog

See [CHANGELOG.md](./CHANGELOG.md) for the full version history.
