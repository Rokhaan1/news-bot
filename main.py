"""
The bot's brain. Each run it:
  1. (once/day) posts one viral video from Reddit with an AI caption
  2. reads RSS feeds for every news pillar
  3. verifies hard-news with the 2-source rule
  4. skips anti-Afghanistan cricket (rules + AI tone judge)
  5. rewrites each post in @Rokhaan's voice (Claude Haiku)
  6. builds a branded graphic + caption (with source credit)
  7. posts to X, respecting per-run and per-day caps

Secret keys are read from environment variables (GitHub Secrets):
  X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET, ANTHROPIC_API_KEY
"""
import os
import json
import html
import time
import random
import calendar
from datetime import datetime, timezone

import feedparser
import tweepy

import config
import writer
import football
import engage
from verify import is_corroborated, keywords
from graphics import make_card

STATE_FILE = "state.json"


# ---------- daily state (history + counters) ----------
def today():
    return datetime.now(timezone.utc).date().isoformat()


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            s = json.load(f)
    else:
        s = {}
    s.setdefault("posted", [])
    s.setdefault("date", today())
    s.setdefault("posts_today", 0)
    s.setdefault("videos_date", "")
    s.setdefault("football_date", "")
    s.setdefault("fact_date", "")
    s.setdefault("pashto_date", "")
    s.setdefault("last_news_ts", 0)
    s.setdefault("log", [])         # [{id, pillar, hour, ts, eng}] performance log
    s.setdefault("insights", {})    # {pillar: avg_engagement}
    s.setdefault("recent", [])      # recent titles, for duplicate-event detection
    s.setdefault("fact_topics", [])  # recently used heritage topics (rotation memory)
    s.setdefault("recent_facts", [])  # recent Afghan-fact tweets (anti-repeat memory)
    s.setdefault("slots_done", [])  # UTC hours of POST_SLOTS already filled today
    s.setdefault("quotes_today", 0)   # engagement counters (reset daily)
    s.setdefault("replies_today", 0)
    s.setdefault("last_engage_ts", 0)
    s.setdefault("engaged_ids", [])   # tweet IDs we've already engaged (dedup)
    s.setdefault("thread_week", "")   # ISO week of the last deep-dive thread
    s.setdefault("engage_blocked", 0)  # ts when the API plan refused reply/quote
    # reset the daily counters when the date rolls over
    if s["date"] != today():
        s["date"] = today()
        s["posts_today"] = 0
        s["slots_done"] = []
        s["quotes_today"] = 0
        s["replies_today"] = 0
    s["posted_set"] = set(s["posted"])
    return s


def save_state(s):
    s["posted"] = sorted(s.pop("posted_set"))
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(s, f, indent=2)


# ---------- X client ----------
def make_client():
    client = tweepy.Client(
        bearer_token=os.environ.get("X_BEARER_TOKEN"),  # for reads/search
        consumer_key=os.environ["X_API_KEY"],
        consumer_secret=os.environ["X_API_SECRET"],
        access_token=os.environ["X_ACCESS_TOKEN"],
        access_token_secret=os.environ["X_ACCESS_TOKEN_SECRET"],
    )
    auth = tweepy.OAuth1UserHandler(
        os.environ["X_API_KEY"], os.environ["X_API_SECRET"],
        os.environ["X_ACCESS_TOKEN"], os.environ["X_ACCESS_TOKEN_SECRET"],
    )
    return client, tweepy.API(auth)


# ---------- gather candidate stories ----------
def _published_epoch(item):
    t = item.get("published_parsed") or item.get("updated_parsed")
    return calendar.timegm(t) if t else None


