---
name: dashboard
description: CCAF study app — generates & opens your offline study app with your progress dashboard (accuracy, per-domain stats, exam history) AND a configurable mock exam (start it from the in-app "Mock Exam" button), plus Weak spots and a Cheatsheet reference. Prints a short text recap. Read-only; run /ccaf:dashboard.
disable-model-invocation: true
allowed-tools: Bash, Read, Write
---

# CCAF — Study App & Progress Dashboard

You build and open the single self-contained offline app and give a tight text recap. This is
**read + report only** — you never record or modify progress (building the HTML is not a write to
the store). `/ccaf:result` is the only recorder. Manual only; do NOT auto-invoke other skills.

## Build & open
A plugin hook rebuilds+opens the app deterministically when `/ccaf:dashboard` is typed.
- **If you see a `[ccaf-hook] Rebuilt & opened …` marker in context**, the hook already did it — do
  **NOT** build again; just give the text recap below.
- **If there is no such marker** (hooks disabled, or the first run right after a `/plugin marketplace
  update` before a reinstall), run the fallback build yourself:
  `python3 "${CLAUDE_PLUGIN_ROOT}/data/build-app.py" --open` (it bootstraps + rebuilds + opens; never
  open a stale `ccaf-exam.html`).

The app opens on the **Dashboard**; everything else is a tab (**Weak spots**, **Cheatsheet**) and
**Mock Exam** is a button in the top bar.

## To sit an exam
Tell the user: click **Mock Exam** in the app, pick a mode (weak / unseen / random / review),
optionally narrow to domains, choose a length, then **Start**. Pause/resume and resume-later work;
on **Submit** they get a scored review + a **Copy results as JSON** button — paste that into
**`/ccaf:result`** to record it, else it stays only in the page's local storage (flagged "unrecorded").

## If the store is empty
If `stats.json` has no `exam_history` and an empty `answered`, say so plainly (the app shows a
welcome/empty state) and suggest starting a mock exam or a `/ccaf:dN-teacher`. Never fabricate numbers.

## Print a short text recap (from `stats.json`, never invent)
- overall accuracy (correct / seen across `answered`, latest attempt per question),
- per-domain accuracy + weakest domain,
- exams taken (mock vs external separately, never averaged),
- dominant failure axis (highest `axis_tally`),
- any sittings the page will flag as **unrecorded**,
- **Focus check:** read `profile.md`'s `## Focus domains`. If `_(unset)_` but `exam_history` has
  entries, warn weak-mode won't bias to weak domains until focus is set — tell them to re-run
  `/ccaf:result` or add `D<n>` lines by hand.

Then recommend the single next command (`/ccaf:dN-teacher` for the weakest domain, or record a
result) and stop.
