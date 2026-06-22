"""
Configuration for the news bot.
Edit this file to change sources, posting rules, and limits.
No secret keys live here — those are stored safely in GitHub Secrets.
"""

# ----- POSTING LIMITS (keeps cost low + account safe) -----
MAX_POSTS_PER_RUN = 2          # tweets per scheduled run (x4 runs/day = up to ~8/day)
MIN_MINUTES_BETWEEN_POSTS = 0  # spacing handled by the schedule itself

# ----- COST CONTROL -----
# Posts with a URL cost ~$0.20 vs ~$0.015 without. So we credit sources by
# NAME, not link, by default. Only "video" items may include a link.
ALLOW_LINKS = False            # set True only for selective video-link posts

# ----- CONTENT PILLARS + THEIR RSS FEEDS -----
# Each pillar lists trusted feeds. "hard_news" pillars require 2-source
# confirmation before posting; others (sports) can post from one source.
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
