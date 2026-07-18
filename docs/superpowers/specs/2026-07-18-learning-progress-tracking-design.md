# CCAF — Learning-Progress Tracking (design spec)

**Date:** 2026-07-18
**Status:** Approved design — ready for implementation planning
**Plugin version at design time:** 0.6.6

## Problem

The plugin persists **exam results** (`stats.json` via `/ccaf:result`) and **missed
questions / trap patterns** (`fails-tracker.md`, `trap-log.md`), but nothing captures the
**learning process** itself:

- which task statements (e.g. 4.1–4.6) a learner has actually worked through with a tutor;
- the score of the in-tutor 8-question domain drill (distinct from mock/official exams);
- when each domain was last studied;
- per-axis *mastery* (where the learner reliably recognises a trap), as opposed to the
  misses-only `axis_tally` already in `stats.json`.

Teacher sessions are stateless: their progress lives only in the chat and is lost on `/clear`.

## Goal

Add durable **learning-progress tracking** — task-statement coverage, in-tutor drill scores,
last-visited per domain, and per-axis mastery — written by the domain tutors at hand-off, and
surfaced both as chat text in `/ccaf:init` and as a **dashboard card in the HTML study app**
(`/ccaf:stats`).

Non-goals: changing what `stats.json` / `/ccaf:result` do; tracking anything for the
`/ccaf:exam` app sittings (already covered); a separate `/ccaf:progress` command (rejected).

## Scope decisions (locked with the user)

- **Track:** covered task statements · in-tutor drill scores (with date) · last-visited per
  domain · per-axis mastery (seen/correct, not just misses). (All four.)
- **Write + display mechanism:** each `dN-teacher` writes at hand-off into a **new
  `learning-progress.json`**; displayed in `/ccaf:stats` and `/ccaf:init`. (Not a new command;
  not merged into `stats.json`.)
- **Display depth:** approach **B** — textual in `/ccaf:init` **and** a new card injected into
  the HTML dashboard (touches `app-build.md` + `app-template.html`).

## Data model — `learning-progress.json`

Lives in `~/.claude/ccaf-progress/`; shipped as `data/progress-template/learning-progress.json`.
Existing stores pick it up automatically because Step-0 bootstrap uses `cp -rn`, which copies
**missing** files without overwriting existing ones.

```json
{
  "schema": 1,
  "domains": {
    "1": { "status": "not_started", "last_visited": null, "task_total": null, "task_statements": {}, "drills": [] },
    "2": { "status": "not_started", "last_visited": null, "task_total": null, "task_statements": {}, "drills": [] },
    "3": { "status": "not_started", "last_visited": null, "task_total": null, "task_statements": {}, "drills": [] },
    "4": { "status": "not_started", "last_visited": null, "task_total": null, "task_statements": {}, "drills": [] },
    "5": { "status": "not_started", "last_visited": null, "task_total": null, "task_statements": {}, "drills": [] }
  },
  "axis_mastery": {
    "1": { "seen": 0, "correct": 0 },
    "2": { "seen": 0, "correct": 0 },
    "3": { "seen": 0, "correct": 0 },
    "4": { "seen": 0, "correct": 0 },
    "5": { "seen": 0, "correct": 0 }
  }
}
```

Field semantics:
- `domains[d].task_total` — number of task statements in that domain; the tutor knows its own
  set (D4 = 6: 4.1–4.6) and writes it. Avoids hardcoding domain sizes in the app.
- `domains[d].task_statements[<id>]` — `{ "covered": true, "ts": "<YYYY-MM-DD>" }`. A task
  statement is marked ONLY when it was fully taught **and** its check-question was attempted.
- `domains[d].drills[]` — `{ "ts": "<YYYY-MM-DD>", "score": <int>, "total": <int> }`, one entry
  per 8-question in-tutor domain exam taken.
- `domains[d].last_visited` — `YYYY-MM-DD` of the most recent tutor session for that domain.
- `domains[d].status` — derived: `complete` when `len(covered) == task_total` **and** the most
  recent drill passed (`score/total >= 7/8`); else `in_progress` once any activity exists; else
  `not_started`.
- `axis_mastery[a]` — cumulative `seen`/`correct` over check-questions and drill questions whose
  axis is known, across all domains. Complements the misses-only `stats.json.axis_tally`.

