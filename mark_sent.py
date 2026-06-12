"""
mark_sent.py — Called by the Claude routine after a successful Gmail send.

Appends today's date to memory/sent_dates.json so email_sender.py
knows not to send again if the routine re-runs on the same day.
"""

import json
import sys
from datetime import datetime, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30))

from config import MEMORY_DIR

SENT_DATES_FILE = MEMORY_DIR / "sent_dates.json"


def mark_sent(date_str: str | None = None) -> None:
    if date_str is None:
        date_str = datetime.now(IST).strftime("%Y-%m-%d")

    dates: list[str] = []
    if SENT_DATES_FILE.exists():
        dates = json.loads(SENT_DATES_FILE.read_text(encoding="utf-8"))

    if date_str in dates:
        print(f"{date_str} already in sent log — nothing to do.")
        return

    dates.append(date_str)
    SENT_DATES_FILE.write_text(
        json.dumps(sorted(dates), indent=2),
        encoding="utf-8",
    )
    print(f"Marked {date_str} as sent in {SENT_DATES_FILE}")


if __name__ == "__main__":
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    mark_sent(date_arg)
