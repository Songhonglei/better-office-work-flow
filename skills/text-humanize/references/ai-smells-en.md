# AI Smells Reference: Patterns That Make English Text Sound AI-Generated

> Derived from real HN flag data (9/10 comments flagged on 2026-07-28) and multi-platform testing.
> These patterns get detected by both algorithms (spam filters) and humans (community flaggers).

---

## Category 1: Structural Smells

### S1 — Multi-paragraph Essay Structure
**Signal:** 4+ paragraphs, each 2-3 sentences, with clear progression: intro → argument → counterpoint → conclusion.
**Why flagged:** Human comments are conversational, not structured essays. Nobody formats a forum reply like a blog post.
**Examples of S1:**
```
[Para 1: Acknowledge point, set up thesis]
[Para 2: Supporting argument with example]
[Para 3: Nuance/counterpoint]
[Para 4: Conclusion/synthesis]
```
**Fix:** Collapse to 1-2 paragraphs max. Break the structure. Don't "conclude."

### S2 — Numbered or Bullet Lists
**Signal:** `1. First point`, `2. Second point`, or bullet lists in comments.
**Why flagged:** Lists signal "content marketing," not conversation. Overwhelmingly AI-generated pattern.
**Fix:** Weave points into flowing text. If you must enumerate, use natural language: "one thing i found... also..."

### S3 — Quote-Then-Respond Pattern
**Signal:** Block-quoting a sentence from the parent comment, then responding to it.
**Why flagged:** This is a debate-club / academic pattern, not how people talk in forums.
**Fix:** Reference the parent casually: "what X said about Y made me think..."

---

## Category 2: Opening Smells

### O1 — Academic/Sympathy Openers
**Signal:** "This resonates...", "The key insight here is...", "This is a great point...", "I appreciate this perspective..."
**Why flagged:** These are LinkedIn-comment openers. They signal "I'm about to write an essay," not "I have a quick thought."
**Fix:** Open with your opinion directly, or with identity: "i build X and..."

### O2 — "From building/running/teaching X..." Opener
**Signal:** Starts by establishing credentials before making the point.
**Why flagged:** Combined with structured content below, it reads like a canned testimonial. Especially bad when followed by a list of features.
**Fix:** Weave identity into the point itself: "we had this exact problem in our coding app and..."

### O3 — "As someone who..." Opener
**Signal:** "As someone who has worked in X for Y years..."
**Why flagged:** Same pattern as O2 — credential-establishing preamble that humans rarely use in casual comments.
**Fix:** Skip the preamble. Just dive in.

---

## Category 3: Body Smells

### B1 — Balanced Argumentation
**Signal:** "On one hand... on the other hand..." or explicit trade-off analysis with equal weight to both sides.
**Why flagged:** Humans in forums take sides. They argue. Balanced "both sides have merit" is AI trying to be safe.
**Fix:** Have an opinion. Be slightly wrong. Be willing to say "honestly i think the other side is just wrong here."

### B2 — Feature/Product Listing
**Signal:** Describing what a project DOES in a list-like way: "it has drag-and-drop, multiple question types, i18n across 3 languages, and TTS..."
**Why flagged:** This is product pitch language. Even if true, it reads as self-promotion.
**Fix:** Describe ONE specific struggle, not the feature set: "the hardest part was making it work on crappy school Chromebooks."

### B3 — "The X isn't Y, it's Z" Formula
**Signal:** "The real gap isn't hours logged. It's transfer." / "The problem isn't volume, it's quality."
**Why flagged:** This is TED-talk / thought-leader sentence construction. Feels manufactured.
**Fix:** Be messier: "everyone talks about hours but honestly that wasnt our problem at all"

### B4 — Example Cascading
**Signal:** 3+ examples in sequence to "prove" a point: "A kid debugging Python... A kid in Roblox... A kid reading GDScript..."
**Why flagged:** Humans give one example that matters to them. Multiple examples feel like evidence-gathering.
**Fix:** One personal example, max two if they contrast naturally.

### B5 — Overuse of Collective "We"
**Signal:** Defaulting to "we" as the subject even for personal views: "We need to recognize...", "We should consider...", "We've found in practice that..."
**Why flagged:** AI defaults to the institutional, impersonal "we." Humans say "I" unless they genuinely speak for a team. Combined with multi-paragraph formatting, this reads like a press release or internal memo.
**Fix:** Use "I" for personal views and individual experience. Reserve "we" for actual team actions only. "I think this approach is wrong" beats "We should reconsider this approach."

