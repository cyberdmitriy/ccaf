---
name: exam
description: CCAF study app — builds and opens your offline HTML exam workspace, where you pick a mode (weak / unseen / random / review), choose domains and length, sit the exam with a timer, and see your dashboard. Recording is handled by /ccaf:result. Manual only; run /ccaf:exam.
disable-model-invocation: true
allowed-tools: Bash, Read, Write
---

# CCAF — Study App (mock exam + dashboard)

You build and open a single self-contained offline HTML app. You do **not** select questions,
score anything, or record results — the page does selection and scoring client-side, and
`/ccaf:result` records. Manual only; do NOT auto-invoke other skills.

There are **no arguments** — mode, domains and length are chosen on the page itself.

## Build & open
Follow the shared recipe **`${CLAUDE_PLUGIN_ROOT}/data/app-build.md`** exactly (bootstrap the store →
read `profile.md` → run the Python builder that injects the full bank + authoritative history into
`app-template.html` → write `$HOME/.claude/ccaf-progress/ccaf-exam.html` → open it).

## Then tell the user (briefly)
- The app opened on the **Dashboard** (their progress, per-domain accuracy, exam history, weak areas).
- To sit an exam: click **New exam**, pick a **mode** (weak / unseen / random / review), optionally
  narrow to specific **domains**, choose a **length**, then **Start**.
- They can **pause/resume**, and even close the tab and reopen the file to continue an in-progress exam.
- On **Submit** they get a scored breakdown + a full review with explanations, and a
  **"Copy results as JSON"** button.
- **To record it:** copy that JSON, then run **`/ccaf:result`** in Claude Code and paste it — otherwise
  the sitting stays only in the page's local storage (the dashboard flags it as "unrecorded").

Stop after opening + explaining. Do not try to score or record here.
