# Changelog

All notable changes to the `ccaf` plugin. Dates are ISO (YYYY-MM-DD).

This file also records **content reviews** — the periodic sync against the official Exam Guide and
Claude Code / API docs (procedure: `maintenance/RUNBOOK.md`; sources + last-verified stamp:
`maintenance/sources.md`).

## [0.19.1] — 2026-08-28
### Added
- **Prefill coverage — the one blueprint gap found by a score-report cross-check.** A colleague's official Score Report listed *response prefilling* as one of three structured-output methods (task 4.3), but the plugin taught only `tool_use` + schema and prompt-based formatting. `data/tutor-prompts.md` (4.3) now teaches assistant-turn prefill and the reliability order (`tool_use` + schema > prefill / prompt-based); `data/exam-traps.md` (4.3) gains a matching trap + Core-rule clause. Two bank questions added: **241** (strict schema compliance → `tool_use`, prefill enforces no schema) and **242** (prefill's real niche — skip preamble / control first tokens).
- **Domain 3 config-enforcement drill deepened (`3.1` 4→7 questions).** The most-failed objective on the same report — distinguishing what belongs in a hook/`settings.json` vs `CLAUDE.md` — was thin in the bank. Added **243** (violated commit rules → deterministic hook, not prose), **244** (map each of hard-block / path-convention / soft-preference to the right mechanism), **245** (blocked `Read` → `deny`/PreToolUse prevention, PostToolUse log only detects).
- **Cheatsheet synced to the five new questions (204 reference rows, 100% coverage).** `quick-reference.json` gains four rows (prefill-for-schema, prefill-for-preamble, mechanism-by-guidance-type, prevent-vs-detect forbidden reads) and attaches 243; `maintenance/reference-coverage.py` reports 0 unreferenced per domain.

