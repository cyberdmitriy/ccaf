# CCAF — Exam Traps (from claudecertificationguide.com)

Verbatim "Exam Trap" callouts + core rule for all 32 lessons across the 5 domains
(D1 7 · D2 6 · D3 7 · D4 6 · D5 6). These are the study guide's **lessons**, not the official
blueprint's 30 **task statements** (D1 7 · D2 5 · D3 6 · D4 6 · D5 6 — see `maintenance/sources.md`),
so the two counts differ on purpose.
Source: https://claudecertificationguide.com/learn (scanned 2026-07). **Focus domains from official fail: D3 (59%) and D4 (57%).**

How to use with `trap-log.md`: each trap below maps to one of the 5 axes —
**1 Determinism · 2 Exact hit · 3 Right diagnosis · 4 Proportionality · 5 Root-cause/antipattern.**

---

## Domain 1 — Agentic Architecture & Orchestration (27%)

### 1.1 Agentic Loops
**Exam Traps:**
- Using `response.content[0].type == 'text'` to determine loop completion — Claude can return text alongside tool_use blocks. Text presence ≠ completion.
- Setting arbitrary iteration caps (e.g. "stop after 10 loops") as the primary stopping mechanism.
- Parsing natural-language phrases like "I'm done" / "task complete" to decide termination.
- Forcing `tool_choice: 'any'` to prevent the agent returning text — creates infinite loops.

**Core rule:** Stop on the `stop_reason` field. Never stop on text presence, an iteration cap, a natural-language phrase, or a forced `tool_choice`.

### 1.2 Multi-Agent Orchestration
**Exam Traps:**
- Blaming downstream subagents for coverage gaps when the coordinator's decomposition was too narrow.
- Assuming subagents share memory or inherit the coordinator's conversation history.
- Proposing direct inter-subagent communication as an efficiency improvement.
- Adding more subagents to fix a decomposition problem.

**Core rule:** The coordinator's decomposition sets the coverage. Subagents are isolated and talk only through the coordinator. Fix the decomposition. Do not add agents or wire them to each other.

### 1.3 Subagent Invocation and Context Passing
**Exam Traps:**
- Assuming subagents auto-access the coordinator's history or other subagents' outputs.
- Blaming the synthesis agent for missing citations when the real issue is context passing without metadata.
- Proposing sequential invocation for tasks that can run independently (use parallel Task calls in one response).
- Confusing `fork_session` with `--resume`.

**Core rule:** A subagent gets only what the coordinator passes it, metadata included. Pass the full context, and run independent work in parallel.

### 1.4 Workflow Enforcement and Handoff
**Exam Traps:**
- Enhanced system-prompt instructions as the fix for high-stakes compliance failures (a stronger prompt drops 8%→3-4%, never 0%).
- Few-shot examples as sufficient for guaranteed compliance (still probabilistic).
- Routing classifiers to fix per-agent compliance (failure is within the agent sequence, not routing).
- Handoff summaries that omit critical fields (customer ID, recommended action) — the human can't see the transcript.

**Core rule:** High-stakes compliance needs deterministic enforcement, not prompts, few-shot or routing. Every handoff must carry every critical field.

### 1.5 Agent SDK Hooks
**Exam Traps:**
- Using PostToolUse hooks to *block* policy-violating actions — too late, action already ran. Use **PreToolUse** to block.
- Enhanced prompt instructions for 100% compliance — prompts are probabilistic; only hooks give deterministic guarantees.
- Model-side data transformation instead of PostToolUse hooks for normalisation — model normalisation is inconsistent.
- Confusing hook direction — PreToolUse blocks *before*, PostToolUse transforms *after*.

**Core rule:** PreToolUse blocks before the action runs. PostToolUse normalises after it. Only hooks enforce 100%. Prompts never do.

