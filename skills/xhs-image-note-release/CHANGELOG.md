# Changelog

All notable changes to this skill are documented here.
Format loosely follows [Keep a Changelog](https://keepachangelog.com/); versions follow [SemVer](https://semver.org/).

### v1.4.0 (2026-08-01)

- **Feature**: 新增「图文卡片」布局（`--layout image-text`），与现有「纯文字」布局（`--layout text`，默认）并列可选。
- **Image-text layout**: 顶部插画 + 窄列居中文字（默认宽度 65%）+ 底部署名短横线 + 账号，整体延续温暖简笔哲思风。
- **New theme**: `warm_illust`（温暖简笔哲思），配色与截图示例一致：米白底 `#FAF7F2`、黑线稿、琥珀色 `#D4A84B` 点缀。
- **New CLI args**:
  - `--layout {text,image-text}` — 切换布局
  - `--illustration PATH` — image-text 布局的插画文件（支持 `.svg` / `.png` / `.jpg`）
  - `--image-text-width RATIO` — 文字区宽度占比（0.5–0.8，默认 0.65）
- **SVG illustration handling**: 自动提取 SVG 第一个 `<g>` 元素，移除原 `transform` 后居中放置，避免与卡片坐标叠加偏移。
- **Raster illustration handling**: PNG/JPG 转 base64 data URI，按最大 55% 宽度 / 32% 高度等比缩放（`preserveAspectRatio="xMidYMid meet"`）。
- **Docs**: SKILL.md 与 README 主题画廊更新为 25 种主题，新增图文布局用法示例。

### v1.3.3 (2026-08-01)

- **Audit Fix**: UGLIC + skill-release-audit 两轮审计发现的全部 ERR/WARN 修复。
- **Fix (I1/U1)**: SKILL.md body 版本号 `1.3.0` 与 frontmatter `1.3.2` 不一致 → 统一为 `1.3.3`。
- **Fix (L1/C1)**: 删除 `NODE_BIN`/`NODE_PATH` 死代码（硬编码用户路径 `/Users/songhonglei/...`，全文件无引用）。
- **Fix (L2)**: 清理 `build_svg()` 中废弃的 `gradient_defs`/`gradient_id` 逻辑（SVG 侧渐变从未生效，实际由 CSS 处理）。
- **Fix (U2)**: 删除 4 个 `--show-*` 无操作 CLI 标志（`action="store_true", default=True` 永远为 True），只保留 `--hide-*`。
- **Fix (U3)**: Dependencies 表新增 Google Chrome / Chromium 依赖声明。
- **Fix (I2)**: 删除过期审计报告 `AUDIT-2026-07-31.md`（引用 v1.1.0，未被 SKILL.md 引用）。
- **Fix (I3)**: 删除 `__pycache__/` 构建产物。
- **Fix (C2)**: `render_png()` 改用 `try/finally` 确保临时 HTML 文件在 Chrome 崩溃时也能清理。
- **Fix (audit 模块6)**: 本地 skill 目录补齐 `README.md` 和 `LICENSE`（从 GitHub 仓库同步）。
- **Known**: I4 frontmatter 额外字段 (`version`/`bins`/`metadata`) 保留——ClawHub 发布需要，strict YAML 解析器可能报 warning 但不影响功能。

### v1.3.2 (2026-07-31)

- **Fix**: `doodle` theme font now uses **ZCOOL KuaiLe** (站酷快乐体) from Google Fonts — a playful, rounded Chinese display font that matches the hand-drawn doodle decorations. Previously Caveat/Permanent Marker are Latin-only and silently fell back to system Songti/PingFang, which broke the playful style.
- **Fix**: `steampunk` theme font now uses **Rye** (Western vintage slab) + **Noto Serif SC** from Google Fonts. Previously PingFang SC/Georgia looked too clean and modern for the dark brass/gear aesthetic; the new combination gives a vintage print feel consistent with steampunk.
- **Docs**: README theme preview images regenerated for doodle and steampunk to reflect the new typography.

### v1.3.1 (2026-07-31)

- **Fix**: XiaoHongShu style now has **two distinct modes** as originally documented in `text-to-elegant-image` repo: `xhs` = clean/formal mode, `xhs_rich` = lively/rich mode. Previously only the clean variant was implemented.
- **Mode A (`xhs`)**: white background + faint 45° red pinstripes + minimal dot accents — high breathing room for knowledge notes.
- **Mode B (`xhs_rich`)**: warm-pink gradient + hand-account dot pattern + glassmorphism blobs + three-segment gradient wave line — playful life-guide feel.
- **Total themes**: **24** (18 repo styles, with xhs split into A/B + 4 young-people + 1 warm original).
- **CLI**: added `--list-themes` to print all 24 themes and their display names.
- **Docs**: SKILL.md theme table updated to reflect all 24 themes and xhs/xhs_rich distinction.

### v1.3.0 (2026-07-31)

- **Breaking**: Port ALL 18 styles from `text-to-elegant-image` repo into the unified card generator. Total themes: **23** (18 repo + 4 young-people + 1 warm original).
- **Themes added**: cyberpunk, elegant, apple, cowork, newspaper, bloomberg, ink, steampunk, xhs, morandi (upgraded), glass, palace (upgraded), fresh, earthy, dreamy, macaron, carbon, vivid.
- **Each theme** extracts original repo's color palette, font stack, Google Fonts declaration, and decorative elements — all adapted to the unified layout (tag + centered text + footer).
- **Decorations**: 15 unique decoration styles (grid lines, scan lines, ink splashes, gears, glass blobs, leaves, sparkles, dots, etc.) — each theme has its own visual signature.
- **Google Fonts**: Themes requiring special fonts (palace: Ma Shan Zheng + ZCOOL XiaoWei; morandi/glass/fresh/earthy/dreamy/macaron/carbon/vivid: Inter; doodle: Caveat + Permanent Marker) all load via multi-mirror CDN fallback.

### v1.2.7 (2026-07-31)

- **Fix**: Remove the horizontal line above subtitle text in all themes. Subtitle now displays as `— 副标题 —` without the extra separator line above it, matching the user's reference screenshot style more closely.

### v1.2.6 (2026-07-31)

- **Feature**: Multi-mirror Google Fonts fallback for China network — `build_html()` now generates `<link>` tags for 3 CDN sources simultaneously: `fonts.loli.net` (community mirror), `fonts.googleapis.cn` (Google official China mirror), `fonts.googleapis.com` (original). Browser uses whichever loads first.
- **Feature**: JS-based font loading detection — after 3s timeout, checks `document.fonts.check()` for each declared font; if not loaded, dynamically injects mirror CSS as last resort
- **Why**: Google Fonts CDN (`fonts.googleapis.com`) is frequently blocked or extremely slow in mainland China, causing Chrome headless to fall back to system fonts and ruin theme-specific typography (e.g., palace theme falling back to Songti instead of Ma Shan Zheng calligraphy)

### v1.2.5 (2026-07-31)

- **Feature**: Google Fonts CDN loading in `build_html()` — themes declare `google_fonts` list, HTML auto-generates `<link>` tags to load fonts from `fonts.googleapis.com` regardless of local installation
- **Feature**: Add `palace` theme (故宫金红) — uses Ma Shan Zheng + ZCOOL XiaoWei calligraphic fonts from Google Fonts, gold-on-dark-red palette, corner ornaments and seal stamp decoration
- **Feature**: Add `morandi` theme (莫兰迪灰) — uses Inter from Google Fonts, desaturated muted palette
- **Improvement**: `doodle` theme now loads Caveat + Permanent Marker from Google Fonts for authentic hand-drawn feel
- **Fix**: Chrome `--virtual-time-budget=10000` added to ensure web fonts are fully loaded before screenshot capture
- **Architecture**: Every theme has `google_fonts` field (empty list = system fonts only), preventing silent fallback to wrong fonts

### v1.2.4 (2026-07-31)

- **Fix**: Card generator now auto-scales font size based on text length and line count to prevent overflow/cropping
- **Improvement**: Theme-specific font stacks for better style matching
  - `warm`/`minimal`: Songti SC serif (elegant/warm)
  - `y2k`: geometric sans-serif (tech/cool)
  - `doodle`: Chalkduster/Bradley Hand/Marker Felt with Kaiti fallback (hand-drawn feel)
  - `pop`: bold sans-serif (energetic)

### v1.2.3 (2026-07-31)

- **Feature**: Add built-in card generator (`references/card-generator/card_generator.py`) with 5 themes
  - `warm`（温暖哲思）、`minimal`（极简日系）、`y2k`（Y2K 千禧潮酷）、`doodle`（手绘涂鸦）、`pop`（渐变波普）
- **Feature**: Unified card layout matching classic XHS quote card style: top tag + quote marks, centered large text, bottom divider, page number and account
- **Feature**: Customizable footer parameters: `--hide-page-number`, `--hide-account`, `--hide-tag`, `--hide-subtitle`, `--page-number`, `--total-pages`, `--account`
- **Documentation**: Add card generation usage to SKILL.md

### v1.2.2 (2026-07-31)

- **Fix**: Support both UI entry points for entering image note page — try top "上传图文" tab first, fall back to "发布笔记" dropdown menu. Uses `input.upload-input` presence as the success check.
- **Fix**: Correct v1.2.0 changelog — both top tab and dropdown menu are valid, not a UI deprecation

### v1.2.1 (2026-07-31)

- **Fix**: Frontmatter dependency declaration for skill-release-audit
  - Add `bins: [ego-browser, node]`
  - Move env vars to `metadata.openclaw.requires.env`

### v1.2.0 (2026-07-31)

- **Fix**: Add support for top "上传图文" tab as an alternative entry point (both tab and dropdown menu work)
- **Fix**: Update publish success verification to also recognize `published=true` URL parameter
- **Fix**: Increase post-upload wait from 8s to 10s for more reliable image processing

### v1.1.0 (2026-07-31)

- **Security**: Fix shell variable injection risk in `publish_note.sh` — all user parameters now passed via `process.env` instead of shell heredoc expansion
- **Documentation**: Add formal Dependencies section with installation instructions and verification steps
- **Documentation**: Add reference load timing guidance for `references/publish-method.md`
- **Documentation**: Strengthen guardrail statements (advisory → mandatory)
- **Documentation**: Update Repository URL to multi-skill repo `better-office-work-flow`
- **Documentation**: Add input validation for TITLE (no single quotes) and BODY (no backticks/`${`)

### v1.0.0 (2026-07-31)

- Initial open-source release
