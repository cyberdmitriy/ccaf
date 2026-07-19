---
name: init
description: Set up the CCAF exam tutor — creates your progress store, shows your bank/stats, and routes you to the right study activity.
disable-model-invocation: true
allowed-tools: Bash, Read, Write
argument-hint: "(no arguments needed)"
---

# CCAF — Onboarding & Router

You are onboarding the user to the CCAF (Claude Certified Architect – Foundations) study plugin. Be warm, brief, and concrete. This command is the **guided hub**: Claude Code has no skill→skill call, so you do NOT auto-invoke other skills — you set things up, then tell the user the exact `/ccaf:...` command to run next.

## Step 1 — Create the per-user progress store (idempotent)
Run bash: `mkdir -p "$HOME/.claude/ccaf-progress" && cp -rn "${CLAUDE_PLUGIN_ROOT}/data/progress-template/." "$HOME/.claude/ccaf-progress/"`
This creates `~/.claude/ccaf-progress/` from the template on first run and never overwrites existing files. Confirm to the user where their progress lives.

## Step 2 — Detect returning vs new user
Read `$HOME/.claude/ccaf-progress/{profile.md, stats.json}`.
- If `stats.json` has history (exam_history non-empty or answered non-empty), greet as a returning user and summarise: overall accuracy, per-domain accuracy, weakest domains, questions answered vs. remaining.
- Otherwise treat as first run.

## Step 3 — Show the question bank at a glance
Read `${CLAUDE_PLUGIN_ROOT}/data/questions.json` `meta`. Tell the user: total questions in the bank and the per-domain counts, and (from stats.json `answered`) how many they've already answered / have left.

## Step 3.5 — Show learning progress (from tutor sessions)
Read `$HOME/.claude/ccaf-progress/learning-progress.json` (read-only; never write it here). If it
is missing, or every domain is `not_started` with no drills, say plainly that no tutor sessions are
recorded yet and point them at `/ccaf:d1-teacher`…`/ccaf:d5-teacher` — do NOT invent progress. If the
file **exists but won't parse** (malformed), say so plainly (do NOT report zero progress and do NOT
overwrite it) — suggest `python3 ${CLAUDE_PLUGIN_ROOT}/data/validate.py --learning $HOME/.claude/ccaf-progress/learning-progress.json`
to see what's wrong.

Otherwise print one line per domain that has any activity, e.g.:
`D4: task statements 2/6 · last drill 6/8 · last visited 2026-07-18 · in progress`
(omit the drill part if `drills` is empty; show `task statements 0/6` when `task_total` is known but
none covered). Then print one `axis_mastery` line summarising recognition across all domains, e.g.:
`Axis recognition — 1:3/4 · 2:2/2 · 4:3/5` (show only axes with `seen > 0`; say "none yet" if all
zero). This is separate from `stats.json`'s misses-based axis tally — it's where the tutors saw you
get traps *right*.

## Step 4 — Prior result? (first run, or on request)
Ask **only** this: "Do you already have a past exam result (official or practice) you want on record?" If yes, do NOT write it yourself — `/ccaf:result` is the single recorder. Tell the user to run `/ccaf:result` and paste the screenshot/score; it will populate `stats.json`, `profile.md` and the ranked weak-domain list consistently. (You may note in `profile.md` any weak *topics* they mention in prose, but leave scores and focus ranking to `/ccaf:result`.)

Do NOT ask for a name, target date, session goal, or any other profile field — the plugin doesn't use them. Personalisation comes entirely from recorded results (focus domains) and answered-question stats.

## Step 5 — Route (present the menu, then hand off)
Present the menu and, based on their choice + the weak domains recorded in `profile.md`/`stats.json`, tell them the **exact command to run** (do not invoke it yourself). Focus is data-driven: never assume a fixed focus domain — read it from the user's files, and if there's no result yet, say so and recommend recording one or taking a diagnostic mock first.
- **(a) Record a prior result first** — if they have an official/practice score, recommend `/ccaf:result` so the rest of the plugin can bias toward *their* weak domains.
- **(b) Guided full curriculum** — domain by domain. Start `/ccaf:d1-teacher`, then d2…d5. If their files already flag weak domains, suggest starting there instead.
- **(c) Targeted drill** — one domain. Recommend their weakest *from the data* (`/ccaf:dN-teacher`); if no data yet, let them pick.
- **(d) Mock exam** — a generated, configurable exam biased to weak areas. Command: `/ccaf:exam`.
- **(e) Progress dashboard** — visual breakdown once they have history. Command: `/ccaf:stats`.

End by restating the single command you recommend they type next, and remind them their progress is tracked automatically in `~/.claude/ccaf-progress/`.

## Notes
- Never fabricate stats — read them from the files. If a file is missing/empty, say so plainly.
- Keep the whole onboarding tight; don't lecture. The teaching happens in the domain skills.
