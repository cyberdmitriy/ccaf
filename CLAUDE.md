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

1. **Reason before you propose — PRINT the checkpoint, don't just intend it.** A rule you only intend to follow is the failure this replaces: this rule and #2 existed as prose and got skipped anyway. So before ANY non-trivial proposal or edit, emit these four lines in the turn; a blank or hand-wavy line is the visible tell that you skipped the thinking, and I will call it:
   - **Pattern** — the general class this case belongs to. One file/bug/lesson is an *example*, not the unit of work; if the same thing can recur elsewhere, the fix lives at the class level, never one spot at a time (fixing only where it was noticed is wrong even when I point at that spot).
   - **Union or either/or** — before writing "not X, but Y", check: is it both? is it a union? Most "pick one" framings are wrong; combine for completeness unless one genuinely excludes the other.
   - **Grounded in** — the exact file + line you READ to back each claim about the schema/app/bank/design; assert nothing from memory, mark anything unread as unverified. Here also weigh the concrete regressions: a bank edit vs `stats.json` id refs, an app edit vs the `/*__BANK__*/`/`/*__HISTORY__*/`/`/*__REFERENCE__*/` placeholders + graceful-degrade paths, a lesson edit vs the Exam Guide.
   - **Root cause** — the actual cause, not the symptom's location (see #2). Prefer an honest "both / it depends / not verified" over a tidy answer that is wrong.
