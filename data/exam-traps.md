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
- Cutting round-trips with composite/bundled tools (`get_customer_with_orders`), speculative execution, or a larger `max_tokens` — the fix is prompting Claude to batch tool requests per turn and return all results together.
- Treating every iteration cap as an anti-pattern — a cap is fine as a SECONDARY backstop against runaway loops, as long as `stop_reason` stays the primary stop.
- Treating `stop_reason: "max_tokens"` like `end_turn` and presenting the cut-off text as the final answer — the response is truncated: not done, and not a tool call to run.
- Executing an incomplete `tool_use` block after `max_tokens`, or splicing a "continue" reply onto its cut-off input — discard it and retry the request with a higher `max_tokens`.
- Returning parallel tool results one user message per result — return one `tool_result` per `tool_use` id, all together in the next single user message, `tool_result` blocks before any text.
- Omitting the result of a parallel call that failed or was skipped — it still gets a `tool_result` with `is_error: true` and a brief explanation.
- Merging parallel results into one plain-text summary — each result is its own `tool_result` block matched by `tool_use_id`.

**Core rule:** Stop on the `stop_reason` field: `tool_use` → run every requested tool and return one `tool_result` per call, all in the next user message; `end_turn` → final answer; `max_tokens` → truncated, never final — retry an incomplete `tool_use` with a higher `max_tokens`. Never stop on text presence, an iteration cap, a natural-language phrase, or a forced `tool_choice`. An iteration cap is allowed only as a secondary runaway backstop, never as the primary stop.

### 1.2 Multi-Agent Orchestration
**Exam Traps:**
- Blaming downstream subagents for coverage gaps when the coordinator's decomposition was too narrow.
- Assuming subagents share memory or inherit the coordinator's conversation history.
- Proposing direct inter-subagent communication as an efficiency improvement.
- Adding more subagents to fix a decomposition problem.
- Spawning a subagent (or adding prompt caching / cached summaries) for a summary the coordinator can already answer from its own context.
- Delegating a trivial single-file task to a subagent instead of handling it in the coordinator directly.
- Running dependent consumer agents in parallel against the original input, or wiring a shared memory store so they can watch each other's work.
- Using /compact, /clear, or Grep to shrink the main context instead of delegating verbose multi-file work to a fresh-context Explore subagent.
- Picking a winner between two conflicting credible sources via credibility heuristics (or passing both unflagged) instead of annotating both with attribution and deferring to the coordinator.
- Standardizing every subagent output to one format (all JSON, all prose) or adding a common intermediate representation, instead of rendering each content type appropriately in synthesis.

**Core rule:** The coordinator's decomposition sets the coverage. Subagents are isolated and talk only through the coordinator. Fix the decomposition. Do not add agents or wire them to each other. Delegate by size and dependency: the coordinator handles trivial or already-held work itself, sends only large multi-file work to fresh-context subagents, and runs a producing agent before the consumers that depend on its output.

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
- A loop that treats every non-`tool_use` exit as "done" and closes the ticket — only an `end_turn` / `success` exit may be closed as resolved; the cap firing, the budget running out, and errors after retries must retry, resume or escalate.
- A Stop hook as the "always escalate" safeguard — hooks may not fire when the agent hits `max_turns`, and an API error ends the turn via `StopFailure`, not `Stop`; route on the result `subtype` in orchestrator code.
- A system-prompt rule such as "escalate if you can't finish" — probabilistic, and the model never gets a turn to react to a budget cut-off or an API failure.
- Raising or removing `max_turns` / the budget so sessions stop dying unresolved — this moves the limit and still leaves the exit unhandled.
- Rerunning the whole session until one run ends normally — unbounded, repeats the same failing exit, and never reaches a human; the failure exit must end in an escalation.
- Reading `result`, or parsing the final text for "resolved", without checking `subtype` — `result` exists only on `success`; a connection failure yields no result message at all (needs try/catch).
- Resuming the previous step's session so an approval "carries over" — a session persists the conversation, so the approval stays prose the model interprets and nothing checks it. Pass a structured handoff record and gate the next tool on its fields.
- Pasting the full transcript into the next agent or the human's ticket — the verification and approval state is buried. Compile a structured package instead.
- Running the next step with `bypassPermissions` because "the previous step already verified" — that removes the check instead of carrying the verified state forward.
- Gating the next agent on its own re-verification and its generic limit — it guarantees verification but repeats work already done and enforces the wrong cap. Gate on the approved cap and order from the handoff record.
- A human handoff that leaves out what the agent already verified and did — the human re-verifies or repeats the credit/refund. Add verification status and method, completed actions, and the amount still outstanding to the core fields.

