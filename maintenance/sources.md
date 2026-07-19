# CCAF — Sources of truth & freshness baseline

**Maintainer-only** reference (not shipped runtime data — no skill/command reads it). It holds the
**authoritative-source list**, a **last-verified stamp**, and the official blueprint/task-statements
copied from the Exam Guide. The periodic-review procedure in `maintenance/RUNBOOK.md` consults this
file and updates the stamp when content is refreshed.

Two layers: the **exam blueprint** (format, domains, weights, task statements) changes only when
Anthropic publishes a new **Exam Guide** version — that guide is **publicly downloadable** (see Layer 1),
so it can be checked directly. The **technical behavior** the exam tests (CLI flags, hooks, MCP,
`tool_choice`, Batch API, …) lives in **public product docs** that update continuously.

## Last verified (against the official Exam Guide, primary source)
- **Exam Guide:** **v1.0 · Effective July 2026 · exam code CCAR-F** (title page). "Subject to change
  without notice." Verified against the PDF on 2026-07-18.
- **Product docs / changelogs checked:** 2026-07-19 (Layer-2 fact-currency audit — 0 stale facts across all 5 domains).
- **Bundled content built/last-synced:** 2026-07-18 (bank = 240 questions).

> When you refresh content against the sources below, bump these lines and the plugin version.

## Official exam facts (from Exam Guide v1.0 — authoritative, copy exactly)
- **Format:** 60 items · **multiple-choice AND multiple-response** (each item states how many responses
  to select) · **4 scenarios drawn from a bank of 6** · 120 minutes · proctored (online and/or test
  center) · scaled **720 / 100–1000** to pass · $125 USD · valid 12 months · result = pass/fail +
  percent-correct by domain.
- **Blueprint weights:** **D1 27% · D2 18% · D3 20% · D4 20% · D5 15%** (matches the plugin).
- **Task statements (30 total)** — the exam items are written against these:
  - **D1 Agentic Architecture & Orchestration (7):** 1.1 agentic loops · 1.2 coordinator–subagent
    orchestration · 1.3 subagent invocation/context/spawning · 1.4 multi-step workflows with
    enforcement & handoff · 1.5 Agent SDK hooks (interception & data normalization) · 1.6 task
    decomposition strategies · 1.7 session state (resume/fork).
  - **D2 Tool Design & MCP Integration (5):** 2.1 tool interfaces/descriptions · 2.2 structured error
    responses · 2.3 tool distribution & `tool_choice` · 2.4 MCP server integration · 2.5 built-in tools.
  - **D3 Claude Code Configuration & Workflows (6):** 3.1 CLAUDE.md hierarchy/scoping · 3.2 slash
    commands & skills · 3.3 path-specific `.claude/rules` · 3.4 plan mode vs direct · 3.5 iterative
    refinement · 3.6 CI/CD integration.
  - **D4 Prompt Engineering & Structured Output (6):** 4.1 explicit criteria · 4.2 few-shot · 4.3
    tool_use + JSON schemas · 4.4 validation/retry/feedback · 4.5 Batch API · 4.6 multi-instance /
    multi-pass review.
  - **D5 Context Management & Reliability (6):** 5.1 context preservation · 5.2 escalation & ambiguity ·
    5.3 error propagation · 5.4 context in large-codebase exploration · 5.5 human review & confidence
    calibration · 5.6 provenance & uncertainty in synthesis.
- These per-domain counts are the authoritative `task_total` the `dN-teacher` tutors should write into
  `learning-progress.json`: **D1=7 · D2=5 · D3=6 · D4=6 · D5=6**.

> ⚠️ **Known fidelity gap:** the exam has **multiple-response** items, but the bundled bank
> (`questions.json`) is **single-answer only** (`correct` = one letter A–D) and the mock app grades
> single-select. Multi-select is currently untrained. Tracked as a follow-up (would touch the schema,
> the app grader, and `validate.py`).