### 1.6 Task Decomposition Strategies
**Exam Traps:**
- A more powerful model / larger context window as the fix for attention dilution (it's architectural, not capability).
- Single-pass review with better prompts as equivalent to multi-pass (better prompts ≠ fixing attention allocation).
- Fixed pipelines for open-ended investigation (open-ended needs adaptability).
- Batching files without a cross-file integration pass (misses cross-batch issues).

**Core rule:** Attention dilution needs multi-pass decomposition, a cross-batch integration pass, and flows that adapt. A bigger model, prompt or window does not fix it.

### 1.7 Session State and Resumption
**Exam Traps:**
- Full re-exploration of a 50-file codebase when only 3 files changed (inform agent of the 3; reuse prior summary).
- `--resume` after files modified — preserves stale tool results → reasoning from outdated contents.
- Confusing `fork_session` (divergent branches) with `--resume` (continuation).
- Using `fork_session` for stale context after file changes — the fork inherits stale results.

**Core rule:** After files change, start a fresh session and inject a summary. Do not use `--resume` or `fork_session`. `--resume` continues a session, `fork_session` branches off to explore.

---

## Domain 2 — Tool Design & MCP Integration (18%)

### 2.1 Tool Interface Design
**Exam Traps:**
- Few-shot examples to fix tool misrouting caused by minimal descriptions.
- A routing classifier as the first step to fix tool selection.
- Consolidating similar tools into one as the first step.
- Ignoring system-prompt wording after updating tool descriptions.

**Core rule:** Claude picks tools from their descriptions. Improve the descriptions first.

### 2.2 Structured Error Responses
**Exam Traps:**
- Retrying when a tool returns an empty result from a *successful* query.
- Generic messages like "Operation failed" without structured metadata.
- Treating business errors as retryable.
- Silently suppressing subagent errors by returning empty results as success.

**Core rule:** Structured error fields (`errorCategory`, `isRetryable`, `description`) let the agent pick the right recovery. Uniform retries cannot.

### 2.3 Tool Distribution & Tool Choice
**Exam Traps:**
- Routing all simple verification through the coordinator when 85% are simple lookups.
- `tool_choice: 'auto'` when structured output is required.
- Giving an agent 18 tools and expecting reliable selection.
- Giving a subagent a generic `fetch_url` when a constrained `load_document` would suffice.

**Core rule:** Give each agent about 4 or 5 tools for its own role, and scope down the tools that cross roles. That keeps selection reliable and latency low.

### 2.4 MCP Server Integration
**Exam Traps:**
- Building a custom MCP server for a standard integration like Jira.
- Team-wide MCP config in `~/.claude.json` (that's user-level/personal).
- Committing credentials in `.mcp.json` instead of env-var expansion.
- Sparse MCP tool descriptions → agent prefers built-in tools.

**Core rule:** A project `.mcp.json` serves the whole team. A user `~/.claude.json` is personal. Keep secrets in `${VAR}` expansion.

### 2.5 Built-in Tools
**Exam Traps:**
- Using Glob to find function callers (Glob searches *paths*, not contents).
- Using Grep to find files by extension/naming pattern.
- Reading all source files upfront before knowing what's relevant.
- Defaulting to Read + Write for every modification instead of trying Edit first.
- Jumping to Read + Write the moment Edit reports a non-unique match (widen context first).

**Core rule:** Grep searches contents. Glob matches paths. Try Edit first, and widen the context before you fall back to Read plus Write.

### 2.6 MCP Tool Search & Protocol Mechanics
**Exam Traps:**
- "All tool definitions load into context at connection time" — the OLD behaviour; with tool search on (default) only names + server instructions load, full schemas are deferred/on-demand.
- Confusing discovery (which tools exist — always happens at connect) with loading definitions into context (deferred).
- Exposing read-only data as a tool (causes exploratory calls) or a user-workflow as a tool (fires at the wrong time).
- One direct resource per object when many share the same shape → use a single templated URI (`db://tables/{name}/schema`).
- Assuming the client re-requests `tools/list` every turn (the server notifies via `list_changed`).

**Core rule:** Three primitives, told apart by who starts them. A tool is an action the model controls. A resource is read-only data the app controls. A prompt is a template the user controls, which is a slash command in Claude Code. The order is `initialize`, then `*/list` discovery at connect, then `tools/call` on use, then `list_changed` when something changes. `ENABLE_TOOL_SEARCH`: unset or `true` defers the schemas, `false` loads them upfront, `auto` loads them if the set is small and defers otherwise.

---

## Domain 3 — Claude Code Configuration & Workflows (20%)

### 3.1 CLAUDE.md Hierarchy, Scoping & Modular Organisation
**Exam Traps:**
- New team member not receiving instructions despite same repo/branch (check whether config is committed / where it lives).
- Thinking `/memory` *triggers* configuration loading.
- Assuming a directory-level CLAUDE.md is best for cross-directory conventions.

**Core rule:** CLAUDE.md joins up across 3 levels (user, project, directory) and has **no strict precedence**. Enforce conflicting rules with `settings.json` or a hook, not with scoping.

### 3.2 Custom Slash Commands and Skills
**Exam Traps:**
- Team-shared command in a user-scoped path (`~/.claude/commands|skills/`) instead of project-scoped.
- Thinking skills behave like CLAUDE.md for always-on guidance.
- Not knowing when to use `context: fork`.
- Putting task-specific workflows in CLAUDE.md.

**Core rule:** A skill runs on demand for one task, when you call it or it matches your intent. CLAUDE.md always loads and holds the universal standards.

### 3.3 Path-Specific Rules for Conditional Convention Loading
**Exam Traps:**
- Choosing directory-level CLAUDE.md over path-specific rules for cross-directory conventions.
- Placing file-type-specific conventions in root CLAUDE.md.
- Confusing skills with path-specific rules for automatic convention application.

**Core rule:** Path-specific rules use a glob in the frontmatter. They load conventions only when you edit a matching file type, so they stay cheap across many folders.

### 3.4 Plan Mode vs Direct Execution
**Exam Traps:**
- Defaulting to direct execution for multi-file architectural changes.
- Using plan mode for a single-file bug fix with a clear stack trace.
- Not recognising the plan-then-execute hybrid pattern.
- Starting direct execution and switching to plan mode only when complexity emerges.

**Core rule:** Choose by **scope and ambiguity, not difficulty**. Plan mode for multi-file or architectural work, direct execution for a well-scoped fix.

### 3.5 Iterative Refinement Techniques
**Exam Traps:**
- Refining prose descriptions when the model interprets them inconsistently (use concrete examples instead).
- Not recognising when to batch vs sequence feedback.
- Confusing the interview pattern with the examples technique.

**Core rule:** Inconsistent interpretation needs concrete input and output examples. A complex transform needs test-driven iteration. **An unfamiliar domain needs the interview pattern.**

### 3.6 CI/CD Integration
**Exam Traps:**
- CI hanging waiting for interactive input → fix is the `-p` flag (not env vars/stdin redirection).
- Assuming self-review in the same session ≈ independent review (retained reasoning biases it).
- Using the Batch API for pre-merge CI checks (no latency SLA → use real-time API for blocking flows).
- Not including prior review findings in later runs → duplicate comments erode trust.

**Core rule:** `-p` runs without a prompt. `--output-format json` gives a machine-readable result. Automated review needs a separate session plus the earlier findings as context.

### 3.7 System-Prompt & Startup Flags (CLI)
**Exam Traps:**
- Appending negative instructions (`--append-system-prompt "don't suggest tests"`) to fix a persona that is wholly wrong for the task — replace with `--system-prompt` instead.
- Replacing the whole prompt (`--system-prompt`) when you only need to add one rule — that discards the default identity/tool guidance/safety; use `--append-system-prompt`.
- Reaching for `--strict-mcp-config` or `--disable-slash-commands` (each skips only PART of discovery) when the scenario wants the ENTIRE startup pipeline skipped → that's `--bare`.
- Using `--bare` when the job still needs CLAUDE.md/skills/hooks and only wants to scope MCP config → that's `--strict-mcp-config`.

**Core rule:** Append layers on top of the default and keeps the identity. Replace swaps the base, so you own the tool guidance and the safety text. The `-file` variants read the text from a file. Append composes with one replacement base, but there is only ever one base identity. `--bare` skips ALL auto-discovery (CLAUDE.md, skills, hooks, plugins, MCP) and leaves Bash plus the file tools, which suits scripted `-p` runs.

---

## Domain 4 — Prompt Engineering & Structured Output (20%)

### 4.1 System Prompts with Explicit Criteria
**Exam Traps:**
- Choosing "be conservative" / "only report high-confidence findings" as valid prompt improvements.
- Assuming confidence thresholds fix false-positive problems.
- Keeping all review categories active while iterating on a high-false-positive category.

**Core rule:** Explicit criteria (exactly what to flag and what to skip) plus concrete code examples beat vague instructions and confidence filtering.

### 4.2 Few-Shot Prompting
**Exam Traps:**
- Choosing "add more detailed instructions" when output formatting is inconsistent.
- Thinking few-shot examples only teach literal pattern-matching (they teach judgment criteria that generalise).
- Using confidence thresholds to fix inconsistent judgement calls.

**Core rule:** When detailed instructions still give inconsistent output, few-shot examples with the reasoning shown are the best first move.

### 4.3 Structured Output with Tool Use
**Exam Traps:**
- Believing tool_use with JSON schemas prevents *all* extraction errors (kills syntax errors only; semantic still needs validation).
- Confusing `tool_choice: 'auto'` (may return text) with `'any'` (guarantees a tool call).
- Making all schema fields required → model fabricates values when the source lacks info (use optional/nullable).

**Core rule:** `tool_use` with optional or nullable fields stops syntax errors and fabrication. You still validate the values separately.

### 4.4 Validation, Retry, and Feedback Loops
**Exam Traps:**
- Assuming retries always work — retries fix format/structural/misplaced-value errors, NOT genuinely absent information.
- Retrying without including the specific validation error → identical mistakes repeat.
- Relying on schema validation alone without semantic checks.

**Core rule:** A good retry resends the original document, the failed extraction and the exact error. A retry cannot invent information that is not there.

### 4.5 Batch Processing Strategies
**Exam Traps:**
- Switching all workflows to batch for cost savings (blocking/real-time flows must stay synchronous).
- Assuming batch results arrive quickly (no latency SLA; up to 24h).
- Using batch API for workflows needing multi-turn tool calling (unsupported in a single request).

**Core rule:** Use the Batch API only where waiting is fine and the results are read later. Use the synchronous API when someone waits on the answer, or when you need multi-turn tool calling. Batch costs 50% less, uses `custom_id`, and has a 24-hour window.

### 4.6 Multi-Instance and Multi-Pass Review
**Exam Traps:**
- Self-review in the same session (retained reasoning context → won't question its own decisions).
- Single pass for large multi-file reviews (inconsistent depth, missed bugs, contradictions).
- Switching to a larger-context model to fix attention dilution.
- Uncalibrated confidence scores for automated review routing.

**Core rule:** An independent instance with no prior context beats self-review. A large review needs one pass per file plus a separate pass across files.

---

## Domain 5 — Context Management & Reliability (15%)

### 5.1 Context Window Management
**Exam Traps:**
- Thinking progressive summarisation is safe for transactional data (destroys numbers/dates/IDs).
- Assuming "lost in the middle" is solved by telling the model to pay attention (fix is structural: key facts first + section headers).
- Keeping full tool results "in case" (40+ field lookups exhaust the budget).
- Believing history can be selectively truncated freely (API is stateless; each request needs full history).

**Core rule:** Pull transactional facts into a structured facts block and send it with every prompt. Then summarising can never destroy them.

### 5.2 Escalation & Ambiguity Resolution
**Exam Traps:**
- Sentiment-based escalation (frustration ≠ complexity).
- Self-reported confidence scores as an escalation signal (poorly calibrated).
- Attempting to resolve before honouring an explicit human request (escalate immediately).
- Selecting from ambiguous customer matches via heuristics (privacy risk — ask for more identifiers).

**Core rule:** Escalate on explicit signals only: a request for a human (escalate at once), a policy gap or exception, or being unable to go further. Never on mood or confidence.

### 5.3 Error Propagation in Multi-Agent Systems
**Exam Traps:**
- Catching a timeout and returning empty results marked successful (silent suppression blocks recovery).
- Terminating the whole pipeline when one subagent times out (wastes others' partial results).
- Generic "search unavailable" after retry exhaustion (hides query, partial results, alternatives).
- Retrying a valid empty result because it "looks like" failure.

**Core rule:** Pass on structured error context: the failure type, the attempted action, any partial results and the alternatives. Keep an access failure apart from a valid empty result.

### 5.4 Codebase Exploration & Context Degradation
**Exam Traps:**
- Increasing the context window to fix degradation (it's attention quality, not token exhaustion).
- Assuming subagent delegation is only about parallelisation (primary benefit = context isolation).
- Restarting a session without saving state (persist via scratchpad + state manifests, then inject).
- Using `/compact` only at the limit (apply proactively throughout).

**Core rule:** Degradation is an attention-quality problem. Use scratchpad files, subagents for context isolation, and state manifests. A bigger window does not fix it.

### 5.5 Human Review & Confidence Calibration
**Exam Traps:**
- Aggregate accuracy (97%) to justify automating all high-confidence extractions (hides per-type: could be 40% on one type).
- Only sampling low-confidence items for review (novel errors in high-confidence go undetected without stratified random sampling).
- Raw uncalibrated confidence scores (0.90 on dates ≠ 0.90 on amounts).
- Spreading reviewer capacity evenly (waste on high-confidence; prioritise highest-uncertainty).

**Core rule:** Check accuracy per document type and per field. Calibrate confidence on labelled data. Point stratified review at the most uncertain items.

### 5.6 Information Provenance & Multi-Source Synthesis
**Exam Traps:**
- Selecting the most recent source when two credible sources conflict (annotate both with source + date; let consumer decide).
- Assuming different numbers = contradictions (different dates explain them; require dates in output).
- Letting the synthesis agent paraphrase without preserving claim-source mappings (attribution dies in summarisation).
- Rendering all content types in one uniform format (tables for financial, prose for news, lists for technical).

**Core rule:** Keep structured provenance for every claim (the claim, source URL, document, excerpt and date) through the whole pipeline. Show conflicts with their attribution instead of picking a winner.

---

## Cross-domain trap signatures (the ones that recur everywhere)
- **"Guarantee / 100% / high-stakes"** → hook (PreToolUse block / PostToolUse normalise), never prompt/few-shot/rules/precedence. [Axis 1]
- **"Stronger/longer prompt, more examples, bold NEVER"** → almost always wrong for enforcement. [Axis 1/5]
- **Self-reported confidence / sentiment** → wrong signal for escalation or review routing. [Axis 5]
- **Bigger model / larger context window** → wrong fix for attention dilution or context degradation. [Axis 5]
- **`tool_choice: any/auto`** when a *specific* tool/first-step is required → wrong; force the specific tool. [Axis 2]
- **Bash** where a built-in (Grep/Glob/Edit) fits; **Glob** for contents / **Grep** for names → wrong tool. [Axis 2]
- **Match the technique to the gap:** requirements-unknown → interview; multi-file/architectural → plan mode; well-scoped → direct. [Axis 3]
- **Proportionality:** don't over-delegate trivial work; don't review everything or nothing. [Axis 4]
