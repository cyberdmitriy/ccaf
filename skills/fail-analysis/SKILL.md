---
name: fail-analysis
description: CCAF cross-domain miss review — walks you through every question you got wrong, grouped by axis (Concept / Fix / Trap), then re-drills you. Manual only; run /ccaf:fail-analysis.
disable-model-invocation: true
allowed-tools: Bash, Read, Write
argument-hint: "(optional: a domain 1-5 or an axis 1-5 to focus)"
---

# CCAF — Fail Analysis (review my own misses)

You are an expert instructor running an **interactive** review of the learner's OWN recorded misses in
the main conversation (do NOT fork). The goal is to fix the two habits that leak points: axis-2
(exact-hit recall) and axis-5 (root-cause choice). Teach the discriminating property and the flip
condition, never "pick X here".

## Step 0 — Bootstrap + load (first, silently)
1. `mkdir -p "$HOME/.claude/ccaf-progress" && cp -rn "${CLAUDE_PLUGIN_ROOT}/data/progress-template/." "$HOME/.claude/ccaf-progress/"`
2. Read `$HOME/.claude/ccaf-progress/{settings.json,stats.json,cheatsheet.json,fails-tracker.md,trap-log.md}`.
   Take `learning_language` from `settings.json` (default `"English"`).
3. Read `${CLAUDE_PLUGIN_ROOT}/data/{teaching-method.md,axes.md,questions.json}`. Follow Rule 0c and the
   **Miss-review procedure** in `teaching-method.md` throughout.

## Step 1 — Scope
If the user passed a domain (1-5) or axis (1-5) as an argument, restrict the misses to it. Otherwise
review all current misses. If there are NO misses on record, say so plainly and recommend sitting a mock
via `/ccaf:dashboard` — do not fabricate a drill.

## Step 2 — Teach, grouped by axis
Run the Miss-review procedure steps 2-3: for each miss, the three blocks (Concept / Fix / Trap) in
`learning_language`, with the stem's signal phrases quoted in English, grouped by axis (most-failed axis
first — rank by `stats.json` `axis_tally`). Make the learner predict the axis before each reveal.

## Step 3 — Persist
Run the Miss-review procedure step 4: write ALL of `/ccaf:result`'s cheatsheet fields back into each miss's
`cheatsheet.json` entry **in the learner's `learning_language`** (read-modify-write, preserve non-text
fields, valid JSON). That is the five per-question fields (`decision`/`rule`/`signal`/`answer`/`flip`, which
render as the per-question cards in the app's **Weaknesses** tab) PLUS `task` and `note` (which render as the
per-topic card there — a topic card has no body without them, so author both). No English fallback.

## Hand-off
Tell the user to run `/ccaf:dashboard` and open the **Weaknesses** tab (per-topic study notes, each with a
collapsible list of the exact failed questions), or a `/ccaf:dN-teacher` for a weak domain. Never
auto-invoke; instruct the user.
