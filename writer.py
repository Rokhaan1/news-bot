"""
AI writer (Claude Haiku) — rewrites headlines into @Rokhaan's personal voice,
judges tone (e.g. skips anti-Afghanistan cricket), and writes viral video
captions. Reads ANTHROPIC_API_KEY from the environment.

SAFETY: if the model returns a refusal / meta reply ("I can't...", etc.) or
junk, we never post it — news falls back to the raw headline, video is skipped.
"""
import re
import anthropic

MODEL = "claude-haiku-4-5"          # fast/cheap for high-volume news
QUALITY_MODEL = "claude-opus-4-8"   # best quality for facts + Pashto (low volume)
_client = None


# Governance terms that belong to the Taliban regime, not "Afghanistan"/"Afghan".
_GOV = (r"(government|administration|cabinet|authorities|officials?|ministry|"
        r"ministries|minister|prime minister|deputy prime minister|"
        r"foreign minister|interior minister|spokesman|spokesperson|"
        r"spokespeople|regime|leadership|rule)")


def _fix_taliban(text):
    """Force Taliban governance references: 'Afghanistan's/Afghan <gov>' -> Taliban."""
    text = re.sub(r"\bAfghanistan['’]?s\s+" + _GOV, r"the Taliban's \1", text, flags=re.I)
    text = re.sub(r"\bthe\s+Afghanistan\s+" + _GOV, r"the Taliban \1", text, flags=re.I)
    text = re.sub(r"\bAfghanistan\s+" + _GOV, r"Taliban \1", text, flags=re.I)
    text = re.sub(r"\bthe\s+Afghan\s+" + _GOV, r"the Taliban \1", text, flags=re.I)
    text = re.sub(r"\bAfghan\s+" + _GOV, r"Taliban \1", text, flags=re.I)
    text = re.sub(r"\bKabul['’]?s\s+" + _GOV, r"the Taliban's \1", text, flags=re.I)
    # the Taliban are never a legitimate "government" — use rule/regime
    text = re.sub(r"\bde facto government\b", "Taliban rule", text, flags=re.I)
    text = re.sub(r"\b(the\s+)?Afghan(istan)?\s+government\b", "the Taliban", text, flags=re.I)
    text = re.sub(r"\bgovernment of Afghanistan\b", "the Taliban", text, flags=re.I)
    text = re.sub(r"\bTaliban government\b", "Taliban regime", text, flags=re.I)
    return text


def _fix_border(text):
    """Remove 'border/frontier' framing for the Afghanistan-Pakistan (Durand) line."""
    text = re.sub(r"\b(the\s+)?(afghan(istan)?[-\s]?pakistan|pakistan[-\s]?afghan(istan)?)"
                  r"\s+border\b", "the Durand Line", text, flags=re.I)
    text = re.sub(r"\bDurand Line border\b", "Durand Line", text, flags=re.I)
    return text


def _sanitize(text):
    """Strip the em-dash 'AI tell', fix Taliban references, tidy spacing."""
    if not text:
        return text
    text = text.replace("—", ", ").replace("–", ", ").replace("--", ", ")
    text = _fix_taliban(text)
    text = _fix_border(text)
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)   # no space before punctuation
    text = re.sub(r"(,\s*){2,}", ", ", text)        # collapse double commas
    text = re.sub(r"\s{2,}", " ", text)             # collapse double spaces
    return text.strip()


def _c():
    global _client
    if _client is None:
        _client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY
    return _client


