---
name: dashboard
description: CCAF study app — builds and opens your offline study app (Dashboard, Weak spots, Cheatsheet; start a mock exam from the in-app "Mock Exam" button) and prints a short progress recap. Read-only; run /ccaf:dashboard.
disable-model-invocation: true
allowed-tools: Bash, Read, Write
---

# CCAF — Study App & Progress Dashboard

You build and open the single self-contained offline app and give a tight text recap. This is
**read + report only** — you never record or modify progress (building the HTML is not a write to
the store). `/ccaf:result` is the only recorder. Manual only; do NOT auto-invoke other skills.

## Build & open
A plugin hook rebuilds+opens the app deterministically when `/ccaf:dashboard` is typed. **Belt-and-braces:**
also follow the shared recipe **`${CLAUDE_PLUGIN_ROOT}/data/app-build.md`** (it just runs
`data/build-app.py`) so the app is fresh even if hooks are disabled — always rebuild, never open a
stale `ccaf-exam.html`. The app opens on the **Dashboard**; everything else is a tab
(**Weak spots**, **Cheatsheet**) and **Mock Exam** is a button in the top bar.

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
