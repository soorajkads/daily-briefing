# PLAN.md — Daily Briefing

A credibility-first, memory-driven personal newsletter, delivered by email every morning.

---

## Goal

Every morning, deliver a short email containing the **5 most important stories** across AI/agents, technology, science, tech business, and policy — chosen not just to keep me informed, but to **broaden my thinking over time**, and written so that I can trust every word.

The single most important rule: **the briefing must never mislead me.** What it tells me goes into my head and shapes how I think, so accuracy beats everything except outright safety.

---

## Topic scope

Include stories about:

- AI and AI agents
- Technology
- Science
- Tech business
- **Government and policy — only where it touches the topics above** (e.g. AI regulation, technology and data policy, science funding decisions, central-bank and market moves such as RBI/SEBI). **Not** general or partisan politics.

---

## Daily flow

1. **Gather** a broad pool of headlines from the **last 48 hours** from the sources below.
2. **Remove repeats** — drop anything already sent in the last 30 days.
3. **Choose the 5 most important**, applying the selection rules.
4. **Ground each one** — fetch the real article text and write a faithful summary from it.
5. **Assemble** the email.
6. **Send** it via the connected Gmail.
7. **Remember** — record the 5 stories and their themes into memory for tomorrow.

---

## Selection rules (the editorial brain)

The reader is an **inventor and entrepreneur** — not a software engineer. Ask: *"What does this mean for what I can build or where the world is going?"*

- Only **genuinely important** items are eligible.
- Prefer items across the five lenses: **capability shifts**, **market moves**, **regulation/policy**, **science frontiers**, **macro trends**.
- Prefer items that **connect to recent days' themes but push a step wider** — a new angle or an adjacent area. Never the same narrow corner two days running. Over a week the spread should visibly broaden, not tunnel.
- A **genuinely major story may break the pattern** and be included regardless of how it connects.
- **Exclude** — unless they represent a major industry-level shift: developer tooling updates, security patches, dependency bumps, developer workflow opinion pieces.
- Output **exactly 5** covering at least 3 of the 5 lenses on any given day.

---

## Credibility rules (highest priority)

- **Never state a fact that is not in the fetched article text.** No outside knowledge, no filling gaps, no guessing.
- Always include the **source name and a working link**.
- If only a headline or snippet was available (the article could not be read), **label it plainly** as such.
- The summary is a faithful **pointer to the source**, never a replacement for it.

---

## Visuals

- v1: **none invented.** No generated images. No charts built from guessed numbers.
- Later layers: real source thumbnails (with attribution), then charts only when real figures appear in the source.

---

## Length

- Short and clean: target a few minutes to read, **hard cap ~20 minutes**.
- Each item summary **<= ~80 words** (about 3-4 sentences).
- Show the **estimated reading time** at the top (word count / ~230 words per minute).
- Plain language. One idea per line. No jargon dumps.

---

## Memory (two tiers)

- **Last 30 days — full detail.** Used for both the 5-7 day "connected but widening" window and the 30-day no-repeat check.
- **Older than 30 days — folded into a single rolling "themes covered" note**, so the memory stays tidy instead of growing forever.
- Memory must **persist across runs.** Because each cloud run starts from a fresh copy of the project, the run must write the updated memory back so the next day can read it (commit it back to the repository; a connected Google Drive file is an acceptable alternative).

---

## Sources (v1 — free, no API keys)

- **Google News RSS** — topic feeds (Technology, Business, Science) plus keyword queries for AI/agents and for policy/finance (e.g. AI regulation, RBI, SEBI).
- **Hacker News** — top stories, for the tech/science signal.

Normalize every item to: title, link, source, published date, snippet. Restrict to the **last 48 hours**.

---

## The model

- **Daily run: Claude Sonnet 4.6.** Best balance of faithful summarizing, sound editorial judgment, low cost, and speed for a lightweight daily job. (Opus is overkill and burns more of the allowance; Haiku is too risky on the summaries, which is exactly where faithfulness matters most.)
- **Building the project:** any strong model is fine since it only happens occasionally; Sonnet 4.6 is more than enough.

---

## How it runs

