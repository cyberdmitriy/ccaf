# CCAF — Sources of truth & freshness baseline

This file is the **authoritative-source list** for the plugin's teaching content, plus a
**last-verified stamp**. `/ccaf:sync` reads it to report what has changed upstream since the stamp;
the maintainer updates the stamp (and this list) whenever the bundled content is refreshed against
these sources. It ships with the plugin (read-only at runtime — `/ccaf:sync` never writes it).

Why two layers: the **exam blueprint** (format, domains, weights, task statements) changes only when
Anthropic publishes a new **Exam Guide** version, and that guide lives **behind the Partner Academy
login** — it cannot be fetched automatically, so it is checked by hand. The **technical behavior** the
exam tests (CLI flags, hooks, MCP, `tool_choice`, Batch API, …) lives in **public product docs** that
update continuously and **can** be fetched.

## Last verified
- **Exam Guide:** v0.2 (2026-06-30) — format 60 questions · 120 min · 720/1000 to pass · 5 domains
  weighted **D1 27% · D2 18% · D3 20% · D4 20% · D5 15%**. Delivery via Pearson VUE (OnVUE).
- **Product docs / changelogs checked:** 2026-07-18.
- **Bundled content built/last-synced:** 2026-07-18 (bank = 240 questions).

> When you refresh content against the sources below, bump these three lines and the plugin version.

## Layer 1 — Exam blueprint (GATED · check by hand, not fetchable)
The single authoritative source for the blueprint, domain weights, and task statements. Always
**download the current Exam Guide before booking** — weights and wording shift between versions.
- Anthropic Partner Academy (Skilljar) — the exam + official Exam Guide (login-gated): registration
  starts here, scheduling via Pearson VUE.
- Pearson VUE — Anthropic certification program: https://www.pearsonvue.com/us/en/anthropic.html
- Public overview mirrors (unofficial, handy for a quick blueprint sanity-check, NOT authoritative):
  - https://claudecertifications.com/claude-certified-architect
  - https://claudecertifications.com/claude-certified-architect/domains

## Layer 2 — Technical behavior (PUBLIC · fetchable by `/ccaf:sync`)
These are the official product docs the exam is built on. `/ccaf:sync` fetches the changelog/release
pages and reports entries dated after the "Last verified" stamp above.
- **Claude Code changelog** (D2/D3 — CLI flags, hooks, slash commands, plan mode, CI/CD):
  https://code.claude.com/docs/en/changelog
- **Claude Code releases (GitHub)** (same, sometimes fresher):
  https://github.com/anthropics/claude-code/releases
- **Claude Platform / API release notes** (D2/D4 — tool use, `tool_choice`, Message Batches API, MCP):
  https://platform.claude.com/docs/en/release-notes/overview
- **Claude Help Center release notes** (product-wide):
  https://support.claude.com/en/articles/12138966-release-notes

## Domain → source map (where a change most likely lands)
- **D1 Agentic Architecture** — Agent SDK docs + Claude Code changelog (hooks, subagents, sessions).
- **D2 Tool Design & MCP** — Platform release notes (tool_use, tool_choice) + Claude Code changelog (built-ins, MCP config).
- **D3 Config & Workflows** — Claude Code changelog (CLI flags, CLAUDE.md, rules, plan mode, `-p`/`--output-format`).
- **D4 Prompt Eng & Structured Output** — Platform release notes (Batch API, JSON-schema tool output).
- **D5 Context & Reliability** — Platform release notes + Claude Code changelog (context/session behavior).

## What to do when something changed
`/ccaf:sync` is **report-only** — it never edits the bank. When it flags a drift:
1. Re-download the latest **Exam Guide** from Partner Academy; if the version > the stamp above,
   reconcile blueprint weights / task statements by hand.
2. For behavior changes, run the **bank-extension workflow** in `CLAUDE.md` (extract → classify →
   dedupe → assign ids/axis → `python3 data/validate.py` → version bump) to add/adjust questions.
3. Update the three "Last verified" lines here and bump the plugin version.
