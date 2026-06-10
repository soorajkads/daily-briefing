"""
ground.py — Step 3 of the daily run.

Reads selected.json (the SHORTLIST_STORIES=8 candidates ranked by the
editorial step), fetches full article text for each, then fills exactly
TARGET_STORIES=5 slots by preferring items with real text over headline-only
ones. Writes the final 5 to grounded.json.

Run this after the editorial selection and before writing summaries.
"""

import json
import logging
import sys

from config import BASE_DIR, MAX_HN_STORIES, MAX_THEME_STORIES, SHORTLIST_STORIES, TARGET_STORIES
from grounding import fetch_articles

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

SELECTED_FILE = BASE_DIR / "selected.json"
GROUNDED_FILE = BASE_DIR / "grounded.json"


def _fill_slots(
    grounded: list[dict],
    target: int,
    max_per_theme: int = MAX_THEME_STORIES,
    max_hn: int = MAX_HN_STORIES,
) -> list[dict]:
    """
    Return exactly `target` items from grounded.

    Invariant: headline-only items are NEVER selected if any full-text item
    remains unused — even if relaxing both caps is required to pick it.

    Within full-text items, caps are relaxed in four progressive passes:
      Pass 1 — both theme cap and HN source cap respected (ideal)
      Pass 2 — theme cap relaxed, HN cap still respected
      Pass 3 — HN cap relaxed, theme cap still respected
      Pass 4 — both caps relaxed (any remaining full-text item)
    Headline-only items are only added in Pass 5 when the full-text pool is
    completely exhausted.
    """
    full_text    = [s for s in grounded if not s.get("headline_only")]
    headline_only = [s for s in grounded if s.get("headline_only")]

    selected: list[dict] = []
    used: set[int]        = set()
    theme_counts: dict[str, int] = {}
    hn_count = 0

    def _try_add(pool: list[dict], theme_cap: int, hn_cap: int) -> None:
        nonlocal hn_count
        for item in pool:
            if len(selected) >= target:
                break
            if id(item) in used:
                continue
            theme  = (item.get("theme") or "other").lower()
            is_hn  = item.get("origin") == "hacker_news"
            if theme_counts.get(theme, 0) < theme_cap and (not is_hn or hn_count < hn_cap):
                selected.append(item)
                used.add(id(item))
                theme_counts[theme] = theme_counts.get(theme, 0) + 1
                if is_hn:
                    hn_count += 1

    _try_add(full_text, max_per_theme, max_hn)       # Pass 1: both caps
    _try_add(full_text, 999,           max_hn)       # Pass 2: relax theme
    _try_add(full_text, max_per_theme, 999)          # Pass 3: relax HN
    _try_add(full_text, 999,           999)          # Pass 4: all caps off
    _try_add(headline_only, 999,       999)          # Pass 5: last resort only

    return selected[:target]


def main():
    if not SELECTED_FILE.exists():
        print(f"Error: {SELECTED_FILE} not found.")
        print(f"Write selected.json with the {SHORTLIST_STORIES} shortlisted candidates first.")
        sys.exit(1)

    selected = json.loads(SELECTED_FILE.read_text(encoding="utf-8"))
    print(f"Fetching text for {len(selected)} shortlisted stories...\n")

    grounded = fetch_articles(selected)

    n_full = sum(1 for s in grounded if not s.get("headline_only"))
    n_hl = len(grounded) - n_full
    print(f"\nFetch result: {n_full} full text | {n_hl} headline-only")

    final = _fill_slots(grounded, TARGET_STORIES)

    n_final_full = sum(1 for s in final if not s.get("headline_only"))
    n_final_hl = TARGET_STORIES - n_final_full
    print(f"Final {TARGET_STORIES} slots: {n_final_full} full text | {n_final_hl} headline-only")

    if n_final_hl > 0:
        print(f"  Warning: {n_final_hl} slot(s) fell back to headline-only — "
              f"only {n_full} of {len(selected)} shortlisted stories had fetchable text.")

    theme_tally: dict[str, int] = {}
    hn_in_final = 0
    for s in final:
        t = (s.get("theme") or "other").lower()
        theme_tally[t] = theme_tally.get(t, 0) + 1
        if s.get("origin") == "hacker_news":
            hn_in_final += 1
    over_cap = {t: c for t, c in theme_tally.items() if c > MAX_THEME_STORIES}
    if over_cap:
        print(f"  Warning: theme cap relaxed for {over_cap} — pool lacked diversity.")
    else:
        print(f"  Theme spread: {dict(sorted(theme_tally.items()))}")
    if hn_in_final > MAX_HN_STORIES:
        print(f"  Warning: HN cap relaxed — {hn_in_final} HN stories in final {TARGET_STORIES}.")
    else:
        print(f"  HN stories: {hn_in_final} of {TARGET_STORIES}")

    GROUNDED_FILE.write_text(
        json.dumps(final, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Written to {GROUNDED_FILE}")


if __name__ == "__main__":
    main()
