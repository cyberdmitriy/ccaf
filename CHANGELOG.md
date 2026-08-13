# Changelog

All notable changes to the `ccaf` plugin. Dates are ISO (YYYY-MM-DD).

This file also records **content reviews** — the periodic sync against the official Exam Guide and
Claude Code / API docs (procedure: `maintenance/RUNBOOK.md`; sources + last-verified stamp:
`maintenance/sources.md`).

## [0.15.0] — 2026-08-13
### Added
- **Rule 0b: one plain-language register for every explanation a learner reads.** New section in `data/teaching-method.md`: one idea per sentence, active voice, everyday words, fact then consequence, no em dashes, no filler. A 12-year-old should follow any sentence that is not a technical term. It lives in ONE place (all five tutors already read that file), so `skills/dN-teacher/SKILL.md` only gained a pointer to it. Two hard boundaries stated in the rule itself: exam vocabulary keeps its exact English form inline (`stop_reason`, `tool_choice`, `PreToolUse`, *winning condition*, *axis*, every flag/field/file name), and question stems, options and the bank's `explanation` field are exam artefacts that stay exactly as `questions.json` has them.
- **Exam-realistic fresh-question rules.** When the bank runs dry and a tutor invents a question, it must hold to the bank's own bar: three genuine near-misses (each tripping exactly one axis, no joke or off-topic options), no length tell, no formatting tell (plain text everywhere, since bolding a phrase in the correct option hands the answer away), one clear winning condition, anchored in one of the six scenarios. Includes a giveaway-vs-exam-grade worked example.
- **Copy register for the app**, documented as its own section in `maintenance/app-internals.md`, so future UI edits hold the same bar.