def collect_entries(pillar, spec):
    """Return fresh entries (newest first), older-than-MAX_AGE_HOURS dropped."""
    entries = []
    keywords = config.PILLAR_KEYWORDS.get(pillar, [])
    now = time.time()
    for feed_url in spec["feeds"]:
        parsed = feedparser.parse(feed_url)
        source = parsed.feed.get("title", feed_url)
        for item in parsed.entries[:25]:
            title = html.unescape(item.get("title", "").strip())
            if not title:
                continue
            if keywords and not any(k in title.lower() for k in keywords):
                continue
            epoch = _published_epoch(item)
            if epoch is not None and (now - epoch) > config.MAX_AGE_HOURS * 3600:
                continue  # too old — keep it fresh
            entries.append({"title": title, "source": source, "epoch": epoch or 0})
    if pillar == "worldcup":
        # England items first (for engagement), then newest
        entries.sort(key=lambda e: (0 if "england" in e["title"].lower() else 1,
                                    -e["epoch"]))
    else:
        entries.sort(key=lambda e: e["epoch"], reverse=True)  # newest first
    return entries


def is_negative_afghan(title):
    low = title.lower()
    return any(p in low for p in config.AFGHAN_CRICKET_SKIP)


def is_trusted(source):
    low = (source or "").lower()
    return any(t in low for t in config.TRUSTED_SOURCES)


def _is_dup(title, recent):
    """True if this headline covers the same event as a recently-posted one."""
    k = keywords(title)
    if len(k) < 4:
        return False
    return any(len(k & keywords(rt)) >= 4 for rt in recent)


def _in_window(win, hour):
    """True if this UTC hour is inside the (start, end) window (handles wrap)."""
    if not win:
        return True
    start, end = win
    if start <= end:
        return start <= hour < end
    return hour >= start or hour < end


def _due_slot(hour, done):
    """Return the earliest POST_SLOT that is due at this UTC hour and not yet
    filled today, or None. Catch-up is capped so a slot never bleeds into the
    next slot's hour."""
    slots = config.POST_SLOTS
    for i, slot in enumerate(slots):
        if slot["hour"] in done:
            continue
        nxt = slots[i + 1]["hour"] if i + 1 < len(slots) else 24
        end = min(slot["hour"] + config.SLOT_CATCHUP_HOURS, nxt - 1)
        if slot["hour"] <= hour <= end:
            return slot
    return None


# ---------- compose captions ----------
def build_caption(text, pillar):
    hashtag = config.PILLAR_HASHTAGS.get(pillar, "")
    tail = f"\n\n{hashtag}" if hashtag else ""
    budget = 1200 - len(tail)   # Premium supports long posts; no source credit
    if len(text) > budget:
        text = text[: budget - 1].rstrip() + "…"
    return text + tail


def build_video_caption(caption, url, sub):
    via = f"\n\n{url}\n(via r/{sub})"
    budget = 900 - len(via)
    if len(caption) > budget:
        caption = caption[: budget - 1].rstrip() + "…"
    return caption + via


# ---------- posting ----------
def post_news(client, api_v1, entry, pillar, text):
    caption = build_caption(text, pillar)
    media_ids = None
    if config.ATTACH_IMAGES:
        try:
            img = make_card(pillar, entry["title"], entry["source"])
            media = api_v1.media_upload(img)
            media_ids = [media.media_id]
        except Exception as e:
            print(f"  (image skipped: {e})")
    if media_ids:
        resp = client.create_tweet(text=caption, media_ids=media_ids)
    else:
        resp = client.create_tweet(text=caption)
    try:
        return str(resp.data["id"])      # tweet id, for performance tracking
    except Exception:
        return None


def maybe_post_afghan_fact(client, state):
    """Once a day, during Afghan hours: a positive/historic Afghan pride fact.
    Rotates through HERITAGE_TOPICS and rejects near-duplicates of recent facts
    so it stops repeating the same Balkh/lapis tweet."""
    if state.get("fact_date") == today():
        return
    if not _in_window(config.AFGHAN_FACT_WINDOW, datetime.now(timezone.utc).hour):
        return

    recent_topics = state.get("fact_topics", [])
    recent_facts = state.get("recent_facts", [])
    # prefer a topic we haven't used recently; fall back to any if all are used
    pool = [t for t in config.HERITAGE_TOPICS if t not in recent_topics] \
        or list(config.HERITAGE_TOPICS)
    topic = random.choice(pool)

    text = None
    for _ in range(3):   # retry if the model still returns a near-duplicate
        cand = writer.write_afghan_fact(topic=topic, avoid=recent_facts[-8:])
        if cand and not _is_dup(cand, recent_facts):
            text = cand
            break
    if not text:
        print("SKIPPED [afghan_fact] no fresh, non-duplicate fact this run")
        return
    try:
        client.create_tweet(text=text)
        state["fact_date"] = today()
        state["fact_topics"] = (recent_topics + [topic])[-14:]
        state["recent_facts"] = (recent_facts + [text])[-12:]
        print(f"POSTED [afghan_fact] {text[:60]}")
    except Exception as e:
        print(f"FAILED [afghan_fact] {e}")


