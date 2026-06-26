"""
Find a viral English-football post on X (Twitter) to share with our own text.
Uses the X API recent-search (small read cost). Returns the best tweet or None.
"""

QUERY = ('(England OR "Three Lions" OR "Premier League" OR #ENG OR #ThreeLions '
         'OR "Harry Kane" OR Bellingham) has:media lang:en -is:retweet -is:reply')


def find_viral_football(client):
    """Return recent English-football tweets, highest engagement first."""
    try:
        resp = client.search_recent_tweets(
            query=QUERY, max_results=25,
            tweet_fields=["public_metrics", "lang", "possibly_sensitive"],
            user_auth=False,   # use app-only Bearer token
        )
    except Exception as e:
        print(f"  (football search failed: {e})")
        return []

    scored = []
    for t in (resp.data or []):
        if getattr(t, "possibly_sensitive", False):
            continue
        m = t.public_metrics or {}
        score = (m.get("like_count", 0)
                 + 2 * m.get("retweet_count", 0)
                 + m.get("reply_count", 0))
        scored.append((score, t))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [t for _, t in scored]
