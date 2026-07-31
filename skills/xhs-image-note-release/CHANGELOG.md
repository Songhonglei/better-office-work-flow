# Changelog

All notable changes to this skill are documented here.
Format loosely follows [Keep a Changelog](https://keepachangelog.com/); versions follow [SemVer](https://semver.org/).

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
