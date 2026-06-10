"""
sources.py — gather candidate stories from Google News RSS and Hacker News.

Returns a list of dicts, each with these keys:
    title        : str  — headline
    url          : str  — article URL (may be a Google News redirect; resolved later)
    source_label : str  — feed name, e.g. "Technology", "Hacker News"
    published    : str  — ISO-8601 UTC datetime string
    snippet      : str  — short text from the feed (may be empty)
    origin       : str  — "google_news" or "hacker_news"
"""

import html
import logging
import re
from datetime import datetime, timedelta, timezone

import feedparser
import requests

from config import (
    DIRECT_RSS_FEEDS,
    FETCH_TIMEOUT_SECONDS,
    GATHER_WINDOW_HOURS,
    GOOGLE_NEWS_KEYWORD_FEEDS,
    GOOGLE_NEWS_TOPIC_FEEDS,
    HN_ITEM_URL,
    HN_MAX_STORIES,
    HN_TOP_STORIES_URL,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Theme assignment
# ---------------------------------------------------------------------------

# Maps each feed label to a primary theme tag used by the theme-cap logic in ground.py.
_FEED_THEMES: dict[str, str] = {
    "Technology":           "Technology",
    "Business":             "Business",
    "Science":              "Science",
    "Science Discovery":    "Science",
    "Tech Business":        "Business",
    "AI Agents":            "AI",
    "AI Regulation":        "AI",
    "RBI":                  "Finance",
    "SEBI":                 "Finance",
    "TechCrunch":           "Technology",
    "Ars Technica":         "Technology",
    "MIT Technology Review":"Technology",
    "Science Daily":        "Science",
}

# Keywords for inferring the theme of a Hacker News story from its title.
_HN_THEME_KEYWORDS: dict[str, list[str]] = {
    "AI":       ["ai", "gpt", "llm", "claude", "gemini", "openai", "anthropic",
                 "neural", "chatgpt", "copilot", "diffusion", "transformer"],
    "Security": ["security", "hack", "malware", "vulnerability", "breach",
                 "exploit", "ransomware", "cve", "phishing", "zero-day"],
    "Finance":  ["bank", "fund", "market", "finance", "stock", "economy",
                 "inflation", "interest rate", "rbi", "sebi", "crypto", "bitcoin"],
    "Science":  ["science", "research", "physics", "biology", "space",
                 "climate", "study", "paper", "discovery", "nasa"],
}

def _infer_hn_theme(title: str) -> str:
    """Return a primary theme label for a Hacker News story based on its title."""
    t = title.lower()
    for theme, keywords in _HN_THEME_KEYWORDS.items():
        if any(kw in t for kw in keywords):
            return theme
    return "Technology"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _cutoff_time() -> datetime:
    return datetime.now(timezone.utc) - timedelta(hours=GATHER_WINDOW_HOURS)


def _parse_feed_time(entry) -> datetime | None:
    """Extract published or updated time from a feedparser entry."""
    for attr in ("published_parsed", "updated_parsed"):
        t = getattr(entry, attr, None)
        if t:
            return datetime(*t[:6], tzinfo=timezone.utc)
    return None


def _strip_html(text: str) -> str:
    """Remove HTML tags and normalize whitespace."""
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return " ".join(text.split())


# ---------------------------------------------------------------------------
# Google News RSS
# ---------------------------------------------------------------------------

def _fetch_one_feed(label: str, url: str, cutoff: datetime) -> list[dict]:
    """Fetch a single RSS feed and return normalized items within the window."""
    try:
        feed = feedparser.parse(url)
    except Exception as exc:
        logger.warning("Could not parse feed '%s': %s", label, exc)
        return []

    items = []
    for entry in feed.entries:
        pub = _parse_feed_time(entry)
        # Drop items outside the 48-hour window; keep items with no date
        # (rare but real) so we don't silently lose fresh stories.
        if pub is not None and pub < cutoff:
            continue

        url = entry.get("link", "")

        items.append({
            "title":        _strip_html(entry.get("title", "")).strip(),
            "url":          url,
            "source_label": label,
            "published":    pub.isoformat() if pub else "",
            "snippet":      _strip_html(entry.get("summary", "")).strip(),
            "origin":       "google_news",
            "theme":        _FEED_THEMES.get(label, "Technology"),
        })

    logger.info("Google News [%-15s]: %d items in window", label, len(items))
    return items


def fetch_google_news(cutoff: datetime) -> list[dict]:
    """Fetch all configured topic and keyword Google News RSS feeds."""
    items = []
    for label, url in GOOGLE_NEWS_TOPIC_FEEDS + GOOGLE_NEWS_KEYWORD_FEEDS:
        items.extend(_fetch_one_feed(label, url, cutoff))
    return items


# ---------------------------------------------------------------------------
# Hacker News
# ---------------------------------------------------------------------------

def fetch_hacker_news(cutoff: datetime) -> list[dict]:
    """
    Fetch the top HN_MAX_STORIES ranked stories and keep those within
    the 48-hour window.  HN top stories are ranked, not time-sorted,
    so we check all of them rather than stopping at the first old one.
    """
    try:
        resp = requests.get(HN_TOP_STORIES_URL, timeout=FETCH_TIMEOUT_SECONDS)
        resp.raise_for_status()
        story_ids = resp.json()[:HN_MAX_STORIES]
    except Exception as exc:
        logger.warning("Could not fetch HN story list: %s", exc)
        return []

    items = []
    for sid in story_ids:
        try:
            r = requests.get(HN_ITEM_URL.format(sid), timeout=FETCH_TIMEOUT_SECONDS)
            r.raise_for_status()
            item = r.json()
        except Exception as exc:
            logger.debug("Skipped HN item %s: %s", sid, exc)
            continue

        # Only regular link stories; skip Ask HN, jobs, polls, self-posts
        if item.get("type") != "story" or not item.get("url"):
            continue

        pub_ts = item.get("time")
        if not pub_ts:
            continue
        pub = datetime.fromtimestamp(pub_ts, tz=timezone.utc)
        if pub < cutoff:
            continue

        title = item.get("title", "").strip()
        items.append({
            "title":        title,
            "url":          item.get("url", ""),
            "source_label": "Hacker News",
            "published":    pub.isoformat(),
            "snippet":      "",          # HN items carry no snippet
            "origin":       "hacker_news",
            "hn_score":     item.get("score", 0),
            "theme":        _infer_hn_theme(title),
        })

    logger.info("Hacker News: %d items in window", len(items))
    return items


# ---------------------------------------------------------------------------
# Direct publisher RSS feeds
# ---------------------------------------------------------------------------

def fetch_direct_feeds(cutoff: datetime) -> list[dict]:
    """
    Fetch configured direct-URL RSS feeds. These give real article URLs with
    no Google News redirect, so grounding succeeds reliably.
    """
    items = []
    for label, feed_url in DIRECT_RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
        except Exception as exc:
            logger.warning("Could not parse direct feed '%s': %s", label, exc)
            continue

        count = 0
        for entry in feed.entries:
            pub = _parse_feed_time(entry)
            if pub is not None and pub < cutoff:
                continue
            url = entry.get("link", "")
            if not url:
                continue
            items.append({
                "title":        _strip_html(entry.get("title", "")).strip(),
                "url":          url,
                "source_label": label,
                "published":    pub.isoformat() if pub else "",
                "snippet":      _strip_html(entry.get("summary", "")).strip(),
                "origin":       "direct_feed",
                "theme":        _FEED_THEMES.get(label, "Technology"),
            })
            count += 1

        logger.info("Direct RSS  [%-15s]: %d items in window", label, count)

    return items


# ---------------------------------------------------------------------------
# Combined entry point
# ---------------------------------------------------------------------------

def gather_all(cutoff: datetime | None = None) -> list[dict]:
    """
    Gather candidate stories from all sources.
    Deduplicates by URL so the same article doesn't appear twice if it
    shows up in multiple Google News feeds.
    """
    if cutoff is None:
        cutoff = _cutoff_time()

    raw = []
    raw.extend(fetch_google_news(cutoff))
    raw.extend(fetch_hacker_news(cutoff))
    raw.extend(fetch_direct_feeds(cutoff))

    # URL-level dedup within this run
    seen: set[str] = set()
    unique = []
    for item in raw:
        url = item["url"]
        if url and url not in seen:
            seen.add(url)
            unique.append(item)

    logger.info("Total unique candidates after URL dedup: %d", len(unique))
    return unique
