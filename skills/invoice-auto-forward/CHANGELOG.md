# Changelog

All notable changes to this skill are documented here.
Format loosely follows [Keep a Changelog](https://keepachangelog.com/); versions follow [SemVer](https://semver.org/).

### v1.0.1 (2026-07-22)

- **Bug 修复**：`extract()` 销售方（seller）字段提取为空。原正则 `销\s*名称` 匹配不到标准增值税电子发票标签「销售方名称」（中间含"售方"），改为 `销售方\s*名称`。E2E 验证发现并修复。

### v1.0.0 (2026-07-22)

- Initial open-source release