- Packaged as a **Claude Code Routine**, scheduled **daily at 3:00 AM IST**, running on Anthropic's cloud so it works while my device is off.
- The **routine's Claude session (Sonnet 4.6) does the editorial work** — selecting the 5 and writing the grounded summaries from the fetched text — so the work stays on subscription usage rather than separate billed calls.
- The **code handles the mechanical parts**: gathering the news, fetching article text, reading/writing memory, and assembling the email.
- **Delivery via the connected Gmail** (no email passwords stored in code).

### Routine prompt (to paste into the routine setup)

> First run `pip install -r requirements.txt --quiet` to ensure dependencies are available.
> Then build today's Daily Briefing by following PLAN.md and CLAUDE.md in this repository.
> Steps: (1) run `python gather.py` — collects the last 48 hours of candidate stories, removes items already in the 30-day memory, writes candidates.json; (2) read candidates.json plus memory/last_30_days.json and memory/themes_summary.md, then select the 8 most important candidates — the reader is an inventor/entrepreneur, not a software engineer, so apply the five-lens test: capability shifts, market moves, regulation/policy, science frontiers, macro trends. Exclude developer tooling, security patches, dependency updates, and dev-workflow opinion pieces unless they represent a major industry-level shift. Each item must include a "theme" field from: AI, Science, Technology, Business, Finance, Policy, Other. Ensure no more than 2 of the 8 share the same primary theme. Prefer candidates with origin "direct_feed" or "hacker_news" over "google_news" — google_news URLs are unresolvable and will be headline-only after grounding. Write selected.json ranked best-first; (3) run `python ground.py` — fetches article text for all 8 and writes the best 5 to grounded.json, enforcing: (a) no headline-only item if any full-text alternative exists, (b) at most 1 HN story, (c) at most 2 stories per theme; (4) for each item in grounded.json, read the "text" field and write a faithful summary of ≤80 words plus a one-line "why it matters" and a one-line connection note — using only the provided text, never outside facts. Write briefing_items.json as {"theme_summary": "3–5 word topic string", "items": [...]}; (5) run `python render.py` — writes the Markdown briefing to briefings/YYYY-MM-DD.md and updates memory; (6) run `python email_sender.py` — sends the email via Gmail SMTP using the RECIPIENT_EMAIL and GMAIL_APP_PASSWORD environment variables; (7) commit the updated memory and briefing back to the repository so tomorrow's run can read them: `git remote set-url origin https://${GITHUB_TOKEN}@github.com/soorajkads/daily-briefing.git && git config user.email "routine@daily-briefing" && git config user.name "Daily Briefing Routine" && git add memory/ briefings/ && git commit -m "briefing: $(date +%Y-%m-%d)" && git push`. If a source or article cannot be read, log it, skip it, and carry on. Never invent facts, images, or charts.

---

## Delivery

Email to **[YOUR_EMAIL — fill this in]** via the connected Gmail.

---

## Build order

- **M1** — gather -> remove repeats -> choose 5 -> fetch-and-summarize -> write the briefing to a file. *(A real, credible briefing saved to disk.)*
- **M2** — send it as a clean email via Gmail.
- **M3** — tune the connected-but-widening behaviour; harden against a dead source or an unreadable article.
- **M4 (later)** — real visuals.

---

## Done when

1. One run produces **exactly 5** important stories across the topics, each with source + link + date + a faithful summary + a one-line "why it matters" + a one-line connection note.
2. Headline-only items are clearly labelled.
3. Re-running the same day does **not** double-send.
4. A broken source or an unreadable article is **skipped, not fatal** (logged and the run finishes).
5. Memory grows with **no repeats inside 30 days**; older entries are folded into the rolling themes note.
6. Day 2's picks visibly connect to Day 1's, and over a week the spread clearly **widens**.
7. Reading time stays **under 20 minutes** (usually a few).
8. It runs automatically at 3:00 AM IST with my device off, and the briefing is waiting when I wake.

---

## Suggested project layout (flexible — Claude Code may simplify)

- a main entry point that runs the daily flow
- a **sources** module (the gatherers)
- a **grounding** module (fetch article text)
- a **memory** module (read/write the two tiers, remove repeats)
- a **render** module (build the email)
- a small **config** (topics, keywords, sources, counts, the recipient, the 48-hour window)
- a run **log**
- folders for memory data and saved briefings

**Dependencies:** Python 3.11+, plus requests, feedparser, trafilatura, and jinja2. Keep secrets out of the code.
