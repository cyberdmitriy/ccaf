# Maintenance backlog — known gaps & deferred work

Maintainer-only. Not shipped runtime; no skill reads this. Track here anything we consciously
deferred so we don't forget where to look when we come back to fix it. Newest first. When an item
ships, move it to `CHANGELOG.md` and delete it here.

---

## OPEN — Hard runtime guarantee for model-executed determinism (app rebuild + tutor progress)

**Logged:** 2026-07-20 · **Priority:** medium · **Owner:** unassigned

**Problem.** Two failures the learner hit, same underlying cause:
1. `/ccaf:dashboard` **opened a stale `ccaf-exam.html`** instead of rebuilding it, so a new view
   (Cheatsheet) appeared "missing" after a plugin update. (Proof: the store's `cheatsheet.json`
   was never even bootstrapped, so Steps 1–4 of `app-build.md` never ran.)
2. **Tutor learning progress was lost** — `teaching-method.md`'s recording contract wrote
   `learning-progress.json` only at hand-off, so a session that ended before hand-off (D3, covered
   3.1–3.2) persisted nothing.

**Root cause (shared).** Both are **model-executed instructions** — the `/ccaf:*` skills and the
`app-build.md` / `teaching-method.md` recipes are prose the model is asked to follow. There is **no
runtime enforcement**: the model can skip the build step or the checkpoint step and nothing catches
it. This is architectural, not a bug in any one file.

**Shipped mitigation (partial — instruction hardening only).**
- `data/app-build.md` + `skills/{exam,stats}/SKILL.md`: explicit "ALWAYS REBUILD — never open a
  stale file" directive (v0.10.1).
- `data/teaching-method.md`: recording contract made **incremental** — checkpoint after each task
  statement + a final hand-off flush (v0.10.2).
These reduce recurrence but **do not eliminate** it — a model can still ignore prose.

**Proposed hard fix (needs design discussion before building — God Rule #9: new mechanism).**
- **Rebuild determinism:** ship a single wrapper script (e.g. `data/build-app.sh`) that does
  bootstrap → build → open in one deterministic call, and have the `exam`/`stats` skills invoke
  *that one command* instead of a multi-step recipe the model can partially execute. Or a
  command/PreToolUse hook that regenerates `ccaf-exam.html` whenever `/ccaf:dashboard` or `/ccaf:dashboard`
  is invoked.
- **Progress persistence:** the tutor's *judgement* (what was truly taught + check-questioned)
  can't be fully mechanised, but the *write* can — ship a tiny helper (e.g.
  `mark-covered.py <domain> <task-id> [--drill s/t]`) that performs the safe read-modify-write, so
  the teacher makes a single deterministic call per lesson instead of hand-authoring JSON (which is
  what gets skipped/mis-serialised).

**Trade-offs.** Adds shipped moving parts (a script and/or a hook) and a new failure surface;
heavier than the current "model follows the recipe" design. Decide whether the reliability win is
worth the added mechanism before implementing.

**Status:** OPEN — awaiting decision on whether to build the wrapper/hook.
