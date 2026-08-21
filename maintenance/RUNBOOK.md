# CCAF plugin — Maintenance Runbook (periodic content review)

**Audience:** the plugin maintainer, working **inside this repo** (not an end user of the installed
plugin). This is the procedure for keeping the plugin current with the official exam and docs. Run it
**every 6–12 months**, or whenever you hear the Exam Guide or Claude Code/API behavior has changed.

It is deliberately **not** a shipped slash command — the review can edit skills, `teaching-method.md`,
lessons, and the question bank, which is maintainer work, not something an installed user should do.

Everything this runbook consults lives in `maintenance/`:
- `sources.md` — authoritative-source list + **"Last verified"** stamp + the official blueprint/task
  statements copied from the Exam Guide + known exam-vs-product divergences.
- `bank-coverage-audit.workflow.js` — stored audit: bank ↔ task-statement coverage + sample questions.
- `fact-currency-audit.workflow.js` — stored audit: cross-checks the bank/lessons' falsifiable
  technical facts (flags, paths, numbers, API params) against current official docs + the Guide.
- `reference-coverage.py` — deterministic report (no agents): `quick-reference.json` coverage vs the
  bank — stale `q_ids` + per-domain unreferenced questions. Run with `python3 maintenance/reference-coverage.py`.

Record every review in the root `CHANGELOG.md`.

---

## Step 0 — Baseline
Read `maintenance/sources.md`. Note the current **"Last verified"** stamp (Exam Guide version + the date
product docs were last checked). Everything below compares reality against that.

## Step 1 — Layer 1: the Exam Guide (blueprint, weights, task statements)
The guide is **publicly downloadable** (not login-gated):
1. Open the landing page in `sources.md` (Skilljar) and download the current **Exam Guide PDF**.
2. Read the **title page** — note the version + effective date. Compare to the stamp.
3. If the version moved, diff **Section 3 (format)**, **Section 4 (blueprint weights)**, and **Section 6
   (task statements)** against the "Official exam facts" block in `sources.md`. Reconcile any changed
   weights / added-removed task statements into that block **and** into `data/tutor-prompts.md` /
   `skills/dN-teacher/SKILL.md` (task-statement counts feed `learning-progress.json` `task_total`) **and**
   into `data/task-statements.json` (the `<d>.<n>` → label map that every bank `task` resolves against —
   keep its keys/labels in sync with the `tutor-prompts.md` headers, and its per-domain counts with
   `validate.py`'s `expected_ts_pd`). An added/removed statement also means re-tagging affected bank
   questions' `task` (classify+verify pass) — see `authoring-questions.md`.

## Step 2 — Layer 2: product docs (behavior — flags, hooks, MCP, tool_choice, Batch API)
Two parts:
- **Changelog scan** — fetch each **Layer 2** source in `sources.md` (Claude Code changelog, Platform
  release notes, GitHub releases, Help Center) and scan for entries **dated after** the stamp. Tag each
  relevant change with the domain it touches (**domain → source map** in `sources.md`). Ignore
  cosmetic/IDE fixes; keep changes touching tested concepts (flags, hooks, MCP config, `tool_choice`,
  Batch API, session state).
- **Fact-currency audit** — run the stored workflow (same opt-in as Step 3):
  ```
  Workflow({ scriptPath: "maintenance/fact-currency-audit.workflow.js",
             args: { root: "<absolute repo path>", guide: "<absolute exam_guide.pdf path>" } })
  ```
  Per domain it extracts the falsifiable technical facts from the bank + lessons and verifies each
  against current official docs, returning `current` / `stale` / `unverifiable` with evidence. A `stale`
  finding means the content contradicts **both** current docs **and** the Guide — a genuine error to
  fix. A fact that matches the Guide but the product changed later is `current` for the exam — record it
  under "Known exam-vs-product divergences" in `sources.md`, **do not edit the content**.

## Step 3 — Audit bank coverage (stored workflow)
Run the stored coverage audit — it maps every bank question to the official task statements and checks the
guide's sample questions, **report-only (no edits)**. In Claude Code, from this repo, ask to run it (the
Workflow tool needs an explicit opt-in — say "run the coverage-audit workflow"):

```
Workflow({
  scriptPath: "maintenance/bank-coverage-audit.workflow.js",
  args: { root: "<absolute path to this repo>",
          guide: "<absolute path to the downloaded exam_guide.pdf>" }
})
```

It returns, per domain: each task statement's covered question ids + a `good`/`thin`/`none` verdict, plus
any `orphan` questions and a sample-question check (`missing_count`). Read the result and decide what (if
anything) to reinforce. **Note:** "orphan" flags are advisory — many are intentional cross-domain
**axis-1 (Determinism)** questions (a config-lever scenario whose real answer is a hook); do not
re-domain them without judgment. See `data/axes.md`.

## Step 4 — Apply changes (only if drift found)
- **Blueprint/task-statement drift** → reconcile `sources.md` "Official exam facts" + the affected
  `tutor-prompts.md` / tutor SKILLs **and `data/task-statements.json`** (keep it in sync with the
  `tutor-prompts.md` headers; a count change also means updating `validate.py`'s `expected_ts_pd`) by hand.
- **Behavior drift, or thin coverage** → run the **bank-extension workflow** documented in the root
  `CLAUDE.md` (extract → classify domain → dedupe → assign ids + `axis` + `task` → `python3 data/validate.py`
  → bump `meta`). New questions append at the end; never renumber. Assign each new question its canonical
  `task` (a `<d>.<n>` key from `task-statements.json`) — `validate.py` fails without it. **Then** run
  `python3 maintenance/reference-coverage.py` and add `quick-reference.json` rows for any flagged
  unreferenced criteria (curated `see`/`answer`; hand-pick `q_ids`).
- **Lesson/trap drift** → edit `data/tutor-prompts.md` / `data/exam-traps.md` / `data/axes.md`.
  `exam-traps.md` is the **source** for `quick-reference.json` — when a core rule there changes, update
  the matching Reference row so the see→answer projection doesn't drift.

## Step 5 — Close out (always)
1. Update the three **"Last verified"** lines in `maintenance/sources.md` (Exam Guide version, docs-checked
   date, content-built date).
2. Add a dated entry to the root **`CHANGELOG.md`** — what you checked, what changed, what you edited (or
   "no changes; verified current").
3. Bump the plugin **version** (`.claude-plugin/plugin.json` + `.claude-plugin/marketplace.json`)
   **only if shipped content changed** (bank / skills / lessons / app). A "verified current, no change"
   review updates the stamp + CHANGELOG but does **not** bump the version (nothing shipped changed).
4. If the bank changed, run `python3 data/validate.py` and confirm it passes, then
   `python3 maintenance/reference-coverage.py` to confirm no new criteria are left unreferenced.

## Known follow-ups (open)
- **Multiple-response items:** the exam has multi-select questions; the bank + app are single-answer only.
  Adding support touches `questions.json` schema, the app grader (`data/app-template.html`), and
  `data/validate.py`. Tracked but not yet done.
