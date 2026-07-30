# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [1.1.0] - 2026-07-30

### Fixed
- 添加 YAML frontmatter（`name` + `description`），Agent 可正常发现和触发
- 修复 `format_tokens(0)` 返回 "1 KB" 的误导显示
- 修复默认输出路径在无 `output/` 目录时崩溃（改为输出到 skill 目录 + `os.makedirs`）
- 消除 `MODEL_LABELS` 在 Python 和 HTML 中的重复定义（改为 JSON 注入）
- 修复 `switchChart()` 使用已废弃的全局 `event` 变量
- 修复 DB 方法未 null-check `self.conn` 的问题
- 新增 `--no-open` 参数，支持 headless / SSH 场景

### Removed
- 删除未使用的 `format_tokens_short()` 死代码

## [1.0.0] - 2026-07-30

### Added
- 初始版本
- Neon Dashboard 风格 HTML 报告（深色科技风 + 粒子动画 + Chart.js）
- 按天 / 按模型汇总，Top N 消耗任务排名
- 自定义模型（`custom-local:*`）支持
- 6 类优化建议自动检测
- CLI + Python API 双入口