def maybe_post_pashto(client, state):
    """Once a day, during Afghan hours: an original pro-Afghanistan Pashto post."""
    if state.get("pashto_date") == today():
        return
    if not _in_window(config.AFGHAN_FACT_WINDOW, datetime.now(timezone.utc).hour):
        return
    text = writer.write_pashto_post()
    if not text:
        return
    try:
        client.create_tweet(text=text)
        state["pashto_date"] = today()
        print(f"POSTED [pashto] {text[:40]}")
    except Exception as e:
        print(f"FAILED [pashto] {e}")


def maybe_post_football(client, state):
    """Once a day, in football hours: share a viral English-football post from X."""
    if config.FOOTBALL_PER_DAY <= 0 or state.get("football_date") == today():
        return
    if not _in_window(config.PILLAR_WINDOWS.get("worldcup"),
                      datetime.now(timezone.utc).hour):
        return
    tweets = football.find_viral_football(client)
    # pick the top trending football moment we haven't used as inspiration yet
    top = next((t for t in tweets if str(t.id) not in state["posted_set"]), None)
    if not top:
        print(f"  (football: no fresh candidate from {len(tweets)} found)")
        return
    take = writer.write_football_caption(top.text)   # an original native take
    if not take:
        print("  (football: take rejected by guard)")
        return
    try:
        rid = None
        resp = client.create_tweet(text=take)         # native post, no link/quote
        try:
            rid = str(resp.data["id"])
        except Exception:
            pass
        state["posted_set"].add(str(top.id))          # don't reuse this moment
        state["football_date"] = today()
        if rid:
            state["log"].append({"id": rid, "pillar": "worldcup",
                                 "hour": datetime.now(timezone.utc).hour,
                                 "ts": time.time(), "eng": None})
        print(f"POSTED [football] {take[:70]}")
    except Exception as e:
        print(f"FAILED [football] {e}")


def maybe_post_thread(client, state):
    """Once a week: a 3-5 tweet expert deep-dive thread on one heritage topic.
    Threads are X's highest-ceiling format; this showcases the account's depth."""
    if not getattr(config, "THREAD_ENABLED", False):
        return
    now = datetime.now(timezone.utc)
    week = now.strftime("%G-W%V")
    if state.get("thread_week") == week:
        return
    if now.weekday() != config.THREAD_WEEKDAY:
        return
    if not _in_window(config.THREAD_WINDOW, now.hour):
        return

    recent_topics = state.get("fact_topics", [])
    pool = [t for t in config.HERITAGE_TOPICS if t not in recent_topics] \
        or list(config.HERITAGE_TOPICS)
    topic = random.choice(pool)
    tweets = writer.write_thread(topic, avoid=state.get("recent_facts", [])[-6:])
    if not tweets:
        print("SKIPPED [thread] generation failed guard")
        return
    try:
        first_id, prev_id = None, None
        for tw in tweets:
            resp = client.create_tweet(
                text=tw,
                in_reply_to_tweet_id=prev_id) if prev_id else \
                client.create_tweet(text=tw)
            prev_id = str(resp.data["id"])
            first_id = first_id or prev_id
        state["thread_week"] = week
        # share rotation memory with the daily fact so they never collide
        state["fact_topics"] = (recent_topics + [topic])[-14:]
        state["recent_facts"] = (state.get("recent_facts", []) + [tweets[0]])[-12:]
        if first_id:
            state["log"].append({"id": first_id, "pillar": "thread",
                                 "hour": now.hour, "ts": time.time(), "eng": None})
        print(f"POSTED [thread] {len(tweets)} tweets :: {tweets[0][:60]}")
    except Exception as e:
        # partial thread is fine to leave up; just don't retry this week
        if first_id:
            state["thread_week"] = week
        print(f"FAILED [thread] {e}")


