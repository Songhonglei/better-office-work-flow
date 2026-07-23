---
name: invoice-auto-forward
description: 自动扫描邮箱（默认QQ邮箱）里的发票邮件，解析发票PDF后按标准化模板转发给指定收件人（如财务/行政），支持抬头白名单过滤、定时无人值守运行。This skill should be used when 用户想把邮箱收到的发票自动转发给他人、设置发票自动归档/报销流程、配置发票转发规则（授权码/收件人/主题模板），或触发词包括：发票转发、发票自动转发、QQ邮箱发票、转发发票给财务、invoice forward。
version: 1.0.2
python_optional: ["pdfplumber", "pymupdf", "fitz"]
metadata: {"openclaw": {"envVars": [{"name": "INVOICE_FORWARD_CONFIG", "required": false, "description": "自定义 config.json 路径（可选）"}]}}
---

# Invoice Auto Forward — 邮箱发票自动转发

## 概述

本 skill 引导用户完成一次性配置（邮箱授权码、转发规则、收件人、主题/正文模板），之后即可自动扫描邮箱中的发票邮件，解析 PDF 发票并按统一格式转发给指定人。支持定时无人值守运行与对话手动触发。

- 主脚本：`scripts/invoice_forward.py`（子命令：`check` / `scan` / `run` / `parse`）
- 配置模板与全字段说明：`references/config.example.json`
- 排障与授权码获取指引：`references/troubleshooting.md`

## 依赖

- **Python 3.8+**，网络可达邮箱 IMAP/SMTP 服务器
- **首次使用自动安装**（`check --install-deps`，装到当前 Python 环境）：`pdfplumber`（发票解析首选）、`pymupdf`（兜底，二者至少其一）
- 手动安装等价命令：`pip install pdfplumber pymupdf`
- 可选环境变量：`INVOICE_FORWARD_CONFIG`（自定义 config.json 路径，默认 `~/.workbuddy/invoice-forward/config.json`）

## Setup 引导流程（首次使用，按序执行）

1. **检查依赖**：直接运行 `python3 scripts/invoice_forward.py check --install-deps`——缺少 `pdfplumber`/`pymupdf` 时会自动 pip 安装到当前 Python 环境（执行前向用户说明将安装这两个库）；若用户环境禁止自动安装，改为给出 `pip install pdfplumber pymupdf` 命令让其自行执行。
2. **收集凭证**：向用户询问邮箱地址与 SMTP/IMAP 授权码（QQ 邮箱获取路径：网页版 → 设置 → 账号 → POP3/IMAP/SMTP 服务 → 生成授权码，详见 references/troubleshooting.md）。写入 secrets 文件（默认 `~/.workbuddy/secrets/invoice-forward.env`），内容形如：
   ```
   MAIL_USER=user@qq.com
   MAIL_AUTH_CODE=xxxxxxxxxxxxxxxx
   ```
   随后立即 `chmod 600`。**授权码只进 secrets 文件，绝不写入 config.json、SKILL.md 或任何 skill 包内文件。**
3. **收集转发规则**（逐项询问，给默认值，允许用户直接回车采用）：
   - 抬头白名单：默认空 = 全部转发；填写后仅转发购买方抬头匹配的发票
   - 扫描天数：默认 7
   - 主题关键词：默认 `["发票"]`
   - 收件人（必填，支持多个）
   - 主题模板：默认 `{item} {amount} {date}`
   - 正文模板：默认含发票号码/日期/抬头/销售方/物品/金额六要素
4. **生成配置**：按 `references/config.example.json` 的结构写入 `~/.workbuddy/invoice-forward/config.json`。
5. **验证**：依次执行
   - `python3 scripts/invoice_forward.py check` — 体检全过才继续
   - `python3 scripts/invoice_forward.py scan` — 干跑预览，向用户展示将转发的邮件清单（主题渲染结果），请用户确认
6. **定时任务（可选，引导创建）**：询问用户是否创建定时任务及频率（如每 3 天）。WorkBuddy 环境用 automation 工具创建，任务内容就是执行 `run` 子命令并复述输出；非 WorkBuddy 环境给出 crontab 行。提醒：创建后核对下次运行时间是否符合预期。
7. **完成汇报**：告知用户配置位置、手动执行方式、如何修改规则。

## 日常使用

- **对话手动执行**：用户说"跑一次发票转发"等——先执行 `python3 scripts/invoice_forward.py scan` 向用户展示将发送清单，**用户确认后**再执行 `python3 scripts/invoice_forward.py run` 并复述输出（已发送/跳过/无PDF 各几封）。仅当用户明确说"直接发、不用确认"时才跳过 scan 直接 run。
- **指定扫描窗口**：`scan --days 30` / `run --days 30`（默认取 config.json 的 scan.days）。
- **预览不发送**：`python3 scripts/invoice_forward.py scan`（不写状态、不发送，随时可跑）。
- **修改规则**：直接编辑 `~/.workbuddy/invoice-forward/config.json` 后重跑 `check` 验证。
- **调试单张发票**：`python3 scripts/invoice_forward.py parse /path/to/发票.pdf`。

## 行为与边界

- 去重：按 Message-ID + 发票号双重去重，`run` 重复执行不会重复转发（状态存于 `~/.workbuddy/invoice-forward/processed.json`）。
- 无 PDF 的发票邮件（链接型/图片型）：跳过并列入"无PDF待人工"，不阻塞其他邮件。
- 防循环：收件人地址发来的邮件自动排除。
- 凭证安全：secrets 文件 chmod 600；排查问题时不得把授权码打印到聊天或日志。
- 发送侧记录：QQ 邮箱默认不把 SMTP 发出的邮件存入网页版「已发送」，验证送达以收件方为准（用户可在邮箱设置中开启保存）。

## 常见问题

优先查阅 `references/troubleshooting.md`（含授权码获取、QQ IMAP 三个实测坑、限流说明、扩展支持 163 等其他邮箱的方法）。