### Changed
- **Mock exam — `unseen` mode is now strictly never-answered.** `data/app-template.html`: the unseen pool no longer tops up with least-seen questions once true-unseen runs out; the Length buttons disable above what a mode+domain actually offers, and `All` caps at the shown-available count (the mode card's "N new" for unseen). Removes the old fallback that could inflate an "unseen" sitting with seen questions.
- **Eight bank questions retagged to their canonical `task`.** Cross-session `task` drift corrected on ids 21, 22, 42, 63, 99, 110, 195, 232 (each stays within its domain); `quick-reference.json` q_id attachments realigned to match.

### Fixed
- **Reference tab: active domain filter now visible.** `data/app-template.html`: added the missing `.miss-chip.active` rule (accent fill + white text, mirroring `.cs-chip.on`) so the selected `All`/`D1`–`D5` chip is distinguishable from the rest.

### Internal
- **New authoring guard against the "reasoning tell."** `maintenance/authoring-questions.md`: the correct option must never name or justify the tested principle (rationale lives in `explanation` only) — otherwise a candidate keyword-matches instead of reasoning. Reworded Q243 (dropped "Enforce them with deterministic mechanisms …") and Q245 (dropped "… regardless of what the model decides") whose correct option gave the answer away in its wording.

## [0.19.0] — 2026-08-25
### Changed
- **Weaknesses card redesigned — grouped by task, theme paired to its question.** Misses now aggregate into **one card per task statement `<d>.<n>`** (via `topicKey`, the canonical grouping — every 2.3 miss lands in the 2.3 card regardless of per-miss wording), all-collapsible and closed by default under a domain-coloured header. Inside, a `Failed questions · N` list where **each failed question is paired with its own theme**: a `Тема:` chevron disclosure (its study note) joined to the question by a light left thread, so which theme belongs to which question is unambiguous. Each question's summary **is the question** — the bank stem clamped to two lines, un-clamping to the full stem on open (no repeated question, no stats in the header); its body reorders to **options → `Breakdown` panel → `Answer stats` panel** (the learner's wrong pick in **red**, the correct one green; `Breakdown` = `rule` + the three beats + axis badge; `Answer stats` = every attempt `✗n · ✓n` + `✓/✗ · Exam #N · date` rows). Replaces the previous decision-headline summary + dots/attempt-list body (`wkDots`/`wkLast`/`wkHistory`/`cheatScenario` removed; `wkQuestion` is 2-arg with new `wkOptions`/`wkStatsPanel`).
- **Domain-coloured, expressive headers across Weaknesses and the Cheatsheet.** Both tabs share one header language: a domain-coloured kicker over a big title, with the card/section left rail and rules tinted by `DOMAIN_VAR[domain]`. The Cheatsheet domain header is now a large hero title with a domain-coloured `Dn` + description subtitle; its section headers are a coloured `<n.n>` kicker over a big title with a coloured left rule (`.ref-dnum` gradient chip retired). The Weaknesses `Topic:` label is domain-tinted, and a `` `token` `` inside the task title renders as a domain-coloured mono word rather than a boxed code chip.
- **Pre-teach audit is now a hard gate — the UNION of three sources.** `data/teaching-method.md`: before writing the Concept block for a task statement, the tutor builds the teaching spec as the union of that statement's `tutor-prompts.md` bullets + its `exam-traps.md` traps + every winning condition its `questions.json` pool tests, and must teach every item before the first Check (running it only at question-selection time was the failure this closes).
- **God Rules #1/#2 rewritten to a printed checkpoint.** `CLAUDE.md`: Rule #1 now requires emitting a four-line **Pattern / Union-or-either-or / Grounded-in / Root-cause** checkpoint before any non-trivial proposal or edit; Rule #2 binds the fix to that Root-cause line.
- **Denser app at 90%.** The root font-size is now `90%` (and `body` follows it via `1rem` instead of a pinned `16px`), so the whole rem-based layout renders ~10% smaller — the equivalent of a permanent 90% browser zoom, fitting more per screen. Px-based hairlines/shadows/`--maxw` stay crisp.
- **Even dashboard block spacing.** A leading banner (e.g. "N exams not recorded") now carries the same 1.1rem bottom gap as `.coach`/`.hero2` via `#view-dashboard > .banner`, so the banner→coach gap no longer collapses to 0 (the base `.banner` spaces siblings with `margin-top` only). Scoped to the dashboard; the exam/Weaknesses banners are untouched.
- **Readiness card: "Exams taken" → "Avg mock score".** The third readiness stat now shows the average score across MOCK sittings only (external results are never folded in) with a matching ring, and the count in its caption ("across N mock exams") is **mock-only** — resolving the old "Exams taken" showing all types (mock + external + pending), which read one higher than the mock count. The truncated per-exam value strip ("87·80·87·67·93", only the last five) is dropped — the full picture lives in the Score-trend chart.
- **Accuracy card shows the right/wrong split.** Its caption now reads `N right · N wrong` (green / red) instead of `N / N answered`; `wrong` = questions whose latest answer is wrong (`seen − correct`, the Review-misses set). The wrong clause is hidden at 100% correct.
- **Readiness ring: projected score is blueprint-weighted and mock-only.** The `PROJECTED SCORE` ring now shows your per-domain **mock** accuracy weighted by each domain's share of the real exam (27/18/20/20/15), compared to the 72% pass line — external results are excluded, fixing a latent bug where the old "average of the last 3 scored exams" could fold in an external result despite the "mock" label. The caption spells out what the number is, and a themed hover/focus tooltip lists the domain weights.
- **Learning progress moved below "By domain".** The dashboard order is now Exam readiness → Exam history → By domain → Learning progress → The 5 axes (was: Learning progress directly under readiness).

