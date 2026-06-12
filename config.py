from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent
MEMORY_DIR = BASE_DIR / "memory"
BRIEFINGS_DIR = BASE_DIR / "briefings"
LOGS_DIR = BASE_DIR / "logs"

MEMORY_RECENT_FILE    = MEMORY_DIR / "last_30_days.json"   # filename kept for compatibility
MEMORY_30_DAYS_FILE   = MEMORY_RECENT_FILE                  # backwards-compat alias
MEMORY_THEMES_FILE    = MEMORY_DIR / "themes_summary.md"
MEMORY_RUN_COUNT_FILE = MEMORY_DIR / "run_count.json"
CANDIDATES_FILE = BASE_DIR / "candidates.json"

# ---------------------------------------------------------------------------
# Time windows
# ---------------------------------------------------------------------------
GATHER_WINDOW_HOURS = 48      # only stories published in the last 48 hours
MEMORY_WINDOW_RUNS = 30        # deduplicate against stories from the last 30 newsletters sent
MEMORY_THEMES_WINDOW_RUNS = 500  # themes_summary.md retains entries for the last 500 newsletters

# ---------------------------------------------------------------------------
# Counts
# ---------------------------------------------------------------------------
TARGET_STORIES = 5            # always output exactly 5 in the final briefing
SHORTLIST_STORIES = 8         # editorial step selects this many; ground.py fills 5 slots,
                              # skipping headline-only items so the final 5 have real text
MAX_THEME_STORIES = 2         # no more than this many of the 5 final stories may share one theme
MAX_HN_STORIES = 1            # Hacker News dominates developer topics; cap its contribution
                              # to 1 story so broader sources fill the other 4 slots
HN_MAX_STORIES = 60           # how many HN top-story IDs to inspect

# ---------------------------------------------------------------------------
# Reading time
# ---------------------------------------------------------------------------
READING_WPM = 230             # words-per-minute used for the estimated reading time

# ---------------------------------------------------------------------------
# HTTP fetch settings
# ---------------------------------------------------------------------------
FETCH_TIMEOUT_SECONDS = 15
MAX_ARTICLE_FETCH_WORKERS = 5   # parallel article-text fetches

# ---------------------------------------------------------------------------
# Google News RSS — topic feeds (broad breadth)
#
# Using the search-based RSS endpoint with `when:2d` so Google pre-filters
# to the last 48 hours before we apply our own time check.
# Tune the queries in M3 if you want to narrow or broaden any feed.
# ---------------------------------------------------------------------------
GOOGLE_NEWS_TOPIC_FEEDS = [
    ("Technology", "https://news.google.com/rss/search?q=technology+when:2d&hl=en-US&gl=US&ceid=US:en"),
    ("Business",   "https://news.google.com/rss/search?q=tech+business+when:2d&hl=en-US&gl=US&ceid=US:en"),
    ("Science",    "https://news.google.com/rss/search?q=science+when:2d&hl=en-US&gl=US&ceid=US:en"),
]

# Google News RSS — keyword feeds
GOOGLE_NEWS_KEYWORD_FEEDS = [
    ("AI Agents",        "https://news.google.com/rss/search?q=%22AI+agents%22+when:2d&hl=en-US&gl=US&ceid=US:en"),
    ("AI Regulation",    "https://news.google.com/rss/search?q=%22AI+regulation%22+when:2d&hl=en-US&gl=US&ceid=US:en"),
    # "RBI" alone returns baseball (Runs Batted In); exact phrase avoids that
    ("RBI",              "https://news.google.com/rss/search?q=%22Reserve+Bank+of+India%22+when:2d&hl=en-US&gl=US&ceid=US:en"),
    ("SEBI",             "https://news.google.com/rss/search?q=SEBI+when:2d&hl=en-US&gl=US&ceid=US:en"),
    ("Science Discovery","https://news.google.com/rss/search?q=%22science+discovery%22+when:2d&hl=en-US&gl=US&ceid=US:en"),
    ("Tech Business",    "https://news.google.com/rss/search?q=%22technology+business%22+when:2d&hl=en-US&gl=US&ceid=US:en"),
]

# ---------------------------------------------------------------------------
# Direct RSS feeds — real article URLs, no redirect chain.
# Chosen to cover the editorial lens: capability shifts, market moves,
# science discoveries, and policy.  Deliberately broader than developer-only.
# ---------------------------------------------------------------------------
DIRECT_RSS_FEEDS = [
    ("TechCrunch",           "https://techcrunch.com/feed/"),
    ("Ars Technica",         "https://feeds.arstechnica.com/arstechnica/index"),
    ("MIT Technology Review","https://www.technologyreview.com/feed/"),
    ("Science Daily",        "https://www.sciencedaily.com/rss/all.xml"),
]

# ---------------------------------------------------------------------------
# Hacker News public Firebase API (no key required)
# ---------------------------------------------------------------------------
HN_TOP_STORIES_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
HN_ITEM_URL        = "https://hacker-news.firebaseio.com/v0/item/{}.json"
