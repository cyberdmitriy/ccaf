# The 5-Axis Distractor Framework (shared across all CCAF domains)

Every CCAF question is one correct answer + three plausible distractors. Each wrong-but-plausible
option fails on **exactly one axis**. Teaching the student to *name the axis* is the transferable skill —
it generalises across every practice exam even though the specific questions differ.

## The 5 axes

1. **Determinism — "influences" vs "guarantees".**
   Anything the model *reads* (system prompt, CLAUDE.md, `.claude/rules`, tool description, few-shot examples)
   is **probabilistic**. Only code *outside* the model is **deterministic**: a hook (PreToolUse block,
   PostToolUse validate/normalise), schema-reject, or `tool_choice` forced to a **specific** named tool.
   Trigger words in the stem: *guarantee / always / without exception / 100% / on every save / without relying on the model.*

2. **Exact hit — "similar" vs "exactly the thing".**
   The option does something in the right area but misses the precise target.
   `tool_choice: 'any'` forces *a* tool, not *the* tool; `'auto'` may return text. Grep = file **contents**,
   Glob = file **paths**. Forced-first-step vs "call some tool".

3. **Right diagnosis — solves the *stated* problem?**
   A gap in *requirements* ≠ a gap in *code* (interview pattern, not plan mode). Synthesis needs the
   *complete* findings, not a lean summary. Fix the thing the stem actually describes.

4. **Proportionality — not over- or under-engineered.**
   Don't delegate a trivial single-file task to a subagent; don't add agents to fix a decomposition bug;
   don't review everything or nothing (stratify by risk). Match effort to stakes.

5. **Root-cause / antipattern — fixes cause, not symptom.**
   Bigger model / larger context window ≠ fix for attention dilution or context degradation.
   Stronger/longer prompt, bold "NEVER", or `.claude/rules` ≠ enforcement. Self-reported confidence
   and sentiment ≠ valid signals. "Add more instructions" when examples are what's needed.

## How to use it in a session
For every question, make the student:
1. Underline the **winning condition** in the stem (the exact word that defines "correct").
2. Predict the answer **before** reading options.
3. For each distractor, ask "does THIS satisfy that exact condition?" and **name the axis it fails on**.
4. Eliminate three by axis; the survivor is the answer. Then confirm against the answer key + explanation.

## Cross-domain trap signatures (recur on every exam)
- **"Guarantee / 100% / high-stakes"** → hook (PreToolUse block / PostToolUse normalise / forced-specific-tool), never prompt / few-shot / `.claude/rules` / CLAUDE.md precedence. [Axis 1]
- **"Stronger/longer prompt, more examples, bold NEVER"** for enforcement → wrong. [Axis 1/5]
- **Self-reported confidence / sentiment** as a signal for escalation or review routing → wrong. [Axis 5]
- **Bigger model / larger context window** as a fix for attention dilution or context degradation → wrong. [Axis 5]
- **`tool_choice: any/auto`** when a *specific* tool or first step is required → force the specific tool. [Axis 2]
- **Bash** where a built-in (Grep/Glob/Edit) fits; **Glob** for contents / **Grep** for names → wrong tool. [Axis 2]
- **Match technique to the gap:** requirements-unknown → interview; multi-file/architectural → plan mode; well-scoped → direct execution. [Axis 3]
- **Proportionality:** don't over-delegate trivial work; don't review everything or nothing. [Axis 4]
