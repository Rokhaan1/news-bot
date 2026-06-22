"""
Fetches trending viral videos from Reddit (funny / motivational / loveable)
to share as LINKS with an AI-written caption. Free JSON API.
"""
import requests

# mood -> subreddit
SUBREDDITS = {
    "funny": "funny",
    "motivational": "GetMotivated",
    "heartwarming": "MadeMeSmile",
    "loveable": "aww",
}

VIDEO_DOMAINS = ("youtube.com", "youtu.be", "v.redd.it", "streamable.com",
                 "gfycat.com")
HEADERS = {"User-Agent": "RokhaanNewsBot/1.0 (by /u/Rokhaan1)"}


def fetch_videos(limit=12):
    """Return a list of {title, url, mood, subreddit, score}, best first."""
    out = []
    for mood, sub in SUBREDDITS.items():
        url = f"https://www.reddit.com/r/{sub}/top.json?t=day&limit={limit}"
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            children = r.json()["data"]["children"]
        except Exception as e:
            print(f"  (reddit r/{sub} failed: {e})")
            continue
        for child in children:
            p = child.get("data", {})
            is_video = p.get("is_video") or p.get("domain", "") in VIDEO_DOMAINS
            if not is_video or p.get("over_18"):
                continue
            out.append({
                "title": p.get("title", "").strip(),
                "url": "https://www.reddit.com" + p.get("permalink", ""),
                "mood": mood,
                "subreddit": sub,
                "score": p.get("score", 0),
            })
    out.sort(key=lambda v: v["score"], reverse=True)
    return out