**Core rule:** High-stakes compliance needs deterministic enforcement, not prompts, few-shot or routing. Every session ends in a resolution or a human escalation: orchestrator code (not a hook, not the prompt) maps every exit path — each `stop_reason`, each result `subtype`, thrown exceptions — to one outcome. Every handoff, to the next agent step or to a human, is a structured package: the critical fields (customer ID, root cause, amount, recommended action) AND the authorization state — what was verified and how, what was approved, by whom, and the limits. A transcript or a resumed session carries approvals only as prose.

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
- Reading every file whose name or content matches a keyword (`auth`, `token`, `permission`) to understand a system — exhaustive upfront reading, not entry-point navigation.
- Fanning out parallel subagents across services before an entry point is found (premature parallelism with no grounding), or asking the human to name the 10-15 key files instead of the agent tracing them.

**Core rule:** Attention dilution needs multi-pass decomposition, a cross-batch integration pass, and flows that adapt. A bigger model, prompt or window does not fix it. And to understand an unfamiliar codebase, `Grep` for entry points then follow imports outward incrementally — never read every keyword-matching file at once.

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
- Reaching for a decomposition preprocessing layer or response-validation re-prompting when the model already selects single-concern tools well and few-shot fits.
- Padding the prompt with 10-15 unambiguous or tool-grouped few-shot examples instead of 4-6 targeting the ambiguous cases with comparative reasoning.
- Trusting a tool description, system-prompt rule, or few-shot example to *guarantee* a destructive tool never runs without approval (they only make it likely).

**Core rule:** Claude picks tools from their descriptions. Improve the descriptions first. When descriptions already work, few-shot (4-6 ambiguous cases with comparative reasoning) fixes the reasoning gap, and only a `PreToolUse` hook — never prompt text — hard-guarantees a call cannot run without approval.

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
- Relying on description tuning alone to route a context-free prompt between two same-named tools (no environment cue = still ambiguous).
- Editing or removing a server from the shared `.mcp.json` to dodge a local collision (mutates team state for a personal problem).
- Forcing `tool_choice` to pin the agent to one tool for the whole session instead of making the tools distinguishable.
- Moving the personal server into the shared `.mcp.json` at equal precedence to 'let the agent disambiguate' — identical scope disambiguates nothing.
- Treating the `Added …` line from `claude mcp add` as proof the server works — it only means the config was written. Check `claude mcp list` / `claude mcp get <name>` / `/mcp` for Connected, Needs authentication, Failed to connect or Pending approval.
- Tuning tool descriptions or adding CLAUDE.md lines when the server never connected — verify discovery (status, tool count) first; enrich descriptions only once the tools are there.
- Believing an unset `${VAR}` blocks the server from loading — it loads with the literal `${VAR}` text and a missing-variable warning, and auth fails. Set the variable in your own environment.
- Fixing a missing token by inlining it, or by adding a `${VAR:-<secret>}` default, in the committed `.mcp.json` — either way the secret gets committed.
- Naming a remote server's token after a covered credential (`NPM_TOKEN`, `ANTHROPIC_API_KEY`, `AWS_BEARER_TOKEN_BEDROCK`) in `url`/`headers` — it always reads as empty with no warning, so the server returns 401. Use a server-specific name.
- Adding a same-named `--scope user` copy to override a project server — the order is local > project > user and the whole entry wins with no merge, so the user copy is shadowed.
- Confusing MCP "local scope" (`~/.claude.json` under the project path) with `.claude/settings.local.json`.

