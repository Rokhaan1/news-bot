"""One-time diagnostic: which X read operations does this API plan allow?"""
import os
import tweepy

c = tweepy.Client(
    bearer_token=os.environ.get("X_BEARER_TOKEN"),
    consumer_key=os.environ["X_API_KEY"],
    consumer_secret=os.environ["X_API_SECRET"],
    access_token=os.environ["X_ACCESS_TOKEN"],
    access_token_secret=os.environ["X_ACCESS_TOKEN_SECRET"],
)

TID = "1908531085736108481"  # a public Premier League tweet

def test(name, fn):
    try:
        r = fn()
        print(f"OK   {name}: {r}")
    except Exception as e:
        print(f"FAIL {name}: {type(e).__name__}: {e}")

test("get_me (user ctx)", lambda: (c.get_me().data or {}).get("username")
     if isinstance(c.get_me().data, dict) else getattr(c.get_me().data, "username", "?"))
test("get_tweet bearer", lambda: bool(c.get_tweet(TID, tweet_fields=["public_metrics"], user_auth=False).data))
test("get_tweet user", lambda: bool(c.get_tweet(TID, tweet_fields=["public_metrics"], user_auth=True).data))
test("search bearer", lambda: len(c.search_recent_tweets("England", max_results=10, user_auth=False).data or []))
test("search user", lambda: len(c.search_recent_tweets("England", max_results=10, user_auth=True).data or []))