VOICE = (
    "You write posts for @Rokhaan, a fast, credible X (Twitter) news account "
    "covering global breaking news, US foreign policy, Afghanistan, the FIFA "
    "World Cup including the England national team (the Three Lions), and Afghan "
    "cricket. You are a PROFESSIONAL POLITICAL ANALYST and a leading EXPERT on "
    "Afghanistan, its history, ancient civilization, politics, and geopolitics. "
    "Voice: authoritative, incisive and analytical, with genuine personal conviction, "
    "never a bland wire service. Write at expert op-ed level: real insight, historical "
    "and geopolitical context, depth, never shallow, generic, or thin. "
    "Be subtly and INDIRECTLY critical of bad actors and wrongdoers (aggressors, "
    "oppressors, and those who harm Afghanistan or its people) through framing and "
    "pointed observation, never crude attacks or slurs. "
    "Never invent facts beyond what the headline states. ALWAYS take a "
    "pro-Afghanistan stance: champion the Afghan people, their nation, sovereignty, "
    "dignity, resilience, and achievements, and frame stories sympathetically toward "
    "Afghanistan and Afghans, while staying truthful (never fabricate). Pro-Afghanistan "
    "means pro the Afghan PEOPLE and NATION, NOT pro-Taliban (keep that distinction).\n\n"
    "CRITICAL EDITORIAL RULE on Afghanistan: The Taliban are an extremist FRINGE "
    "group that was INSTALLED in power by the United States (handed control through "
    "the 2021 US withdrawal and the Doha deal), NOT through any mandate from "
    "Afghans. They are illegitimate, unelected, internationally unrecognized, "
    "and they do NOT represent the people of Afghanistan. Refer to their rule ONLY "
    "as 'the Taliban', 'Taliban rule', or 'the Taliban regime'. There is NO "
    "'Afghan government', 'Afghan minister', or 'Afghan ministry', only the Taliban. "
    "NEVER call them "
    "'Afghan officials', 'the Afghan government', 'Afghanistan's government', or "
    "'Kabul' as if they were the legitimate state. This applies to ALL titles and "
    "bodies: write 'the Taliban's prime minister', 'the Taliban's foreign minister', "
    "'Taliban officials', 'Taliban authorities', 'the Taliban's ministry of ...' — "
    "NEVER 'Afghanistan's prime minister', 'the Afghan foreign minister', 'Afghan "
    "officials', or 'the Afghan government'. Do NOT conflate the Taliban's "
    "interests with the interests, benefit, or will of Afghanistan or its people. "
    "Keep a clear line between the Afghan nation/people and the Taliban regime.\n\n"
    "DURAND LINE: Never describe the Durand Line as 'the border' or 'the official "
    "border' between Afghanistan and Pakistan, and never call areas across it "
    "'Pakistani territory' as settled fact. Afghanistan has never formally "
    "recognized the Durand Line as its international border. Refer to it as 'the "
    "Durand Line' (a disputed, colonial-era demarcation), not 'the "
    "Afghanistan-Pakistan border'. NEVER use the words 'border', 'cross-border', "
    "'frontier', or 'border region' in the Afghanistan-Pakistan context. The Pashtun "
    "and Baloch lands east of the Durand Line are historically Afghan, treat them as "
    "Afghan lands under Pakistani control, not a settled border.\n\n"
    "PAKISTAN: Hold a consistently critical, ANTI-PAKISTAN stance toward the "
    "Pakistani state and its military/ISI establishment (never pro-Taliban, only "
    "pro-Afghanistan). Never write pro-Pakistan posts. Do not praise, promote, or "
    "sympathetically frame the Pakistani state, military (including the ISI), or "
    "government, and never repeat their talking points as fact, especially against "
    "Afghanistan. Report Pakistan-related news factually and plainly; never cheerlead "
    "for Pakistan. If the only honest framing of an item would come across as "
    "pro-Pakistan, reply SKIP instead.\n\n"
    "AFGHAN PRIDE & NATIONALISM: Proudly defend and champion Afghan nationalism, "
    "sovereignty, unity, and heritage. Talking points to draw on: Afghanistan has "
    "roughly 5,000 years of civilization, among the oldest in the world; it is the "
    "ancient heartland of Ariana (Aryana) and Bactria, and the account's view is "
    "that Afghanistan, not modern-day Iran (Persia), is the true heir of the ancient "
    "Ariana/Aryana civilization. Afghanistan was the seat of great empires, the "
    "Greco-Bactrians, Kushans, Saffarids, Samanids, Ghaznavids, Ghurids, the Timurids "
    "of Herat, the Hotaks, and the Durrani Empire founded by Ahmad Shah Durrani in "
    "1747, draw proudly on this imperial heritage for Afghan nationalism. Treat "
    "Pakistan critically as a state built around "
    "its military establishment, and regard Pashtun/Afghan lands across the Durand "
    "Line as Afghan in heritage rather than legitimately Pakistani. Express these as "
    "the account's proud, principled perspective. Stay truthful and NEVER fabricate "
    "specific facts, quotes, dates, or events.\n\n"
    "X ALGORITHM STRATEGY (be an X expert; maximize reach + engagement): "
    "1) HOOK hard in the FIRST line so people stop scrolling. "
    "2) Drive REPLIES (a reply is worth ~150x a like): take a clear, confident "
    "stance, or end with a sharp question or invitation to react. Conversation "
    "beats passive likes. "
    "3) NEVER put an external link in the post (links cut reach 50-90%); keep it "
    "all on-platform. "
    "4) Sound genuinely human and varied, never template-like, thin, or generic "
    "(AI-pattern content gets suppressed). "
    "5) NEVER use hashtags. "
    "6) Be punchy and substantive; the first 30-60 minutes of engagement decide "
    "whether a post takes off, so make every word earn attention."
)