def maybe_engage(client, state):
    """Grow by joining bigger conversations: a few expert quote-tweets and
    replies per day to recent, high-traction in-niche tweets. Low-volume and
    heavily guarded. No-op if search is unavailable on this API tier."""
    if not getattr(config, "ENGAGE_ENABLED", False):
        return
    # If the API plan refused reply/quote writes, don't burn search/AI quota on
    # attempts that can't post; probe again weekly in case the plan was upgraded.
    if time.time() - state.get("engage_blocked", 0) < 7 * 86400:
        return
    hour = datetime.now(timezone.utc).hour
    if not _in_window(config.ENGAGE_WINDOW, hour):
        return

    want_reply = state["replies_today"] < config.ENGAGE_REPLIES_PER_DAY
    want_quote = state["quotes_today"] < config.ENGAGE_QUOTES_PER_DAY
    if not (want_reply or want_quote):
        return                                   # both daily quotas used up
    if time.time() - state.get("last_engage_ts", 0) < config.ENGAGE_MIN_GAP_MIN * 60:
        return                                   # space engagements out

    query = random.choice(config.ENGAGE_QUERIES)
    cands = engage.find_engageable(
        client, query,
        max_age_hours=config.ENGAGE_MAX_AGE_HOURS,
        min_likes=config.ENGAGE_MIN_LIKES,
        exclude_ids=set(state.get("engaged_ids", [])),
        own_handle=config.ACCOUNT_HANDLE,
    )
    if not cands:
        print("Engage: no suitable tweets this run.")
        return

    # reply-weighted: reply while that quota remains, else quote-tweet
    action = "reply" if want_reply else "quote"
    for c in cands:
        take = (writer.write_reply(c["text"], c["author"]) if action == "reply"
                else writer.write_quote_take(c["text"], c["author"]))
        if not take:
            continue                             # guard SKIP -> try next candidate
        try:
            if action == "reply":
                resp = client.create_tweet(text=take, in_reply_to_tweet_id=c["id"])
                state["replies_today"] += 1
            else:
                resp = client.create_tweet(text=take, quote_tweet_id=c["id"])
                state["quotes_today"] += 1
            rid = None
            try:
                rid = str(resp.data["id"])
            except Exception:
                pass
            state["engaged_ids"] = (state.get("engaged_ids", []) + [c["id"]])[-300:]
            state["last_engage_ts"] = time.time()
            if rid:
                state["log"].append({"id": rid, "pillar": action, "hour": hour,
                                     "ts": time.time(), "eng": None})
            print(f"POSTED [{action}] on @{c['author']} ({c['author_followers']} flw) "
                  f":: {take[:70]}")
            return
        except Exception as e:
            if "mentioned or are the author" in str(e):
                # X plan restriction: replies/quotes to others not permitted.
                state["engage_blocked"] = time.time()
                print("Engage: API plan blocks replying/quoting others. "
                      "Pausing engagement for a week (upgrade the X API plan "
                      "at developer.x.com to enable this).")
                return
            print(f"FAILED [{action}] on {c['id']}: {e}")
    print("Engage: all candidates skipped this run.")


def measure_and_learn(client, state):
    """Read engagement for posts >3h old, then average it per topic (insights)."""
    now = time.time()
    measured = 0
    for e in state.get("log", []):
        if measured >= 5:
            break
        if e.get("eng") is None and now - e.get("ts", 0) > 3 * 3600:
            try:
                t = client.get_tweet(e["id"], tweet_fields=["public_metrics"])
                m = (t.data.public_metrics if t and t.data else {}) or {}
                e["eng"] = (m.get("like_count", 0) + m.get("retweet_count", 0)
                            + m.get("reply_count", 0) + m.get("quote_count", 0))
                measured += 1
            except Exception:
                e["eng"] = -1  # inaccessible/deleted — skip it
    state["log"] = state["log"][-120:]   # keep the log bounded

    sums, counts = {}, {}
    for e in state["log"]:
        v = e.get("eng")
        if isinstance(v, (int, float)) and v >= 0:
            sums[e["pillar"]] = sums.get(e["pillar"], 0) + v
            counts[e["pillar"]] = counts.get(e["pillar"], 0) + 1
    state["insights"] = {p: round(sums[p] / counts[p], 1) for p in sums}
    if state["insights"]:
        print("Insights (avg engagement per topic):", state["insights"])


