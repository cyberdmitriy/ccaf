# CCAF plugin — Maintenance Runbook (periodic content review)

**Audience:** the plugin maintainer, working **inside this repo** (not an end user of the installed
plugin). This is the procedure for keeping the plugin current with the official exam and docs. Run it
**every 6–12 months**, or whenever you hear the Exam Guide or Claude Code/API behavior has changed.

It is deliberately **not** a shipped slash command — the review can edit skills, `teaching-method.md`,
lessons, and the question bank, which is maintainer work, not something an installed user should do.

Everything this runbook consults lives in `maintenance/`:
- `sources.md` — authoritative-source list + **"Last verified"** stamp + the official blueprint/task
  statements copied from the Exam Guide.
- `bank-coverage-audit.workflow.js` — the stored multi-agent audit (below).

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
   `skills/dN-teacher/SKILL.md` (task-statement counts feed `learning-progress.json` `task_total`).

## Step 2 — Layer 2: product docs (behavior — flags, hooks, MCP, tool_choice, Batch API)
Fetch each **Layer 2** source in `sources.md` (Claude Code changelog, Platform release notes, GitHub
releases, Help Center) and scan for entries **dated after** the stamp. Tag each relevant change with the
domain it touches using the **domain → source map** in `sources.md`. Ignore cosmetic/IDE fixes; keep
changes that touch tested concepts (flags, hooks, MCP config, `tool_choice`, Batch API, session state).

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
  `tutor-prompts.md` / tutor SKILLs by hand.
- **Behavior drift, or thin coverage** → run the **bank-extension workflow** documented in the root
  `CLAUDE.md` (extract → classify domain → dedupe → assign ids + `axis` → `python3 data/validate.py`
  → bump `meta`). New questions append at the end; never renumber.
- **Lesson/trap drift** → edit `data/tutor-prompts.md` / `data/exam-traps.md` / `data/axes.md`.

## Step 5 — Close out (always)
1. Update the three **"Last verified"** lines in `maintenance/sources.md` (Exam Guide version, docs-checked
   date, content-built date).
2. Add a dated entry to the root **`CHANGELOG.md`** — what you checked, what changed, what you edited (or
   "no changes; verified current").
3. Bump the plugin **version** in `.claude-plugin/plugin.json` + `.claude-plugin/marketplace.json`.
4. If the bank changed, run `python3 data/validate.py` and confirm it passes.

## Known follow-ups (open)
- **Multiple-response items:** the exam has multi-select questions; the bank + app are single-answer only.
  Adding support touches `questions.json` schema, the app grader (`data/app-template.html`), and
  `data/validate.py`. Tracked but not yet done.