2. **Fix the cause, not the symptom (the checkpoint's Root-cause line is binding).** This is literally axis 5 — the plugin teaches it; hold yourself to it. Never ship a workaround or symptom patch (e.g. a silent fallback that hides bad data, or a fix applied only to the one spot where a general problem surfaced). If only a workaround fits, say so explicitly, name the root cause it leaves unresolved, propose the proper fix, and ask which to do.
3. **Follow existing patterns, never invent.** Before adding anything, read a sibling first and match it exactly: a command → `commands/{init,result}.md`; a skill → an existing `SKILL.md` frontmatter (`disable-model-invocation: true`, `allowed-tools`, `argument-hint`); a question → a `questions.json` entry (schema below); a stored audit → `maintenance/*.workflow.js`. Place logic where the **architecture** dictates, not where convenient: runtime data → `data/`; maintainer-only → `maintenance/`; per-user state → `~/.claude/ccaf-progress/`. If no precedent exists, ask.
4. **Ask, don't guess.** If a requirement is ambiguous, ask a clarifying question before implementing. Never assume intent.
5. **Explain before acting.** Before non-trivial changes, briefly say what you'll do and why, then confirm. (Small, obviously-correct edits with clear instruction may proceed — state them in the result.)
6. **Push back when something seems wrong.** Don't blindly follow instructions. If a change would break an invariant, corrupt user history, or contradict the Exam Guide, stop and say so before proceeding.
7. **Never push or publish without asking.** Always ask before `git push`, `/plugin marketplace` publish, or anything that distributes the plugin externally.
8. **Maintain the invariants/schema proactively.** This repo has no `.claude/rules/` — its rules ARE this `CLAUDE.md` (Invariants, the `questions.json` schema, these God Rules) plus `maintenance/sources.md`. If a fix or decision reveals one is missing/outdated/wrong, flag it explicitly: name the section, show the exact replacement text, and ask before editing. Rule drift causes repeated bugs — treat it as first-class work.
9. **Design for extension, not just the current case.** When behavior branches on a finite set (domain 1–5, axis 1–5, exam mode weak/unseen/random/review/failed, mock vs external, status not_started/in_progress/complete), keep the branch in ONE place — a constants map, an enum-like table, the domain→source map — so new cases opt in without hunting call sites. Heavier abstraction (new file, new mechanism) needs an explicit trade-off discussion first.
10. **Evidence before hypothesis.** When debugging the bank/app/build/validator, gather the actual measurement first — run `python3 data/validate.py`, the build harness, `node --check` on the extracted app script, or read a workflow's `journal.jsonl` — before diagnosing. If a fix doesn't produce the expected output, **revert it** before the next hypothesis; never stack guesses.
11. **NEVER destroy user state or bank integrity without explicit approval.** The per-user store `~/.claude/ccaf-progress/` holds real learner state (stats, fails, learning-progress) — never wipe or overwrite it; bootstrap only via `cp -rn` (never overwrite), and a malformed progress file is backed up to `.bak` and surfaced, never skeleton-recreated. **Never renumber or reorder existing `questions.json` ids** — `stats.json` references them; changing ids corrupts every user's history (append-only, always). "Verifying it works" is not a reason to touch real state — use a throwaway `HOME`/store (as the build/coverage harnesses do).
12. **Never commit or bump the version on your own.** Do NOT `git commit` and do NOT change the plugin version (`plugin.json`/`marketplace.json`/`CHANGELOG.md` release headers) as a side effect of making changes. Edit → verify → **stop and report what changed**. Commit/bump only (a) when the user explicitly asks, or (b) after you propose it and they approve. The version is a release decision the user makes — **one** coherent bump per release the user names, never one per small change. (Rebuilding the user's `ccaf-exam.html` preview is fine — it's a regenerable artifact, not a commit.)
13. **UI/UX: propose options BEFORE you build.** For ANY user-facing UI/UX change (a new view/screen, a layout, a component, restyling, or reworking how something reads), do NOT jump straight to code. First sketch **2–3 concrete approaches** — ASCII mockups or short descriptions, each with its trade-offs — recommend one, and get the user's pick. Only then implement. Optimise for **readability and clarity first**, then a distinctive, considered look: never bland/generic "just a table", never over-engineered either — **usability wins**. Before offering any option, ask yourself the gate question: *would this actually be readable and understandable to the user?* If not, it is not a candidate. (This rule exists because building UI first and iterating on taste later wastes rounds.)

## What this is
A self-contained plugin teammates install and drive with slash commands. It teaches the 5 CCAF domains,
drills exam traps via a 5-axis framework, and generates configurable offline HTML mock exams. All learner
progress is per-user and lives OUTSIDE the plugin.

## Layout
```
.claude-plugin/{plugin.json, marketplace.json}   # manifest + single-plugin marketplace
commands/{init.md, result.md}                     # /ccaf:init (hub), /ccaf:result (single result recorder)
skills/{d1..d5-teacher, dashboard}/SKILL.md       # tutors + the single study-app/dashboard command
hooks/{hooks.json, ccaf-build.sh}                 # UserPromptSubmit hook: deterministic rebuild on /ccaf:{init,dashboard}
data/
  questions.json        # CANONICAL question bank (the thing you'll extend most)
  quick-reference.json  # curated see→answer map (domain→section→row); projection of exam-traps.md; injected via /*__REFERENCE__*/
  task-statements.json  # canonical <d>.<n> → label map (the ONE source of task-statement labels); referenced by questions.json `task`
  validate.py           # read-only validator: bank + quick-reference.json + task-statements.json (run after every edit: python3 data/validate.py)
  app-template.html     # the self-contained study app (dashboard+select+exam+cheatsheet+reference); 3 inject points
  build-app.py          # deterministic builder (bootstrap→build→open); single source of truth, run by the hook + skills
  app-build.md          # SHARED build recipe (thin: runs build-app.py) that /ccaf:dashboard follows
  teaching-method.md    # HOW the d1..d5 tutors teach (Rule 0b plain-language register + Concept→Axis→Apply→Check)
  tutor-prompts.md      # per-domain lesson script (task statements) — the WHAT the tutors teach
  exam-traps.md         # verbatim "Exam Trap" + core rule per lesson, 5 domains
  axes.md               # the 5-axis distractor framework (+ cross-domain signatures)
  progress-template/    # copied to ~/.claude/ccaf-progress/ on a user's first run
maintenance/            # MAINTAINER-ONLY reference (not shipped runtime; no skill reads it; read on demand)
  RUNBOOK.md            # periodic content-review procedure (every 6–12 months)
  sources.md            # authoritative-source list + "Last verified" stamp + official blueprint/task statements + exam-vs-product divergences
  bank-coverage-audit.workflow.js  # stored audit: bank ↔ task-statement coverage + sample questions
  fact-currency-audit.workflow.js  # stored audit: bank/lesson facts (flags/paths/numbers) vs current docs
  reference-coverage.py  # deterministic report: quick-reference.json coverage vs the bank (set arithmetic, no agents)
  app-internals.md      # feature-by-feature reference for data/app-template.html (read before editing the app)
  authoring-questions.md # detailed bank-authoring rules + the full extend-the-bank workflow
README.md               # end-user facing (install + usage)
CHANGELOG.md            # version history + content-review log
```

**Planning artifacts:** superpowers specs/plans go under `.superpowers/` (git-ignored scratch) —
never create a `docs/` tree. If a skill defaults to `docs/superpowers/…`, redirect it to `.superpowers/`.

## Invariants — do not break these
1. **Manual-only:** every skill/command sets `disable-model-invocation: true` (blocks auto-invocation AND removes it from ambient context). Never remove this; never set `user-invocable: false`.
2. **No skill→skill calls:** Claude Code can't invoke one skill from another. `/ccaf:init` routes by *instructing* the user which command to type. Keep hand-offs as instructions.
3. **Focus is data-driven, never hardcoded:** teachers/exam read the user's `~/.claude/ccaf-progress/{profile.md,stats.json}` and bias toward THEIR weak domains. Do not bake any person's results (percentages, "focus domain") into skills.
4. **Progress lives at `~/.claude/ccaf-progress/`**, never in the plugin dir (plugin dirs are wiped on update). Skills bootstrap it from `data/progress-template/` with `cp -rn` (never overwrite).
5. **`/ccaf:result` is the single recorder** (mock JSON — one sitting or a batch array — or external screenshot). `/ccaf:dashboard` and `/ccaf:init` **build & open the same app** (`ccaf-exam.html`); the rebuild is **enforced deterministically by the `UserPromptSubmit` hook** (`hooks/ccaf-build.sh` → `data/build-app.py`), with the skills' `data/app-build.md` recipe (also `build-app.py`) as a fallback if hooks are disabled — never open a stale file, never write to the store; the app hands results back only via copy-JSON. The app itself does question selection + scoring client-side. `/ccaf:result` also upserts a per-user `cheatsheet.json` — the app's miss-driven *trigger→rule* table — on each mock miss (additive, never in the bank; the app reads it read-only). Each entry's authored fields are written **in the learner's `learning_language`** (exam text, the `signal` quotes, and API tokens stay English) by both `/ccaf:result` and `/ccaf:fail-analysis` — no separate localized copy, no English fallback. Two field groups feed the single **Weaknesses** tab: `task` + `note` (a generalized markdown study note per topic) render as the per-topic card; the five per-question fields (`decision`/`rule`/`signal`/`answer`/`flip`) render as the failed-question cards inside that topic's collapsible list. Both groups are required on every miss — a topic card has no body without `note`/`task`.
6. **Path refs:** bundled files via `${CLAUDE_PLUGIN_ROOT}/data/...`; progress via `$HOME/.claude/ccaf-progress/...`.
7. **One app file, no archive:** `/ccaf:dashboard` & `/ccaf:init` (via the hook / `build-app.py`) overwrite a single `$HOME/.claude/ccaf-progress/ccaf-exam.html`. No per-exam files. `stats.json` is the authoritative history; the app reconciles unrecorded local sittings against `recorded_exam_ids` so nothing is double-counted. To change the app UI/logic, edit `data/app-template.html` (keep the `/*__BANK__*/[]`, `/*__HISTORY__*/{}` and `/*__REFERENCE__*/{}` placeholders valid as empty literals); to change what data it gets, edit `data/app-build.md`. The **Reference** tab renders `/*__REFERENCE__*/` (bundled `quick-reference.json`, a see→answer map) — bundled content, a sibling of `BANK`, not per-user `HISTORY`.
8. **Exam content is always English; only prose is localized.** A per-user `learning_language`
(`~/.claude/ccaf-progress/settings.json`, default `"English"`, free-form) drives ONLY model-generated
explanatory prose (tutors, `/ccaf:fail-analysis`, and the `/ccaf:result` `cheatsheet.json` explanation fields `decision`/`rule`/`signal`/`answer`/`flip`).
Question stems/options/answers, verbatim signal phrases, and API tokens stay English always; the mock
exam is English-only. The read rule lives once in `data/teaching-method.md` (Rule 0c). The app chrome is
NOT localized, with ONE carve-out: the handful of **content-labels in the Weaknesses tab** that sit
directly on the localized cheatsheet prose (`Topic`, `Failed questions`, `Breakdown`, `What gave it away`,
`So the answer is`, `Your instinct, and when it is right`, `your pick`, `Answer stats`) ARE localized, so an
English label never sits over Russian text. Mechanism: `build-app.py` injects `learning_language` into `HISTORY`, and the
template's `UI_I18N` table + `t()` helper map only these keys, falling back to English for any language not
in the table (free-form language safe). Adding a language = one `UI_I18N` block; localizing more chrome =
add the key to every block. All other chrome (nav, dashboard, mock exam) stays English.

## App UI internals
The offline study app (`data/app-template.html`) has many client-side features (results review, 5-axis
tally, score-trend sparkline, weak-mode spaced repetition, one-question-per-screen exam, mark-for-review
gate, timed mode, learning-progress card + malformed handling, Weaknesses view, reference view, …). The feature-by-feature reference lives
in **`maintenance/app-internals.md`** — read it before editing the app. Hard constraint: keep the
`/*__BANK__*/[]`, `/*__HISTORY__*/{}` and `/*__REFERENCE__*/{}` placeholders valid as empty literals; change the injected data via
`data/app-build.md`.

## questions.json — schema & rules
```json
{ "meta": { "total": 261, "per_domain": {"1":70,"2":49,"3":53,"4":43,"5":46} },
  "questions": [
    { "id": 1, "domain": 3, "stem": "…", "options": {"A":"…","B":"…","C":"…","D":"…"},
      "correct": "A", "axis": 1, "task": "3.1", "explanation": "…" }
  ] }
```
- **`id`** = sequential integer by array order. **APPEND new questions at the end with the next id. NEVER renumber or reorder existing entries** — `~/.claude/ccaf-progress/stats.json` references ids (`answered`), so changing them corrupts every user's history.
- **`domain`** = integer 1–5. **`correct`** = single letter A–D. **`explanation`** verbatim (or "").
- **`axis`** = integer **1–5** — the ONE axis (`data/axes.md`) the strongest near-miss distractor trips on: **1** Determinism · **2** Exact-hit · **3** Right-diagnosis · **4** Proportionality · **5** Root-cause. Every question carries exactly one; it powers the dashboard 5-axis tally + the results-review badge and is read directly by `/ccaf:result`.
- **`task`** = the canonical task-statement string `"<d>.<n>"` (e.g. `"3.1"`) — a **key in `data/task-statements.json`** whose domain-prefix must equal `domain`. Every question carries exactly one. It is the single source of truth for which sub-topic a question tests, so `/ccaf:result` and the tutors **look it up** instead of guessing (fixes cross-session drift — the same question tagged `1.2` in one sitting and `1.6` in another). The number lives here; the human label lives once in `task-statements.json`.
- Current count: **261** (D1:70 D2:49 D3:53 D4:43 D5:46).
- **Detailed authoring rules** (answer-letter balance · real near-miss / length-tell · imported-vs-authored scope · axis detail · batch provenance) **and the full "extend the bank" workflow** (extract → classify → dedupe → assign ids+axis+task → `validate.py` → version bump) live in **`maintenance/authoring-questions.md`** — read it before adding/editing questions.

## quick-reference.json — the Reference tab's see→answer map
`{ "meta": {"version":1}, "domains": { "1".."5": { "title": "…", "sections": [ { "title": "…", "rows": [ { "see": "…", "answer": "…", "q_ids": [12,45] } ] } ] } } }`
- A **curated projection of `data/exam-traps.md`** (the source of the row content): each `section` **IS a domain task statement**, titled `"<d>.<n> <label>"` to match `data/task-statements.json` + the tutors + the bank `task` (so the Cheatsheet tab lines up with what's taught and tested). **Section titles are plain text** (rendered via `esc()`, so no `code`/markdown — use the plain label, not the backticked map label). Each `row` is a signal phrase (`see`) → short mechanism (`answer`), both rendering `code`/`**bold**` via the app's `rich()`. `validate.py` enforces that every section title starts with a valid `<d>.<n>` of its domain.
- **`q_ids`** = bank question ids the criterion reflects — **hand-picked or `[]`, NEVER keyword-grepped** (a substring match makes the coverage report lie). Used by the coverage report AND by the Cheatsheet tab's exam filter (a row shows under "My misses" / an exam chip only through its `q_ids`), so a row with `[]` is invisible there — fill `q_ids` when you add a row.
- **No `axis` field** (axis lives in `questions.json` — a copy here would be a second source of truth). **No `meta.last_verified`** (that stamp lives once, in `maintenance/sources.md`).
- Validated by `data/validate.py`; coverage vs the bank reported by `python3 maintenance/reference-coverage.py`. When you change a core rule in `exam-traps.md`, update the matching reference row so the projection doesn't drift.

## task-statements.json — the canonical <d>.<n> → label map
`{ "meta": {"version":1}, "statements": { "1.1": "agentic loops", …, "5.6": "information provenance" } }`
- The **single source of truth** for task-statement labels. Every `questions.json` `task` number resolves its human label here; `/ccaf:result` and the tutors read it to render `Domain <d> · <task>`.
- **32 statements**, numbering mirrors the `TASK STATEMENT <d>.<n>` headers in `data/tutor-prompts.md` (D1:7 · D2:6 · D3:7 · D4:6 · D5:6). This is the study-guide numbering the tutors teach and `/ccaf:result` uses — NOT the official blueprint's 30 (D2:5, D3:6). The blueprint-30 stays the target of the maintenance coverage audit (`maintenance/bank-coverage-audit.workflow.js`), which folds `2.6`/`3.7` into their blueprint parents.
- Labels are **English** (exam terminology, Invariant #8 — not localized). Keep them in sync with the `tutor-prompts.md` headers.
- Validated by `data/validate.py` (key shape `<d>.<n>`, non-empty labels, per-domain counts 7/6/7/6/6, and every bank `task` ∈ these keys with a matching domain-prefix).

## Extending lessons / traps
`data/tutor-prompts.md` (lesson scripts) and `data/exam-traps.md` (verbatim traps + core rules) are organised by `## Domain N`. Add/refine within the right domain section; the skills read their domain's section by `${CLAUDE_PLUGIN_ROOT}/data/...`. The 5 axes live in `data/axes.md`. **`data/teaching-method.md` is the shared *pedagogy* (HOW every `/ccaf:dN-teacher` teaches — the Concept→Axis→Apply→Check loop); edit it to change teaching style for all domains at once, not per-domain content.** **Rule 0b** in that file sets the plain-language register for every learner-facing explanation (the app's UI copy follows the same rule — see `maintenance/app-internals.md`); exam terms and bank question text stay exact.

## Test locally before publishing
```
/plugin marketplace add /Users/dmitryantonenko/Projects/exam/ccaf-plugin
/plugin install ccaf@ccaf-marketplace
/ccaf:init            # opens the app (hook rebuild); click Mock Exam → sit it → copy JSON → /ccaf:result → /ccaf:dashboard
```
**Ship after edits — the installed copy is what runs.** The hook and every `/ccaf:*` command execute from
`~/.claude/plugins/cache/ccaf-marketplace/ccaf/<version>/`, not from this repo. Until the steps below are done the
user sees nothing, and the next `/ccaf:dashboard` rebuilds the app from the OLD cached template. After any change:
(1) version bump + commit, only with the user's approval per God Rule #12; (2) `claude plugin update ccaf@ccaf-marketplace`;
(3) `CCAF_NO_OPEN=1 python3 ~/.claude/plugins/cache/ccaf-marketplace/ccaf/<new-version>/data/build-app.py`;
(4) grep `~/.claude/ccaf-progress/ccaf-exam.html` for a symbol from the change to prove it landed; (5) the user must
reload the app page, and an exam already started keeps its old question set. **The first sentence of the report
after an edit names which of these are done and what the user still has to do.**

## Staying current (content freshness)
Keeping bundled content aligned with the official exam is a **maintainer task, every 6–12 months** — NOT
a shipped command. Full procedure → **`maintenance/RUNBOOK.md`**; authoritative source list + "Last
verified" stamp + official blueprint/task statements + exam-vs-product divergences → **`maintenance/sources.md`**;
stored audits → `maintenance/{bank-coverage,fact-currency}-audit.workflow.js`; each review logged in
**`CHANGELOG.md`**. Current baseline: **Exam Guide v1.0 (July 2026)**; weights 27/18/20/20/15 and the 30
task statements (D1:7 D2:5 D3:6 D4:6 D5:6) **match**. Known gap: multiple-response items untrained.
When you **add bank questions**, run `python3 maintenance/reference-coverage.py` and add `quick-reference.json`
rows for any flagged unreferenced criteria (curated — the script finds gaps, a human writes the answer +
hand-picks `q_ids`). `exam-traps.md` is the **source** for `quick-reference.json`: change a core rule there
→ update the matching reference row so the see→answer projection doesn't drift.

## Provenance
Bank built from `../source/{exam-1.html, exam-2.html, test-exam.pdf}` (study workspace). Lesson/trap
material bundled from `../reference/{tutor-prompts.md, exam-traps.md}` (originals also live there).
