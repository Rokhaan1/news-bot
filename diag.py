"""Find which search query shape works on this plan."""
import os
import tweepy

c = tweepy.Client(
    bearer_token=os.environ.get("X_BEARER_TOKEN"),
    consumer_key=os.environ["X_API_KEY"],
    consumer_secret=os.environ["X_API_SECRET"],
    access_token=os.environ["X_ACCESS_TOKEN"],
    access_token_secret=os.environ["X_ACCESS_TOKEN_SECRET"],
)

QUERIES = {
    "simple": "England lang:en",
    "or_terms": '(England OR "Premier League" OR Bellingham) lang:en -is:retweet',
    "has_media": '(England OR "Premier League") has:media lang:en -is:retweet',
    "has_videos": '(England OR "Premier League") has:videos lang:en -is:retweet',
    "no_reply": '(England OR "Premier League") has:media lang:en -is:retweet -is:reply',
    "full": ('(England OR "Three Lions" OR "Premier League" OR #ENG OR #ThreeLions '
             'OR "Harry Kane" OR Bellingham) has:media lang:en -is:retweet -is:reply'),
}

for name, q in QUERIES.items():
    try:
        r = c.search_recent_tweets(q, max_results=10, user_auth=False)
        print(f"OK   {name}: {len(r.data or [])} results")
    except Exception as e:
        print(f"FAIL {name}: {type(e).__name__}: {e}")
