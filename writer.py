"""
AI writer (Claude Haiku) — rewrites headlines into @Rokhaan's personal voice,
judges tone (e.g. skips anti-Afghanistan cricket), and writes viral video
captions. Reads ANTHROPIC_API_KEY from the environment.

If the API is unavailable for any reason, it falls back gracefully so the
bot keeps running (raw headline / raw title).
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


def write_news(pillar, headline, source):
    """
    Returns {"skip": bool, "text": str}.
    skip=True means don't post this item.
    """
    prompt = (
        f"Pillar: {pillar}\nHeadline: {headline}\nSource: {source}\n\n"
        "Decide and respond:\n"
        "- If this item is embarrassing/negative for Afghanistan in CRICKET "
        "(e.g. Afghanistan losing heavily), OR is off-topic, OR is not "
        "substantive news, reply with exactly: SKIP\n"
        "- Otherwise reply with ONLY the rewritten post in the account's voice "
        "(max 240 characters, no quotes, no preamble, no hashtags). A source "
        "credit is added separately, so don't include one."
    )
    try:
        resp = _c().messages.create(
            model=MODEL, max_tokens=400, system=VOICE,
            messages=[{"role": "user", "content": prompt}],
        )
        out = next(b.text for b in resp.content if b.type == "text").strip()
        if out.upper().startswith("SKIP"):
            return {"skip": True, "text": ""}
        return {"skip": False, "text": out.strip('"')}
    except Exception as e:
        print(f"  (AI writer fell back to raw headline: {e})")
        return {"skip": False, "text": headline}


def write_video_caption(title, subreddit):
    """Returns a short, viral-style caption for a video."""
    prompt = (
        f"A viral video titled '{title}' from r/{subreddit}. "
        "Write ONE short caption (max 180 characters) that could go viral — "
        "hook the reader and match the mood (funny / heartwarming / "
        "motivational). No hashtags, no surrounding quotes, no preamble."
    )
    try:
        resp = _c().messages.create(
            model=MODEL, max_tokens=200, system=VOICE,
            messages=[{"role": "user", "content": prompt}],
        )
        return next(b.text for b in resp.content if b.type == "text").strip().strip('"')
    except Exception as e:
        print(f"  (caption fell back to title: {e})")
        return title
