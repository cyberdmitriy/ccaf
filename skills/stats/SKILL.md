---
name: stats
description: CCAF progress dashboard — builds and opens your offline study app on the Dashboard view (accuracy, per-domain and axis breakdowns, exam history, recurring fails) and prints a short text summary. Read-only; run /ccaf:stats.
disable-model-invocation: true
allowed-tools: Bash, Read, Write
---

# CCAF — Progress Dashboard

You open the study app on its **Dashboard** and give a tight text summary. This is **read + report
only** — you never record or modify progress (building the HTML is not a write to the store).
Manual only; do NOT auto-invoke other skills.

## Build & open
Follow the shared recipe **`${CLAUDE_PLUGIN_ROOT}/data/app-build.md`** exactly (same build as
`/ccaf:exam` — it opens on the Dashboard). **Rebuild every run:** run the recipe's build step (Steps
1–4) even if `ccaf-exam.html` already exists — never just `open` a stale file, or new questions,
freshly-recorded history, and new views (e.g. the Cheatsheet tab) won't appear. The dashboard shows overall accuracy, per-domain
accuracy vs blueprint weight with focus markers, coverage (answered vs remaining), exam history
(mock and external kept **separate**, never averaged), a **Learning progress** card (tutor
task-statement coverage + in-tutor drill scores + per-axis mastery, from `learning-progress.json`),
the 5-axis trap tally, and recurring misses.

## If the store is empty
If `stats.json` has no `exam_history` and an empty `answered`, say so plainly — the dashboard will
show a welcome/empty state — and suggest `/ccaf:exam` or a `/ccaf:dN-teacher`. Do not fabricate numbers.

## Print a short text summary (from `stats.json`, never invent)
After opening, print a tight recap so the user gets value without switching to the browser:
- overall accuracy (correct / seen across `answered`, latest attempt per question),
- per-domain accuracy + which domain is weakest,
- number of exams taken (note mock vs external separately),
- the dominant failure axis (highest `axis_tally` — recomputed by `/ccaf:result` from your latest-attempt misses, so it matches the dashboard's 5-axis chart),
- any sittings the page will flag as **unrecorded** if you can tell (otherwise mention the page shows them).
- **Focus check:** read `profile.md`'s `## Focus domains` section. If it's still `_(unset)_` **but** `exam_history` already has entries (e.g. an external/official result), warn the user that weak-mode won't bias toward their weak domains until focus is set, and tell them to re-run `/ccaf:result` (which now writes that section) or add `D<n>` lines by hand.

Then recommend the single next command — `/ccaf:dN-teacher` for the weakest domain, or `/ccaf:exam` —
and stop. Do not auto-invoke it.
