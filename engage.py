"""
Find recent, high-traction tweets in our niches to engage with (quote-tweet or
reply) so we grow by joining bigger conversations instead of only broadcasting.

Degrades gracefully: if search is unavailable on the current API tier (403) or
rate-limited (429), it logs and returns [] rather than crashing the run.
"""
from datetime import datetime, timezone


def find_engageable(client, query, max_age_hours, min_likes,
                    exclude_ids=None, own_handle=None, max_results=25):
    """Return recent tweets matching `query`, best first, as a list of dicts:
    {id, text, author, author_followers, score}. Empty list on any failure."""
    exclude_ids = exclude_ids or set()
    # never engage our own posts
    q = query
    if own_handle:
        q = f"{query} -from:{own_handle}"
    try:
        resp = client.search_recent_tweets(
            query=q, max_results=max_results,
            tweet_fields=["public_metrics", "created_at", "possibly_sensitive", "lang"],
            expansions=["author_id"],
            user_fields=["public_metrics", "username"],
            user_auth=False,
        )
    except Exception as e:
        print(f"  (engage search failed: {e})")
        return []

    users = {u.id: u for u in ((resp.includes or {}).get("users") or [])}
    now = datetime.now(timezone.utc)
    scored = []
    for t in (resp.data or []):
        if getattr(t, "possibly_sensitive", False):
            continue
        if getattr(t, "lang", "en") not in ("en", None):
            continue
        ca = getattr(t, "created_at", None)
        if ca is None or (now - ca).total_seconds() > max_age_hours * 3600:
            continue
        m = t.public_metrics or {}
        likes = m.get("like_count", 0)
        if likes < min_likes:
            continue                      # need some traction to borrow an audience
        if str(t.id) in exclude_ids:
            continue                      # already engaged this tweet

        u = users.get(t.author_id)
        followers = (u.public_metrics or {}).get("followers_count", 0) if u else 0
        if followers > 3_000_000:
            continue                      # so huge our reply/quote would be buried
        # reward engagement + a meaningfully-sized (but not giant) audience
        score = (likes + 2 * m.get("retweet_count", 0) + m.get("reply_count", 0)
                 + min(followers, 200_000) / 1000)
        scored.append((score, {
            "id": str(t.id),
            "text": t.text,
            "author": u.username if u else None,
            "author_followers": followers,
            "score": round(score, 1),
        }))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored]
