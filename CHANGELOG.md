# Changelog

All notable changes to the `ccaf` plugin. Dates are ISO (YYYY-MM-DD).

This file also records **content reviews** — the periodic sync against the official Exam Guide and
Claude Code / API docs (procedure: `maintenance/RUNBOOK.md`; sources + last-verified stamp:
`maintenance/sources.md`).

## [0.9.1] — 2026-07-19
### Fixed
- **Learning-progress reads no longer fail silently.** `app-build.md`'s `load_learning()` now
  distinguishes an **absent** file (expected first run → skeleton, no warning) from a **present-but-
  malformed** one (→ skeleton for rendering **plus** a `learning_unreadable` flag). The dashboard shows
  a warning banner instead of silently rendering zero progress, and `/ccaf:init` reports the corruption
  plainly rather than "no progress yet."
- **Tutor write-contract no longer risks silent data loss.** `teaching-method.md` now says: a
  present-but-unparseable `learning-progress.json` must be backed up to `.bak` and surfaced — **never**
  skeleton-recreated (which would wipe the other domains' progress). Only a genuinely missing file is
  safe to recreate.
### Added
- `data/validate.py --learning <path>` — shape-checks a `learning-progress.json` (schema, domains 1–5
  keys + valid status, `axis_mastery`, drills/task_statements shape). Referenced by the warning banner,
  `/ccaf:init`, and the maintenance runbook.

## [0.9.0] — 2026-07-18
### Changed
- **Sync is now a maintainer procedure, not a shipped command.** Removed the `/ccaf:sync` slash command
  (`commands/sync.md`) — keeping the plugin's content current can edit skills, lessons, and the bank,
  which is maintainer work, not something an installed user should run.
- Moved the source-of-truth + last-verified stamp from `data/sources.md` to `maintenance/sources.md`
  (no longer runtime data).
### Added
- `maintenance/` (maintainer-only, not referenced by any skill/command):
  - `RUNBOOK.md` — the every-6–12-months content-review procedure.
  - `bank-coverage-audit.workflow.js` — stored multi-agent audit that maps the bank to the official task
    statements and checks the guide's sample questions (report-only).
  - `sources.md` — moved here.
- This `CHANGELOG.md`.

## [0.8.1] — 2026-07-18
### Fixed
- Corrected the Exam Guide facts against the **primary source** (official PDF): the guide is **v1.0,
  Effective July 2026, CCAR-F** (not the v0.2 taken from a third-party summary), and it is **publicly
  downloadable** (Skilljar landing → public S3 PDF), **not** login-gated.
### Added
- Authoritative data from Exam Guide v1.0 in `sources.md`: format (60 items, multiple-choice **and
  multiple-response**, 4-of-6 scenarios, 720/1000, $125), blueprint weights **27/18/20/20/15** (matches),
  and the **30 task statements** (D1:7 D2:5 D3:6 D4:6 D5:6 → authoritative `task_total`).
- Documented a **known fidelity gap**: the exam has multiple-response items; the bank is single-answer only.

## [0.8.0] — 2026-07-18  _(superseded by 0.9.0)_
### Added
- `/ccaf:sync` freshness-check command + `data/sources.md` baseline. *(The command was removed in 0.9.0
  in favor of the maintainer runbook; the sources file moved to `maintenance/`.)*

## [0.7.0] — 2026-07-18
### Added
- **Learning-progress tracking.** A per-user `~/.claude/ccaf-progress/learning-progress.json` (separate
  from `stats.json`) records task-statement coverage, in-tutor drill scores, last-visited, and per-axis
  mastery. Written by the `dN-teacher` tutors at hand-off; surfaced as text in `/ccaf:init` and as a
  "Learning progress" card in the `/ccaf:stats` dashboard. Bootstrapped additively via `cp -rn`.

## [0.6.6] — baseline
- Pre-changelog baseline: 5 domain tutors, `/ccaf:init` / `/ccaf:result`, offline mock-exam app
  (`/ccaf:exam` + `/ccaf:stats`), 240-question bank, 5-axis trap framework.

---

## Content reviews
| Date | Exam Guide | Docs checked | Outcome |
|------|-----------|--------------|---------|
| 2026-07-18 | v1.0 (Effective July 2026) | 2026-07-18 | Blueprint + 30 task statements verified against the guide — **match**. Coverage audit: all 30 task statements `good`, 0 of 12 sample questions missing. No bank edits needed. Open gap: multiple-response items untrained. |
| 2026-07-19 | v1.0 (Effective July 2026) | 2026-07-19 | **Layer-2 fact-currency audit** (per-domain, vs current Claude Code + Platform docs): **0 stale facts** across all 5 domains — every falsifiable flag/path/number/API detail is current. 2 D3 semantic nuances (`allowed-tools` = restrict; `/memory` = shows loaded files) match the Guide but the product moved past it → recorded under "Known exam-vs-product divergences" in `sources.md`; **content unchanged** (correct for the exam). No bank/skill/lesson edits. Added stored `maintenance/fact-currency-audit.workflow.js`. |
