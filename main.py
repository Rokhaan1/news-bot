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
import videos
from verify import is_corroborated
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
    s.setdefault("fact_date", "")
    # reset the daily counter when the date rolls over
    if s["date"] != today():
        s["date"] = today()
        s["posts_today"] = 0
    s["posted_set"] = set(s["posted"])
    return s


def save_state(s):
    s["posted"] = sorted(s.pop("posted_set"))
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(s, f, indent=2)


# ---------- X client ----------
def make_client():
    client = tweepy.Client(
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


def _in_window(win, hour):
    """True if this UTC hour is inside the (start, end) window (handles wrap)."""
    if not win:
        return True
    start, end = win
    if start <= end:
        return start <= hour < end
    return hour >= start or hour < end


# ---------- compose captions ----------
def build_caption(text, source, pillar):
    hashtag = config.PILLAR_HASHTAGS.get(pillar, "")
    credit = f"\n\nSource: {source}"
    tail = f"\n{hashtag}" if hashtag else ""
    budget = 1200 - len(credit) - len(tail)   # Premium supports long posts
    if len(text) > budget:
        text = text[: budget - 1].rstrip() + "…"
    return text + credit + tail


def build_video_caption(caption, url, sub):
    via = f"\n\n{url}\n(via r/{sub})"
    budget = 900 - len(via)
    if len(caption) > budget:
        caption = caption[: budget - 1].rstrip() + "…"
    return caption + via


# ---------- posting ----------
def post_news(client, api_v1, entry, pillar, text):
    caption = build_caption(text, entry["source"], pillar)
    media_ids = None
    if config.ATTACH_IMAGES:
        try:
            img = make_card(pillar, entry["title"], entry["source"])
            media = api_v1.media_upload(img)
            media_ids = [media.media_id]
        except Exception as e:
            print(f"  (image skipped: {e})")
    if media_ids:
        client.create_tweet(text=caption, media_ids=media_ids)
    else:
        client.create_tweet(text=caption)


def maybe_post_afghan_fact(client, state):
    """Once a day, during Afghan hours: a positive/historic Afghan pride fact."""
    if state.get("fact_date") == today():
        return
    if not _in_window(config.AFGHAN_FACT_WINDOW, datetime.now(timezone.utc).hour):
        return
    text = writer.write_afghan_fact()
    if not text:
        return
    try:
        client.create_tweet(text=text)
        state["fact_date"] = today()
        print(f"POSTED [afghan_fact] {text[:60]}")
    except Exception as e:
        print(f"FAILED [afghan_fact] {e}")


def maybe_post_video(client, state):
    if config.VIDEOS_PER_DAY <= 0 or state["videos_date"] == today():
        return
    for v in videos.fetch_videos():
        if not v["title"] or v["url"] in state["posted_set"]:
            continue
        caption = writer.write_video_caption(v["title"], v["subreddit"])
        if not caption:          # bad/refusal reply -> don't post junk
            continue
        text = build_video_caption(caption, v["url"], v["subreddit"])
        try:
            client.create_tweet(text=text)
            state["posted_set"].add(v["url"])
            state["videos_date"] = today()
            print(f"POSTED [video/{v['mood']}] {v['title'][:60]}")
            return
        except Exception as e:
            print(f"FAILED [video] {v['title'][:50]}: {e}")


# ---------- main loop ----------
def main():
    state = load_state()
    client, api_v1 = make_client()

    # 1) one Afghan pride fact + one viral video per day
    maybe_post_afghan_fact(client, state)
    maybe_post_video(client, state)

    # 2) news — respect per-run and per-day caps
    posts_made = 0
    hour = datetime.now(timezone.utc).hour
    pillars = list(config.PILLARS.items())
    random.shuffle(pillars)  # vary which topic leads each run

    for pillar, spec in pillars:
        if posts_made >= config.MAX_POSTS_PER_RUN:
            break
        if state["posts_today"] >= config.MAX_POSTS_PER_DAY:
            print("Daily post cap reached.")
            break
        if not _in_window(config.PILLAR_WINDOWS.get(pillar), hour):
            continue  # outside this topic's geo/time window

        entries = collect_entries(pillar, spec)
        for entry in entries:
            if entry["title"] in state["posted_set"]:
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
                post_news(client, api_v1, entry, pillar, result["text"])
                posts_made += 1
                state["posts_today"] += 1
                print(f"POSTED [{pillar}] :: {result['text']}")
                break  # one post per pillar per run -> variety
            except Exception as e:
                print(f"FAILED [{pillar}] {entry['title'][:50]}: {e}")

    save_state(state)
    print(f"Done. {posts_made} news post(s) this run; {state['posts_today']}/"
          f"{config.MAX_POSTS_PER_DAY} today.")


if __name__ == "__main__":
    main()
