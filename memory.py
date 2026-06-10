"""
memory.py — two-tier story memory.

Tier 1 (last_30_days.json): full records for every story sent in the last 30 days.
Tier 2 (themes_summary.md): rolling plain-text note for older themes.

Public API:
    load()               → (records, themes_text)
    filter_candidates()  → removes stories already in memory from a candidate list
    update()             → adds today's 5 stories; prunes & folds expired records
"""

import json
import logging
import re
from datetime import date, timedelta

from config import MEMORY_30_DAYS_FILE, MEMORY_THEMES_FILE, MEMORY_WINDOW_DAYS

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _norm_url(url: str) -> str:
    """Strip query parameters so URLs differing only in tracking params match."""
    return url.split("?")[0].rstrip("/").lower()


def _norm_title(title: str) -> str:
    """Lowercase + strip punctuation for fuzzy title matching."""
    return re.sub(r"[^a-z0-9 ]", "", title.lower()).strip()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load() -> tuple[list[dict], str]:
    """
    Load both memory tiers from disk.
    Returns (records, themes_text).  Safe to call on a fresh install.
    """
    try:
        records = json.loads(MEMORY_30_DAYS_FILE.read_text(encoding="utf-8"))
        if not isinstance(records, list):
            records = []
    except (FileNotFoundError, json.JSONDecodeError):
        records = []

    try:
        themes_text = MEMORY_THEMES_FILE.read_text(encoding="utf-8")
    except FileNotFoundError:
        themes_text = ""

    return records, themes_text


def filter_candidates(candidates: list[dict], records: list[dict]) -> list[dict]:
    """
    Remove candidates whose URL or title already appears in the 30-day memory.
    Matching is URL-based (query params stripped) and title-based (fuzzy).
    """
    known_urls = {_norm_url(r["url"]) for r in records if r.get("url")}
    known_titles = {_norm_title(r["title"]) for r in records if r.get("title")}

    fresh = []
    for c in candidates:
        if _norm_url(c.get("url", "")) in known_urls:
            logger.debug("In memory (URL): %s", c.get("title", "")[:60])
            continue
        if _norm_title(c.get("title", "")) in known_titles:
            logger.debug("In memory (title): %s", c.get("title", "")[:60])
            continue
        fresh.append(c)

    removed = len(candidates) - len(fresh)
    logger.info("Memory filter: removed %d known stories, %d remain", removed, len(fresh))
    return fresh


def update(chosen: list[dict], existing_records: list[dict], existing_themes: str) -> None:
    """
    Persist today's chosen stories into memory.

    Steps:
    1. Separate records still within the 30-day window from those that have expired.
    2. Fold expired records' themes into themes_summary.md.
    3. Append today's 5 stories and write last_30_days.json.
    """
    today_iso = date.today().isoformat()
    cutoff_iso = (date.today() - timedelta(days=MEMORY_WINDOW_DAYS)).isoformat()

    recent = [r for r in existing_records if r.get("date", "0000") >= cutoff_iso]
    expired = [r for r in existing_records if r.get("date", "0000") < cutoff_iso]

    # Fold expired records into the themes summary file
    if expired:
        lines = []
        for r in expired:
            tags = r.get("themes") or []
            tag_str = f" [{', '.join(tags)}]" if tags else ""
            lines.append(f"- {r.get('date', '?')}: {r.get('title', '')[:70]}{tag_str}")
        block = "\n".join(lines)

        placeholder = "no runs yet" in existing_themes.lower()
        if existing_themes.strip() and not placeholder:
            updated = existing_themes.rstrip() + "\n" + block + "\n"
        else:
            updated = "# Themes covered before the last 30 days\n\n" + block + "\n"
        MEMORY_THEMES_FILE.write_text(updated, encoding="utf-8")
        logger.info("Folded %d expired records into themes summary", len(expired))

    # Build new records from today's chosen stories
    new_records = []
    for story in chosen:
        new_records.append({
            "url":          story.get("final_url") or story.get("url", ""),
            "title":        story.get("title", ""),
            "date":         today_iso,
            "source_label": story.get("source_label", ""),
            "themes":       story.get("themes") or [],
            "why_matters":  story.get("why_matters", ""),
        })

    all_records = recent + new_records
    MEMORY_30_DAYS_FILE.write_text(
        json.dumps(all_records, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    logger.info(
        "Memory saved: %d total records (%d kept, %d new today, %d expired)",
        len(all_records), len(recent), len(new_records), len(expired),
    )
