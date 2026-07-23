# Changelog

All notable changes to this skill are documented here.
Format loosely follows [Keep a Changelog](https://keepachangelog.com/); versions follow [SemVer](https://semver.org/).

### v1.0.2 (2026-07-23)

- **Bug 修复**：`scan` 干跑预览漏报发票号重复。原 `_nos`（同轮内按发票号去重集合）累加被关在 `if do_send`（run 真实发送）分支内，`scan` 不维护它，导致预览与实际行为不一致——同一张发票被不同邮件多次投递时，预览会显示多封、而 run 实际只发一封。改为在循环体中无论是否发送都维护 `_nos`，使 `scan` 与 `run` 去重行为一致。

### v1.0.1 (2026-07-22)

- **Bug 修复**：`extract()` 销售方（seller）字段提取为空。原正则 `销\s*名称` 匹配不到标准增值税电子发票标签「销售方名称」（中间含"售方"），改为 `销售方\s*名称`。E2E 验证发现并修复。

### v1.0.0 (2026-07-22)

- Initial open-source release
