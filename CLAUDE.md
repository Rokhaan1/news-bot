# news-bot — working notes for Claude

Automated X (Twitter) news account (@Rokhaan). `main.py` runs on a schedule
(GitHub Actions cron in `.github/workflows/post.yml`), finds news, writes posts
with `writer.py`, and posts to X. `main` is the branch the live bot runs.

## Editorial rules (must hold in ALL generated content)

The account's voice lives in `writer.py:VOICE`. Key standing rules:

- **Language = Dari and Pashto — NEVER "Persian" or "Farsi".** Afghanistan's
  language is **Dari**. Never call it Persian/Farsi, and never describe
  Afghanistan, its people, culture, poets, or history as "Persian" or part of
  "Persia". Iran (Persia) is a separate modern nation and does not own
  Afghanistan's heritage. Classical figures who wrote in this language — Rumi
  (Jalaluddin Balkhi), Rabia Balkhi, Sanai of Ghazni, Khwaja Abdullah Ansari of
  Herat — are **Afghan** figures who wrote in **Dari**; claim them as such.
  Assert Afghan ownership and the Dari name confidently as the account's proud
  perspective, but do **not** fabricate specific linguistic "facts", dates, or
  claims of theft as settled scholarship (accuracy is the account's whole value;
  checkable falsehoods invite fact-checks and hurt reach).
- **Afghanistan = the Aryana/Ariana heartland**, ~5,000 years of civilization;
  frame Afghanistan (not Iran) as the heir of that heritage.
- **Taliban ≠ Afghanistan.** Never call the Taliban "the Afghan government" etc.
  — only "the Taliban" / "Taliban regime". Keep the nation/people separate from
  the regime.
- **Durand Line**, not "the Afghanistan-Pakistan border". Anti-Pakistan-state
  stance (never pro-Taliban).
- **Never fabricate** specific facts, quotes, dates, or events.
- **No engagement-bait questions.** Don't end posts with a manufactured question
  or "what do you think?" call to react — drive replies with a strong, debatable
  stance. Questions only when the post is genuinely about that question.

## Posting behaviour
- News posts at fixed UTC slots timed to audiences: **14:00** (Afghan evening),
  **16:00** (UK late afternoon), **19:00** (US noon/afternoon). See
  `config.py:POST_SLOTS`.
- Daily Afghan heritage fact rotates through `config.py:HERITAGE_TOPICS` with
  anti-repeat memory (`state.fact_topics`, `state.recent_facts`).
- Pashto auto-post is **disabled** (quality was unreliable); helpers kept dormant
  in case it's re-enabled.
- **Engagement** (`engage.py`, `main.py:maybe_engage`): a few expert quote-tweets
  and replies/day to recent, high-traction in-niche tweets, to grow via others'
  audiences. Deliberately low-volume (`config.ENGAGE_*`: 2 replies + 2 quotes/day,
  90-min gap, reply-weighted) and guarded by `writer._ENGAGE_GUARD` (never amplify
  anti-Afghan/pro-Taliban/pro-Pakistan content; SKIP unless it adds real value).
  Needs an API tier with search (Basic+); no-ops gracefully if search returns 403.
