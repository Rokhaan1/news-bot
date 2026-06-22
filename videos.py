"""
Fetches trending viral videos from Reddit (funny / motivational / loveable)
to share as LINKS with an AI-written caption.

Reddit blocks datacenter IPs / generic bot user-agents, so we send a real
browser User-Agent and fall back from the JSON API to the RSS feed.
"""
import requests
import feedparser

# mood -> subreddit
SUBREDDITS = {
    "funny": "funny",
    "motivational": "GetMotivated",
    "heartwarming": "MadeMeSmile",
    "loveable": "aww",
}

VIDEO_DOMAINS = ("youtube.com", "youtu.be", "v.redd.it", "streamable.com",
                 "gfycat.com")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")


def _from_json(sub, limit):
    url = f"https://www.reddit.com/r/{sub}/top.json?t=day&limit={limit}"
    r = requests.get(url, headers={"User-Agent": UA}, timeout=15)
    if r.status_code != 200:
        raise RuntimeError(f"HTTP {r.status_code}")
    items = []
    for child in r.json()["data"]["children"]:
        p = child.get("data", {})
        is_video = p.get("is_video") or p.get("domain", "") in VIDEO_DOMAINS
        if not is_video or p.get("over_18"):
            continue
        items.append({
            "title": p.get("title", "").strip(),
            "url": "https://www.reddit.com" + p.get("permalink", ""),
            "score": p.get("score", 0),
        })
    return items


def _from_rss(sub):
    # RSS fallback: can't detect video reliably, so take top posts as-is.
    url = f"https://www.reddit.com/r/{sub}/top/.rss?t=day"
    feed = feedparser.parse(url, agent=UA)
    items = []
    for e in feed.entries[:10]:
        link = e.get("link", "")
        if not link:
            continue
        items.append({"title": e.get("title", "").strip(), "url": link,
                      "score": 0})
    return items


def fetch_videos(limit=12):
    """Return a list of {title, url, mood, subreddit, score}, best first."""
    out = []
    for mood, sub in SUBREDDITS.items():
        try:
            items = _from_json(sub, limit)
        except Exception as e:
            print(f"  (reddit json r/{sub} failed: {e}; trying RSS)")
            try:
                items = _from_rss(sub)
            except Exception as e2:
                print(f"  (reddit rss r/{sub} failed: {e2})")
                items = []
        for it in items:
            it.update({"mood": mood, "subreddit": sub})
            out.append(it)
    out.sort(key=lambda v: v["score"], reverse=True)
    return out