### B6 — Overuse of Formal Connectors
**Signal:** Academic transition phrases: "Furthermore...", "Moreover...", "Consequently...", "In contrast...", "Additionally...", "Nevertheless..."
**Why flagged:** Natural conversation doesn't use these. They signal "I formatted this like a white paper" and create a mechanical rhythm that screams AI.
**Fix:** Drop them entirely. Short sentences that stand on their own feel more human. "Also..." is fine. "Furthermore..." is not.

---

## Category 4: Closing Smells

### C1 — Polished Conclusion / "Mic Drop"
**Signal:** "We're measuring the wrong meal." / "The appetite is there." / "Sometimes the right tool is no tool."
**Why flagged:** These are crafted for retweets/upvotes. They feel like someone spent 5 minutes polishing the last sentence.
**Fix:** End with uncertainty, an open question, or just stop mid-thought. Real comments trail off.

### C2 — "Curious what others think" / "Would love to hear..."
**Signal:** Polite invitation to discussion at the end.
**Why flagged:** Combined with an otherwise AI-structured comment, this is the cherry on top. It's the default "be helpful" closer.
**Fix:** If you want to invite discussion, be specific: "has anyone actually solved this?" not "curious what others think."

### C3 — Forced Positivity / Toxic Optimism
**Signal:** Ending with uplift or forced encouragement: "Keep pushing!", "We'll figure this out together!", "The future is bright!", "Stay curious!"
**Why flagged:** Real comment threads aren't motivational posters. AI loves a positive wrap-up because it's been RLHF'd to be helpful and agreeable. Humans in forums are more likely to end with a shrug, a question, or a problem.
**Fix:** Don't cheerlead. If the topic is hard, say it's hard. If you don't have a solution, say so. "Still struggling with this tbh" is infinitely more credible than "Together we can solve this!"

---

## Category 5: Surface Smells

### SS1 — Zero Typos
**Signal:** Perfect spelling, grammar, punctuation, capitalization throughout.
**Why flagged:** Humans make mistakes. Perfect text = AI.
**Fix:** Deliberately leave 1-2 missing apostrophes (`dont`, `isnt`, `thats`, `im`, `wont`). These are the most natural-looking "typos."

### SS2 — Em-Dashes (`—`)
**Signal:** Using proper em-dashes instead of double hyphens.
**Why flagged:** Em-dashes are formal writing. Most people type `--` or `-` in quick comments.
**Fix:** Use `--` or `-` instead.

### SS3 — Zero Filler Words
**Signal:** No `honestly`, `tbh`, `like`, `kinda`, `i mean`, `you know`, `i guess`.
**Why flagged:** Filler is the signature of human speech. Absence signals machine text.
**Fix:** Add 1-2 fillers in natural positions.

### SS4 — Uniform Sentence Length
**Signal:** Most sentences are 15-25 words, forming a consistent rhythm.
**Why flagged:** Human writing is jagged. Run-ons, fragments, very short sentences mixed with long ones.
**Fix:** Vary sentence length aggressively. Throw in a 3-word sentence after a 30-word one.

### SS5 — Semantic Punctuation
**Signal:** Using semicolons, colons for clause connection, parenthetical asides with em-dashes.
**Why flagged:** These are formal writing conventions. In comments, people use periods or just keep going.
**Fix:** Use commas and periods. No semicolons unless it's a code example.

---

## Platform-Specific Adjustments

### HN (Hacker News)
- **Highest scrutiny** for AI detection. The community actively flags.
- Comments should be 1-3 paragraphs, max 5-6 lines total.
- Technical detail is valued but must feel offhand, not pre-written.
- Self-deprecation and admitting ignorance play well.
- Never link to own project unless directly asked.

### Twitter / X
- Short-form: 1-2 sentences or a punchy thread.
- Voice is everything. Be slightly opinionated, slightly informal.
- Hashtags and @mentions are fine but don't overdo.
- Threads that look like essays (numbered 1/9, 2/9) are the new AI flag.

### Reddit
- Subreddit-specific. r/programming is closer to HN; r/CasualConversation is closer to group chat.
- General rule: write like you're talking to a smart friend, not publishing an article.
- Replies to existing comments are safer than top-level posts.

### Facebook / LinkedIn
- LinkedIn: the "professional" platform where AI content is ironically most accepted but least respected. Keep it casual.
- Facebook: group context matters. In tech groups, HN rules apply. In personal feed, just be human.

### Dev.to / Medium comments
- Similar to HN but slightly more tolerant of longer form.
- Still avoid structured essays. Be conversational.
