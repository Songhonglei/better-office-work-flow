# wb-token-analyzer

> WorkBuddy Token / Credit 使用量分析 Agent — 生成科技炫酷的 Neon Dashboard 报告。

## Features

- 按天 / 按模型汇总 Credits、Tokens、会话数
- Top N 消耗任务排名（标记自动化 / 手动）
- 自定义模型（`custom-local:*`）支持
- 6 类优化建议自动检测
- 深色科技风 HTML 报告（Chart.js 交互图表 + 粒子动画）

## Quick Start

```bash
# 分析最近 30 天
python3 wb_token_analyzer.py --days 30

# 分析最近 7 天，Top 20
python3 wb_token_analyzer.py --days 7 --top 20

# 导出到指定路径
python3 wb_token_analyzer.py --days 30 --export report.html

# 不自动打开浏览器
python3 wb_token_analyzer.py --days 30 --no-open
```

## Requirements

- Python 3.8+（仅标准库，无第三方依赖）
- WorkBuddy 本地数据库 `~/.workbuddy/workbuddy.db`
- 浏览器（Chart.js 从 CDN 加载）

## Install

```bash
# 复制到你的 agent skills 目录
cp -r skills/wb-token-analyzer ~/.workbuddy/skills/
```

## License

MIT (see [LICENSE](./LICENSE))

## Author

Evan Song · [github.com/Songhonglei](https://github.com/Songhonglei)
