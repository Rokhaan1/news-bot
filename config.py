"""
Configuration for the news bot.
Edit this file to change sources, posting limits, and behaviour.
No secret keys live here — those are stored safely in GitHub Secrets.
"""

# ----- POSTING LIMITS (cost control) -----
# X charges ~$0.015 per post (text/image), ~$0.20 if the post contains a link.
MAX_POSTS_PER_RUN = 1     # news posts per scheduled run (runs every ~15 min)
MAX_POSTS_PER_DAY = 6     # experts: 3-6 quality posts/day beats 10+ (authority)
FOOTBALL_PER_DAY  = 1     # viral English-football share from X per day (quote tweet)
MIN_MINUTES_BETWEEN_NEWS = 110  # spread posts across the day for steady early engagement

# Attach a generated graphic to each post? Off = clean text-only posts.
ATTACH_IMAGES = False

# FRESHNESS: only post genuinely recent news (no stale, days-old items).
MAX_AGE_HOURS = 24        # ignore anything older than this; newest posted first

# Major outlets we trust to post from a single source (so news isn't blocked
# waiting for a 2nd source). All our feeds are reputable.
TRUSTED_SOURCES = [
    "bbc", "al jazeera", "aljazeera", "reuters", "associated press", "ap ",
    "khaama", "tolonews", "ariana", "espn", "cricinfo", "afghanistan international",
    "guardian", "un news", "united nations",
]

# ----- CONTENT PILLARS + THEIR RSS FEEDS -----
# "hard_news" pillars require 2-source confirmation before posting.
PILLARS = {
    "global": {
        "hard_news": True,
        "feeds": [
            "https://www.aljazeera.com/xml/rss/all.xml",
            "http://feeds.bbci.co.uk/news/world/rss.xml",
            "https://www.theguardian.com/world/rss",
            "https://news.un.org/feed/subscribe/en/news/all/rss.xml",
        ],
    },
    "us_foreign_policy": {
        "hard_news": True,
        "feeds": [
            "http://feeds.bbci.co.uk/news/world/us_and_canada/rss.xml",
            "https://www.theguardian.com/us-news/rss",
            "https://www.aljazeera.com/xml/rss/all.xml",
        ],
    },
    "afghanistan": {
        "hard_news": True,
        "feeds": [
            "https://www.khaama.com/feed/",
            "https://tolonews.com/rss.xml",
            "https://www.ariananews.af/feed/",
            "https://www.aljazeera.com/xml/rss/all.xml",
            "https://news.un.org/feed/subscribe/en/news/region/asia-pacific/rss.xml",
        ],
    },
    "worldcup": {
        "hard_news": False,
        "feeds": [
            "https://www.espn.com/espn/rss/soccer/news",
        ],
    },
    "afghan_cricket": {
        "hard_news": False,
        "feeds": [
            "https://www.espncricinfo.com/rss/content/story/feeds/40.xml",
        ],
    },
}

# Keyword filters so each feed only yields posts relevant to the pillar
PILLAR_KEYWORDS = {
    "afghanistan": ["afghan", "kabul", "taliban", "afghanistan"],
    "afghan_cricket": ["afghan", "rashid", "nabi", "gurbaz"],
    "worldcup": [],  # World Cup is the dominant soccer story now — take top items
    "us_foreign_policy": ["u.s.", "us ", "washington", "biden", "trump",
                          "state department", "pentagon"],
    "global": [],  # no filter — takes top world headlines
}

# Hashtags appended per pillar (kept minimal)
PILLAR_HASHTAGS = {
    "worldcup": "#WorldCup2026",
    "afghan_cricket": "#AfghanAtalan",
    "afghanistan": "#Afghanistan",
    "global": "",
    "us_foreign_policy": "",
}

# Geo-aware posting windows (UTC). Each topic only posts while its target
# audience is awake/active. (start, end) in UTC hours; start>end wraps midnight.
# None = post any time. Afghanistan is UTC+4:30; US is UTC-5..-8.
PILLAR_WINDOWS = {
    "global": None,                  # world audience, any time
    "afghanistan": (2, 19),          # ~06:30-23:30 Afghan time
    "us_foreign_policy": (13, 5),    # ~US morning to late evening (wraps midnight)
    "worldcup": (12, 4),             # UK afternoon + Americas match hours (wraps)
    "afghan_cricket": (3, 17),       # South Asia match hours
}
AFGHAN_FACT_WINDOW = (2, 19)         # post the daily Afghan pride fact in Afghan hours

# Cricket headlines that are negative for Afghanistan are skipped (cheap rule
# pre-filter; the AI writer also judges tone as a backstop).
AFGHAN_CRICKET_SKIP = [
    "beat afghanistan", "sweep afghanistan", "thrash afghanistan",
    "afghanistan lose", "afghanistan lost", "afghanistan slump",
    "afghanistan collapse", "defeat afghanistan", "hammer afghanistan",
    "crush afghanistan", "dominate afghanistan", "afghanistan beaten",
    "afghanistan crash", "afghanistan thrashed", "afghanistan humbled",
    "win against afghanistan", "victory over afghanistan", "rout afghanistan",
]
