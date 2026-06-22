"""
Configuration for the news bot.
Edit this file to change sources, posting limits, and behaviour.
No secret keys live here — those are stored safely in GitHub Secrets.
"""

# ----- POSTING LIMITS (cost control) -----
# X charges ~$0.015 per post (text/image), ~$0.20 if the post contains a link.
MAX_POSTS_PER_RUN = 1     # news posts per scheduled run (runs every ~15 min)
MAX_POSTS_PER_DAY = 6     # hard daily cap on news posts (tune freely)
VIDEOS_PER_DAY    = 1     # viral video link-posts per day ($0.20 each)

# ----- CONTENT PILLARS + THEIR RSS FEEDS -----
# "hard_news" pillars require 2-source confirmation before posting.
PILLARS = {
    "global": {
        "hard_news": True,
        "feeds": [
            "https://www.aljazeera.com/xml/rss/all.xml",
            "http://feeds.bbci.co.uk/news/world/rss.xml",
        ],
    },
    "us_foreign_policy": {
        "hard_news": True,
        "feeds": [
            "http://feeds.bbci.co.uk/news/world/us_and_canada/rss.xml",
            "https://www.aljazeera.com/xml/rss/all.xml",
        ],
    },
    "afghanistan": {
        "hard_news": True,
        "feeds": [
            "https://www.khaama.com/feed/",
            "https://tolonews.com/rss.xml",
            "https://www.aljazeera.com/xml/rss/all.xml",
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
    "worldcup": ["world cup", "fifa"],
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
