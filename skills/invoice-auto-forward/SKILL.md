---
name: invoice-auto-forward
description: 自动扫描邮箱（支持 QQ/163/126 等主流邮箱，provider 一键切换）里的发票邮件，解析发票（PDF/OFD/XML 三种格式）后按标准化模板转发给指定收件人（如财务/行政），支持抬头白名单过滤、定时无人值守运行、发送节奏控制（防反垃圾风控）。对「链接型发票」（邮件只有下载链接、无 PDF 附件，如腾讯云电子发票）也能自动扫描正文链接并下载发票文件（PDF/OFD/XML）后转发。This skill should be used when 用户想把邮箱收到的发票自动转发给他人、设置发票自动归档/报销流程、配置发票转发规则（授权码/收件人/主题模板），或触发词包括：发票转发、发票自动转发、QQ邮箱发票、163邮箱发票、126邮箱发票、链接型发票、OFD发票、XML发票、转发发票给财务、invoice forward。
version: 1.0.7
python_optional: ["pdfplumber", "pymupdf", "fitz"]
metadata: {"openclaw": {"envVars": [{"name": "INVOICE_FORWARD_CONFIG", "required": false, "description": "自定义 config.json 路径（可选）"}]}}
---

# Invoice Auto Forward — 邮箱发票自动转发

## 概述

本 skill 引导用户完成一次性配置（邮箱授权码、转发规则、收件人、主题/正文模板），之后即可自动扫描邮箱中的发票邮件，解析 PDF 发票并按统一格式转发给指定人。支持定时无人值守运行与对话手动触发。

- 主脚本：`scripts/invoice_forward.py`（子命令：`setup` / `check` / `scan` / `run` / `parse`）
- 配置模板与全字段说明：`references/config.example.json`
- 排障与授权码获取指引：`references/troubleshooting.md`

## 依赖

- **Python 3.8+**，网络可达邮箱 IMAP/SMTP 服务器
- **首次使用自动安装**（`check --install-deps`，装到当前 Python 环境）：`pdfplumber`（PDF 解析首选）、`pymupdf`（PDF 兜底，二者至少其一）。**OFD / XML 用 Python 内置 `zipfile` + `xml.etree` 解析，无需任何额外依赖。**
- 手动安装等价命令：`pip install pdfplumber pymupdf`
- 可选环境变量：`INVOICE_FORWARD_CONFIG`（自定义 config.json 路径，默认 `~/.workbuddy/invoice-forward/config.json`）

## Setup 引导流程（首次使用，按序执行）

1. **检查依赖**：直接运行 `python3 scripts/invoice_forward.py check --install-deps`——缺少 `pdfplumber`/`pymupdf` 时会自动 pip 安装到当前 Python 环境（执行前向用户说明将安装这两个库）；若用户环境禁止自动安装，改为给出 `pip install pdfplumber pymupdf` 命令让其自行执行。
2. **收集凭证**：向用户询问邮箱地址与 SMTP/IMAP 授权码。QQ 获取路径：网页版 → 设置 → 账号 → POP3/IMAP/SMTP 服务 → 生成授权码；163/126 获取路径：网页版 → 设置 → 开启 POP3/SMTP/IMAP 服务（默认禁用）→ 短信验证 → 生成授权码（详见 references/troubleshooting.md）。这些值与转发规则可**一次性交给 `setup` 子命令**完成（推荐，见下方「一键配置」），它会验证连通性后写入 secrets（chmod 600）+ config.json，无需手工改文件。**授权码只进 secrets 文件，绝不写入 config.json、SKILL.md 或任何 skill 包内文件。**
3. **收集转发规则**（逐项询问，给默认值，允许用户直接回车采用）：
   - 抬头白名单：默认空 = 全部转发；填写后仅转发购买方抬头匹配的发票
   - 扫描天数：默认 7
   - 主题关键词：默认 `["发票"]`
   - 收件人（必填，支持多个）
   - 主题模板：默认 `{item} {amount} {date}`
   - 正文模板：默认含发票号码/日期/抬头/销售方/物品/金额六要素
4. **生成配置**：按 `references/config.example.json` 的结构写入 `~/.workbuddy/invoice-forward/config.json`（用 `setup` 子命令则自动生成）。
5. **验证**：依次执行
   - `python3 scripts/invoice_forward.py check` — 体检全过才继续
   - `python3 scripts/invoice_forward.py scan` — 干跑预览，向用户展示将转发的邮件清单（主题渲染结果），请用户确认
6. **定时任务（可选，引导创建）**：询问用户是否创建定时任务及频率（如每 3 天）。WorkBuddy 环境用 automation 工具创建，任务内容就是执行 `run` 子命令并复述输出；非 WorkBuddy 环境给出 crontab 行。提醒：创建后核对下次运行时间是否符合预期。
7. **完成汇报**：告知用户配置位置、手动执行方式、如何修改规则。

## 一键配置（setup 子命令，推荐）

把上面步骤 2–5 合并成一条命令：自动合并已有配置、应用你给的参数、交互补缺失项、验证 IMAP/SMTP 连通性，**确认授权码真能用后才写入 secrets（chmod 600）与 config.json**。凭证绝不会写进 config.json。

