"""
email_sender.py — Step 6 of the daily run.

Reads briefing_items.json, checks idempotency, builds an HTML email,
and sends it via the Resend API (HTTPS, port 443 — works in cloud sandboxes).

Required env keys:
  RECIPIENT_EMAIL  — where to send the briefing
  RESEND_API_KEY   — API key from resend.com (free tier: 3 000 emails/month)

Run this after render.py. On success it updates memory/sent_dates.json
so a re-run on the same day is a no-op.
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30))

import requests
from dotenv import load_dotenv

from config import BASE_DIR, MEMORY_DIR, READING_WPM

load_dotenv()

BRIEFING_ITEMS_FILE = BASE_DIR / "briefing_items.json"
EMAIL_DRAFT_FILE    = BASE_DIR / "email_draft.html"
SENT_DATES_FILE     = MEMORY_DIR / "sent_dates.json"

RECIPIENT      = os.getenv("RECIPIENT_EMAIL", "")
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
# Sender shown in the From field. Resend's shared domain works without DNS setup.
RESEND_FROM    = os.getenv("RESEND_FROM", "Daily Briefing <onboarding@resend.dev>")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_sent_dates() -> list[str]:
    if not SENT_DATES_FILE.exists():
        return []
    return json.loads(SENT_DATES_FILE.read_text(encoding="utf-8"))


def _format_date(iso_str: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_str)
        return f"{dt.day} {dt.strftime('%b %Y')}"
    except Exception:
        return iso_str[:10] if iso_str else ""


def _count_words(*texts: str) -> int:
    return sum(len(t.split()) for t in texts if t)


def _reading_time(items: list[dict]) -> int:
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


def _esc(text: str) -> str:
    """Minimal HTML escaping for plain-text fields inserted into HTML."""
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


# ---------------------------------------------------------------------------
# HTML builder
# ---------------------------------------------------------------------------

def build_html(items: list[dict], display_date: str, reading_mins: int) -> str:
    stories_html = ""

    for i, item in enumerate(items, 1):
        title         = item.get("title", "(no title)")
        source_label  = item.get("source_label", "")
        url           = item.get("final_url") or item.get("url", "")
        pub_date      = _format_date(item.get("published", ""))
        headline_only = item.get("headline_only", False)
        summary       = item.get("summary", "")
        why_matters   = item.get("why_matters", "")
        connection    = item.get("connection_note", "")

        hl_banner = (
            '<div style="background:#fff8e6;border-left:3px solid #d4a017;'
            'padding:10px 14px;margin-bottom:14px;'
            'font-family:\'Helvetica Neue\',Arial,sans-serif;'
            'font-size:13px;color:#7a5000;">'
            '&#9888; Headline only &#8212; article text could not be retrieved.'
            "</div>"
        ) if headline_only else ""

        why_html = (
            f'<p style="margin:0 0 10px;font-size:14px;line-height:1.65;color:#333;">'
            f'<strong>Why it matters:</strong> {_esc(why_matters)}</p>'
        ) if why_matters else ""

        thread_html = (
            f'<p style="margin:0;font-size:13px;line-height:1.55;color:#888;'
            f'font-style:italic;">Thread: {_esc(connection)}</p>'
        ) if connection else ""

        stories_html += f"""
      <div style="border-bottom:1px solid #e8e5e0;padding:24px 0;">
        <div style="font-family:'Helvetica Neue',Arial,sans-serif;color:#aaa;font-size:10px;
                    letter-spacing:2px;text-transform:uppercase;margin-bottom:8px;">{i} / {len(items)}</div>
        <h2 style="margin:0 0 8px;font-size:18px;line-height:1.35;font-weight:bold;color:#1a1a1a;">
          <a href="{_esc(url)}" style="color:#1a1a1a;text-decoration:none;">{_esc(title)}</a>
        </h2>
        <div style="font-family:'Helvetica Neue',Arial,sans-serif;font-size:12px;
                    color:#999;margin-bottom:16px;">
          <a href="{_esc(url)}" style="color:#777;text-decoration:none;">{_esc(source_label)}</a>
          &nbsp;&nbsp;·&nbsp;&nbsp;{_esc(pub_date)}
        </div>
        {hl_banner}
        <p style="margin:0 0 12px;font-size:15px;line-height:1.75;color:#333;">{_esc(summary)}</p>
        {why_html}
        {thread_html}
      </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>Daily Briefing &#8212; {_esc(display_date)}</title>
