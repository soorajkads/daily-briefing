"""
delete_old_briefings.py — Standalone cleanup script. NOT integrated into the routine yet.

Lists all files in the 'Daily Briefing' Google Drive folder and deletes the
oldest ones when the count exceeds KEEP_COUNT (default: 7).

Required env keys (add to the routine environment when integrating):
  GOOGLE_CLIENT_ID
  GOOGLE_CLIENT_SECRET
  GOOGLE_REFRESH_TOKEN

Usage (run manually or add as the final step in the routine):
  python delete_old_briefings.py

To integrate into the routine: add `python delete_old_briefings.py` as a step
after the Drive upload step (6) in the routine instructions.
"""

import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()

KEEP_COUNT  = 7               # number of briefings to retain in the Drive folder
FOLDER_NAME = "Daily Briefing"

CLIENT_ID     = os.getenv("GOOGLE_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
REFRESH_TOKEN = os.getenv("GOOGLE_REFRESH_TOKEN", "")


def _get_access_token() -> str:
    resp = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id":     CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "refresh_token": REFRESH_TOKEN,
            "grant_type":    "refresh_token",
        },
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def _get_folder_id(token: str) -> str | None:
    resp = requests.get(
        "https://www.googleapis.com/drive/v3/files",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "q": (
                f"mimeType = 'application/vnd.google-apps.folder' "
                f"and name = '{FOLDER_NAME}' and trashed = false"
            ),
            "fields": "files(id, name)",
        },
        timeout=15,
    )
    resp.raise_for_status()
    files = resp.json().get("files", [])
    return files[0]["id"] if files else None


def _list_files(token: str, folder_id: str) -> list[dict]:
    """Return all non-trashed files in the folder, oldest first."""
    resp = requests.get(
        "https://www.googleapis.com/drive/v3/files",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "q": f"'{folder_id}' in parents and trashed = false",
            "orderBy": "createdTime",
            "fields": "files(id, name, createdTime)",
        },
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json().get("files", [])


def _delete_file(token: str, file_id: str) -> None:
    resp = requests.delete(
        f"https://www.googleapis.com/drive/v3/files/{file_id}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    )
    resp.raise_for_status()


def main() -> None:
    if not all([CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN]):
        print(
            "Error: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, and GOOGLE_REFRESH_TOKEN "
            "must be set in the environment."
        )
        sys.exit(1)

    token = _get_access_token()

    folder_id = _get_folder_id(token)
    if not folder_id:
        print(f"Folder '{FOLDER_NAME}' not found in Drive — nothing to clean up.")
        return

    files = _list_files(token, folder_id)
    print(f"Found {len(files)} briefing(s) in '{FOLDER_NAME}'.")

    if len(files) <= KEEP_COUNT:
        print(f"Within the {KEEP_COUNT}-briefing window — no deletion needed.")
        return

    to_delete = files[: len(files) - KEEP_COUNT]  # oldest first
    for f in to_delete:
        _delete_file(token, f["id"])
        print(f"Deleted: {f['name']} (created {f['createdTime']})")

    print(f"Done: deleted {len(to_delete)}, retained {KEEP_COUNT}.")


if __name__ == "__main__":
    main()
