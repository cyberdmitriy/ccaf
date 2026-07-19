# ccaf plugin — Maintainer / Extension Guide

This repo IS the `ccaf` Claude Code plugin (CCAF exam tutor + mock-exam generator). This file is maintainer
context — read it before changing anything. End users never see it (plugin installs load
skills/commands/hooks, not this CLAUDE.md).

**Role split:** how to *use* the installed plugin lives in `README.md` (end-user facing). This file covers
only how to *change* it — architecture, invariants, schema, and the extend/test workflow. Keep it that way:
don't add usage/marketing here, don't add schema/invariants to the README.

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
maintenance/            # MAINTAINER-ONLY (not shipped runtime; no skill reads it)
  RUNBOOK.md            # periodic content-review procedure (every 6–12 months)
  bank-coverage-audit.workflow.js  # stored multi-agent bank↔blueprint coverage audit
  sources.md            # authoritative-source list + "Last verified" stamp + official blueprint/task statements
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

## App UI internals (v0.6.3 — all in `data/app-template.html`)
- **Discard unrecorded sittings** (`discardPending()`): the dashboard pending banner has a **Discard** button beside **Export unrecorded** that clears `LS_PENDING` (finished-but-unrecorded sittings held only in `localStorage`) after a confirm. Needed because `localStorage` is keyed to the `file://` origin, so it survives deletion of `~/.claude/ccaf-progress/` and a rebuild to the same path — Discard is the in-UI way to drop stale local sittings. Recorded progress in `stats.json` is untouched.
- **Results review** (`renderResults` → `renderReviewList()` + `reviewState`): opens **misses-only** by default; a segmented `[Misses only | All]` toggle and per-domain filter chips (only the domains present in that exam) re-render the list in place without leaving the view. Empty states: "No misses — nice." vs "No questions match this filter." Each review card shows an **axis badge** (`Axis N · <name>`) from `q.axis`. Score hero / per-domain / export are untouched.
- **Dashboard 5-axis tally** (`computeAxisTally(merged)`): computed **client-side** from `BANK[id].axis` over the user's misses (latest attempt wrong); `HISTORY.axis_tally` is only a fallback when the bank has no axis data.
- **Score-trend sparkline** (`renderTrend(allExams)` + `examPct`): self-contained inline SVG above the exam-history list. Mock sittings = connected line + dots; external results = separate diamond markers on the same timeline, **never averaged in**. Degrades to a "not enough data" note when <2 mock sittings.
- **Weak-mode spaced-repetition** (`selectSet` weak branch): a `due` term ranks unseen / long-unseen questions higher (`min(1.5, ageDays/14)`, unseen = full 1.5), on top of the missed/unseen/domain-weakness/focus/blueprint terms. Depends on `answered[id].last_ts` injected by `app-build.md` (ISO ts of the most recent attempt).
- **Exam is one-question-per-screen** (`renderExam` → `renderCurrentQuestion()`, `examStage` = `"question"|"review"`): only the current question's `.q` card is in the DOM (mirrors the real proctored exam; no scroll-spy — the old `IntersectionObserver` was removed). `currentQId` is the single source of truth (keyboard answers can no longer hit the wrong question). Navigation: **Prev / Next** buttons in the card footer (last question's Next = **Review & submit**), the `.navgrid` chips (real `<button>`s, `gotoQ(i)`), a **Jump to unanswered** header button, and keys `1–4`/`A–D` = pick, `J/K`/`←→↑↓` = move, `F` = flag. `gotoQ` re-renders the single card + persists + scrolls to top. `pickAnswer(id,L)` is the shared select path.
- **Mark for review + review-before-submit gate** (`toggleFlag()`, `exam.flagged`, `showReviewScreen()`): a per-question flag (persisted, shown as a warn dot on the navchip). Submit (header button or last Next) opens `showReviewScreen()` — lists unanswered + flagged as clickable jump chips — instead of a bare `confirm`; its **Submit exam** calls `submitExam()`. Header **Quit** (`quitExam()`) leaves without submitting: persists in-progress, restores the dashboard resume banner.
- **Navchip states disambiguated**: answered = solid neutral `--ink2` (was `--accent`), current = accent ring, flagged = warn dot — so "answered" and "current" no longer share the accent hue.
- **Accessibility pass**: global `:focus-visible` / `.opt:focus-within` outlines; `@media (prefers-reduced-motion:reduce)` + `scrollTopSmooth()` gate all smooth-scroll/animation; navchips are real buttons with `aria-label` state; `showView()` moves focus to the view heading and announces via the `#srStatus` `aria-live` region (exam view manages its own focus in `renderCurrentQuestion`); export `<textarea>` is labelled.
- **Optional time limit — 2 min/question, never auto-submits** (`cfg.timed` → `exam.limit_seconds = count*120`; `updateClock()`, `showTimeUp()`/`hideTimeUp()`, `exam.over_time`): a **Time limit** field on New exam (`No limit` / `Timed · 2 min/question`). When timed, the header clock counts **down** (red-pulse `.clock.low` in the last minute); at zero it does **NOT** submit — it sets `exam.over_time=true`, shows the non-blocking `#timeUpBanner`, and the clock flips to counting **up** in steady red `.clock.over` (`+MM:SS`). This is practice: the learner always finishes every question and submits manually through the normal review gate. `grade()` writes `over_time` + `limit_seconds` into the result JSON; `/ccaf:result` copies them onto the `exam_history` entry; results header and dashboard history show an "⏳ over time" marker (score unaffected). `limit_seconds`/`over_time` persist in `localStorage` and restore on resume-later. Untimed = `0` (clock counts up, no banner).
- **Injected `HISTORY` is minimal**: `app-build.md` parses the user's `profile.md` **Focus domains** automatically (no manual value to fill) and does **not** inject blueprint weights or per-domain accuracy — the app owns the constant blueprint and recomputes per-domain accuracy client-side, so nothing stale is shipped in the payload.

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
- **`axis`** = integer **1–5** — the ONE axis (from `data/axes.md`) that the question's strongest near-miss distractor trips on: **1** Determinism · **2** Exact-hit · **3** Right-diagnosis · **4** Proportionality · **5** Root-cause/antipattern. Assigned by the correct-vs-distractor logic in the `explanation`. The app injects the whole question object, so `axis` rides along automatically and powers the dashboard 5-axis tally (computed client-side over the user's misses) and the per-question axis badge in results review. `/ccaf:result` reads it directly instead of guessing. **Every question must carry exactly one `axis` 1–5.**
- **Balance the correct-answer letter.** When authoring new questions, deliberately vary which letter is correct — never let the correct answer default to the same position (an easy, unconscious habit is keying everything to B). Shuffle each new question's options so `correct` spreads roughly evenly across A/B/C/D, and check the batch distribution before committing: `python3 -c "import json,collections;d=json.load(open('data/questions.json'));print(collections.Counter(q['correct'] for q in d['questions']))"`. If a batch skews to one letter, reorder the options (the option texts are self-contained, so reordering is safe — but then fix any explanation that names an option by letter).
- **Every question needs a real near-miss.** Each question must have at least one distractor (ideally two) plausible enough to make a *well-prepared* candidate hesitate — the tempting wrong answer that reflects a common mental-model error (the "trap" from `axes.md`), not three throwaways with one obvious answer. Concretely: (a) no giveaway where the correct option is the only substantive/reasonable one; (b) avoid the **length tell** — the correct answer must not be the conspicuously longest / most-qualified / most-detailed option while distractors are short stubs (savvy test-takers just pick the longest); keep option lengths comparable. When a distractor pool is all-obviously-wrong (e.g. three "probabilistic" non-solutions against one deterministic answer), replace one with a believable-but-inferior real pattern (e.g. a retry loop, a plausible-but-wrong protocol ordering, a workaround that "works but doesn't scale").
- **Scope of the balance + length-tell rules — authored questions ONLY.** The correct-answer-letter balancing and the length-tell guidance above apply **only to questions Claude writes from scratch**. Questions imported verbatim from real practice exams are kept **as-is** — never reword, reorder options, or pad/trim an imported question just to even out the answer-letter distribution or option lengths; fidelity to the source is what makes the bank useful for memorising exact wording, and it wins. A mild length skew across the whole bank (the correct option running a little longer than average) is therefore expected and acceptable, because most entries are copied, not generated — do **not** "fix" it by editing imported questions. Only balance *within a new batch you author*.
- Current count: **240** (D1:64 D2:47 D3:42 D4:41 D5:46), **all carrying an `axis` 1–5** (backfilled 2026-07 by a classify+verify subagent workflow against `data/axes.md`). Sources so far: exam-1.html, exam-2.html, test-exam.pdf, practice-1 screenshots, owner-authored questions, + cheatsheet gap-fill (2026-07, ids 213–234: CLI system-prompt/`--bare` flags, MCP tool-search/primitives/connection-sequence/templated-resources, escalation payload, batch pilot-test, `detected_pattern`, and several THIN-nuance fills), + axis-1 (Determinism) coverage fill (2026-07, ids 235–240: hook-vs-CLAUDE.md/rules/prompt guarantees, forced/schema-constrained determinism — added because axis 1 was under-represented at 16/234).