**Core rule:** A project `.mcp.json` serves the whole team. A user `~/.claude.json` is personal. Keep secrets in `${VAR}` expansion, which each developer sets in their own environment. An unset `${VAR}` with no default still loads, but as literal text with a warning, so set the variable. The same server name in several scopes is not merged: local > project > user, and the whole entry wins. `Added …` only means the config was written, so verify discovery with `claude mcp list` / `/mcp` before tuning anything. When two same-named tools collide across scopes, resolve it locally in `~/.claude.json` by renaming to a distinct id, putting the environment in the description, AND adding an explicit session routing rule. Description tuning alone cannot route a context-free prompt.

### 2.5 Built-in Tools
**Exam Traps:**
- Using Glob to find function callers (Glob searches *paths*, not contents).
- Using Grep to find files by extension/naming pattern.
- Reading all source files upfront before knowing what's relevant.
- Defaulting to Read + Write for every modification instead of trying Edit first.
- Jumping to Read + Write the moment Edit reports a non-unique match (widen context first).
- Calling Edit once per occurrence (with unique surrounding context) to rename a string that appears many times, instead of `replace_all: true` in one operation.
- Reaching for Read + Write or Bash `sed` to rename every occurrence, when `Edit` with `replace_all: true` does it in a single call.

**Core rule:** Grep searches contents. Glob matches paths. Try Edit first, and widen the context before you fall back to Read plus Write. To change every occurrence of a string in one file, use Edit with `replace_all: true` in one operation.

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
- Writing a hard prohibition ("never edit db/migrations/", "never read .env") in CLAUDE.md, making it bolder, or moving it into a `.claude/rules/` file — all of these are context the model reads, not enforced configuration. Move it to `permissions.deny` (or a PreToolUse hook) and keep only style/behavioural guidance in CLAUDE.md.
- Putting a team-wide deny in `.claude/settings.local.json` — that file is personal. Team enforcement goes in the committed `.claude/settings.json` (or managed settings).
- Adding a narrower `allow` rule (in another scope, or via `--allowedTools`) to override a broad `deny` — rules evaluate deny → ask → allow, a deny at any level wins, and an allow can't carve an exception out of a deny.
- Using a PreToolUse hook that returns "allow" to get past a deny rule — hook decisions don't bypass deny/ask rules. A blocking hook (exit 2) does beat an allow rule, so replace the broad deny with a hook that blocks everything except the permitted case.
- Putting a soft style preference behind a blocking hook — that over-enforces a judgement call. Preferences stay in CLAUDE.md.
- Adding a file needed for one task to CLAUDE.md (or `@import`ing it there): it then loads in every session for every teammate. Reference `@path` in the prompt instead.
- Assuming `@src/some-dir/` loads every file's contents: it gives a file listing only. Reference the files themselves.
- Describing in prose where the code lives ("the invoice module in billing"): reference it with `@path` so the full content is included.
- Putting a one-off constraint for this task into CLAUDE.md: state it inline in the prompt.
- Thinking `@import` in CLAUDE.md saves context: imports expand at launch. They organise, they don't shrink.

