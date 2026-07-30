---
name: wb-token-analyzer
description: >
  查询 WorkBuddy token/credit 使用量，按天、按模型汇总，列出消耗最多的 Top 任务。
  给出节省 token 的优化建议，也包含自定义模型。触发词：token 使用量、token 分析、
  消耗报告、credit 统计、token 报表
---

# WorkBuddy Token 使用分析 Agent

- **Version**: 1.1.0
- **License**: MIT (see [LICENSE](./LICENSE))
- **Author**: Evan Song · [github.com/Songhonglei](https://github.com/Songhonglei)
- **Repository**: https://github.com/Songhonglei/better-office-work-flow
- **Changelog**: [CHANGELOG.md](./CHANGELOG.md)

> 查询 WorkBuddy 本地数据库中的 token/credit 使用量，生成科技炫酷风格的 Neon Dashboard 报告。

## 功能

- **按天汇总** — Credits / Tokens / 会话数 / 主要模型
- **按模型汇总** — 支持全部内置模型 + 自定义模型（`custom-local:*`）
- **Top N 消耗任务** — 排名 + 标题 + 模型 + 类型标记（自动/手动）
- **自动化任务统计** — 运行次数 / 成功 / 失败 / 天数
- **优化建议** — 6 类场景自动检测：模型选择、自定义模型、自动化优化、上下文管理、使用模式、通用优化
- **Neon Dashboard** — 深色科技风 + 动态粒子背景 + 渐变发光 + 交互式 Chart.js 图表

## 数据源

- 数据库路径: `~/.workbuddy/workbuddy.db`
- 核心表: `sessions` + `session_usage` + `automations` + `automation_runs`

## 用法

### 直接运行（推荐）

```bash
# 分析最近 30 天，生成 Neon Dashboard 报告并自动打开
python3 ~/.workbuddy/skills/wb-token-analyzer/wb_token_analyzer.py --days 30

# 分析最近 7 天，Top 20
python3 ~/.workbuddy/skills/wb-token-analyzer/wb_token_analyzer.py --days 7 --top 20

# 导出到指定路径
python3 ~/.workbuddy/skills/wb-token-analyzer/wb_token_analyzer.py --days 30 --export output/my_report.html

# 指定其他数据库路径
python3 ~/.workbuddy/skills/wb-token-analyzer/wb_token_analyzer.py --db /path/to/workbuddy.db --days 30

# 生成报告但不自动打开浏览器（适用于自动化/SSH 场景）
python3 ~/.workbuddy/skills/wb-token-analyzer/wb_token_analyzer.py --days 30 --no-open
```

### CLI 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--days` | int | 30 | 分析最近 N 天 |
| `--top` | int | 15 | Top N 消耗任务数量 |
| `--export` | str | 无 | 导出 HTML 到指定路径（不指定则输出到 skill 目录下） |
| `--db` | str | `~/.workbuddy/workbuddy.db` | 数据库路径 |
| `--no-open` | flag | false | 不自动打开浏览器 |

### 作为 Python 模块调用

```python
import sys, os
sys.path.insert(0, os.path.expanduser("~/.workbuddy/skills/wb-token-analyzer"))
from wb_token_analyzer import TokenAnalyzer

analyzer = TokenAnalyzer()
if not analyzer.conn:
    print("数据库不可用，请确认 WorkBuddy 已安装")
    exit(1)

sessions = analyzer.get_sessions_with_usage(days=30)
daily, models, top = analyzer.summarize(sessions)
suggestions = analyzer.generate_suggestions(sessions, models, daily)
analyzer.close()
```

## 错误处理

| 场景 | 表现 | 处理方式 |
|------|------|----------|
| 数据库文件不存在 | 脚本打印 `❌ 数据库文件不存在` 并退出 | 确认 WorkBuddy 已安装且 `~/.workbuddy/workbuddy.db` 存在 |
| 查询无数据 | 脚本打印 `⚠️ 该时间段内无数据` 并退出 | 增大 `--days` 参数，或确认该时间段内有使用记录 |
| 输出目录不存在 | 脚本自动创建目录 | 无需手动处理 |
| 浏览器无法打开 | 报告文件仍已生成，手动打开即可 | 用 `--no-open` 跳过自动打开，手动在浏览器中打开文件 |

## 输出

生成一个自包含的 HTML 文件，包含：
- 4 个动态统计卡片（Credits / Tokens / 会话数 / 自动化占比）
- 按天趋势柱状图（Credits + Tokens 双轴）
- 模型分布环形图 + 表格
- Top N 消耗任务列表（带进度条）
- 优化建议卡片（优先级标记）

## 依赖

- Python 3.8+
- 无第三方 Python 依赖（仅用标准库）
- HTML 报告需要浏览器打开，Chart.js 从 CDN 加载

## 文件结构

```
wb-token-analyzer/
├── SKILL.md                          # 本文件
├── wb_token_analyzer.py              # 主脚本（生成报告）
└── wb_token_report_template.html     # HTML 模板（Neon Dashboard）
```

## 自定义

### 修改模型映射

编辑 `wb_token_analyzer.py` 中的 `MODEL_LABELS` 字典。修改后 Python 端和 HTML 端会自动同步（标签通过 JSON 注入模板，无需修改 HTML）。

### 修改报告样式

编辑 `wb_token_report_template.html`，所有 CSS 和 JS 都在单文件中，无外部依赖（除 Chart.js CDN）。

### 添加优化建议

在 `generate_suggestions()` 方法中按相同格式追加。