## ▶ Extending the bank from a new resource (the common task)
Recommended workflow — this is how the bank was built (multiple sources, deduped; currently **240** questions):

1. **Extract** every question from the resource VERBATIM: stem, 4 options (A–D), the marked correct answer, and the explanation if present. For a big source, dispatch a subagent to parse it (one subagent per source file/PDF parses in ≤20-page ranges) and return structured entries — keeps the main context clean.
2. **Classify domain** with these cues:
   - **1 Agentic Architecture & Orchestration** — agentic loop/`stop_reason`, coordinator↔subagent, Task tool, context passing, Pre/PostToolUse hooks, workflow-enforcement gates, task decomposition, session state (`--resume`/`fork_session`).
   - **2 Tool Design & MCP** — tool descriptions/misrouting, structured errors (`errorCategory`/`isRetryable`), `tool_choice`, tool distribution, `.mcp.json` vs `~/.claude.json`, MCP resources, built-ins (Grep/Glob/Read/Write/Edit/Bash).
   - **3 Claude Code Config & Workflows** — CLAUDE.md hierarchy/@import, `.claude/rules` glob, slash commands vs skills, SKILL.md frontmatter, plan mode vs direct, iterative refinement, CI/CD (`-p`, `--output-format json`, session isolation).
   - **4 Prompt Engineering & Structured Output** — explicit criteria vs vague, few-shot, tool_use JSON schema/nullable fields, validation+retry, `detected_pattern`, Message Batches API, multi-instance vs self review.
   - **5 Context Management & Reliability** — case-facts block/summarization, lost-in-the-middle, trimming tool output, escalation criteria, error propagation, scratchpad/state manifests, `/compact`, stratified sampling/confidence calibration, provenance/claim-source, temporal.
