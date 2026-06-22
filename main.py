"""
The bot's brain. Each run it:
  1. reads RSS feeds for every pillar
  2. filters to relevant, fresh headlines
  3. verifies hard-news with the 2-source rule
  4. skips anything already posted
  5. builds a graphic + caption (with source credit)
  6. posts to X via the API
  7. remembers what it posted

Secret keys are read from environment variables (set in GitHub Secrets) —
never written in the code.
"""
import os
import json
import html
import feedparser
import tweepy

import config
from verify import is_corroborated
from graphics import make_card

HISTORY_FILE = "posted.json"


# ---------- history (so we never repeat a post) ----------
def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(history), f, indent=2)


# ---------- gather candidate stories ----------
def collect_entries(pillar, spec):
    """Return a list of {title, link, source} for one pillar."""
    entries = []
    keywords = config.PILLAR_KEYWORDS.get(pillar, [])
    for feed_url in spec["feeds"]:
        parsed = feedparser.parse(feed_url)
        source = parsed.feed.get("title", feed_url)
        for item in parsed.entries[:15]:
            title = html.unescape(item.get("title", "").strip())
            if not title:
                continue
            # keyword filter (empty list = accept all)
            if keywords and not any(k in title.lower() for k in keywords):
                continue
            entries.append({
                "title": title,
                "link": item.get("link", ""),
                "source": source,
            })
    return entries


# ---------- compose the tweet text ----------
def build_caption(entry, pillar):
    hashtag = config.PILLAR_HASHTAGS.get(pillar, "")
    source = entry["source"]
    text = entry["title"]
    # leave room for source credit + hashtag within 280 chars
    credit = f"\n\nSource: {source}"
    tail = f"\n{hashtag}" if hashtag else ""
    budget = 280 - len(credit) - len(tail)
    if len(text) > budget:
        text = text[: budget - 1].rstrip() + "…"
    return text + credit + tail


# ---------- post to X ----------
def make_client():
    client = tweepy.Client(
        consumer_key=os.environ["X_API_KEY"],
        consumer_secret=os.environ["X_API_SECRET"],
        access_token=os.environ["X_ACCESS_TOKEN"],
        access_token_secret=os.environ["X_ACCESS_TOKEN_SECRET"],
    )
    # v1.1 API is needed for media (image) upload
    auth = tweepy.OAuth1UserHandler(
        os.environ["X_API_KEY"], os.environ["X_API_SECRET"],
        os.environ["X_ACCESS_TOKEN"], os.environ["X_ACCESS_TOKEN_SECRET"],
    )
    api_v1 = tweepy.API(auth)
    return client, api_v1


def post_item(client, api_v1, entry, pillar):
    caption = build_caption(entry, pillar)
    img = make_card(pillar, entry["title"], entry["source"])
    media = api_v1.media_upload(img)
    client.create_tweet(text=caption, media_ids=[media.media_id])


# ---------- main loop ----------
def main():
    history = load_history()
    client, api_v1 = make_client()
    posts_made = 0

    for pillar, spec in config.PILLARS.items():
        if posts_made >= config.MAX_POSTS_PER_RUN:
            break

        entries = collect_entries(pillar, spec)
        for entry in entries:
            if posts_made >= config.MAX_POSTS_PER_RUN:
                break
            if entry["title"] in history:
                continue
            # hard news must be corroborated by 2+ sources
            if spec["hard_news"] and not is_corroborated(entry, entries):
                continue
            try:
                post_item(client, api_v1, entry, pillar)
                history.add(entry["title"])
                posts_made += 1
                print(f"POSTED [{pillar}] {entry['title']}")
            except Exception as e:
                print(f"FAILED [{pillar}] {entry['title']}: {e}")

    save_history(history)
    print(f"Done. {posts_made} post(s) this run.")


if __name__ == "__main__":
    main()