### Known exam-vs-product divergences — DO NOT "fix" these
The exam is closed-book against **Exam Guide v1.0 (July 2026)**, a point-in-time snapshot. In a few
spots the live product has since moved past the Guide. The bundled content deliberately follows the
**Guide** (that is what the exam tests), so these look "wrong" against today's docs but are **correct
for the exam** — do not edit them to match current docs:
- **`allowed-tools` skill frontmatter** — the Guide (task 3.2) frames it as **restricting** tool access
  during skill execution; current Claude Code docs say `allowed-tools` *grants* pre-approval and does
  **not** restrict (use `disallowed-tools` to restrict). Content follows the Guide. (bank q94; tutor 3.2)
- **`/memory` command** — the Guide (task 3.1) says `/memory` shows **which memory files are loaded**;
  current docs route "which actually loaded" to `/context` and describe `/memory` as listing file
  locations + toggling auto-memory. Content follows the Guide. (bank q201; tutor 3.1)
Re-evaluate each only when a **new Exam Guide version** changes the framing (Layer-1 review).

## Layer 1 — Exam blueprint (PUBLIC · downloadable, checkable directly)
The single authoritative source for the blueprint, domain weights, and task statements. Always
**download the current Exam Guide before booking** — weights/wording shift between versions.
- **Exam Guide landing (stable, fetchable):**
  https://anthropic-partners.skilljar.com/claude-certified-architect-foundations-certification
  — carries the current **Exam Guide PDF** download link (the PDF's title page states the version).
- Direct PDF link is an S3 URL generated by that page (may rotate) — get it fresh from the landing page,
  don't hardcode it.
- Pearson VUE — Anthropic certification program (registration/scheduling):
  https://www.pearsonvue.com/us/en/anthropic.html
- Public overview mirrors (unofficial, quick sanity-check only, NOT authoritative):
  https://claudecertifications.com/claude-certified-architect · .../domains

## Layer 2 — Technical behavior (PUBLIC · fetchable during review)
Official product docs the exam is built on. During a review (see `RUNBOOK.md`), fetch these and check
for entries dated after the "Last verified" stamp above.
- **Claude Code changelog** (D2/D3 — CLI flags, hooks, slash commands, plan mode, CI/CD):
  https://code.claude.com/docs/en/changelog
- **Claude Code releases (GitHub)** (same, sometimes fresher):
  https://github.com/anthropics/claude-code/releases
- **Claude Platform / API release notes** (D2/D4 — tool use, `tool_choice`, Message Batches API, MCP):
  https://platform.claude.com/docs/en/release-notes/overview
- **Claude Help Center release notes** (product-wide):
  https://support.claude.com/en/articles/12138966-release-notes

## Domain → source map (where a change most likely lands)
- **D1 Agentic Architecture** — Agent SDK docs + Claude Code changelog (hooks, subagents, sessions).
- **D2 Tool Design & MCP** — Platform release notes (tool_use, tool_choice) + Claude Code changelog (built-ins, MCP config).
- **D3 Config & Workflows** — Claude Code changelog (CLI flags, CLAUDE.md, rules, plan mode, `-p`/`--output-format`).
- **D4 Prompt Eng & Structured Output** — Platform release notes (Batch API, JSON-schema tool output).
- **D5 Context & Reliability** — Platform release notes + Claude Code changelog (context/session behavior).

## What to do when something changed
The review is a maintainer task (see `RUNBOOK.md`) — it may edit the bank, skills, or lessons. When a
review finds drift:
1. Re-download the latest **Exam Guide** from the Layer-1 landing page; if the version > the stamp above,
   reconcile blueprint weights / task statements by hand (and update the "Official exam facts" block here).
2. For behavior changes, run the **bank-extension workflow** in `CLAUDE.md` (extract → classify →
   dedupe → assign ids/axis → `python3 data/validate.py` → version bump).
3. Update the "Last verified" lines here, add a CHANGELOG entry, and bump the plugin version.