### Changed
- **Every learner-facing string in the offline app rewritten to the register**: the 5-axis explainer (`AXIS_DESC` / `AXIS_ONELINE` / `AXIS_INFO`), the coach banner, the readiness verdict, the three malformed-JSON banners, all empty states, the mock-exam modes, the timer hint, the review-before-submit gate, the confirm dialogs, and the results + export screens. Layout, CSS classes and logic are untouched: only strings changed.
- **`data/quick-reference.json`: all 83 `answer` rows rewritten** (the app's Cheatsheet/Reference tab), and **`data/exam-traps.md`: all 32 `Core rule` lines rewritten** so the projection does not drift from its source. The verbatim **"Exam Trap"** callouts are quotations from claudecertificationguide.com and were deliberately left as they are.
- **`data/exam-traps.md` header: lesson count corrected from 30 to 32** (D1 7 · D2 6 · D3 7 · D4 6 · D5 6), with a note that these are the study guide's *lessons*, not the official blueprint's 30 *task statements* (D1 7 · D2 5 · D3 6 · D4 6 · D5 6), so the two counts differ on purpose.

### Fixed
- **`renderResults` hardcoded the pass line.** The verdict read "Above the 72% line" as a literal while `PASS_PCT` already existed, so changing the threshold would have left the text lying. It now reads from `PASS_PCT`.
- **Dead code removed from the dashboard.** The v0.14 cinematic redesign replaced the 4-tile KPI strip with the readiness orb plus stat tiles but left the `kpis` array and `projColor` unread. Both are gone; `proj` stays, since the orb, verdict and hero subtitle use it.
- Documented that **`AXIS_INFO.triggers` is data, not prose**: `axisTriggers()` splits the trigger chips from the trailing note on `" — "`, so that one em dash must survive any future copy pass. Noted in the code and in `maintenance/app-internals.md`.

## [0.14.0] — 2026-07-21
### Changed
- **Merged `/ccaf:exam` + `/ccaf:stats` into a single `/ccaf:dashboard`.** Both opened the same app on the Dashboard; the merged skill opens it (Dashboard · Weak spots · Cheatsheet) and prints the text recap, and an exam is started from the in-app **Mock Exam** button. The old skills are deleted; all forward-facing refs repointed.
- **App/dashboard UI cleanup.** Tabs renamed — personal miss-driven tab → **Weak spots**, the see→answer reference → **Cheatsheet**; **New exam** tab → a standalone **Mock Exam** accent button; dashboard review-launcher + "Start a new exam" footer removed; `page-head` (eyebrow + h1) dropped on every view; app content width is now fluid (`--maxw min(94vw, 1240px)`).
### Added
- **Deterministic app rebuild.** `data/build-app.py` (bootstrap → build → open, single source of truth) + a `UserPromptSubmit` hook (`hooks/ccaf-build.sh`) that runs it on `/ccaf:init` and `/ccaf:dashboard` — a runtime-enforced rebuild outside the model, so a stale `ccaf-exam.html` no longer hides new views/stats after a plugin update. The hook prints a marker so the skill skips a redundant second build; activates after a `/plugin marketplace update` reinstall.
### Fixed
- **Auto-open actually works.** `build-app.py --open` no longer gates on `sys.stdout.isatty()` (always false under a hook / the Bash tool, which wrongly suppressed the GUI); it opens unless `CCAF_NO_OPEN` is set.
- **Malformed `stats.json` no longer crashes the build or fails silently.** It's backed up to `.bak` and surfaced via a dashboard banner (God Rule #11), building with empty stats instead of aborting. `HOME` unset falls back to `~` instead of a raw `KeyError`.
- **Hook overhead + discoverability.** The hook now runs a cheap pure-bash prefilter (skips the python cold-start on the ~99% of prompts that don't mention `ccaf`). The `/ccaf:dashboard` skill description now names both the stats dashboard and the configurable mock exam, so the merged command still advertises exam-taking in the command list.

## [0.13.0] — 2026-07-21
### Added
- **Reference tab — a curated "signal phrase → answer" cheat sheet across all five domains.** A new **Reference** view in the offline app (distinct from the personal, miss-driven **Cheatsheet**): per-domain, per-subtopic tables of *See in the question → Answer*, with a domain filter and search. Rendered as an aligned **zebra dictionary** (`table-layout:fixed` so long `code` tokens wrap instead of overflowing), accent arrow on each answer, coloured domain badges. Content lives in a new bundled **`data/quick-reference.json`** (83 rows, a curated projection of `exam-traps.md`; rows carry `see`/`answer`/`q_ids` — `q_ids` hand-picked or empty, never keyword-grepped; no `axis` field). Injected via a third build placeholder `/*__REFERENCE__*/{}` (a sibling of the bank, not per-user state; graceful `{}` when absent). The bank is untouched.
- **`maintenance/reference-coverage.py`** — a deterministic report (pure set arithmetic, no agents) of `quick-reference.json` coverage vs the bank: stale `q_ids` + per-domain unreferenced questions. Run it when the bank grows to see which criteria still need a Reference row.
### Changed
- **App content width is now fluid** — `--maxw` is `min(94vw, 1240px)` (was a fixed 940px), so the app uses more of a wide screen while staying readable on smaller ones.
- **`data/validate.py`** now also validates `quick-reference.json` (domains 1–5, non-empty see/answer, `q_ids` exist in the bank). New maintainer **God Rule #13**: propose 2–3 UI/UX options before building; readability and usability first.

## [0.12.0] — 2026-07-20
### Changed
- **5 axes reframed from "what the wrong option looks like" → "why the right answer beats the near-miss".** Each axis is now taught on one template — a plain **one-liner** (what the right answer wins on), a **quick test** (the one question to ask the distractor), **stem triggers**, **wrong-looks-like**, and a **❌→✅ example** drawn from a spread of domains (hook vs CLAUDE.md, forced-specific `tool_choice`, plan-mode vs interview, subagent-for-one-file, one-prompt vs TDD). Added a **decision order** ("which axis is it? ask in order"). Term **"Litmus" → "Quick test"**. Applied consistently across `data/axes.md` (canon), `data/teaching-method.md` (the 5-axis table), and the dashboard card.
- **Dashboard "The 5 axes of failure" card rebuilt for readability.** Axes are now **collapsible cards** (`<details>`): collapsed shows the number, name, a status badge, and a two-line teaser (one-liner + quick-test question); the stem-triggers/wrong-looks-like/example expand on click. Stem triggers render as **scannable chips**; the ❌/✅ example uses **Wrong/Right badges** instead of emoji. The misleading shared-baseline progress bar is **replaced by explicit badges** — green **✓ clear** (no misses on that axis) / red **N misses** (weak spot) — removing the "full bar = good" false signal. Canonical 1→5 order kept.

## [0.11.0] — 2026-07-20
### Changed
- **Cheatsheet cards rebuilt to teach the transferable principle, not "pick X here".** Each card now reads as one line of reasoning: a plain-language **decision** headline (the question behind the question), a scenario-independent **rule**, **What gave it away** (verbatim signal words from the stem), **So the answer is** (the correct mechanism + why), and **Your instinct — and when it's right** (why the tempting option fails *here* **and the exact condition under which it would be correct**) — so the learner can answer similar-but-different questions instead of memorising an answer. The learner's pick is shown once, inside a **Show the full question** accordion (stem + all four options, correct in green, pick tagged), not a duplicate block. Card text renders **bold**, *italic*, and `code`.
- **Dashboard: three blocks reworked.**
  - *The 5 axes of failure* — cleaner heading (a numbered pill + name, replacing "1 Determinism"), a one-line "where you get caught" summary, a shared-baseline bar per axis for at-a-glance comparison, 2-line clamped descriptions, and dimmed "✓ clear" rows for axes with no misses (canonical 1→5 order kept).
  - *Recurring misses* table (a truncated-stem list that duplicated the Cheatsheet) → a slim **review launcher**: backlog count + per-domain chips that deep-link into a pre-filtered Cheatsheet.
  - *Avg mock time* tile → **Projected score** — the mean of the last up-to-3 recorded exams, colour-referenced to the 72% pass line.
### Fixed
- `/ccaf:result` cheatsheet authoring rewritten to enforce the discriminating-principle format (`decision`/`rule`/`signal`/`answer`/`flip`, anchored to each question's axis) instead of a generic "trigger → rule → why".

## [0.10.0] — 2026-07-20
### Added
- **Cheatsheet — a per-user, miss-driven study aid.** A new **Cheatsheet** view in the offline app, built from the questions you get wrong. Each miss is a card: the scenario **trigger**, **Pick this** (rule + correct option), **Why it fits**, **The trap** (why the tempting distractor is wrong *here* and when it would be right), **You picked** (your wrong option), an axis badge + a per-domain-coloured tag, and a collapsible **Show the scenario** accordion with the full question stem + all four options (correct green, your pick red). Active misses on top; a later correct answer moves the card to a **Mastered** section. Filter by domain/axis/search. Content lives in a new per-user store file `cheatsheet.json` (survives plugin updates); `/ccaf:result` writes it and **backfills** entries for misses recorded before the feature existed. The question bank is untouched.
### Changed
- **Blueprint-weight tick is bright red** on the dashboard "By domain" bars, so the target marker stands out against the coverage fill.
### Fixed
- **`/ccaf:exam` & `/ccaf:stats` always rebuild the app.** `app-build.md` + both skills now state that `ccaf-exam.html` is a disposable artifact regenerated every run, never opened stale — so a new view no longer appears "missing" after an update. (Instruction hardening; a hard guarantee would need a hook — logged in `maintenance/BACKLOG.md`.)
- **Tutor progress checkpoints incrementally.** `teaching-method.md`'s recording contract now persists `learning-progress.json` after each task statement is taught + check-questioned (plus a hand-off flush), so a session interrupted before hand-off keeps what it covered.

## [0.9.1] — 2026-07-19
### Fixed
- **Learning-progress reads no longer fail silently.** `app-build.md`'s `load_learning()` now
  distinguishes an **absent** file (expected first run → skeleton, no warning) from a **present-but-
  malformed** one (→ skeleton for rendering **plus** a `learning_unreadable` flag). The dashboard shows
  a warning banner instead of silently rendering zero progress, and `/ccaf:init` reports the corruption
  plainly rather than "no progress yet."
- **Tutor write-contract no longer risks silent data loss.** `teaching-method.md` now says: a
  present-but-unparseable `learning-progress.json` must be backed up to `.bak` and surfaced — **never**
  skeleton-recreated (which would wipe the other domains' progress). Only a genuinely missing file is
  safe to recreate.
### Added
- `data/validate.py --learning <path>` — shape-checks a `learning-progress.json` (schema, domains 1–5
  keys + valid status, `axis_mastery`, drills/task_statements shape). Referenced by the warning banner,
  `/ccaf:init`, and the maintenance runbook.

## [0.9.0] — 2026-07-18
### Changed
- **Sync is now a maintainer procedure, not a shipped command.** Removed the `/ccaf:sync` slash command
  (`commands/sync.md`) — keeping the plugin's content current can edit skills, lessons, and the bank,
  which is maintainer work, not something an installed user should run.
- Moved the source-of-truth + last-verified stamp from `data/sources.md` to `maintenance/sources.md`
  (no longer runtime data).
### Added
- `maintenance/` (maintainer-only, not referenced by any skill/command):
  - `RUNBOOK.md` — the every-6–12-months content-review procedure.
  - `bank-coverage-audit.workflow.js` — stored multi-agent audit that maps the bank to the official task
    statements and checks the guide's sample questions (report-only).
  - `sources.md` — moved here.
- This `CHANGELOG.md`.

## [0.8.1] — 2026-07-18
### Fixed
- Corrected the Exam Guide facts against the **primary source** (official PDF): the guide is **v1.0,
  Effective July 2026, CCAR-F** (not the v0.2 taken from a third-party summary), and it is **publicly
  downloadable** (Skilljar landing → public S3 PDF), **not** login-gated.
### Added
- Authoritative data from Exam Guide v1.0 in `sources.md`: format (60 items, multiple-choice **and
  multiple-response**, 4-of-6 scenarios, 720/1000, $125), blueprint weights **27/18/20/20/15** (matches),
  and the **30 task statements** (D1:7 D2:5 D3:6 D4:6 D5:6 → authoritative `task_total`).
- Documented a **known fidelity gap**: the exam has multiple-response items; the bank is single-answer only.

## [0.8.0] — 2026-07-18  _(superseded by 0.9.0)_
### Added
- `/ccaf:sync` freshness-check command + `data/sources.md` baseline. *(The command was removed in 0.9.0
  in favor of the maintainer runbook; the sources file moved to `maintenance/`.)*

## [0.7.0] — 2026-07-18
### Added
- **Learning-progress tracking.** A per-user `~/.claude/ccaf-progress/learning-progress.json` (separate
  from `stats.json`) records task-statement coverage, in-tutor drill scores, last-visited, and per-axis
  mastery. Written by the `dN-teacher` tutors at hand-off; surfaced as text in `/ccaf:init` and as a
  "Learning progress" card in the `/ccaf:stats` dashboard. Bootstrapped additively via `cp -rn`.

## [0.6.6] — baseline
- Pre-changelog baseline: 5 domain tutors, `/ccaf:init` / `/ccaf:result`, offline mock-exam app
  (`/ccaf:exam` + `/ccaf:stats`), 240-question bank, 5-axis trap framework.

---

## Content reviews
| Date | Exam Guide | Docs checked | Outcome |
|------|-----------|--------------|---------|
| 2026-07-18 | v1.0 (Effective July 2026) | 2026-07-18 | Blueprint + 30 task statements verified against the guide — **match**. Coverage audit: all 30 task statements `good`, 0 of 12 sample questions missing. No bank edits needed. Open gap: multiple-response items untrained. |
| 2026-07-19 | v1.0 (Effective July 2026) | 2026-07-19 | **Layer-2 fact-currency audit** (per-domain, vs current Claude Code + Platform docs): **0 stale facts** across all 5 domains — every falsifiable flag/path/number/API detail is current. 2 D3 semantic nuances (`allowed-tools` = restrict; `/memory` = shows loaded files) match the Guide but the product moved past it → recorded under "Known exam-vs-product divergences" in `sources.md`; **content unchanged** (correct for the exam). No bank/skill/lesson edits. Added stored `maintenance/fact-currency-audit.workflow.js`. |