Timestamps: tutors run as an interactive LLM turn and know the session date from context; they
stamp `ts` as `YYYY-MM-DD` best-effort. (The Python app-builder has no clock — see below — but
it only *reads* this file, so that's fine.)

## Write path — tutors (at hand-off)

Add a shared **"Recording learning progress"** section to `data/teaching-method.md` (the file
that defines HOW every tutor teaches). Contract, performed at hand-off BEFORE suggesting the
next command:

1. Ensure the store + file exist (Step-0 `cp -rn` already handles first-run bootstrap).
2. **Read** `learning-progress.json`, **modify only this domain's** entry, **write** it back
   (read-modify-write; never clobber other domains or `axis_mastery` from a stale copy).
3. Set `last_visited = <today>`; set `task_total` = this domain's task-statement count.
4. For each task statement fully taught + checked this session, set
   `task_statements[<id>] = {covered:true, ts:<today>}`.
5. If the 8-question domain drill was taken, append `{ts, score, total}` to `drills`.
6. Increment `axis_mastery[a].seen` (and `.correct` when right) for every check-question /
   drill question whose axis is known.
7. Recompute `status`. Write valid JSON (no trailing commas).

Each `skills/dN-teacher/SKILL.md` gets a one-line reference in its Hand-off step pointing to the
shared contract (mirrors how the existing "Step 4 — Log new fails" works).

## Display path

### `/ccaf:init` (`commands/init.md`)
After the existing bank/stats summary, read `learning-progress.json` and print a per-domain
line — `D4: task statements 2/6 · last drill 8/8 · last visited 2026-07-18` — plus a one-line
`axis_mastery` summary (correct/seen per axis). If the file is missing/empty, say so plainly
(never fabricate). Reads only; does not write.

### `/ccaf:stats` (HTML dashboard) — approach B
- **`data/app-build.md`**: the Python builder loads `learning-progress.json` (default skeleton
  if absent) and adds it to the injected `HISTORY` object as `HISTORY.learning`. Existing
  `js_safe()` escaping applies unchanged.
- **`data/app-template.html`**: render a new **"Learning progress"** dashboard card from
  `HISTORY.learning`:
  - per-domain progress bars: covered task statements / `task_total`, `status` chip, latest
    drill score, `last_visited`;
  - an `axis_mastery` mini-view (correct/seen per axis) placed beside the existing misses-based
    5-axis tally, so "where I'm confident" and "where I miss" read together.
  - Keep the `/*__BANK__*/[]` and `/*__HISTORY__*/{}` placeholders valid as empty literals.
  - Degrade gracefully when `HISTORY.learning` is absent or all-`not_started`.

## Files touched

| File | Change |
|---|---|
| `data/progress-template/learning-progress.json` | **new** — initial skeleton |
| `data/teaching-method.md` | **new section** — "Recording learning progress" write contract |
| `skills/d1-teacher/SKILL.md` … `d5-teacher/SKILL.md` | one-line Hand-off reference to the contract |
| `data/app-build.md` | load `learning-progress.json` → `HISTORY.learning` |
| `data/app-template.html` | new "Learning progress" dashboard card |
| `skills/stats/SKILL.md` | mention the new card (build recipe is shared, so mostly no logic change) |
| `commands/init.md` | print learning-progress summary |
| `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` | version bump |

## Invariants preserved (from plugin maintainer `CLAUDE.md`)

1. Progress lives only in `~/.claude/ccaf-progress/`, never in the plugin dir.
2. `cp -rn` bootstrap never overwrites existing files (new template file is additive).
3. `disable-model-invocation: true` untouched on all skills/commands.
4. No skill→skill calls — tutors write; `init`/`stats` read & display; hand-offs stay as
   *instructions* to the user.
5. `learning-progress.json` is separate from the authoritative `stats.json`; `/ccaf:result`
   remains the single recorder of exam results and does not touch learning-progress.
6. One app file, overwritten each build; two placeholders stay valid empty literals.
7. Bump plugin version after changes so teachers/app pick them up.

## Testing / acceptance

- Fresh store: Step-0 bootstrap creates `learning-progress.json` from template; an existing
  store (without the file) gains it via `cp -rn` without losing other files.
- After a `dN-teacher` hand-off: the domain's `task_statements`, `drills`, `last_visited`,
  `status`, and `axis_mastery` reflect the session; other domains' data is untouched.
- `/ccaf:init` prints an accurate per-domain summary (and says so plainly when empty).
- `/ccaf:stats` opens the app with a populated "Learning progress" card; placeholders resolved;
  no console errors; graceful when learning data is absent.
- JSON written by tutors is valid (no trailing commas); malformed input is never produced.

## Open follow-ups (out of scope here)

- Optional: extend `data/validate.py` to sanity-check the learning-progress template shape.
- Optional: spaced-repetition nudges in `/ccaf:init` driven by `last_visited`.
