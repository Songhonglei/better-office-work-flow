# Changelog

All notable changes to this skill are documented here.
Format loosely follows [Keep a Changelog](https://keepachangelog.com/); versions follow [SemVer](https://semver.org/).

### v1.0.3 (2026-07-23)

- **多邮箱支持（provider preset）**：`account` 新增 `provider` 字段（`qq`/`163`/`126`/`yeah` 或域名后缀如 `163.com`），配置即自动填入对应 IMAP/SMTP 主机与端口，免去手动查 host。同时修了 `__version__` 长期停留在 1.0.0 的版本号不一致问题（现与包版本对齐 1.0.3）。
- **发送节奏参数（防反垃圾风控）**：新增 `send` 配置段——`interval`（每封最小间隔秒）、`jitter`（额外随机秒上限）、`batch_limit`（单批最多发送封数，超出则本轮延后、下轮自动续跑，配合 `processed.json` 去重天然支持）。163/126 等严格风控邮箱必配，避免相似内容 + 脚本连发被判群发机器人。
- **文档**：troubleshooting.md 新增「163/126 接入」专节（授权码获取路径、风控提醒、发送节奏建议、接入步骤）；config.example.json 增加 `provider` 与 `send` 示例；SKILL.md 描述与支持范围扩至 163/126。

### v1.0.2 (2026-07-23)

- **Bug 修复**：`scan` 干跑预览漏报发票号重复。原 `_nos`（同轮内按发票号去重集合）累加被关在 `if do_send`（run 真实发送）分支内，`scan` 不维护它，导致预览与实际行为不一致——同一张发票被不同邮件多次投递时，预览会显示多封、而 run 实际只发一封。改为在循环体中无论是否发送都维护 `_nos`，使 `scan` 与 `run` 去重行为一致。

### v1.0.1 (2026-07-22)

- **Bug 修复**：`extract()` 销售方（seller）字段提取为空。原正则 `销\s*名称` 匹配不到标准增值税电子发票标签「销售方名称」（中间含"售方"），改为 `销售方\s*名称`。E2E 验证发现并修复。

### v1.0.0 (2026-07-22)

- Initial open-source release
