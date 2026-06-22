"""
AI writer (Claude Haiku) — rewrites headlines into @Rokhaan's personal voice,
judges tone (e.g. skips anti-Afghanistan cricket), and writes viral video
captions. Reads ANTHROPIC_API_KEY from the environment.

SAFETY: if the model returns a refusal / meta reply ("I can't...", etc.) or
junk, we never post it — news falls back to the raw headline, video is skipped.
"""
import anthropic

MODEL = "claude-haiku-4-5"   # cheapest capable model (~$1 / 1M input tokens)
_client = None


def _c():
    global _client
    if _client is None:
        _client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY
    return _client


VOICE = (
    "You write posts for @Rokhaan, a fast, credible X (Twitter) news account "
    "covering global breaking news, US foreign policy, Afghanistan, the FIFA "
    "World Cup, and Afghan cricket. Voice: sharp, confident, human and personal "
    "— like an individual journalist with a point of view, not a wire service. "
    "Never invent facts beyond what the headline states. A pro-Afghanistan "
    "perspective is welcome, but never at the cost of the truth."
)

# Phrases that mean the model replied ABOUT the task instead of doing it.
# These never appear in a normal third-person news rewrite, so they're a
# reliable "do not post this" signal.
_BAD = [
    "i can't", "i cannot", "i am unable", "i'm unable", "unable to",
    "as an ai", "as a language model", "language model", "i apologize",
    "i apologise", "i'm sorry", "i am sorry", "i won't", "i will not",
    "i don't have", "i do not have", "i'm not able", "i am not able",
    "cannot fulfill", "can't fulfill", "cannot assist", "can't assist",
    "cannot help", "can't help", "i'm just an", "i cannot create",
    "i can't create", "i cannot write", "i can't write", "i need more",
    "could you", "please provide", "the task", "you have asked",
]


def _looks_bad(text):
    if not text or len(text.strip()) < 8 or len(text) > 320:
        return True
    low = text.lower()
    return any(p in low for p in _BAD)


def write_news(pillar, headline, source):
    """Returns {"skip": bool, "text": str}. Safe — never returns junk text."""
    prompt = (
        f"Pillar: {pillar}\nHeadline: {headline}\nSource: {source}\n\n"
        "Decide and respond:\n"
        "- If this item is embarrassing/negative for Afghanistan in CRICKET "
        "(e.g. Afghanistan losing heavily), OR is off-topic, OR is not "
        "substantive news, reply with exactly: SKIP\n"
        "- Otherwise reply with ONLY the rewritten post in the account's voice "
        "(max 240 characters, no quotes, no preamble, no hashtags, third person). "
        "A source credit is added separately, so don't include one."
    )
    try:
        resp = _c().messages.create(
            model=MODEL, max_tokens=400, system=VOICE,
            messages=[{"role": "user", "content": prompt}],
        )
        out = next(b.text for b in resp.content if b.type == "text").strip().strip('"')
        if out.upper().startswith("SKIP"):
            return {"skip": True, "text": ""}
        if _looks_bad(out):
            print("  (AI reply looked off — using raw headline instead)")
            return {"skip": False, "text": headline}
        return {"skip": False, "text": out}
    except Exception as e:
        print(f"  (AI writer fell back to raw headline: {e})")
        return {"skip": False, "text": headline}


def write_video_caption(title, subreddit):
    """Returns a viral caption, or None if the model gave a bad/refusal reply."""
    prompt = (
        f"A trending post titled '{title}' from r/{subreddit}. "
        "Write ONE short caption (max 180 characters) that could go viral — "
        "hook the reader and match the mood (funny / heartwarming / "
        "motivational). No hashtags, no surrounding quotes, no preamble. "
        "Output ONLY the caption."
    )
    try:
        resp = _c().messages.create(
            model=MODEL, max_tokens=200, system=VOICE,
            messages=[{"role": "user", "content": prompt}],
        )
        cap = next(b.text for b in resp.content if b.type == "text").strip().strip('"')
        if _looks_bad(cap):
            print("  (video caption looked off — skipping this video)")
            return None
        return cap
    except Exception as e:
        print(f"  (caption failed, skipping video: {e})")
        return None