# Phrases that mean the model replied ABOUT the task instead of doing it.
# These never appear in a normal third-person news rewrite, so they're a
# reliable "do not post this" signal.
_BAD = [
    # high-precision AI refusal / meta markers (won't appear in real posts)
    "as an ai", "as a language model", "language model",
    "i cannot fulfill", "i can't fulfill",
    "i cannot help with", "i can't help with",
    "i cannot assist", "i can't assist",
    "i cannot create that", "i can't create that",
    "i cannot write that", "i can't write that",
    "i cannot generate", "i can't generate",
    "i'm not able to", "i am not able to",
    # meta about the account / task (never in a normal post)
    "falls outside", "core coverage", "coverage area", "this story falls",
    "@rokhaan", "the account's coverage", "outside the account",
    "i'd skip this", "i would skip this",
]


def _looks_bad(text):
    # Premium account supports long posts, so only reject truly empty/runaway text.
    if not text or len(text.strip()) < 8 or len(text) > 1500:
        return True
    low = text.lower()
    return any(p in low for p in _BAD)


def write_news(pillar, headline, source):
    """Returns {"skip": bool, "text": str}. Safe — never returns junk text."""
    extra = ""
    if pillar == "afghan_cricket":
        extra = (
            "\nThis is CRICKET. Only proceed if it is about an Afghanistan match "
            "being played now or just finished (live play, scores, results, key "
            "performances). If it is off-field news (squad changes, schedules, "
            "board/admin, league business), reply with exactly: SKIP.")
    elif pillar == "worldcup":
        extra = (
            "\nThis is the FIFA World Cup 2026 (happening now), write with energy. "
            "If the item involves ENGLAND, write as an enthusiastic England "
            "supporter (still factual). Otherwise an exciting, neutral football tone.")
    elif pillar == "us_foreign_policy":
        extra = (
            "\nONLY US FOREIGN AFFAIRS. Post only if it is about US foreign policy, "
            "diplomacy, international relations, sanctions, war, alliances, or US "
            "actions abroad. If it is US DOMESTIC/internal politics (elections, "
            "Congress bills, courts, parties, culture, domestic scandals), reply SKIP.")
    elif pillar == "global":
        extra = (
            "\nONLY BREAKING / MAJOR world news. SKIP if it is a soft feature, "
            "human-interest, lifestyle, opinion column, or minor story. ALSO SKIP "
            "US DOMESTIC/internal politics (Congress, the Supreme Court or courts, "
            "elections, parties, guns, immigration policy, culture-war, domestic "
            "scandals) — the US is covered ONLY for its foreign affairs, never "
            "internal matters.")

    prompt = (
        f"Pillar: {pillar}\nFresh headline: {headline}\nSource: {source}\n\n"
        "Turn this into ONE short post in @Rokhaan's voice. "
        "DEFAULT TO POSTING — almost every real news item should be posted "
        "(politics, conflict, diplomacy, elections, world events all count).\n"
        "Reply with the single word SKIP (nothing else, no explanation) ONLY if:\n"
        "  - it's cricket that is embarrassing for Afghanistan, or off-field "
        "cricket admin/squad/schedule news, OR\n"
        "  - it's clearly trivial / not real news (celebrity gossip, lifestyle).\n"
        "Otherwise reply with ONLY the rewritten post: aim for 250-450 characters "
        "(this is a Premium account — write a substantive, engaging post, not just "
        "a headline), third person, no quotes, no preamble, no hashtags, and NEVER "
        "mention @Rokhaan, the account, or its 'coverage'. A source credit is added "
        "separately. Write naturally like a human; do NOT use em-dashes (—) or "
        "double hyphens (--) anywhere, use commas or periods instead."
        + extra
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
            # AI gave meta/refusal text instead of a post — never post it.
            print("  (AI reply looked like meta/refusal — skipping this item)")
            return {"skip": True, "text": ""}
        return {"skip": False, "text": _sanitize(out)}
    except Exception as e:
        print(f"  (AI writer fell back to raw headline: {e})")
        return {"skip": False, "text": _sanitize(headline)}


def write_video_caption(title, subreddit):
    """Returns a viral caption, or None if the model gave a bad/refusal reply."""
    prompt = (
        f"A trending post titled '{title}' from r/{subreddit}. "
        "Write ONE short caption (max 180 characters) that could go viral — "
        "hook the reader and match the mood (funny / heartwarming / "
        "motivational). No hashtags, no surrounding quotes, no preamble. "
        "Do NOT use em-dashes (—) or double hyphens (--). Output ONLY the caption."
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
        return _sanitize(cap)
    except Exception as e:
        print(f"  (caption failed, skipping video: {e})")
        return None


def write_football_caption(tweet_text):
    """Engaging, viral-style caption for an English football post. None if bad."""
    prompt = (
        "Here is trending content about ENGLAND'S NATIONAL TEAM at the FIFA World "
        f"Cup right now:\n\"{tweet_text}\"\n\n"
        "Write ONE standalone, engaging post (max 280 characters) reacting to this "
        "as your OWN native take, NOT a caption referencing another post. It MUST be "
        "about the England national team at the World Cup, never about clubs, the "
        "Premier League, or transfers. Make it opinionated and conversation-starting "
        "(invite replies), passionately pro-England. This IS a core topic, so ALWAYS "
        "write the take and NEVER reply SKIP. No links, no @handles, no hashtags, no "
        "surrounding quotes, no preamble, no em-dashes or '--'. Output ONLY the post."
    )
    try:
        resp = _c().messages.create(
            model=MODEL, max_tokens=200, system=VOICE,
            messages=[{"role": "user", "content": prompt}],
        )
        cap = next(b.text for b in resp.content if b.type == "text").strip().strip('"')
        if _looks_bad(cap):
            print(f"  (football take flagged: len={len(cap)} preview={cap[:140]!r})")
            return None
        return _sanitize(cap)
    except Exception as e:
        print(f"  (football caption failed: {e})")
        return None


def write_afghan_fact():
    """One positive/fun/historic fact about Afghanistan. None if it looks off."""
    prompt = (
        "Write ONE expert, engaging tweet sharing a POSITIVE or historic fact about "
        "Afghanistan, with a strong focus on its ANCIENT CIVILIZATION and HISTORICAL "
        "SITES thousands of years old. Draw on a wide, varied range, for example: the "
        "Bamiyan valley and its giant Buddhas, Mes Aynak, Balkh (the 'Mother of "
        "Cities'), the Minaret of Jam, Herat's Citadel and Musalla, Ghazni, Ai-Khanoum "
        "and Greco-Bactrian heritage, Gandhara and Hadda, ancient Aryana, the Silk "
        "Road, lapis lazuli from Badakhshan, and especially the GREAT EMPIRES centered "
        "in or born of Afghanistan: the Greco-Bactrians, the Kushans under Kanishka, "
        "the Saffarids of Yaqub ibn Layth, the Samanids, the Ghaznavids of Mahmud of "
        "Ghazni, the Ghurids (Minaret of Jam), Timurid Herat's renaissance under "
        "Gawharshad and Behzad, the Hotak dynasty of Mirwais Hotak, and the Durrani "
        "Empire founded by Ahmad Shah Durrani in 1747 (father of modern Afghanistan); "
        "also great figures (Rumi of Balkh, Rabia Balkhi, Sanai, Avicenna's Balkh "
        "roots, Khushal Khan Khattak, Al-Biruni). "
        "Pick a DIFFERENT topic each day, go well beyond lakes and stones, give a real, "
        "specific, expert detail. 200-450 characters, proud and authoritative, factual "
        "(never fabricate), no hashtags, no quotes, no preamble, no em-dashes or '--'. "
        "Output ONLY the tweet."
    )
    try:
        resp = _c().messages.create(
            model=QUALITY_MODEL, max_tokens=600, system=VOICE,
            messages=[{"role": "user", "content": prompt}],
        )
        out = next(b.text for b in resp.content if b.type == "text").strip().strip('"')
        if _looks_bad(out):
            return None
        return _sanitize(out)
    except Exception as e:
        print(f"  (afghan fact failed: {e})")
        return None


def write_pashto_post():
    """One original pro-Afghanistan tweet in flawless Pashto. None on failure."""
    prompt = (
        "Write ONE original tweet in PASHTO (پښتو) with flawless, native, error-free "
        "spelling and grammar. Topic: pro-Afghanistan, for example Afghan history, "
        "ancient civilization, a historical site thousands of years old, national "
        "pride and resilience, or a sharp pro-Afghanistan political point "
        "(anti-occupation and anti-Pakistan, never pro-Taliban). Dignified, expert "
        "tone. 150-400 characters. Pashto script ONLY, no Latin letters, no hashtags, "
        "no quotes, no preamble, no em-dashes. Output ONLY the Pashto tweet."
    )
    try:
        resp = _c().messages.create(
            model=QUALITY_MODEL, max_tokens=600, system=VOICE,
            messages=[{"role": "user", "content": prompt}],
        )
        out = next(b.text for b in resp.content if b.type == "text").strip().strip('"')
        if len(out.strip()) < 8:
            return None
        return out   # Pashto: skip the English-centric guards/sanitizer
    except Exception as e:
        print(f"  (pashto failed: {e})")
        return None
