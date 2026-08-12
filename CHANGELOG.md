# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **zhihu-yanghao** v1.0.0 — 知乎养号 skill：三线选题模型 + 每日1回答（写→发布→折叠验证）+ 点赞互动（计数差值自校正防误 toggle），依赖 ego-browser

### Changed
- **zhihu-yanghao** v1.2.0 — 基于 2026-08-04~08-12 实战校验的重大修正：
  - 🐛 **点赞 selector 死路径修复**：旧 `button.VoteButton:not(.VoteButton--down)` / `button.VoteButton--up` 在新版知乎已失效，改为 `button[aria-label*="赞同"]`（aria-label 形如 `"已赞同 1020 "`，含尾空格必须 trim）。
  - 🐛 **已赞判定修正**：由 innerText 含「已赞同」改为 `classList.contains('is-active')`（class 含 `VoteButton is-active`），避免重复点赞取消。
  - ⚠️ **innerText 零宽字符坑**：实测点赞按钮 innerText 为 `"\u200b 已赞同 87"`（前导零宽字符），不能用 `===`/`startsWith` 精确匹配，一律走 aria-label + trim。
  - ✅ **发布验证强化**：`run_shift.js` 验证步骤加 `updated_time` + content 乱码检测，对应「发布中…」卡 UI 假象（8/5 验证）。
  - ✅ **连续发文错峰**：补充「同主线不同子方向也要错峰」（8/11 父子→8/12 中年女性实证），写入风控与选题策略。

## [1.0.0] - 2026-07-22

### Added
- **invoice-auto-forward** v1.0.0 — 邮箱发票自动转发 skill（IMAP 扫描 + PDF 解析 + SMTP 转发）
