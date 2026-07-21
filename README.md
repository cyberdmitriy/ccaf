# CCAF Architect Exam Tutor — Claude Code plugin

Interactive tutor + mock-exam generator for the **Claude Certified Architect – Foundations (CCAF)** exam.
Five domain teachers, trap drills built on a 5-axis distractor framework, and a configurable offline
HTML mock exam. Per-user progress is tracked locally and never ships with the plugin.

## Install

Clone this repo (or copy the `ccaf-plugin/` folder) somewhere on your machine, then in Claude Code point the
marketplace at that folder's **absolute path** and install:

```
/plugin marketplace add /absolute/path/to/ccaf-plugin
/plugin install ccaf@ccaf-marketplace
```

Once it's pushed to a git host, `/plugin marketplace add <git-host>/ccaf-plugin` works the same way.
Reinstall after updates with `/plugin marketplace update ccaf-marketplace`.

Then run **`/ccaf:init`** to set up and get routed.

## Commands / skills (all manual-only — never auto-invoked)

| Invoke | What it does |
|--------|--------------|
| `/ccaf:init` | Onboarding hub: creates your progress store, shows bank stats, and routes you to the right activity (records results via `/ccaf:result`). |
| `/ccaf:d1-teacher` … `/ccaf:d5-teacher` | Interactive domain tutors (D1 Agentic Arch · D2 Tool Design/MCP · D3 Config & Workflows · D4 Prompt Eng & Structured Output · D5 Context & Reliability). |
| `/ccaf:dashboard` | Build & open your offline study app. Pick a mode (`weak`/`unseen`/`random`/`review`), narrow to domains, choose a length **on the page**, sit it with a timer (pause/resume, resume-later, and an optional **2-min-per-question time limit**: at zero it tells you "time's up" and flags the attempt as *over time*, but never submits for you — you always finish every question). **Sit it from the keyboard:** `1`–`4`/`A`–`D` answer the current question, `J`/`K` (or `↑`/`↓`) move between questions, the nav highlights where you are, and **Jump to unanswered** skips to the first blank. `weak` mode now also resurfaces questions you haven't seen in a while (light spaced repetition). Copy the results JSON when done and record it with `/ccaf:result`. |
| `/ccaf:result` | **The single recorder.** Records ANY result — the study app's results JSON (one sitting or a batch), or an external attempt (official/other practice) from a screenshot or pasted breakdown — and re-ranks your focus domains. |
| `/ccaf:dashboard` | Opens the same offline app on its **Dashboard** — accuracy, per-domain accuracy vs blueprint weight, coverage, exam history (mock vs external kept separate) with a **score-trend sparkline**, 5-axis trap tally, recurring fails — plus a **Cheatsheet** tab: your personal *trigger keyword → pick this, not that → why* table, built from the questions you've missed (active on top, mastered ones collapsed once you later answer them right; filter by domain/axis/search). It's populated by `/ccaf:result` — including a backfill of misses you recorded before the cheatsheet existed. Plus a short text summary. There's also a **Reference** tab — a curated *signal phrase in the question → the answer* cheat sheet across all five domains (a study aid built from the exam traps; distinct from the personal, miss-driven Cheatsheet), with a domain filter and search. |

**Reviewing results:** the results page opens on your **misses only** (no more scrolling a whole 60-question exam); flip to **All** or filter by domain with one click, and each question shows the **axis** its trap trips on so you learn the pattern, not just the answer.

## How focus works

There are **no hardcoded focus domains** — focus is data-driven per user. All results go through
`/ccaf:result`: a `/ccaf:dashboard` JSON updates per-question stats + fails, while an external screenshot/text
records a per-domain snapshot. Either way it writes a ranked weak-domain list to `profile.md` and a
distinct, timestamped entry to `stats.json` (mock and external are never averaged together). Every
teacher/exam reads those on startup and biases toward your weakest domains. During onboarding `/ccaf:init`
points you to `/ccaf:result` to record any prior result.

Every skill sets `disable-model-invocation: true`, so Claude never triggers them on its own and they add
zero ambient context — they run only when you type them.

## Per-user progress (not in the plugin)

Created on first run at **`~/.claude/ccaf-progress/`** — unique per person, survives plugin updates *and*
uninstalls:
- `profile.md` — recorded prior results + ranked weak/focus domains (the only thing the app reads for personalisation)
- `fails-tracker.md` — verbatim missed questions
- `trap-log.md` — trap types by axis + tally
- `stats.json` — machine-readable per-question/-domain stats + exam history (the app's authoritative source)
- `ccaf-exam.html` — the generated offline study app (rebuilt each `/ccaf:dashboard` or `/ccaf:dashboard`; holds in-progress + unrecorded sittings in its own `localStorage` until you record them)

## The 5-axis framework

Every distractor fails on exactly one axis: **1 Determinism · 2 Exact-hit · 3 Right-diagnosis ·
4 Proportionality · 5 Root-cause/antipattern.** The teachers drill you to *name the axis* — the skill that
transfers across every practice exam. See `data/axes.md`.

## Maintaining or extending the plugin

Adding questions, lessons, or traps — or changing how it works? The schema, invariants, and full
workflow live in **`CLAUDE.md`** (auto-loaded when you work in this repo) — the single source of truth
for changing the plugin. Every release and content review is logged in **`CHANGELOG.md`**. This README
stays focused on *using* it.

**Keeping content current (periodic, every 6–12 months).** The exam and docs drift, so the bundled
content is re-verified against the official sources on a schedule. Full procedure: **`maintenance/RUNBOOK.md`**.
To run it: open this repo in Claude Code, download the current Exam Guide PDF (link in
`maintenance/sources.md`), then prompt *"run the CCAF maintenance review per `maintenance/RUNBOOK.md`"*.
It fetches the latest Exam Guide + Claude Code / API docs and runs two stored, **report-only** audits —
`bank-coverage-audit` (bank ↔ official task statements) and `fact-currency-audit` (flags/paths/numbers
vs current docs) — then proposes any edits for your approval. This is a **maintainer** task, not
something plugin users run.

## Layout
```
ccaf-plugin/
├─ .claude-plugin/{plugin.json, marketplace.json}
├─ commands/{init.md, result.md}
├─ skills/{d1..d5-teacher, exam, stats}/SKILL.md
├─ data/{questions.json, validate.py, tutor-prompts.md, exam-traps.md, axes.md, teaching-method.md,
│        app-template.html, app-build.md, progress-template/}
└─ maintenance/  # maintainer-only: RUNBOOK.md, sources.md, bank-coverage-audit.workflow.js (see CLAUDE.md)
```
