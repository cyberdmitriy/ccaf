# Shared build recipe — the CCAF study app (`ccaf-exam.html`)

`/ccaf:dashboard` (and `/ccaf:init`) build the **same** self-contained offline app from
`app-template.html` + the user's progress store, then open it. This file is the single source of
truth for that build so the two skills stay in sync. Follow it verbatim.

> **ALWAYS REBUILD — never open a stale file.** `ccaf-exam.html` is a disposable build artifact.
> On **every** `/ccaf:dashboard` (and `/ccaf:init`), run Steps 1–4 in full and **overwrite** any existing
> `ccaf-exam.html`. **Do NOT** shortcut to `open`-ing a pre-existing `ccaf-exam.html` because "the
> file already exists" — a stale file silently hides newly-recorded history and new app features
> (this is exactly how a new tab/view appears "missing" after a plugin update). Running the build is
> read-only w.r.t. the store, so there is never a reason to skip it. If the build errors, surface the
> error — do not fall back to opening the old file.

The app is one page with four client-side views: **Dashboard** (progress + history), **New exam**
(mode/domain/length selection), **Exam** (timer, pause/resume, resume-later), **Results** (score +
annotated review + copy-JSON export). All logic is client-side JS. The whole question bank
(including answer keys) is injected; scoring and selection happen in the browser.

## Step 1 — Bootstrap the per-user store (never overwrite)
```
mkdir -p "$HOME/.claude/ccaf-progress" && cp -rn "${CLAUDE_PLUGIN_ROOT}/data/progress-template/." "$HOME/.claude/ccaf-progress/"
```

## Step 2 — Personalisation is automatic
There is nothing to fill in by hand. The script below **reads `profile.md` itself** and parses the
explicit **Focus domains** section (a list like `D3, D4`); that overrides the accuracy-derived default.
If the section is unset/empty it falls back to the two lowest-accuracy domains with data, else none —
it never invents focus.

## Step 3 — Build & open with one deterministic script
Do NOT hand-copy the bank or hand-edit the template. Run this **one** command — the build logic lives
in `data/build-app.py` (the single source of truth, also run by the `UserPromptSubmit` hook). It
bootstraps the store, reads the bank + `stats.json` + `profile.md`, composes the authoritative
`HISTORY`, injects all three placeholders (bank, history, reference), writes `ccaf-exam.html`, and
opens it (`--open` opens only in an interactive terminal, so headless/`-p` runs never block on a GUI):

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/data/build-app.py" --open
```

If it prints the path but no window appears (e.g. a remote/headless session), tell the user to open
`$HOME/.claude/ccaf-progress/ccaf-exam.html` manually.

## Notes / invariants
- **Single file, overwritten** each build (`ccaf-exam.html`). No per-exam files, no archive.
- The app **never** writes to the store — it holds in-progress + unrecorded sittings in
  `localStorage` and hands results back via copy-JSON for `/ccaf:result` to record.
- Unrecorded sittings are reconciled on the next build via `recorded_exam_ids` (the page drops any
  local sitting whose `exam_id` is already recorded), so nothing is double-counted.
- Focus is **data-driven** (profile's explicit list, else lowest-accuracy domains) — never hardcode
  a person's results.
