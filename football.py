"""
Find trending content about ENGLAND'S NATIONAL TEAM at the World Cup, to react
to with our own take. National team only (no clubs/Premier League/transfers),
and only very recent content so we post around actual match time.
"""
from datetime import datetime, timezone

# England national team + World Cup context; exclude clubs/league/cricket.
QUERY = ('England ("World Cup" OR "Three Lions" OR #ThreeLions OR #ENG '
         'OR #WorldCup) has:media lang:en -is:retweet -is:reply '
         '-"Premier League" -transfer -cricket -Test -ODI -wicket')

MAX_AGE_HOURS = 3   # only "live match" buzz from the last few hours


def find_viral_football(client):
    """Return recent England-NT World-Cup tweets (last few hours), best first."""
    try:
        resp = client.search_recent_tweets(
            query=QUERY, max_results=25,
            tweet_fields=["public_metrics", "created_at", "possibly_sensitive"],
            user_auth=False,
        )
    except Exception as e:
        print(f"  (football search failed: {e})")
        return []

    now = datetime.now(timezone.utc)
    scored = []
    for t in (resp.data or []):
        if getattr(t, "possibly_sensitive", False):
            continue
        ca = getattr(t, "created_at", None)
        if ca is None:
            continue
        if (now - ca).total_seconds() > MAX_AGE_HOURS * 3600:
            continue   # too old -> no live match happening
        m = t.public_metrics or {}
        score = (m.get("like_count", 0)
                 + 2 * m.get("retweet_count", 0)
                 + m.get("reply_count", 0))
        scored.append((score, t))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [t for _, t in scored]
