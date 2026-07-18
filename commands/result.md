---
name: result
description: Record any CCAF exam result — a /ccaf:exam results JSON, or an external attempt (official or other practice) from a screenshot/pasted text. Updates your progress and re-ranks your focus domains.
disable-model-invocation: true
allowed-tools: Bash, Read, Write
argument-hint: "(then paste the exam results JSON, or a screenshot / the score + per-domain breakdown)"
---

# CCAF — Record an Exam Result (single recorder for mock + external)

The user is giving you an exam result to record. It comes in one of two forms — **auto-detect which**:
- **MOCK** — a JSON produced by the `/ccaf:exam` study-app page (has `"type":"mock"` and an `answers` array of `{id, chosen, correct, is_correct}`). It may be a **single object OR a JSON array** of such objects — the page exports an array when several sittings are still unrecorded. Record **each** object in the array (in order), applying Step 3A to every one.
- **EXTERNAL** — a screenshot or pasted text of another exam (official attempt or other practice), typically an overall score + a per-domain % breakdown, with no per-question data.

Manual only; do NOT auto-invoke other skills.

## Step 1 — Ensure the store exists
`mkdir -p "$HOME/.claude/ccaf-progress" && cp -rn "${CLAUDE_PLUGIN_ROOT}/data/progress-template/." "$HOME/.claude/ccaf-progress/"`
Then read `$HOME/.claude/ccaf-progress/{stats.json,profile.md,trap-log.md}`. For the MOCK path you'll also read `${CLAUDE_PLUGIN_ROOT}/data/questions.json` to resolve question ids to full text.

## Step 2 — Detect the input type & echo what you parsed
Decide MOCK vs EXTERNAL from the input. Echo back the key figures (overall score, per-domain result) and confirm with the user before writing anything. Never invent numbers — if a figure isn't present, leave it null.

## Step 3A — MOCK results JSON
Parse the JSON (trust only what's pasted). **If the input is an array, loop over its objects and apply the steps below to each**, in order (each has its own `exam_id`, so they become distinct `exam_history` entries and none is double-counted). Then update:
1. **stats.json**
   - For each answer: `answered["<id>"]` → append to `.attempts` `{exam_id, correct:is_correct, ts}` and set `.last_correct = is_correct`.
   - Recompute `stats.json` `per_domain[d].seen/correct` from `answered` (count each question's latest attempt).
   - Push `exam_history` entry: `{exam_id, ts, type:"mock", mode, count, score, per_domain, time_spent_seconds, limit_seconds, over_time}`. Use the `per_domain` block from the results JSON if present; if an older JSON lacks it, derive it from the `answers` array (`domain` + `is_correct`). Copy `over_time` (and `limit_seconds`) straight from the JSON when present — a timed sitting the learner didn't finish in the allotted 2-min-per-question budget is `over_time:true`; the dashboard shows an "⏳ over time" marker but the score is unaffected. Older JSONs without these fields → treat as `over_time:false` / omit `limit_seconds`.
   - **Recompute `axis_tally` from `answered`** (do NOT cumulatively bump): for each question whose **latest** attempt is wrong, add 1 to its `axis`, with the axis **looked up directly** from `questions.json` (see step below) — no guessing. Recomputing on the latest-attempt basis keeps `axis_tally` consistent with the `per_domain` recompute above and with the dashboard's client-side 5-axis chart (which counts latest-attempt misses), so the number `/ccaf:stats` prints matches the chart.
2. **fails-tracker.md** — for each `is_correct:false`, look up the question by `id` in `questions.json` and append it VERBATIM (stem, options, the user's `chosen` vs `correct`, explanation).
3. **trap-log.md** — for each miss add a row (domain · axis · trigger phrase · correct principle). **Look up the axis directly:** read the missed question's `axis` field (1–5) from `${CLAUDE_PLUGIN_ROOT}/data/questions.json` — every question carries one — and use `${CLAUDE_PLUGIN_ROOT}/data/axes.md` only for the axis's name/description in the row. Bump that axis's tally. (Only if an unusually old question somehow lacks `axis` should you fall back to inferring it from `axes.md`.)

## Step 3B — EXTERNAL result (screenshot / text)
Extract overall score and per-domain % (map the exam's domain names to 1–5: 1 Agentic Architecture & Orchestration · 2 Tool Design & MCP · 3 Claude Code Config & Workflows · 4 Prompt Engineering & Structured Output · 5 Context Management & Reliability). Then update:
1. **stats.json** — push `exam_history` entry: `{exam_id:"external-<date>", ts, type:"external", label:"<official|practice|source>", score:{correct,total}, per_domain_pct:{"1":81,...}}`. Make `exam_id` unique — if an `external-<date>` id already exists in `exam_history`, append a disambiguator (`external-<date>-2`, `-3`, …) so same-day results don't collide. Do NOT touch `answered` (there's no per-question data).
2. **profile.md** — add a dated line under "Prior results" with the score + breakdown.

## Step 4 — Re-rank focus (both paths) & report
Rewrite **both** ranked lists in `profile.md`, weakest domain first. Weight a real EXTERNAL/official result as the strongest signal; corroborate with MOCK per-domain accuracy. This is a *ranking*, never a blended average — each result stays its own entry in `exam_history`.
1. **`## Self-reported weak domains`** — the full ranked list, weakest first (e.g. `- D4 — Prompt Engineering (57%)`).
2. **`## Focus domains`** — the **top 1–2 weakest** from that ranking, one per line, weakest first (e.g. `- D4` then `- D3`). **This section is required and load-bearing:** the study app (`/ccaf:exam`, `/ccaf:stats`) parses ONLY `## Focus domains` for `focus_domains`, and an EXTERNAL-only result leaves no per-question data for the app to derive focus from — so if you don't write this section, weak-mode gets no focus. **Edit the existing heading in place** — the template already ships a `## Focus domains` section (initially `_(unset)_`); replace its body, do NOT append a second `## Focus domains` (the parser reads the FIRST one, so a duplicate leaves the stale one winning). Write plain `D<n>` tokens (the parser reads `D1`–`D5` in written order); never leave it as `_(unset)_` once a result exists.
- Report: the result, current weakest domains, and the single next command you recommend (`/ccaf:dN-teacher` for the weakest, or `/ccaf:exam`). Do not auto-invoke it.

## Notes
- Keep both result types as distinct, timestamped `exam_history` entries — mock (per-question) and external (per-domain %) are never merged into one number; `/ccaf:stats` shows them separately.
- Write valid JSON (no trailing commas). Only record what the input actually contains.
