"""
Configuration for the news bot.
Edit this file to change sources, posting limits, and behaviour.
No secret keys live here — those are stored safely in GitHub Secrets.
"""

# ----- POSTING LIMITS (cost control) -----
# X charges ~$0.015 per post (text/image), ~$0.20 if the post contains a link.
MAX_POSTS_PER_RUN = 1     # news posts per scheduled run (runs every ~15 min)
MAX_POSTS_PER_DAY = 2     # authority recovery: every low-engagement post lowers
                          # future reach, so fewer + better beats volume
FOOTBALL_PER_DAY  = 0     # disabled: England-football takes diluted the Afghan
                          # analyst identity (profile coherence -> follows)

# ----- WEEKLY DEEP-DIVE THREAD -----
# Once a week: a 3-5 tweet expert thread on one Afghan heritage/history topic.
# Threads are X's highest-ceiling format (bookmarks + shares) and showcase the
# account's analyst depth better than single posts.
THREAD_ENABLED = False           # owner call: threads off (n=1 sample anyway)
THREAD_WEEKDAYS = [1, 4]         # 0=Mon .. 6=Sun; used only if re-enabled
THREAD_WINDOW = (13, 19)         # UTC hours; Afghan evening + Western daytime

# ----- MENTION REPLIES (permitted on pay-per-use: "summoned" posts) -----
# The pay-per-use API track blocks cold replies/quotes to strangers, but allows
# replying when @Rokhaan is mentioned or is the author. So: reply to people who
# reply to/mention us. Keeps our threads alive (conversation ranks well) and
# rewards commenters. Reads of own mentions are cheap Owned Reads.
MENTION_REPLIES_PER_DAY = 5
MENTION_MAX_AGE_HOURS = 12       # only reply while the conversation is warm

# ----- ENGAGEMENT (grow via others' audiences) -----
# The bot joins bigger in-niche conversations with a FEW expert quote-tweets and
# replies per day. Kept deliberately low-volume and value-additive: automated
# high-volume engagement is what X's spam systems punish. Needs an API tier with
# search (Basic+); degrades gracefully to no-op if search is unavailable.
ACCOUNT_HANDLE = "Rokhaan"        # our own handle, excluded from search results
ENGAGE_ENABLED = True
ENGAGE_REPLIES_PER_DAY = 2        # reply-weighted (replies grow reach, lower risk)
ENGAGE_QUOTES_PER_DAY = 2
ENGAGE_WINDOW = (13, 21)          # UTC hours to engage (active global audience)
ENGAGE_MIN_GAP_MIN = 90           # min minutes between engagement actions
ENGAGE_MIN_LIKES = 15             # only join tweets with real traction
ENGAGE_MAX_AGE_HOURS = 10         # recent enough that the thread is still live
ENGAGE_QUERIES = [               # one is chosen per run; add/reorder freely
    'Afghanistan (history OR heritage OR Ariana OR ancient OR civilization OR Dari) lang:en -is:retweet -is:reply',
    '(Afghanistan OR Kabul OR Afghan) lang:en -is:retweet -is:reply',
    'Afghan (cricket OR Rashid OR Nabi OR Gurbaz OR Afghanistan) lang:en -is:retweet -is:reply',
    '("Durand Line" OR Pashtun OR "Pakistan Afghanistan") lang:en -is:retweet -is:reply',
    '(US OR Washington OR UN) Afghanistan (policy OR sanctions OR aid OR withdrawal OR women) lang:en -is:retweet -is:reply',
]

