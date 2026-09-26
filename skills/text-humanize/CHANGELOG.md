# Changelog

All notable changes to this skill are documented here.
Format loosely follows [Keep a Changelog](https://keepachangelog.com/); versions follow [SemVer](https://semver.org/).

### v1.1.0 (2026-09-26)

- **新增 SS-CN7 — 半角标点 / 中英标点混用**，列入「表面信号」，标注为优先级最高的一条。
  中文文本里半角引号（`"`）与标点周边空格是最可靠的机器指纹：中文输入法打不出半角引号，
  人也不会在标点旁敲空格。算法可统计，读者一眼也能看出。附自检方法（数全篇 `"` 应为 0）。
- **SKILL.md 新增「Chinese Mode: Run This First」章节**：把标点层自检提到文风审计之前，
  并要求审计报告把「标点/空格规范化」（机械替换）与「内容改动」（需作者判断）**分级列出**，
  让作者能跳过机械部分、只看真正的改动。
- `references/ai-smells-cn.md`：补入长文降级规则说明（此前仅本地存在，本次一并对齐）。
- 修正 `Repository` 字段：原指向 `github.com/Songhonglei/text-humanize`（该仓库不存在，404），
  改指 mono-repo 子目录 `better-office-work-flow/tree/main/skills/text-humanize`。README 的 clone 地址同步修正。

### v1.0.0 (2026-07-28)

- Initial open-source release
