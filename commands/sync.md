---
name: sync
description: Check whether the plugin's study content is still current — fetches Anthropic's official Claude Code / API changelogs, reports what changed since the last verified date, and reminds you to grab the latest Exam Guide. Read-only; never edits the bank. Run /ccaf:sync.
disable-model-invocation: true
allowed-tools: WebFetch, WebSearch, Read
argument-hint: "(no arguments needed)"
---

# CCAF — Freshness Check (report-only)

The CCAF exam and the docs it tests both drift over time (new CLI flags, changed behavior, a new
**Exam Guide** version with different domain weights). This command surfaces that drift so the
maintainer can decide what to refresh. It is **read-only**: it fetches official docs and reports —
it **never edits `questions.json`, the lessons, or any progress file**, and it does not invoke other
skills. Manual only.

## Step 1 — Load the baseline
Read `${CLAUDE_PLUGIN_ROOT}/data/sources.md`. It holds the authoritative-source list, the domain→source
map, and the **"Last verified"** stamp (Exam Guide version + date, and the date the product docs were
last checked). Everything below compares upstream against that stamp. Echo the stamp to the user first
so they know the baseline.

## Step 2 — Fetch the public docs (Layer 2 — fetchable)
Using WebFetch, pull each **Layer 2** source in `sources.md` and extract entries **dated after the
"product docs checked" date** in the stamp:
- `https://code.claude.com/docs/en/changelog` — Claude Code (D2/D3: CLI flags, hooks, slash commands, plan mode, CI/CD).
- `https://platform.claude.com/docs/en/release-notes/overview` — Platform/API (D2/D4: tool_use, `tool_choice`, Message Batches API, MCP).
- `https://github.com/anthropics/claude-code/releases` — GitHub releases (fallback / often fresher).
- `https://support.claude.com/en/articles/12138966-release-notes` — product-wide release notes.

If a fetch fails or WebFetch/WebSearch is unavailable in this session, say so plainly and **skip to
Step 4** — still print the source list + stamp + manual instructions. Do not fabricate changelog
entries; report only what you actually fetched.

## Step 3 — Diff & attribute to domains
For each change dated after the stamp, decide whether it plausibly affects exam content, and tag it
with the domain(s) it touches using the **domain→source map** in `sources.md` (e.g. a new `--output-format`
flag → **D3**; a `tool_choice`/Batch-API change → **D2/D4**; a hooks/subagent change → **D1**). Prefer
changes that touch concepts the bank tests (from `exam-traps.md` / `axes.md` themes); ignore pure
cosmetic/IDE fixes. Keep it short — a bulleted "since <date>" list, newest first, each line:
`<date> · D<n> · <what changed> · <source>`. If nothing relevant changed, say "no exam-relevant changes since <date>".

## Step 4 — Exam Guide reminder (Layer 1 — GATED, cannot fetch)
The official **Exam Guide** (blueprint, domain weights, task statements) lives behind the **Anthropic
Partner Academy** login and **cannot be fetched here**. Remind the user to:
- download the current Exam Guide from Partner Academy and compare its **version** against the stamp in
  `sources.md` (stamp is v0.2 / 2026-06-30 unless updated);
- if the guide version is newer, the **domain weights or task statements may have shifted** — reconcile by hand.

## Step 5 — Report & next steps (write nothing)
Summarise: the baseline stamp, the "since <date>" change list (or "none"), and the Exam Guide reminder.
Then, only if drift was found, point the maintainer at the two refresh paths (do NOT perform them here):
- behavior changes → run the **bank-extension workflow** in `CLAUDE.md` (extract → classify → dedupe →
  assign ids + `axis` → `python3 data/validate.py` → version bump);
- blueprint changes → reconcile weights/task statements against the new Exam Guide, then update the
  **"Last verified"** lines in `data/sources.md` and bump the plugin version.

End there. This command reports; it never edits content, and it never auto-invokes another command.
