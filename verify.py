"""
Automated verification — replaces manual review.
A hard-news story is only cleared to post if it appears in 2+ DIFFERENT sources.
Low-risk pillars (sports) skip this and can post from one source.
"""
import re

STOPWORDS = {
    "the", "a", "an", "to", "of", "in", "on", "for", "and", "or", "at",
    "as", "is", "are", "was", "were", "by", "with", "from", "after",
    "over", "into", "new", "says", "say", "said", "amid", "its", "his",
    "her", "their", "this", "that", "has", "have", "will", "be",
}


def keywords(title):
    """Reduce a headline to its significant lowercase words."""
    words = re.findall(r"[a-zA-Z]+", title.lower())
    return {w for w in words if len(w) > 3 and w not in STOPWORDS}


def is_corroborated(candidate, all_entries, min_sources=2, overlap=3):
    """
    True if `candidate` headline is supported by >= min_sources distinct feeds.
    Two headlines are treated as the same story if they share >= `overlap`
    significant keywords.
    """
    cand_kw = keywords(candidate["title"])
    if len(cand_kw) < overlap:
        return False

    sources_seen = {candidate["source"]}
    for entry in all_entries:
        if entry["source"] in sources_seen:
            continue
        if len(cand_kw & keywords(entry["title"])) >= overlap:
            sources_seen.add(entry["source"])
        if len(sources_seen) >= min_sources:
            return True
    return False