### Added
- **Canonical task-statement labels injected into the app.** `build-app.py` folds `task-statements.json` into `HISTORY.task_labels` (read-only, graceful if absent) → the `TASK_LABELS` global; the Weaknesses header now renders `<n.n> <label>` (e.g. `2.3 tool distribution & tool_choice`) from the canonical source instead of a bare number. Carried inside `HISTORY`, not a fourth placeholder.
- **Cheatsheet coverage synced to the bank (200 reference rows).** `quick-reference.json` expanded so every bank task statement's see→answer criteria are covered (`maintenance/reference-coverage.py` reports 100% per domain); `data/exam-traps.md` gained/refined the per-lesson **Core rule** lines that the reference rows project from, and `data/tutor-prompts.md` picked up the matching exam-trap lines.
- **`maintenance/reference-sync.workflow.js` — stored Cheatsheet-coverage generator.** Maintainer-only workflow that, per section, drafts `q_ids` to attach + new see→answer rows for uncovered nuances, adversarially verified; it edits nothing (returns a reviewable patch). `maintenance/authoring-questions.md` gains step 7 wiring it into the extend-the-bank flow (`reference-coverage.py` → generate → hand-apply rows → re-validate).
- **Four more localized Weaknesses content-labels (Invariant #8 carve-out).** `Topic`, `Breakdown`, `your pick`, `Answer stats` join the localized set; `Show the full question` retired with the old scenario disclosure.

### Docs
- `maintenance/app-internals.md` rewritten to the shipped Weaknesses design (stem-as-summary + Breakdown/Answer-stats panels, domain-coloured treatment-B headers, `TASK_LABELS` injection) and the stale "task labels not injected" limitation note corrected; `CLAUDE.md` Invariant #8 carve-out list updated to the current eight labels.

## [0.18.0] — 2026-08-23
### Changed
- **Weaknesses tab: each failed question is now its own collapsible.** The single wrapping `Failed Questions · N` disclosure (which opened all questions at once) is gone; a topic card now shows a `.wk-qwrap` block — a `Failed questions · N` label followed by one **collapsed `<details class="wk-q">` per question** (flat siblings, each independently expandable). Each question's summary carries its decision headline + axis badge + the `Exam #N · date` it was missed in + the `✓N ✗M` tally; the body holds rule → the three beats → the full question. `cheatCard()` and `examMetaLine()` folded into a new `wkQuestion()`.
- **Domain shown once, on the topic header only.** The redundant per-question `Domain N` badge is removed from each failed-question card — every question in a topic shares that topic's domain, which the card header (`Domain <d> · <task>`) already states.
### Added
- **Localized Weaknesses content-labels (Invariant #8 carve-out).** The five labels that sit directly on the cheatsheet prose the skills already author in `learning_language` — `Failed questions`, `What gave it away`, `So the answer is`, `Your instinct, and when it is right`, `Show the full question` — now render in that language instead of English over Russian text. Mechanism: `build-app.py` injects `learning_language` (read from `settings.json`) into `HISTORY`; the template's `UI_I18N` table + `t()` helper map only these keys, falling back to English for any language not in the table (free-form-language safe). All other app chrome stays English.

## [0.17.1] — 2026-08-23
### Fixed
- **`/ccaf:dashboard` Focus-check recap no longer contradicts the 0.17.0 focus logic.** Since 0.17.0 the app derives weak-mode focus from recent mock exams first (`profile.md` `## Focus domains` is only the cold-start/external-only fallback). The recap still warned "weak-mode won't bias until focus is set" whenever `## Focus domains` was `_(unset)_` and `exam_history` had entries — false for anyone with recorded mocks. It now warns only for **mock-less** history (external-only) with focus unset.
- **`Ever failed` mock mode was missing from the instructions.** Added it to the mode list `skills/dashboard/SKILL.md` tells the learner to pick, and to God Rule #9's enumerated mode set in `CLAUDE.md` (the app already defined all five modes in one place).
- **Stale wording in `commands/result.md`:** "so both tabs are never empty" → "so the Weaknesses tab is never empty" (the two miss tabs merged into one in 0.17.0).

## [0.17.0] — 2026-08-23
### Changed
- **The two miss-driven tabs merged into one `Weaknesses` tab.** The former **Failed Questions** + **Failed Topics** are now a single view: one card per topic (newest first, carrying the topic study note), each with a collapsible **Failed Questions** list of the exact questions missed — every failed question labelled with the exam it was missed in (date + ordinal) and a `✓N ✗M` per-question tally. Renamed consistently across `data/app-template.html`, `data/app-build.md`, `README.md`, `commands/result.md`, `skills/{dashboard,fail-analysis}/SKILL.md`, and `CLAUDE.md` Invariant #5. `cheatsheet.json` schema is unchanged (same two field groups; only how they render moved).
- **Focus tracks recent mock performance, not a frozen rank.** `data/build-app.py` now derives `focus_domains` from the highest per-domain **error rate** over the last few mock sittings (error rate, not raw count, so it is fair across differently-weighted domains). Cold-start fallbacks are unchanged in order: `profile.md` `## Focus domains` → lowest-accuracy-over-history → `[]`. `/ccaf:result` still writes the profile list (the tutors and the app's cold start read it); the ranking logic stays out of any skill per Invariant #3.
- **Cheatsheet/Reference sections are now task statements.** Each `quick-reference.json` section title must start with a valid `<d>.<n>` of its domain, so the Cheatsheet tab lines up with the tutors + the bank `task`. `data/validate.py` enforces it (title head ∈ `task-statements.json`, matching domain prefix); all 83 rows re-sectioned to the `<d>.<n> <label>` form (plain text, `esc()`-rendered).

### Added
- **New `Ever failed` mock mode** — every question you have ever gotten wrong, even ones passed since (distinct from **Review misses** = currently failing). Driven by per-question `right`/`wrong` counts.
- **Domain error trend on the dashboard** — which domains you failed over time, so recent slippage is visible at a glance.
- **Per-miss provenance in `HISTORY`.** Each `answered` entry now carries `misses: [{exam_id, ts}, …]` plus `right`/`wrong` attempt counts (composed in `build-app.py` from `stats.json` attempts), so the Weaknesses tab can tie each failed question to the exam it was missed in and the `Ever failed` mode / `✓N ✗M` tally have their source. Empty for compact/older records with no per-attempt list.

## [0.16.0] — 2026-08-20
### Added
- **Learning-language setting (content-only localization).** New per-user `~/.claude/ccaf-progress/settings.json` (`{"schema":1,"learning_language":"English"}`, free-form, default English), bootstrapped via the existing non-overwriting template copy. The read contract lives in ONE place — new **Rule 0c** in `data/teaching-method.md`: all explanatory prose follows `learning_language`, while question stems/options/answers, verbatim signal phrases, and API tokens stay English always, and the mock exam is English-only. `/ccaf:init` asks for the language once (Step 1.6). New **Invariant 8** in `CLAUDE.md` states the exam-English/prose-localized split; the app chrome is not localized.
- **`/ccaf:fail-analysis` — review my own misses.** New cross-domain skill that gathers the learner's currently-failed questions (latest-wrong in `stats.json`), teaches each grouped by axis as **Concept / Fix / Trap** in the learner's language, re-drills, and persists a localized triple back into `cheatsheet.json`. If there are no misses, it says so and points at a mock (never fabricates a drill). Optional domain/axis argument to focus. Added to the `/ccaf:init` route menu.
- **Shared "Miss-review procedure"** in `data/teaching-method.md` (gather → teach Concept/Fix/Trap → persist), cited by `/ccaf:fail-analysis` and by all five tutors — one source of truth, no duplication.
- **`cheatsheet.json` gains optional localized fields** `concept` / `fix` / `trap` (prose in `learning_language`) plus `explain_lang` (language stamp; the app ignores it). Additive: the English discriminator fields (`decision`/`rule`/`signal`/`answer`/`flip`) authored by `/ccaf:result` are unchanged and still power the Detailed view.

### Changed
- **Tutors route on entry and weave misses into the ordered lesson.** Each `skills/dN-teacher/SKILL.md` gains a **Step 0.5** that runs a shared **Teacher entry router** (`data/teaching-method.md`) and now reads `settings.json` for the language. On a touched domain (or one with misses) the tutor asks the learner what to do — **continue**, **restart**, or **drill only my missed topics in this domain** (the domain-scoped twin of `/ccaf:fail-analysis`); an untouched domain with no misses starts the normal lesson with no question. The ordered lesson then applies **Per-item miss-awareness**: before each item, any of the learner's misses that concern it are surfaced (Concept / Fix / Trap), and a miss already drilled earlier in the session is not re-taught. Personalisation is no longer just weak-domain bias — the session works from the learner's real gaps, in order.
- **Weak spots tab: Detailed / Compact toggle.** New compact review mode groups the learner's misses by axis and shows the short **Concept / Fix / Trap** triple (with an inline label gutter), falling back to `decision` / `answer` / `flip`+`signal` for misses not yet run through `/ccaf:fail-analysis`. Chrome stays English; only the data values are localized. No `build-app.py` change — the whole `cheatsheet` object was already injected, so the new fields ride along.

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