**Core rule:** CLAUDE.md joins up across 3 levels (user, project, directory) and has **no strict precedence**. It is context the model reads, not enforced configuration: keep behavioural and style guidance there, and move anything that must hold (a forbidden path or command, a rule that conflicts across levels) into `permissions` in the committed `.claude/settings.json` or a hook. Permission rules evaluate **deny → ask → allow**; a deny at any level wins and no allow rule can carve an exception out of it. Give context by how far it must reach: every session or the whole team → CLAUDE.md (or `@import`); one file for this task → `@file` in the prompt (`@dir` only lists files); a one-off constraint → inline in the prompt.

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
- Trusting a bold 'NEVER write to /secrets' in CLAUDE.md (or a `.claude/rules` glob scoped to the path) to hard-block it — instructions are probabilistic, the model can override or skip them.
- Putting the formatter/linter in a `PreToolUse` hook — formatting acts on the completed file, so it belongs in `PostToolUse`; `PreToolUse` is for denying a call before it runs.
- Reaching for a path-specific rule or CLAUDE.md when the requirement says 'on every edit' / 'no exceptions' — only a hook (code outside the model) enforces deterministically.
- Creating a `.claude/rules/` file with no `paths` frontmatter (or with YAML that doesn't parse) and expecting it to load conditionally — it loads at launch every session, like `.claude/CLAUDE.md`. Add `paths: [...]`.
- Using `@import` in CLAUDE.md to save context — imports organise the files, but they still load into context at launch.
- Putting an on-demand runbook or checklist in a rules file — rules load by file or at launch, not by task. Use a skill.

**Core rule:** Path-specific rules use a `paths:` glob in the frontmatter. They load conventions only when Claude works with a matching file, so they stay cheap across many folders. A rule file **without** `paths` loads every session like CLAUDE.md, and an `@import` still loads at launch. Pick the mechanism by *when* the guidance applies: always, as advice → CLAUDE.md; on matching files → a `paths` rule; for one task, on demand → a skill; on every matching event → a hook (`PostToolUse` runs a formatter/linter/generator on the finished file); must never happen → a `permissions.deny` rule or a `PreToolUse` hook that blocks the call. Only hooks and permission rules enforce; everything else is text the model reads.

### 3.4 Plan Mode vs Direct Execution
**Exam Traps:**
- Defaulting to direct execution for multi-file architectural changes.
- Using plan mode for a single-file bug fix with a clear stack trace.
- Not recognising the plan-then-execute hybrid pattern.
- Starting direct execution and switching to plan mode only when complexity emerges.
- "It's one file, just run it and `/rewind` if it breaks" for a migration, deploy or data change run through Bash: checkpoints track only Claude's file edits, not Bash or external processes. Plan and review first.
- Committing to git as the safety net for a data migration: git reverts the code, not rows already rewritten.
- Coding first and opening a draft PR when the approach must be approved before implementation: use plan mode, share the plan, get the go-ahead, then execute.
- Approving your own plan and switching to execution when others must accept the approach: plan-then-execute is right, but their sign-off goes between the two.
- Always entering plan mode "for safety": it adds overhead. If the diff fits in one sentence and is a reversible code edit, execute directly.

**Core rule:** Choose by **scope, ambiguity, reversibility and review need, not difficulty**. Plan mode for multi-file or architectural work, for a change whose effect a rewind can't undo (Bash side effects, shared data, deploys), and when others must approve the approach before coding (plan → their sign-off → execute). Direct execution for a well-scoped, reversible fix you could describe in one sentence.

### 3.5 Iterative Refinement Techniques
**Exam Traps:**
- Refining prose descriptions when the model interprets them inconsistently (use concrete examples instead).
- Not recognising when to batch vs sequence feedback.
- Confusing the interview pattern with the examples technique.
- Pasting the full component source and describing the misalignment in prose (the source looks fine; the info is only in the render).
- Writing a precise pixel-by-pixel prose description instead of showing the render.
- Copying console output or a stack trace when there is no exception to copy.

**Core rule:** Inconsistent interpretation needs concrete input and output examples. A complex transform needs test-driven iteration. **An unfamiliar domain needs the interview pattern.**. A pure visual/render bug (no exception, source looks fine) needs a screenshot plus reproduction steps.

### 3.6 CI/CD Integration
**Exam Traps:**
- CI hanging waiting for interactive input → fix is the `-p` flag (not env vars/stdin redirection).
- Assuming self-review in the same session ≈ independent review (retained reasoning biases it).
- Using the Batch API for pre-merge CI checks (no latency SLA → use real-time API for blocking flows).
- Not including prior review findings in later runs → duplicate comments erode trust.
- Capping with `--max-turns` alone, then failing the build on a post-hoc `total_cost_usd` check → detects overspend but the money is already spent (needs `--max-budget-usd` to prevent it).
- Bounding a runaway run with a shell `timeout` or a cheaper `--model` → caps wall-clock seconds or per-token rate, not the total dollar spend.

**Core rule:** `-p` runs without a prompt. `--output-format json` gives a machine-readable result. Automated review needs a separate session plus the earlier findings as context. Bound a runaway run with `--max-turns N` plus `--max-budget-usd X` — the budget flag stops the run before it overspends; a post-hoc `total_cost_usd` check only detects overspend.

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
- For a CI/automation pipeline, forcing review structure via a CLAUDE.md "Output Format" section or a prompt template — prompt-based formatting is followed inconsistently and can't be reliably parsed; use the CLI flags `--output-format json` + `--json-schema`.
- Blaming instruction/tool-name keyword overlap on temperature, an unset `tool_choice`, or too-sparse tool descriptions — then adding longer descriptions or a security-over-performance priority rule; the cause is the shared wording, fixed only by distinct terminology.
- Reaching for response prefilling (or prompt-based JSON) when the requirement is *strict schema compliance* — prefill pins the opening tokens and skips preamble but enforces no schema (and can't be used while `tool_choice` forces a tool); `tool_use` + schema is the method that guarantees shape.

**Core rule:** `tool_use` with optional or nullable fields stops syntax errors and fabrication. You still validate the values separately. For a CLI/automation pipeline `--output-format json` + `--json-schema` enforce parseable output, and instruction wording must stay distinct from tool names so the model invokes the tool instead of following the prose. Response prefilling only steers format / skips preamble — it is not a schema guarantee; reserve it for controlling the first tokens.

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
- Re-adding a `cache_control` breakpoint every N documents to keep the prefix warm (one breakpoint at the prefix end is enough).
- Placing `cache_control` on each document's content block (variable content after the prefix cannot be reused; only the identical prefix caches).
- Assuming the `1h` cache TTL guarantees a cache hit on every request (it only extends the idle window and adds a write premium).

**Core rule:** Use the Batch API only where waiting is fine and the results are read later. Use the synchronous API when someone waits on the answer, or when you need multi-turn tool calling. Batch costs 50% less, uses `custom_id`, and has a 24-hour window. When every request shares a prefix, set one `cache_control` breakpoint at the end of that prefix and keep variable per-document content after it (prefix-match caching).

### 4.6 Multi-Instance and Multi-Pass Review
**Exam Traps:**
- Self-review in the same session (retained reasoning context → won't question its own decisions).
- Single pass for large multi-file reviews (inconsistent depth, missed bugs, contradictions).
- Switching to a larger-context model to fix attention dilution.
- Uncalibrated confidence scores for automated review routing.
- Few-shot examples of complete answers to close gaps that vary case-by-case (examples fix consistent patterns, not per-case variable omissions → use a self-critique / evaluator-optimizer step against completeness criteria).
- Upgrading the model tier or adding a customer confirmation step when resolutions are already accurate but inconsistently explained (the gap is completeness, not correctness — self-critique the draft, don't shift the burden to the customer).
- Surfacing high-confidence findings only, or suppressing false-positive signatures, to cut investigation time (any pre-review filtering is out when stakeholders forbid it → surface reasoning + confidence inline instead).
- Re-categorising findings (blocking vs suggestion) to speed review (reorganises the queue but developers still click into each finding to see why it was flagged).

**Core rule:** An independent instance with no prior context beats self-review. A large review needs one pass per file plus a separate pass across files. Self-critique against explicit completeness criteria still catches per-case coverage gaps; when findings must not be filtered before review, surface reasoning and confidence inline to cut investigation time.

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