```bash
python3 scripts/invoice_forward.py setup \
  --user yourname@163.com \         # 登录邮箱；省略 provider 时由域名推导主机
  --provider 163 \                  # qq/163/126/yeah 或域名；可省略，由 --user 域名自动推导
  --auth-code xxxxxxxx \            # IMAP/SMTP 授权码；不传则交互隐藏输入（getpass，不回显）
  --to finance@example.com \        # 转发收件人，多个用空格分隔
  --days 7 \                        # 扫描天数窗口
  --buyer-whitelist "公司A" "公司B" \  # 抬头白名单，空=全部
  --interval 3 --batch-limit 20 \   # 163/126 防反垃圾节奏（QQ 可设 0）
  --fetch-links \                   # 启用链接型发票抓取（默认开）；--no-fetch-links 关闭
  --link-domains myqcloud.com tencent.com \  # 仅下载这些域名后缀的链接（空=全部，靠 PDF 闸门兜底）
  --config ~/.workbuddy/invoice-forward/config.json   # 可放任意路径；默认即此
```

要点：
- **准确性保证**：默认会真实登录 IMAP + SMTP 验证；验证不通过**绝不写 secrets**（config.json 仍会保存，方便重跑）。加 `--no-verify` 可跳过（仅当你确定授权码正确、或离线调试时）。
- **幂等合并**：目标 config.json 已存在时在其基础上合并，不会清空你已有的其他设置。
- **交互兜底**：缺 `--user`/`--auth-code` 等且在终端（tty）下运行时会逐项交互询问；非交互（agent 批处理）则缺项直接报错，提示补参数。
- **域名推导**：不传 `--provider` 时，按 `--user` 域名（如 `163.com`/`126.com`）自动选主机，少记一个参数。
- 写盘后打印配置路径与权限，并提示下一步跑 `check`。

## 日常使用

- **对话手动执行**：用户说"跑一次发票转发"等——先执行 `python3 scripts/invoice_forward.py scan` 向用户展示将发送清单，**用户确认后**再执行 `python3 scripts/invoice_forward.py run` 并复述输出（已发送/跳过/无PDF 各几封）。仅当用户明确说"直接发、不用确认"时才跳过 scan 直接 run。
- **指定扫描窗口**：`scan --days 30` / `run --days 30`（默认取 config.json 的 scan.days）。
- **预览不发送**：`python3 scripts/invoice_forward.py scan`（不写状态、不发送，随时可跑）。
- **修改规则**：直接编辑 `~/.workbuddy/invoice-forward/config.json` 后重跑 `check` 验证。
- **调试单张发票**：`python3 scripts/invoice_forward.py parse /path/to/发票.pdf`（或 `.ofd` / `.xml`，自动识别格式）。

## 行为与边界

- 去重：按 Message-ID + 发票号双重去重，`run` 重复执行不会重复转发（状态存于 `~/.workbuddy/invoice-forward/processed.json`）。
- **链接型发票（无 PDF 附件）**：邮件没有发票附件时，自动扫描正文链接（HTML 的 href/src + 纯文本 URL，HTML 实体反转义）逐一尝试下载，**仅当最终响应确为发票文件才采用**——支持 PDF / OFD / XML 三种格式（按 Content-Type / Content-Disposition 后缀 / 魔数判定：PDF=`%PDF`、OFD=ZIP 且含 `OFD.xml`、XML=`<?xml` 开头），随后照常解析转发。适用于腾讯云电子发票等"邮件内只有下载链接"的场景（实测：腾讯云用 COS 预签名 URL，无需登录即可下载）。链接均失败才列入"无发票待人工"并注明原因（链接未返回发票文件=可能需登录或链接已过期 / 链接抓取已禁用）。
- **链接抓取安全闸门**：`config.json` 的 `scan` 段可设 `fetch_links`（默认开）、`link_domains`（非空时仅下载这些域名后缀的链接，如 `["myqcloud.com","tencent.com"]`，空=全部）、`link_timeout`（下载超时秒）、`link_max_bytes`（单链接上限字节，默认 25MB）、`link_user_agent`。仅 http(s) 会被下载；字面量私有/环回/链路本地 IP 会被拒绝（SSRF 基础防护）；真正兜底的是"仅接受发票格式响应"——绝不执行下载内容，只保存发票字节。
- 防循环：收件人地址发来的邮件自动排除。
- 发送节奏（防反垃圾风控）：`config.json` 的 `send` 段可设 `interval`（每封最小间隔秒）、`jitter`（额外随机秒上限）、`batch_limit`（单批上限，超出下轮续跑）。QQ 默认 0 即可；163/126 等严格风控邮箱建议 `interval>=3`、`batch_limit<=20`，主题模板建议加 `{invoice_no}` 提升区分度。
- 多邮箱：支持在 `account.provider` 写 `qq`/`163`/`126`/`yeah` 或域名后缀自动选主机；也可直接写 `imap_host`/`smtp_host` 覆盖。网易系（163/126）登录后会自动发 IMAP `ID` 自报身份以绕过 "Unsafe Login" 风控（否则选文件夹会被拒）。
- 凭证安全：secrets 文件 chmod 600；也支持环境变量 `MAIL_USER`/`MAIL_AUTH_CODE` 临时传入（优先级高于 secrets 文件，便于隔离验证 / CI，授权码免落盘）；排查问题时不得把授权码打印到聊天或日志。
- 发送侧记录：QQ 邮箱默认不把 SMTP 发出的邮件存入网页版「已发送」，验证送达以收件方为准（用户可在邮箱设置中开启保存）。

## 常见问题

优先查阅 `references/troubleshooting.md`（含授权码获取、QQ IMAP 三个实测坑、限流说明、扩展支持 163 等其他邮箱的方法）。