</head>
<body style="margin:0;padding:0;background:#f0ede8;">
  <table width="100%" cellpadding="0" cellspacing="0" border="0"
         style="background:#f0ede8;font-family:Georgia,'Times New Roman',serif;">
    <tr><td align="center" style="padding:32px 16px;">

      <table width="600" cellpadding="0" cellspacing="0" border="0"
             style="max-width:600px;background:#ffffff;border-radius:3px;">

        <!-- Header -->
        <tr>
          <td style="background:#1a1a1a;padding:24px 32px 22px;border-radius:3px 3px 0 0;">
            <div style="font-family:'Helvetica Neue',Arial,sans-serif;color:#888;font-size:10px;
                        letter-spacing:2.5px;text-transform:uppercase;margin-bottom:6px;">Daily Briefing</div>
            <div style="color:#ffffff;font-size:22px;font-weight:bold;
                        font-family:Georgia,'Times New Roman',serif;margin-bottom:6px;">{_esc(display_date)}</div>
            <div style="color:#aaa;font-family:'Helvetica Neue',Arial,sans-serif;font-size:13px;">
              Estimated reading time: {reading_mins} min
            </div>
          </td>
        </tr>

        <!-- Stories -->
        <tr>
          <td style="padding:0 32px;">
            {stories_html}
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="padding:20px 32px;font-family:'Helvetica Neue',Arial,sans-serif;
                     font-size:11px;color:#bbb;border-top:1px solid #e8e5e0;">
            Your Daily Briefing&nbsp;&nbsp;·&nbsp;&nbsp;Sources linked above
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""


# ---------------------------------------------------------------------------
# SMTP send
# ---------------------------------------------------------------------------

def send_email(subject: str, html: str, plain: str) -> None:
    """Send via Resend HTTPS API (port 443 — works in cloud sandboxes)."""
    resp = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "from": RESEND_FROM,
            "to": [RECIPIENT],
            "subject": subject,
            "html": html,
            "text": plain,
        },
        timeout=30,
    )
    resp.raise_for_status()


def _plain_fallback(items: list[dict], display_date: str, reading_mins: int) -> str:
    """Minimal plain-text version for email clients that don't render HTML."""
    lines = [
        f"Daily Briefing — {display_date}",
        f"Estimated reading time: {reading_mins} min",
        "",
    ]
    for i, item in enumerate(items, 1):
        lines += [
            f"{i}. {item.get('title', '')}",
            f"   {item.get('source_label', '')} · {_format_date(item.get('published', ''))}",
            f"   {item.get('final_url') or item.get('url', '')}",
        ]
        if item.get("headline_only"):
            lines.append("   [HEADLINE ONLY — article text could not be retrieved]")
        if item.get("summary"):
            lines.append(f"   {item['summary']}")
        if item.get("why_matters"):
            lines.append(f"   Why it matters: {item['why_matters']}")
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    if not RECIPIENT:
        print("Error: RECIPIENT_EMAIL not set in .env")
        sys.exit(1)

    if not RESEND_API_KEY:
        print("Error: RESEND_API_KEY not set in .env")
        print("Get a free key at resend.com")
        sys.exit(1)

    if not BRIEFING_ITEMS_FILE.exists():
        print(f"Error: {BRIEFING_ITEMS_FILE} not found.")
        print("Write briefing_items.json first (editorial step).")
        sys.exit(1)

    raw = json.loads(BRIEFING_ITEMS_FILE.read_text(encoding="utf-8"))
    if isinstance(raw, dict):
        items        = raw.get("items", [])
        theme_summary = raw.get("theme_summary", "")
    else:
        items        = raw
        theme_summary = ""

    today_str    = datetime.now(IST).strftime("%Y-%m-%d")
    display_date = _format_date(today_str + "T00:00:00+00:00")

    reading_mins = _reading_time(items)
    html         = build_html(items, display_date, reading_mins)
    plain        = _plain_fallback(items, display_date, reading_mins)

    # Write draft file so the HTML is inspectable even if send fails
    EMAIL_DRAFT_FILE.write_text(html, encoding="utf-8")

    subject_suffix = f" — {theme_summary}" if theme_summary else ""
    subject = f"Your Daily Briefing — {display_date}{subject_suffix}"

    print(f"Sending to {RECIPIENT} ...")
    print(f"Subject : {subject}")
    send_email(subject, html, plain)

    # Mark sent only after successful delivery
    _mark_sent(today_str)
    print("Sent and logged.")


def _mark_sent(date_str: str) -> None:
    dates: list[str] = []
    if SENT_DATES_FILE.exists():
        dates = json.loads(SENT_DATES_FILE.read_text(encoding="utf-8"))
    if date_str not in dates:
        dates.append(date_str)
        SENT_DATES_FILE.write_text(json.dumps(sorted(dates), indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
