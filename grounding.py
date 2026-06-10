"""
grounding.py — fetch the full text of an article from its URL.

Uses requests to follow redirects (which gives us the real final URL after
any Google News redirect) and trafilatura to extract the clean article body
from the HTML.  Returns headline_only=True whenever the text can't be read,
so the caller can label it rather than crash.
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
import trafilatura

from config import FETCH_TIMEOUT_SECONDS, MAX_ARTICLE_FETCH_WORKERS

logger = logging.getLogger(__name__)

_HEADERS = {
    # A browser-like user-agent so most sites don't block the request.
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

# Text shorter than this is probably a cookie wall or paywall notice, not content.
_MIN_TEXT_CHARS = 200

# Only these Content-Type prefixes contain readable article text.
_READABLE_CONTENT_TYPES = ("text/html", "text/plain", "application/xhtml", "application/xml")

# Minimum fraction of letters + whitespace for text to qualify as prose.
# PDFs extracted as text score much lower because of numeric/special-char density.
_MIN_READABLE_RATIO = 0.50


def _is_readable_prose(text: str) -> bool:
    """
    Return False if the text looks like binary data or PDF extraction garbage.
    Two checks: control-character density and letter+whitespace ratio.
    """
    sample = text[:3000]
    n = len(sample)
    # Control chars (below 0x20, excluding normal whitespace) indicate binary data.
    control = sum(1 for c in sample if ord(c) < 32 and c not in "\t\n\r")
    if control / n > 0.02:
        return False
    # PDF binary decoded as text has many digits/symbols and few letters+spaces.
    readable = sum(1 for c in sample if c.isalpha() or c.isspace())
    return readable / n >= _MIN_READABLE_RATIO


def fetch_article(url: str) -> dict:
    """
    Fetch and extract article text from a single URL.

    Returns a dict with:
        text          : str  — clean article body ("" if unavailable)
        final_url     : str  — URL after following any redirects
        headline_only : bool — True when real text could not be extracted
    """
    try:
        resp = requests.get(
            url,
            timeout=FETCH_TIMEOUT_SECONDS,
            headers=_HEADERS,
            allow_redirects=True,
        )
        resp.raise_for_status()
        final_url = resp.url
    except Exception as exc:
        logger.debug("HTTP fetch failed for %s: %s", url, exc)
        return {"text": "", "final_url": url, "headline_only": True}

    # Skip PDFs, images, and other non-text responses before trafilatura ever runs.
    content_type = resp.headers.get("Content-Type", "").lower()
    if not any(content_type.startswith(t) for t in _READABLE_CONTENT_TYPES):
        logger.debug("Non-HTML content (%s) at %s", content_type, final_url)
        return {"text": "", "final_url": final_url, "headline_only": True}

    # If the redirect chain never left Google News, we got a consent/redirect page.
    if "news.google.com" in final_url:
        logger.debug("Redirect stayed on news.google.com for %s", url)
        return {"text": "", "final_url": final_url, "headline_only": True}

    text = trafilatura.extract(resp.text, url=final_url, include_comments=False)

    if not text or len(text) < _MIN_TEXT_CHARS:
        logger.debug("Insufficient text at %s (%d chars)", final_url, len(text) if text else 0)
        return {"text": "", "final_url": final_url, "headline_only": True}

    # Secondary safety net: catch binary garbage that slipped past the Content-Type check.
    if not _is_readable_prose(text):
        logger.debug("Non-prose text at %s (binary or encoding artifact)", final_url)
        return {"text": "", "final_url": final_url, "headline_only": True}

    return {"text": text.strip(), "final_url": final_url, "headline_only": False}


def fetch_articles(items: list[dict]) -> list[dict]:
    """
    Enrich a list of story dicts with article text, fetched in parallel.
    Adds three keys to each item: text, final_url, headline_only.
    Never raises — failures are logged and marked headline_only.
    """
    # Track editorial rank so we can restore it after concurrent fetch.
    rank = {item["url"]: i for i, item in enumerate(items)}
    enriched = []

    with ThreadPoolExecutor(max_workers=MAX_ARTICLE_FETCH_WORKERS) as pool:
        future_to_item = {
            pool.submit(fetch_article, item["url"]): item
            for item in items
        }
        for future in as_completed(future_to_item):
            item = future_to_item[future]
            try:
                result = future.result()
            except Exception as exc:
                logger.warning("Unexpected error fetching %s: %s", item["url"], exc)
                result = {"text": "", "final_url": item["url"], "headline_only": True}

            merged = {**item, **result}
            enriched.append(merged)

            status = (
                "headline-only"
                if result["headline_only"]
                else f"{len(result['text'])} chars"
            )
            logger.info(
                "  [%s] %s — %s",
                item.get("source_label", "?"),
                item.get("title", "")[:60],
                status,
            )

    # Restore editorial ranking so _fill_slots() respects the AI's priority order.
    enriched.sort(key=lambda s: rank.get(s.get("url", ""), 999))
    return enriched
