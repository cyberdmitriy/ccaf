---
name: result
description: Record any CCAF exam result — a /ccaf:dashboard results JSON, or an external attempt (official or other practice) from a screenshot/pasted text. Updates your progress and re-ranks your focus domains.
disable-model-invocation: true
allowed-tools: Bash, Read, Write
argument-hint: "(then paste the exam results JSON, or a screenshot / the score + per-domain breakdown)"
---

# CCAF — Record an Exam Result (single recorder for mock + external)

The user is giving you an exam result to record. It comes in one of two forms — **auto-detect which**:
- **MOCK** — a JSON produced by the `/ccaf:dashboard` study-app page (has `"type":"mock"` and an `answers` array of `{id, chosen, correct, is_correct}`). It may be a **single object OR a JSON array** of such objects — the page exports an array when several sittings are still unrecorded. Record **each** object in the array (in order), applying Step 3A to every one.
- **EXTERNAL** — a screenshot or pasted text of another exam (official attempt or other practice), typically an overall score + a per-domain % breakdown, with no per-question data.

Manual only; do NOT auto-invoke other skills.

## Step 1 — Ensure the store exists
`mkdir -p "$HOME/.claude/ccaf-progress" && cp -rn "${CLAUDE_PLUGIN_ROOT}/data/progress-template/." "$HOME/.claude/ccaf-progress/"`
Then read `$HOME/.claude/ccaf-progress/{stats.json,profile.md,trap-log.md,settings.json}` (the last gives `learning_language` for authoring cheatsheet prose — default `"English"` if absent). For the MOCK path you'll also read `${CLAUDE_PLUGIN_ROOT}/data/questions.json` to resolve question ids to full text.

## Step 2 — Detect the input type & echo what you parsed
Decide MOCK vs EXTERNAL from the input. Echo back the key figures (overall score, per-domain result) and confirm with the user before writing anything. Never invent numbers — if a figure isn't present, leave it null.

