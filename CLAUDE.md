# ccaf plugin — Maintainer / Extension Guide

This repo IS the `ccaf` Claude Code plugin (CCAF exam tutor + mock-exam generator). This file is maintainer
context — read it before changing anything. End users never see it (plugin installs load
skills/commands/hooks, not this CLAUDE.md).

**Role split:** how to *use* the installed plugin lives in `README.md` (end-user facing). This file covers
only how to *change* it — architecture, invariants, schema, and the extend/test workflow. Keep it that way:
don't add usage/marketing here, don't add schema/invariants to the README.

## Maintaining this file
Keep CLAUDE.md **thin** — it loads every session, so it is standing context cost. Keep only facts needed on
(nearly) every change that **can't be discovered from the repo**: invariants, the schema essentials, God
Rules, and pointers. Everything on-demand — app feature detail, long workflows, reference material — lives
in a sibling file (`maintenance/*.md`, `data/*.md`) reached by a **plain path pointer, NOT `@import`**
(`@import` inlines the file and saves no context). Never duplicate what another file already documents —
reference it. When adding, add only the specific missing fact. **Propose changes to this file and wait for
confirmation before editing** (see God Rule #8).

## God Rules (never skip, no exceptions)

1. **Think deeply before proposing.** Before suggesting any change, analyze the affected skill/command/bank/app/progress-store for gaps, trade-offs, learner-facing impact, and regressions — e.g. does a bank edit break `stats.json` id references? does an app change break the two `/*__BANK__*/`/`/*__HISTORY__*/` placeholders or the graceful-degrade paths? does a lesson edit still match the Exam Guide? Surface anything non-obvious.
2. **Fix the cause, not the symptom.** (This is literally axis 5 — the plugin teaches it; hold yourself to it.) If only a workaround is available, say so explicitly, name the root cause it leaves unresolved, propose the proper fix, and ask which to do — never silently ship a workaround or a symptom patch (e.g. a silent fallback that hides bad data).
3. **Follow existing patterns, never invent.** Before adding anything, read a sibling first and match it exactly: a command → `commands/{init,result}.md`; a skill → an existing `SKILL.md` frontmatter (`disable-model-invocation: true`, `allowed-tools`, `argument-hint`); a question → a `questions.json` entry (schema below); a stored audit → `maintenance/*.workflow.js`. Place logic where the **architecture** dictates, not where convenient: runtime data → `data/`; maintainer-only → `maintenance/`; per-user state → `~/.claude/ccaf-progress/`. If no precedent exists, ask.
4. **Ask, don't guess.** If a requirement is ambiguous, ask a clarifying question before implementing. Never assume intent.
5. **Explain before acting.** Before non-trivial changes, briefly say what you'll do and why, then confirm. (Small, obviously-correct edits with clear instruction may proceed — state them in the result.)
6. **Push back when something seems wrong.** Don't blindly follow instructions. If a change would break an invariant, corrupt user history, or contradict the Exam Guide, stop and say so before proceeding.
7. **Never push or publish without asking.** Always ask before `git push`, `/plugin marketplace` publish, or anything that distributes the plugin externally.
8. **Maintain the invariants/schema proactively.** This repo has no `.claude/rules/` — its rules ARE this `CLAUDE.md` (Invariants, the `questions.json` schema, these God Rules) plus `maintenance/sources.md`. If a fix or decision reveals one is missing/outdated/wrong, flag it explicitly: name the section, show the exact replacement text, and ask before editing. Rule drift causes repeated bugs — treat it as first-class work.
9. **Design for extension, not just the current case.** When behavior branches on a finite set (domain 1–5, axis 1–5, exam mode weak/unseen/random/review, mock vs external, status not_started/in_progress/complete), keep the branch in ONE place — a constants map, an enum-like table, the domain→source map — so new cases opt in without hunting call sites. Heavier abstraction (new file, new mechanism) needs an explicit trade-off discussion first.
10. **Evidence before hypothesis.** When debugging the bank/app/build/validator, gather the actual measurement first — run `python3 data/validate.py`, the build harness, `node --check` on the extracted app script, or read a workflow's `journal.jsonl` — before diagnosing. If a fix doesn't produce the expected output, **revert it** before the next hypothesis; never stack guesses.
11. **NEVER destroy user state or bank integrity without explicit approval.** The per-user store `~/.claude/ccaf-progress/` holds real learner state (stats, fails, learning-progress) — never wipe or overwrite it; bootstrap only via `cp -rn` (never overwrite), and a malformed progress file is backed up to `.bak` and surfaced, never skeleton-recreated. **Never renumber or reorder existing `questions.json` ids** — `stats.json` references them; changing ids corrupts every user's history (append-only, always). "Verifying it works" is not a reason to touch real state — use a throwaway `HOME`/store (as the build/coverage harnesses do).

## What this is
A self-contained plugin teammates install and drive with slash commands. It teaches the 5 CCAF domains,
drills exam traps via a 5-axis framework, and generates configurable offline HTML mock exams. All learner
progress is per-user and lives OUTSIDE the plugin.

## Layout
```
.claude-plugin/{plugin.json, marketplace.json}   # manifest + single-plugin marketplace
commands/{init.md, result.md}                     # /ccaf:init (hub), /ccaf:result (single result recorder)
skills/{d1..d5-teacher, exam, stats}/SKILL.md     # tutors + study-app (exam) + dashboard (stats)
data/
  questions.json        # CANONICAL question bank (the thing you'll extend most)
  validate.py           # read-only bank validator (run after every edit: python3 data/validate.py)
  app-template.html     # the self-contained study app (dashboard+select+exam+results); 2 inject points
  app-build.md          # SHARED build recipe both /ccaf:exam and /ccaf:stats follow (injects bank+history)
  teaching-method.md    # HOW the d1..d5 tutors teach (shared Concept→Axis→Apply→Check pedagogy)
  tutor-prompts.md      # per-domain lesson script (task statements) — the WHAT the tutors teach
  exam-traps.md         # verbatim "Exam Trap" + core rule per lesson, 5 domains
  axes.md               # the 5-axis distractor framework (+ cross-domain signatures)
  progress-template/    # copied to ~/.claude/ccaf-progress/ on a user's first run
maintenance/            # MAINTAINER-ONLY reference (not shipped runtime; no skill reads it; read on demand)
  RUNBOOK.md            # periodic content-review procedure (every 6–12 months)
  sources.md            # authoritative-source list + "Last verified" stamp + official blueprint/task statements + exam-vs-product divergences
  bank-coverage-audit.workflow.js  # stored audit: bank ↔ task-statement coverage + sample questions
  fact-currency-audit.workflow.js  # stored audit: bank/lesson facts (flags/paths/numbers) vs current docs
  app-internals.md      # feature-by-feature reference for data/app-template.html (read before editing the app)
  authoring-questions.md # detailed bank-authoring rules + the full extend-the-bank workflow
README.md               # end-user facing (install + usage)
CHANGELOG.md            # version history + content-review log
```

## Invariants — do not break these
1. **Manual-only:** every skill/command sets `disable-model-invocation: true` (blocks auto-invocation AND removes it from ambient context). Never remove this; never set `user-invocable: false`.
2. **No skill→skill calls:** Claude Code can't invoke one skill from another. `/ccaf:init` routes by *instructing* the user which command to type. Keep hand-offs as instructions.
3. **Focus is data-driven, never hardcoded:** teachers/exam read the user's `~/.claude/ccaf-progress/{profile.md,stats.json}` and bias toward THEIR weak domains. Do not bake any person's results (percentages, "focus domain") into skills.
4. **Progress lives at `~/.claude/ccaf-progress/`**, never in the plugin dir (plugin dirs are wiped on update). Skills bootstrap it from `data/progress-template/` with `cp -rn` (never overwrite).
5. **`/ccaf:result` is the single recorder** (mock JSON — one sitting or a batch array — or external screenshot). `/ccaf:exam` and `/ccaf:stats` both **build & open the same app** (`ccaf-exam.html`) via the shared `data/app-build.md` recipe and never write to the store; the app hands results back only via copy-JSON. The app itself does question selection + scoring client-side.
6. **Path refs:** bundled files via `${CLAUDE_PLUGIN_ROOT}/data/...`; progress via `$HOME/.claude/ccaf-progress/...`.
7. **One app file, no archive:** `/ccaf:exam` & `/ccaf:stats` overwrite a single `$HOME/.claude/ccaf-progress/ccaf-exam.html`. No per-exam files. `stats.json` is the authoritative history; the app reconciles unrecorded local sittings against `recorded_exam_ids` so nothing is double-counted. To change the app UI/logic, edit `data/app-template.html` (keep the `/*__BANK__*/[]` and `/*__HISTORY__*/{}` placeholders valid as empty literals); to change what data it gets, edit `data/app-build.md`.

## App UI internals
The offline study app (`data/app-template.html`) has many client-side features (results review, 5-axis
tally, score-trend sparkline, weak-mode spaced repetition, one-question-per-screen exam, mark-for-review
gate, timed mode, learning-progress card + malformed handling, …). The feature-by-feature reference lives
in **`maintenance/app-internals.md`** — read it before editing the app. Hard constraint: keep the
`/*__BANK__*/[]` and `/*__HISTORY__*/{}` placeholders valid as empty literals; change the injected data via
`data/app-build.md`.

## questions.json — schema & rules
```json
{ "meta": { "total": 240, "per_domain": {"1":64,"2":47,"3":42,"4":41,"5":46} },
  "questions": [
    { "id": 1, "domain": 3, "stem": "…", "options": {"A":"…","B":"…","C":"…","D":"…"},
      "correct": "A", "axis": 1, "explanation": "…" }
  ] }
```
- **`id`** = sequential integer by array order. **APPEND new questions at the end with the next id. NEVER renumber or reorder existing entries** — `~/.claude/ccaf-progress/stats.json` references ids (`answered`), so changing them corrupts every user's history.
- **`domain`** = integer 1–5. **`correct`** = single letter A–D. **`explanation`** verbatim (or "").
- **`axis`** = integer **1–5** — the ONE axis (`data/axes.md`) the strongest near-miss distractor trips on: **1** Determinism · **2** Exact-hit · **3** Right-diagnosis · **4** Proportionality · **5** Root-cause. Every question carries exactly one; it powers the dashboard 5-axis tally + the results-review badge and is read directly by `/ccaf:result`.
- Current count: **240** (D1:64 D2:47 D3:42 D4:41 D5:46).
- **Detailed authoring rules** (answer-letter balance · real near-miss / length-tell · imported-vs-authored scope · axis detail · batch provenance) **and the full "extend the bank" workflow** (extract → classify → dedupe → assign ids+axis → `validate.py` → version bump) live in **`maintenance/authoring-questions.md`** — read it before adding/editing questions.

## Extending lessons / traps
`data/tutor-prompts.md` (lesson scripts) and `data/exam-traps.md` (verbatim traps + core rules) are organised by `## Domain N`. Add/refine within the right domain section; the skills read their domain's section by `${CLAUDE_PLUGIN_ROOT}/data/...`. The 5 axes live in `data/axes.md`. **`data/teaching-method.md` is the shared *pedagogy* (HOW every `/ccaf:dN-teacher` teaches — the Concept→Axis→Apply→Check loop); edit it to change teaching style for all domains at once, not per-domain content.**

## Test locally before publishing
```
/plugin marketplace add /Users/dmitryantonenko/exam/ccaf-plugin
/plugin install ccaf@ccaf-marketplace
/ccaf:init            # then /ccaf:exam (pick mode/length on the page) → copy JSON → /ccaf:result → /ccaf:stats
```
Reinstall after edits: `/plugin marketplace update ccaf-marketplace`.

## Staying current (content freshness)
Keeping bundled content aligned with the official exam is a **maintainer task, every 6–12 months** — NOT
a shipped command. Full procedure → **`maintenance/RUNBOOK.md`**; authoritative source list + "Last
verified" stamp + official blueprint/task statements + exam-vs-product divergences → **`maintenance/sources.md`**;
stored audits → `maintenance/{bank-coverage,fact-currency}-audit.workflow.js`; each review logged in
**`CHANGELOG.md`**. Current baseline: **Exam Guide v1.0 (July 2026)**; weights 27/18/20/20/15 and the 30
task statements (D1:7 D2:5 D3:6 D4:6 D5:6) **match**. Known gap: multiple-response items untrained.

## Provenance
Bank built from `../source/{exam-1.html, exam-2.html, test-exam.pdf}` (study workspace). Lesson/trap
material bundled from `../reference/{tutor-prompts.md, exam-traps.md}` (originals also live there).
