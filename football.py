"""
Find a viral English-football post on X (Twitter) to share with our own text.
Uses the X API recent-search (small read cost). Returns the best tweet or None.
"""

QUERY = ('(England OR "Three Lions" OR "Premier League" OR #ENG OR #ThreeLions '
         'OR "Harry Kane" OR Bellingham) has:media lang:en -is:retweet -is:reply')


def find_viral_football(client):
    """Return the highest-engagement recent English-football tweet, or None."""
    try:
        resp = client.search_recent_tweets(
            query=QUERY, max_results=25,
            tweet_fields=["public_metrics", "lang", "possibly_sensitive"],
        )
    except Exception as e:
        print(f"  (football search failed: {e})")
        return None

    best, best_score = None, -1
    for t in (resp.data or []):
        if getattr(t, "possibly_sensitive", False):
            continue
        m = t.public_metrics or {}
        score = (m.get("like_count", 0)
                 + 2 * m.get("retweet_count", 0)
                 + m.get("reply_count", 0))
        if score > best_score:
            best_score, best = score, t
    return best
