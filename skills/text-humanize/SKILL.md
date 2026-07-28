---
name: text-humanize
description: >
  Audit and de-AI text for social platforms — bilingual (English + 中文). Auto-detects language,
  then detects AI-generated patterns: structural tells, opening/closing clichés, surface signals,
  and platform-specific red flags. Rewrites text to sound like a real human wrote it. Use when
  checking text for "AI smell" before posting to HN, Twitter/X, Reddit, Facebook, LinkedIn,
  Dev.to, 微信公众号, 知乎, 小红书, 即刻, 微博, 抖音, B站, or any public forum.
---

- **Version**: 1.0.0
- **License**: MIT
- **Author**: Evan Song · [github.com/Songhonglei](https://github.com/Songhonglei)
- **Repository**: https://github.com/Songhonglei/text-humanize

# Text Humanize — 中英文去 AI 味检测 + 改写

Bilingual AI-smell auditor and humanizer. Auto-detects whether input is English or Chinese, then applies the right detection patterns and rewrite rules. Built from real flagged data on English platforms (HN, Reddit) and Chinese platforms (公众号, 知乎, 小红书).

## Language Auto-Detection

Before starting any audit, detect the input language:

1. Count CJK characters (Unicode range U+4E00–U+9FFF, U+3400–U+4DBF, U+F900–U+FAFF).
2. Count Latin characters (a-z, A-Z).
3. **Rule:** If CJK characters > 50% of total letters → **Chinese mode**. Otherwise → **English mode**.
4. If the user explicitly says "用中文优化" or "用英文优化", override auto-detection.
5. For mixed text (e.g., Chinese with English code blocks), detect based on the natural-language portions only, ignoring code.

## How It Works — Two Modes

Both modes work identically for English and Chinese; just the pattern catalog differs.

### Mode A: Audit Only (trigger: "check", "audit", "检查", "看看")

1. Auto-detect language.
2. Load the appropriate reference: `references/ai-smells-en.md` for English, `references/ai-smells-cn.md` for Chinese.
3. Scan the text against all 5 smell categories (Structural, Opening, Body, Closing, Surface).
4. Produce a concise audit report listing every detected smell with:
   - The smell code (e.g., S1, O-CN1, B-CN3, SS-CN1)
   - The specific phrase/pattern triggering it
   - A 1-line fix suggestion (in the text's language)
5. Give an overall "AI smell score":
   - **🟢 Green (1-2 smells):** Looks human. Minor suggestions only.
   - **🟡 Yellow (3-5 smells):** Some AI patterns. Consider fixes.
   - **🔴 Red (6+ smells):** High risk of flagging. Strongly recommend rewriting.

### Mode B: Audit + Rewrite (trigger: "humanize", "rewrite", "fix", "优化", "改一下", "去AI味")

1. Run the full audit (Mode A).
2. Produce a rewritten version following language-specific rules (see below).
3. Show the original and rewrite side-by-side with a brief summary of what changed.
4. Ask the user which version to use (or if they want further tweaks).

---

## English Mode

Refer to `references/ai-smells-en.md` for the complete English pattern catalog. Summary of categories:

| Category | Code | Key Signals |
|----------|------|-------------|
| Structural | S1-S3 | 4+ paragraphs, numbered lists, quote-then-respond |
| Opening | O1-O3 | "This resonates...", "From building X...", "As someone who..." |
| Body | B1-B6 | Balanced argumentation, feature listing, insight formula, example cascading, collective "we", formal connectors |
| Closing | C1-C3 | Polished conclusion, "Curious what others think", forced positivity |
| Surface | SS1-SS5 | Zero typos, em-dashes, no filler words, uniform sentence length, semantic punctuation |

### English Rewriting Principles

1. **Structure killer.** Destroy essay structure. 1-2 paragraphs max. No intro-body-conclusion.
2. **Opinion injector.** Take a side. "i think X is wrong" beats "X has merits but also drawbacks."
3. **Human fingerprint.** Add at least: 1 typo (missing apostrophe), 1 filler word, 1 moment of uncertainty.
4. **Experience, not features.** Express a specific struggle, not a feature list.
5. **Stop early.** End with uncertainty or trail off. No polished conclusion.

### English Platform Rules

| Platform | Max Length | Tone | Special Rules |
|----------|-----------|------|---------------|
| **HN** | 1-3 paragraphs, 5-6 lines | Technical, opinionated, humble | Strictest AI detection. No self-linking. Self-deprecation is currency. |
| **Twitter/X** | 1-2 sentences or punchy thread | Punchy, informal, voice-driven | Numbered threads (1/9) = AI flag. Each tweet stands alone. |
| **Reddit** | 1-3 paragraphs | Smart-friend-chat | Subreddit-dependent. r/programming ≈ HN. |
| **Facebook** | 1-2 short paragraphs | Casual, personal | Tech groups: HN rules. Personal feed: be human. |
| **LinkedIn** | 1-2 paragraphs | Casual professional | Avoid "thought leader" tone. |
| **Dev.to** | 2-3 paragraphs | Technical but conversational | Slightly more length-tolerant than HN. |

If no English platform is specified, default to HN rules (strictest baseline).

---

## 中文模式 (Chinese Mode)

Refer to `references/ai-smells-cn.md` for the complete Chinese pattern catalog. Summary of categories:

| 类别 | 代码 | 关键信号 |
|------|------|----------|
| 结构 | S-CN1~S-CN4 | 议论文三段式、"首先其次最后"、编号列表、引用原文再回复 |
| 开头 | O-CN1~O-CN3 | "这个问题很有启发性…"、"作为一个…"、"有道理但是…" |
| 正文 | B-CN1~B-CN7 | 书面连接词过频、对称辩证、金句提炼、举例论证、"我们"滥用、中英混杂、功能罗列 |
| 结尾 | C-CN1~C-CN3 | 升华式收尾、开放式互动、正能量用力过猛 |
| 表面 | SS-CN1~SS-CN6 | 零错别字、句式工整、缺少语气词、句号强迫症、破折号"——"、翻译腔 |

### 中文改写黄金规则

1. **结构打碎。** 不要开头-中间-结尾。1-2 段，直接亮态度。
2. **加语气词。** 至少 1-2 个：吧、嘛、呢、啊、就、还挺、讲真、说实话。
3. **加 1-2 个「错」。** 的/地/得混用，或在/再混用。不要太刻意，2 个就够了。
4. **短句为主，偶尔混长句。** 节奏参差不齐才像人。
5. **有态度。** 敢说"我觉得不对"、"试过就知道坑"。不要和稀泥。
6. **结尾不升华。** 用不确定感收尾或戛然而止。不要"值得深思"。
7. **个人经验 > 通用道理。** 讲自己踩过的坑，不讲放之四海而皆准的道理。
8. **宁可碎一点。** 半句话、反问句、语气词结尾都行，不要追求「完整」。

### 中文平台特定规则

| 平台 | 长度限制 | 语气 | 特别注意 |
|------|---------|------|----------|
| **微信公众号** | 正文 500-1500 字；评论 1-3 句 | 可稍正式但有个性 | AI 检测最严。致命伤：标题党 + 三段式 + 升华结尾 |
| **知乎** | 回答不限；评论 2-5 句 | 有态度，不怕杠 | 致命伤："谢邀"开头 + 分点论述 + "以上"结尾 |
| **小红书** | 正文 50-200 字；评论 1-3 句 | 轻松、口语化 | 善用 emoji 但别每句都加。标签区和正文分开 |
| **即刻** | 1-3 句 | 极随意 | 语气词决定生死。不要长篇大论 |
| **微博** | 1-3 句 | 直接、有梗 | 可用网络用语，但不堆砌 |
| **B站评论区** | 1-3 句 | 弹幕风格 | 语气词 + emoji 友好 |
| **抖音评论区** | 1 句，最多 2 句 | 极短 | 超过 3 句 = 直接判 AI |
| **朋友圈** | 1-3 句 | 熟人聊天感 | 不要"通知"语气，不要排比句 |

如果没有指定中文平台，默认按**知乎评论区**规则处理（适中长度 + 有态度的口语）。

---

## Edge Cases

- **Very short text (under 20 words / 30 字):** Almost certainly human. Only check surface smells. Don't over-audit.
- **Technical code-heavy text:** Code blocks are exempt. Only audit the natural language portions.
- **User wants formal tone:** Skip typo/错别字 injection. Still de-structure and remove academic openers.
- **Text already has human markers:** If 3+ human fingerprints already present, focus on structural smells only. Don't over-humanize.
- **Mixed EN/CN content:** Audit each language block separately against its own catalog. If truly bilingual, note it and ask the user which language to prioritize.
- **Quoted text / retweets:** Only audit the user's own added text. Quoted/retweeted content is exempt.
