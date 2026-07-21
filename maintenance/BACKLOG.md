# Maintenance backlog — known gaps & deferred work

Maintainer-only. Not shipped runtime; no skill reads this. Track here anything we consciously
deferred so we don't forget where to look when we come back to fix it. Newest first. When an item
ships, move it to `CHANGELOG.md` and delete it here.

---

## OPEN — Deterministic write for tutor learning progress

**Logged:** 2026-07-20 · **Updated:** 2026-07-21 · **Priority:** low-medium · **Owner:** unassigned

> The **app-rebuild** half of this item shipped in **0.14.0**: `data/build-app.py` (one deterministic
> bootstrap→build→open) + a `UserPromptSubmit` hook (`hooks/ccaf-build.sh`) that runs it on
> `/ccaf:init` and `/ccaf:dashboard`, so a stale `ccaf-exam.html` can no longer hide new views/stats
> after a plugin update. What remains open is the tutor-progress write below.

**Problem.** Tutor learning progress can still be lost — `teaching-method.md`'s recording contract is
prose the model is asked to follow (write `learning-progress.json` incrementally per task statement).
A session that ends before the checkpoint, or a mis-serialised hand-authored JSON, persists nothing.
This is a **model-executed instruction** with no runtime enforcement.

**Shipped mitigation (partial).** `data/teaching-method.md`: recording made **incremental** —
checkpoint after each task statement + a final hand-off flush (v0.10.2). Reduces but doesn't eliminate.

**Proposed hard fix (needs design discussion — God Rule #9: new mechanism).** The tutor's *judgement*
(what was truly taught + check-questioned) can't be mechanised, but the *write* can — ship a tiny
helper `mark-covered.py <domain> <task-id> [--drill s/t]` doing the safe read-modify-write, so the
teacher makes one deterministic call per lesson instead of hand-authoring JSON (what gets
skipped/mis-serialised). A hook can't help here (there's no per-lesson event to key off).

**Trade-offs.** Adds a shipped helper + a new failure surface. Decide if the reliability win is worth it.

**Status:** OPEN — awaiting decision on whether to build `mark-covered.py`.
