"""
gather.py — Step 1 of the daily run.

Fetches candidates from all sources, removes stories already in the
30-day memory, and writes candidates.json for the editorial step.

The editorial step (selecting 5 + writing summaries) is done by the
Claude session in the routine, not by this script.
"""

import json
import logging
import sys
from datetime import datetime, timezone

from config import CANDIDATES_FILE, LOGS_DIR
from memory import filter_candidates, load as load_memory
from sources import gather_all

# Logging: file + console
LOGS_DIR.mkdir(exist_ok=True)
today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
log_path = LOGS_DIR / f"{today}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    handlers=[
        logging.FileHandler(log_path, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


def main():
    logger.info("=== GATHER STEP STARTED ===")

    # 1. Pull from all sources
    all_candidates = gather_all()
    n_raw = len(all_candidates)
    logger.info("Gathered %d candidates from feeds", n_raw)

    if not all_candidates:
        logger.error("No candidates gathered — check feeds and network")
        sys.exit(1)

    # 2. Remove stories already sent in the last 30 days
    records, _ = load_memory()
    logger.info("Memory: %d stories in last-30-day window", len(records))
    fresh = filter_candidates(all_candidates, records)

    # 3. Write candidates.json
    CANDIDATES_FILE.write_text(
        json.dumps(fresh, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    logger.info("=== GATHER STEP DONE ===")
    print(f"\n{'='*50}")
    print(f"  Gather complete")
    print(f"  Raw from feeds  : {n_raw}")
    print(f"  After dedup     : {len(fresh)}")
    print(f"  Output          : {CANDIDATES_FILE}")
    print(f"  Log             : {log_path}")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()
