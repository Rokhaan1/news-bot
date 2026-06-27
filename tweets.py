"""One-off: list the account's original tweets from the last 24h with metrics."""
import os
import tweepy
from datetime import datetime, timezone

c = tweepy.Client(
    bearer_token=os.environ.get("X_BEARER_TOKEN"),
    consumer_key=os.environ["X_API_KEY"],
    consumer_secret=os.environ["X_API_SECRET"],
    access_token=os.environ["X_ACCESS_TOKEN"],
    access_token_secret=os.environ["X_ACCESS_TOKEN_SECRET"],
)

uid = c.get_me().data.id
resp = c.get_users_tweets(
    uid, max_results=100,
    tweet_fields=["created_at", "public_metrics"],
    exclude=["retweets", "replies"],
)
now = datetime.now(timezone.utc)
count = 0
for t in (resp.data or []):
    if (now - t.created_at).total_seconds() > 24 * 3600:
        continue
    m = t.public_metrics or {}
    count += 1
    print(f"=== {t.created_at:%Y-%m-%d %H:%M} UTC | likes {m.get('like_count',0)} "
          f"RT {m.get('retweet_count',0)} replies {m.get('reply_count',0)} ===")
    print(t.text)
    print()
print(f"TOTAL last 24h: {count}")