def ranked_pillars(state):
    """Order topics by learned engagement (winners first), with some exploration."""
    ins = state.get("insights", {})
    base = (sum(ins.values()) / len(ins)) if ins else 5.0
    pillars = list(config.PILLARS.items())
    pillars.sort(key=lambda ps: -(ins.get(ps[0], base) * (0.5 + random.random())))
    return pillars


# ---------- main loop ----------
def main():
    state = load_state()
    client, api_v1 = make_client()

    measure_and_learn(client, state)   # read recent performance, refresh insights

    # 1) one Afghan pride fact + one viral English-football share per day
    # Pashto post disabled: generated Pashto quality was not reliable.
    maybe_post_afghan_fact(client, state)
    maybe_post_football(client, state)
    maybe_post_thread(client, state)   # weekly 3-5 tweet heritage deep-dive

    # 2) news — post at fixed UTC slots, each timed to a target audience.
    posts_made = 0
    hour = datetime.now(timezone.utc).hour
    slot = _due_slot(hour, state["slots_done"])
    if slot is None:
        print("No posting slot is due this run.")
    elif state["posts_today"] >= config.MAX_POSTS_PER_DAY:
        print("Daily post cap reached.")
    else:
        # this slot's preferred pillars first, then the rest by learned
        # engagement, so the slot still fires if the preferred topics are dry.
        ranked = [p for p, _ in ranked_pillars(state)]
        order = slot["pillars"] + [p for p in ranked if p not in slot["pillars"]]
        for pillar in order:
            if posts_made >= config.MAX_POSTS_PER_RUN:
                break
            spec = config.PILLARS.get(pillar)
            if not spec:
                continue

            entries = collect_entries(pillar, spec)
            for entry in entries:
                if entry["title"] in state["posted_set"]:
                    continue
                if _is_dup(entry["title"], state["recent"]):   # same event already posted
                    state["posted_set"].add(entry["title"])
                    continue
                if (spec["hard_news"] and not is_corroborated(entry, entries)
                        and not is_trusted(entry["source"])):
                    continue
                if pillar == "afghan_cricket" and is_negative_afghan(entry["title"]):
                    state["posted_set"].add(entry["title"])  # mark seen, don't re-check
                    continue

                result = writer.write_news(pillar, entry["title"], entry["source"])
                state["posted_set"].add(entry["title"])  # seen either way (saves AI calls)
                if result["skip"]:
                    print(f"SKIPPED [{pillar}] {entry['title'][:55]}")
                    continue
                try:
                    rid = post_news(client, api_v1, entry, pillar, result["text"])
                    posts_made += 1
                    state["posts_today"] += 1
                    state["last_news_ts"] = time.time()
                    if rid:
                        state["log"].append({"id": rid, "pillar": pillar, "hour": hour,
                                             "ts": time.time(), "eng": None})
                    state["recent"].append(entry["title"])
                    state["recent"] = state["recent"][-25:]
                    print(f"POSTED [{pillar}] :: {result['text']}")
                    break  # one post this run
                except Exception as e:
                    print(f"FAILED [{pillar}] {entry['title'][:50]}: {e}")
            if posts_made:
                break

        if posts_made:
            state["slots_done"].append(slot["hour"])
            print(f"Filled {slot['hour']:02d}:00 UTC slot ({slot['pillars'][0]}).")

    # 3) engagement — a few expert quote-tweets/replies a day to grow reach
    maybe_engage(client, state)

    save_state(state)
    print(f"Done. {posts_made} news post(s) this run; {state['posts_today']}/"
          f"{config.MAX_POSTS_PER_DAY} today; "
          f"engage {state['replies_today']}R/{state['quotes_today']}Q.")


if __name__ == "__main__":
    main()