3. **Dedupe against the existing bank:** merge a new question into an existing one ONLY if ≥90% identical (same meaning AND same option set — minor wording differences OK). If the options differ meaningfully, keep both.
4. **Assign ids** = continue from the current max (`178, 179, …`), appended at the end.
   **Also assign each new question an `axis` 1–5** (see the schema note above + `data/axes.md`): identify the strongest near-miss distractor and name the single axis it fails on, keyed to the explanation. When adding a batch programmatically, a classify+verify subagent pass over `data/axes.md` is the reliable route (that's how the field was first backfilled); for one or two hand-authored questions, just assign it directly.
5. **Update `meta`** — bump `total` and the relevant `per_domain` counts.
6. **Validate:** run **`python3 data/validate.py`** — it asserts unique/sequential ids, A–D options, a valid `correct`, a valid `axis` 1–5 and `domain` 1–5 on every entry, that `meta.total`/`meta.per_domain` match reality, and that no entry contains `</script>`/`<!--` (which would break the injected HTML app). It also prints the correct-answer-letter distribution and warns on a heavy skew (see the "Balance the correct-answer letter" rule above) — don't let a new batch skew to one letter.
7. **Bump the plugin version** in `.claude-plugin/plugin.json` (and marketplace.json) — teachers and `/ccaf:exam` pick up new questions automatically; no code changes needed.

## Extending lessons / traps
`data/tutor-prompts.md` (lesson scripts) and `data/exam-traps.md` (verbatim traps + core rules) are organised by `## Domain N`. Add/refine within the right domain section; the skills read their domain's section by `${CLAUDE_PLUGIN_ROOT}/data/...`. The 5 axes live in `data/axes.md`. **`data/teaching-method.md` is the shared *pedagogy* (HOW every `/ccaf:dN-teacher` teaches — the Concept→Axis→Apply→Check loop); edit it to change teaching style for all domains at once, not per-domain content.**

## Test locally before publishing
```
/plugin marketplace add /Users/dmitryantonenko/exam/ccaf-plugin
/plugin install ccaf@ccaf-marketplace
/ccaf:init            # then /ccaf:exam (pick mode/length on the page) → copy JSON → /ccaf:result → /ccaf:stats
```
Reinstall after edits: `/plugin marketplace update ccaf-marketplace`.

## Staying current (content freshness) — a MAINTAINER task, run periodically
The exam and the docs it tests drift, so bundled content goes stale. Keeping it current is a
**maintainer procedure done every 6–12 months from this repo** — NOT a shipped command (the review can
edit skills, lessons, and the bank). The full procedure lives in **`maintenance/RUNBOOK.md`**; the
authoritative source list + "Last verified" stamp + official blueprint/task statements live in
**`maintenance/sources.md`**; the stored coverage audit is **`maintenance/bank-coverage-audit.workflow.js`**;
record each review in **`CHANGELOG.md`**.

Two layers: **blueprint** (format, weights, task statements) changes only with a new **Exam Guide**
version — publicly downloadable (Skilljar → S3 PDF), reconciled by hand; **technical behavior** (CLI
flags, hooks, MCP, `tool_choice`, Batch API) lives in public docs (Claude Code changelog, Platform
release notes) checked during the review. Current baseline: **Exam Guide v1.0 (Effective July 2026)**;
weights 27/18/20/20/15 and the 30 task statements (D1:7 D2:5 D3:6 D4:6 D5:6) **match** the plugin.
**Known gap:** the exam has multiple-response items; the bank is single-answer only.

## Provenance
Bank built from `../source/{exam-1.html, exam-2.html, test-exam.pdf}` (study workspace). Lesson/trap
material bundled from `../reference/{tutor-prompts.md, exam-traps.md}` (originals also live there).
