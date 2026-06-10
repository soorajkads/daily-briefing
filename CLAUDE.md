# CLAUDE.md — Project Instructions for the Daily Briefing

These instructions apply to building this project and to the routine that runs it. Read `PLAN.md` in full before doing anything; it is the specification.

---

## Who you're working with

An **inventor and entrepreneur/founder** — not a software engineer. Strong first-principles thinker, beginner at hands-on coding. So:

- Explain choices in **plain terms**, not jargon.
- Work in **small steps**.
- After each step, say **what you did, why you did it that way, and the trade-offs**.
- Preferred language: **Python**.

(This builds on the global "about me" instructions; this file is the project-specific layer.)

---

## What we're building

The Daily Briefing described in `PLAN.md`: a credibility-first, memory-driven personal newsletter that picks the 5 most important stories each day and emails them every morning.

---

## Editorial lens

The reader is an inventor and entrepreneur — the briefing must be useful to someone asking **"what does this mean for what I can build or where the world is going?"** Not useful to a software engineer asking "what should I upgrade today?"

**Include** stories that fit at least one of these five lenses:
1. **Capability shifts** — something that has become newly possible (AI, science, engineering)
2. **Market moves** — funding, M&A, disruption, major business pivots
3. **Regulation & policy** — government or regulatory actions that reshape the playing field
4. **Science frontiers** — discoveries that open new problem spaces
5. **Macro trends** — broad structural shifts in technology, economy, or society

**Exclude** — unless they represent a major industry-level shift (not just a niche patch):
- Developer tooling updates (new npm version, IDE feature, linter rule)
- Security patches and CVEs
- Dependency version bumps
- Developer workflow opinion pieces ("how I structure my code")

---

## Non-negotiable rules

- **Credibility first.** Only ever summarize from the actual fetched article text. Never add facts from your own knowledge. Always include the source link. Label any item where only the headline was available.
- **Never invent visuals** — no generated images, no charts from guessed numbers.
- **Keep it short** — within the reading-time cap in `PLAN.md`.

---

## The model

The daily run uses **Claude Sonnet 4.6** — the right balance of faithful summarizing, judgment, cost, and speed for this lightweight daily job. Don't reach for a heavier model for the run.

---

## How it runs

Packaged as a **Claude Code Routine**, daily at **3:00 AM IST**, on Anthropic's cloud (so it works with the device off). The routine's Claude session does the selection and the grounded summaries; the code handles gathering news, fetching article text, memory, and assembling the email. Delivery goes through the **connected Gmail** — keep email credentials out of the code.

Memory must **persist between runs** — write the updated memory back so the next day can read it.

---

## Conventions

- Small, readable modules; clear names; comments that explain **why**, not just what.
- Keep secrets (the recipient address, any keys) **out of the code**.
- Keep a simple **run log** (how many gathered, chosen, grounded, sent).
- Keep this file and all instruction files **lean** — bloated files get ignored.

---

## How to build

Build in the **milestone order set out in `PLAN.md`**. At the end of each milestone: **stop, explain what was built, and wait for review** before continuing. Use the "Done when" list in `PLAN.md` as the definition of finished.