# ----- POSTING SCHEDULE (UTC) -----
# Three news posts/day, each fired at a fixed UTC hour timed to a real
# audience's peak local time (summer offsets: UK=BST/UTC+1, Afghanistan=UTC+4:30,
# US=EDT/UTC-4 .. PDT/UTC-7):
#   14:00 UTC = ~18:30 Afghanistan  -> Afghan evening
#   16:00 UTC = ~17:00 UK           -> UK late afternoon
#   19:00 UTC = ~15:00 US East / 12:00 US West -> US noon/afternoon
# Each slot lists its preferred pillars in order; the bot posts the first that
# has a fresh, verified item and falls back through the rest by learned
# engagement, so a slot is never wasted.
POST_SLOTS = [
    # Afghanistan-only focus (owner call): no global/US/worldcup fallbacks.
    # If Afghan news is dry a slot stays empty — fine during authority recovery.
    {"hour": 14, "pillars": ["afghanistan", "afghan_cricket"]},
    {"hour": 19, "pillars": ["afghanistan", "afghan_cricket"]},
]
# A run may be late (cron hiccup / Actions queue). Still fire a slot up to this
# many UTC hours after its target — but never past the next slot's hour — so one
# missed tick doesn't skip the whole slot.
SLOT_CATCHUP_HOURS = 2

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
            "https://pajhwok.com/feed/",
            "https://feeds.bbci.co.uk/pashto/rss.xml",   # Pashto-language source
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

# No hashtags anywhere (per request; 2026 algorithm doesn't reward them)
PILLAR_HASHTAGS = {
    "worldcup": "",
    "afghan_cricket": "",
    "afghanistan": "",
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

# Heritage topics for the daily Afghan pride fact. The bot rotates through
# these (and avoids recently used ones) so the fact isn't always Balkh/lapis.
# They span the WHOLE country and its full ~5,000-year Aryana (Ariana) timeline
# on purpose. Add or reorder freely — one is chosen per day.
HERITAGE_TOPICS = [
    "the ancient name Aryana/Ariana and the Aryan homeland of the Avesta, marking ~5,000 years of continuous civilization across the Afghan lands",
    "Zoroaster (Zarathustra) and the birth of Zoroastrian thought in ancient Ariana",
    "the Greco-Bactrian kingdom and the Hellenistic city of Ai-Khanoum on the Oxus",
    "the Kushan Empire under Kanishka linking Rome, India and China along the Silk Road",
    "Gandhara civilization and its Greco-Buddhist art at Hadda",
    "the Bamiyan valley, its colossal Buddhas and painted cave monasteries",
    "Mes Aynak, the vast ancient Buddhist copper city south of Kabul",
    "Begram (ancient Kapisa) and the Begram ivories and Roman-Indian treasures",
    "Old Kandahar, Alexandria in Arachosia, and Ashoka's bilingual Greek-Aramaic edicts",
    "the Minaret of Jam and the Ghurid Empire of central Afghanistan",
    "the Ghaznavid Empire of Mahmud of Ghazni and the polymath Al-Biruni at his court",
    "the Saffarids of Yaqub ibn Layth and the Samanid renaissance",
    "Timurid Herat's golden age: Queen Gawharshad, the Musalla complex and the painter Behzad",
    "Herat's Citadel (Qala Ikhtyaruddin) and the city's layered ancient history",
    "the Durrani Empire founded by Ahmad Shah Durrani in 1747, the birth of modern Afghanistan",
    "Mirwais Hotak and the Hotak dynasty of Kandahar",
    "the Kabul Shahi (Hindu Shahi) kingdoms of Kabul and Gandhara",
    "Seistan/Zabulistan and the epic hero Rustam of the Shahnameh",
    "Khwaja Abdullah Ansari, the revered Sage of Herat",
    "Sanai of Ghazni, pioneer of Dari Sufi poetry",
    "Khushal Khan Khattak, the warrior-poet of the Pashtuns",
    "Rumi (Jalaluddin Balkhi) and Rabia Balkhi, poets born of the Afghan lands",
    "the Wakhan corridor, Badakhshan and the ancient Silk Road trade",
    "Nuristan (ancient Kafiristan) and its distinct pre-Islamic culture",
    "Ghazni as a medieval world center of learning, the 'Bride of Cities'",
    "the Kushano-Sasanian era and the crossroads culture of ancient Afghanistan",
]

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