## Step 3A — MOCK results JSON
Parse the JSON (trust only what's pasted). **If the input is an array, loop over its objects and apply the steps below to each**, in order (each has its own `exam_id`, so they become distinct `exam_history` entries and none is double-counted). Then update:
1. **stats.json**
   - For each answer: `answered["<id>"]` → append to `.attempts` `{exam_id, correct:is_correct, ts}` and set `.last_correct = is_correct`.
   - Recompute `stats.json` `per_domain[d].seen/correct` from `answered` (count each question's latest attempt).
   - Push `exam_history` entry: `{exam_id, ts, type:"mock", mode, count, score, per_domain, time_spent_seconds, limit_seconds, over_time}`. Use the `per_domain` block from the results JSON if present; if an older JSON lacks it, derive it from the `answers` array (`domain` + `is_correct`). Copy `over_time` (and `limit_seconds`) straight from the JSON when present — a timed sitting the learner didn't finish in the allotted 2-min-per-question budget is `over_time:true`; the dashboard shows an "⏳ over time" marker but the score is unaffected. Older JSONs without these fields → treat as `over_time:false` / omit `limit_seconds`.
   - **Recompute `axis_tally` from `answered`** (do NOT cumulatively bump): for each question whose **latest** attempt is wrong, add 1 to its `axis`, with the axis **looked up directly** from `questions.json` (see step below) — no guessing. Recomputing on the latest-attempt basis keeps `axis_tally` consistent with the `per_domain` recompute above and with the dashboard's client-side 5-axis chart (which counts latest-attempt misses), so the number `/ccaf:dashboard` prints matches the chart.
2. **fails-tracker.md** — for each `is_correct:false`, look up the question by `id` in `questions.json` and append it VERBATIM (stem, options, the user's `chosen` vs `correct`, explanation).
3. **trap-log.md** — for each miss add a row (domain · axis · trigger phrase · correct principle). **Look up the axis directly:** read the missed question's `axis` field (1–5) from `${CLAUDE_PLUGIN_ROOT}/data/questions.json` — every question carries one — and use `${CLAUDE_PLUGIN_ROOT}/data/axes.md` only for the axis's name/description in the row. Bump that axis's tally. (Only if an unusually old question somehow lacks `axis` should you fall back to inferring it from `axes.md`.)
4. **cheatsheet.json** — the app's miss-driven cheatsheet, one card per missed question (`$HOME/.claude/ccaf-progress/cheatsheet.json`, shape `{"schema":1,"entries":{"<qid>":{…}}}`). Read it first; if absent or unparseable, start from `{"schema":1,"entries":{}}` (never wipe a readable file). For **each answer** in this sitting:
   - **`is_correct:false`** → upsert `entries["<id>"]`. Look up the question by `id` in `${CLAUDE_PLUGIN_ROOT}/data/questions.json` for `domain`, `axis`, `options`, `explanation`.
     - New entry: `{qid:<id>, domain, axis, task, note, decision, rule, signal, answer, flip, correct:<correct letter>, your_pick:<chosen letter>, status:"active", miss_count:1, first_ts:<ts>, last_ts:<ts>}`.
     - Existing entry: `miss_count += 1`; set `your_pick:<chosen>`, `correct`, `status:"active"`, `last_ts:<ts>`; keep `task`/`note`/`decision`/`rule`/`signal`/`answer`/`flip` unless they're missing/empty (then generate). **Always re-derive the `note`'s `[you] ` marker from the new `your_pick`** (the trap they fell for this time may differ).
     - **Authoring principle (this is the whole point):** a card must teach the learner to answer **similar but DIFFERENT** questions — never "pick X here". The SAME option (e.g. few-shot, a schema) is *correct* in one scenario and *wrong* in another; so every field teaches the **discriminating property** (what feature of the scenario decides the answer) and the **flip condition** (when the tempting option becomes right), not this scenario's specifics. If the learner finishes able to say "I choose by <property>; I'd choose differently if <condition>", the card works. Formatting you may use (the app renders all of these): `**bold**` (mechanism names + the flip condition), `*italic*` (light emphasis, e.g. *varies* / *same*), `` `code` `` (API tokens: `tool_use`, `stop_reason`, `null`), and "double quotes" for verbatim stem fragments.
     - **Language:** author `decision`/`rule`/`answer`/`flip` as **prose in the learner's `learning_language`** (read `$HOME/.claude/ccaf-progress/settings.json`, default `"English"`). Keep in English always (the exam is English): the `signal` field's verbatim quoted stem fragments, option letters, and API tokens/mechanism names (`tool_use`, `stop_reason`, `ENABLE_TOOL_SEARCH`, few-shot, schema, hook, …). No English fallback — if `learning_language` is Russian, the card is Russian. See `${CLAUDE_PLUGIN_ROOT}/data/teaching-method.md` Rule 0c.
     - Author these five fields (examples below are English; write them in `learning_language`):
       - `decision` = the **headline**, the question-behind-the-question as a plain either/or, ≤~10 words, ends in `?`. **No scenario nouns, no keyword-salad.** e.g. `Needs a guarantee, or just usually-works?` / `Fixed pattern, or varies case by case?`
       - `rule` = ONE sentence: the **deciding property → mechanism-type** to pick. Must read true for *other* scenarios — refer to mechanism types, never option letters or this stem's nouns. (Test: if it names a noun from this stem, rewrite it.)
       - `signal` = **1–3 verbatim fragments** quoted from the stem + what property each proves. ≤2 sentences. (Trains spotting wording on the next exam.)
       - `answer` = the correct **mechanism** + one clause on *why it satisfies the deciding property*. Do NOT re-quote the full option text (it's shown in the disclosure). **Also preempt the obvious objection to this answer** (see rule below) when there is one. ≤3 sentences.
       - `flip` = name the mechanism the learner picked (by mechanism, no shaming — it's a good instinct, correct **elsewhere** on this exam), why it fails the property **here**, then **"It would be the right call if `<concrete condition>`"** — a real property change, never "if it were correct". 2–3 sentences.
     - **Preempt the obvious objection to the CORRECT answer.** A learner often rejects the right answer because a rule from a *different* axis fires (e.g. "self-critique / a prompt technique is just probabilistic → surely wrong", or "few-shot can't guarantee"). If the correct mechanism has such a plausible objection, disarm it in `answer`: (a) name the property that makes it valid *here* — e.g. a self-critique is legitimate because it's **calibrated against explicit criteria**, not a vague "double-check"; and (b) name the signal under which the objection WOULD disqualify it — e.g. "probabilistic is fine here; if the stem demanded a *guarantee*, you'd need a schema instead." This stops cross-axis confusion (the exact failure that makes a learner distrust a correct answer).
     - **Anchor `rule`/`signal`/`flip` to the question's `axis` (one lens each):** 1 Determinism = *guarantee vs influence* → mechanism lives **outside** the model (schema/hook), signals `guarantee/always/never/not merely usually`; 2 Exact-hit = *similar vs the exact target* (`any` vs the named tool, Grep vs Glob); 3 Right-diagnosis = *does it fix the gap the stem states?*; 4 Proportionality = *effort vs stakes* (over/under-engineered); 5 Root-cause = *cause vs symptom* (correct fix removes the cause; distractor cleans up after it).
     - **Also author `task` and `note` — these feed the app's separate "Failed Topics" tab, and the tab is EMPTY without them, so they are required, not optional.** The five fields above feed "Failed Questions" (per-question). `task` + `note` feed "Failed Topics" (a generalized study note per topic).
       - `task` = the official domain task-statement this topic sits under, as `"<d>.<n> <short English label>"`, e.g. `"5.2 escalation & handoff"`, `"2.3 tool distribution & \`tool_choice\`"`. The domain's task statements are listed in `${CLAUDE_PLUGIN_ROOT}/data/tutor-prompts.md` (that domain's section) — pick the one this question tests. Shown in the card header as `Domain <d> · <task>`.
       - `note` = a **markdown study note on the TOPIC**, in the learner's `learning_language`, in the tutor's teaching voice. It teaches the concept so the learner answers ANY similar question. **NEVER mention the question stem, the option letters, or "ты выбрал / you chose".** Generalize to the concept. Exact markdown shape (the app's `mdBlock` renders it):
         ```
         ## <short concept title>
         <1–2 sentences: what the concept is, plus the one critical insight that decides these questions.>

         **Как правильно.** <the mechanism that wins and WHY it satisfies the deciding property — 1–2 sentences.>

         - <ловушка/антипаттерн 1 — with the "почему" it fails>
         - [you] <the antipattern the learner actually fell for — prefix this ONE bullet with `[you] `>
         - <ловушка 3 …>

         <Где ловят на экзамене: the English signal wording to watch for, then → ось N.>
         ```
         Rules: (a) the `## <title>` heading comes FIRST and is the **topic key** the app dedupes on — two questions on the same topic MUST get the SAME heading (and same `task`) so the tab shows ONE card; keep a topic's heading stable across sittings. (b) Prose in `learning_language`; exam tokens, mechanism names and quoted signal phrases stay English (`tool_choice`, `stop_reason`, `submit_ticket`, few-shot, hook, schema). (c) In the Ловушки bullets, prefix the ONE that matches `your_pick` with `[you] ` (the app badges it "your pick"). If `your_pick` is unknown/absent, mark none. (d) `## `, `- `, `[you] `, `**bold**`, `*italic*`, `` `code` `` and "double quotes" are the only markup `mdBlock` supports — no other markdown.
   - **`is_correct:true`** AND `entries["<id>"]` already exists → set `status:"mastered"`, `last_ts:<ts>` (keep the text). Do **not** create entries for correct answers that were never missed.
   - **Backfill sweep (self-heal from accumulated history):** after the per-answer pass, for **every** `id` in `stats.json` `answered` whose latest attempt is wrong (`last_correct:false`) that has **no** `entries["<id>"]` yet, generate one the same way — look up the question in `questions.json`, author all seven fields (`task`, `note`, `decision`, `rule`, `signal`, `answer`, `flip`), set `status:"active"`, `miss_count:1`, `first_ts`/`last_ts` = that miss's latest-attempt ts. Recover `your_pick` from `fails-tracker.md` if the id is logged there (and mark that trap `[you] ` in the `note`); otherwise omit `your_pick` and mark no `[you] ` bullet (the app renders "—"). This retro-fills misses recorded **before** the cheatsheet existed, so both tabs are never empty for a learner who already has history.
   - **Self-heal missing `note`/`task`:** also sweep entries that already exist but LACK `note` or `task` (e.g. written before this tab existed) and author those two fields for them. Without this, "Failed Topics" stays empty for their old entries.
   Write the file back (pretty JSON). This mirrors the per-user, additive discipline of the other store files — external results (Step 3B) do NOT touch it (no per-question data).

## Step 3B — EXTERNAL result (screenshot / text)
Extract overall score and per-domain % (map the exam's domain names to 1–5: 1 Agentic Architecture & Orchestration · 2 Tool Design & MCP · 3 Claude Code Config & Workflows · 4 Prompt Engineering & Structured Output · 5 Context Management & Reliability). Then update:
1. **stats.json** — push `exam_history` entry: `{exam_id:"external-<date>", ts, type:"external", label:"<official|practice|source>", score:{correct,total}, per_domain_pct:{"1":81,...}}`. Make `exam_id` unique — if an `external-<date>` id already exists in `exam_history`, append a disambiguator (`external-<date>-2`, `-3`, …) so same-day results don't collide. Do NOT touch `answered` (there's no per-question data).
2. **profile.md** — add a dated line under "Prior results" with the score + breakdown.

## Step 4 — Re-rank focus (both paths) & report
Rewrite **both** ranked lists in `profile.md`, weakest domain first. Weight a real EXTERNAL/official result as the strongest signal; corroborate with MOCK per-domain accuracy. This is a *ranking*, never a blended average — each result stays its own entry in `exam_history`.
1. **`## Self-reported weak domains`** — the full ranked list, weakest first (e.g. `- D4 — Prompt Engineering (57%)`).
2. **`## Focus domains`** — the **top 1–2 weakest** from that ranking, one per line, weakest first (e.g. `- D4` then `- D3`). **This section is required and load-bearing:** the study app (`/ccaf:dashboard`) parses ONLY `## Focus domains` for `focus_domains`, and an EXTERNAL-only result leaves no per-question data for the app to derive focus from — so if you don't write this section, weak-mode gets no focus. **Edit the existing heading in place** — the template already ships a `## Focus domains` section (initially `_(unset)_`); replace its body, do NOT append a second `## Focus domains` (the parser reads the FIRST one, so a duplicate leaves the stale one winning). Write plain `D<n>` tokens (the parser reads `D1`–`D5` in written order); never leave it as `_(unset)_` once a result exists.
- Report: the result, current weakest domains, and the single next command you recommend (`/ccaf:dN-teacher` for the weakest, or `/ccaf:dashboard`). Do not auto-invoke it.

## Notes
- Keep both result types as distinct, timestamped `exam_history` entries — mock (per-question) and external (per-domain %) are never merged into one number; `/ccaf:dashboard` shows them separately.
- Write valid JSON (no trailing commas). Only record what the input actually contains.
