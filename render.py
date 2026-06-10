"""
render.py — Step 5 of the daily run.

Reads briefing_items.json (the editorial output written by Claude after
reading the grounded article text), assembles a clean Markdown briefing
file, and updates the two-tier memory.

briefing_items.json format (object with top-level theme_summary):
    {
      "theme_summary": "AI Models, Law & Privacy",   <- 3-5 word email subject suffix
      "items": [
        {
          title          : str
          source_label   : str
          final_url      : str
          published      : str   (ISO-8601 or empty)
          headline_only  : bool
          summary        : str   (<= ~80 words, from the article text)
          why_matters    : str   (one line)
          connection_note: str   (one line)
          themes         : list[str]  (for memory; can be [])
        }, ...
      ]
    }

A bare JSON array is also accepted for backwards compatibility.
"""

import json
import logging
import sys
from datetime import datetime, timezone

from config import BASE_DIR, BRIEFINGS_DIR, READING_WPM, TARGET_STORIES
from memory import load as load_memory
from memory import update as update_memory

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

BRIEFING_ITEMS_FILE = BASE_DIR / "briefing_items.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _format_date(iso_str: str) -> str:
    """Turn an ISO datetime string into '10 Jun 2026'."""
    try:
        dt = datetime.fromisoformat(iso_str)
        return f"{dt.day} {dt.strftime('%b %Y')}"
    except Exception:
        return iso_str[:10] if iso_str else ""


def _count_words(*texts: str) -> int:
    return sum(len(t.split()) for t in texts if t)


def _reading_time(items: list[dict]) -> int:
    """Estimate reading time from summary + why_matters + connection_note words."""
    total = sum(
        _count_words(
            item.get("title", ""),
            item.get("summary", ""),
            item.get("why_matters", ""),
            item.get("connection_note", ""),
        )
        for item in items
    )
    return max(1, round(total / READING_WPM))


# ---------------------------------------------------------------------------
# Renderer
# ---------------------------------------------------------------------------

def build_briefing(items: list[dict], today_str: str) -> str:
    mins = _reading_time(items)
    lines = [
        f"# Daily Briefing — {today_str}",
        "",
        f"*Estimated reading time: {mins} min*",
        "",
        "---",
        "",
    ]

    for i, item in enumerate(items, 1):
        title          = item.get("title", "(no title)")
        source_label   = item.get("source_label", "")
        url            = item.get("final_url") or item.get("url", "")
        published      = _format_date(item.get("published", ""))
        headline_only  = item.get("headline_only", False)
        summary        = item.get("summary", "")
        why_matters    = item.get("why_matters", "")
        connection_note= item.get("connection_note", "")

        lines += [f"## {i}. {title}", ""]

        # Source line: clickable name + date on same line
        pub_part = f"  •  {published}" if published else ""
        lines += [f"**Source:** [{source_label}]({url}){pub_part}", ""]

        if headline_only:
            lines += [
                "> ⚠ **Headline only** — the article text could not be "
                "retrieved. This item is based on the headline and feed "
                "snippet only.",
                "",
            ]

        if summary:
            lines += [summary, ""]

        if why_matters:
            lines += [f"**Why it matters:** {why_matters}", ""]

        if connection_note:
            lines += [f"**Thread:** {connection_note}", ""]

        lines += ["---", ""]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    if not BRIEFING_ITEMS_FILE.exists():
        print(f"Error: {BRIEFING_ITEMS_FILE} not found.")
        print("Write briefing_items.json with the 5 editorial items first.")
        sys.exit(1)

    raw = json.loads(BRIEFING_ITEMS_FILE.read_text(encoding="utf-8"))
    items = raw.get("items", raw) if isinstance(raw, dict) else raw

    if len(items) != TARGET_STORIES:
        print(f"Warning: expected {TARGET_STORIES} items, found {len(items)}")

    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Write briefing file
    BRIEFINGS_DIR.mkdir(exist_ok=True)
    out_path = BRIEFINGS_DIR / f"{today_str}.md"
    out_path.write_text(build_briefing(items, today_str), encoding="utf-8")
    print(f"Briefing written: {out_path}")

    # Update memory
    records, themes_text = load_memory()
    update_memory(items, records, themes_text)
    print("Memory updated.")


if __name__ == "__main__":
    main()
