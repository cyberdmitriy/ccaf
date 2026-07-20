# The 5-Axis Distractor Framework (shared across all CCAF domains)

Every CCAF question is one correct answer + three plausible distractors. Each wrong-but-plausible
option fails on **exactly one axis**. Teaching the student to *name the axis* is the transferable skill —
it generalises across every practice exam even though the specific questions differ.

## The 5 axes — the right answer wins because…
Read each axis as **the dimension on which the right answer beats the near-miss.** First the
one-line summary, then each axis as a *quick test + triggers + shape + example*.

| # | Axis | The right answer wins because… |
|---|---|---|
| 1 | **Determinism** | it **guarantees**; the near-miss only **influences**. |
| 2 | **Exact hit** | it's the **exact** tool/param/event; the near-miss is the right family but **misses**. |
| 3 | **Right diagnosis** | it fixes the **real** problem; the near-miss fixes a **neighbouring** one. |
| 4 | **Proportionality** | it **fits the size** of the task; the near-miss is **too heavy or too thin**. |
| 5 | **Root-cause / antipattern** | it fixes the **cause**; the near-miss patches a **symptom / antipattern**. |

### 1. Determinism — guarantees vs influences
- **Quick test:** does the stem demand a *guarantee*, while the option leans on something the model **reads**?
- **Stem triggers:** *guarantee · always · 100% · on every save · every file · regardless of what
  Claude generates · without relying on the model.* **No such word → probably not axis 1.**
- **Wrong looks like:** a stronger prompt / CLAUDE.md / `.claude/rules` / tool description / few-shot /
  "mark IMPORTANT" / "put it higher in precedence" — all of these only *influence*. Only code *outside*
  the model guarantees: a hook (PreToolUse block / PostToolUse validate-normalise), a schema-reject, or
  `tool_choice` forced to a **specific** named tool.
- **Example (D3):** ❌ Put "always use 4-space indent" in CLAUDE.md to guarantee it on every save →
  ✅ A PostToolUse hook that runs the formatter. *Text the model reads only influences; a hook executes → it guarantees.*

### 2. Exact hit — the exact instance, not the family
- **Quick test:** right family — but is it exactly *that* instance?
- **Stem triggers:** *the specific · exactly that · the first step · that particular tool / file / event.*
- **Wrong looks like:** a near-miss on one parameter — `tool_choice:'any'` vs a forced-specific tool;
  Grep (contents) vs Glob (paths); PreToolUse vs PostToolUse; a hook on Read vs Write.
- **Example (D2):** ❌ `tool_choice:'any'` to make the support agent call `submit_ticket` first →
  ✅ `tool_choice:{type:'tool',name:'submit_ticket'}`. *"any" forces a tool, not the tool.*

### 3. Right diagnosis — the stated problem, not a neighbour
- **Quick test:** does this treat the problem the stem *states*, or a neighbouring one?
- **Stem triggers:** *root cause · the actual problem · what's really failing* — or the stem describes
  one symptom and the option fixes another.
- **Wrong looks like:** a sound mechanism aimed at the wrong gap — plan mode for a *requirements* gap
  that needs an interview; skill-docs where an automatic by-file-type rule is needed; a lean summary
  where *synthesis* needs the complete findings.
- **Example (D3/D1):** ❌ Enter plan mode because the feature request is vague → ✅ Interview the user
  to close the requirements gap first. *Plan mode structures known work; it can't supply missing requirements.*

### 4. Proportionality — right idea, right size
- **Quick test:** right idea — but the right *size*?
- **Stem triggers:** *most effective · simplest · proportionate · first step.*
- **Wrong looks like:** over-engineering (a subagent for a one-file task; agents to fix a *decomposition*
  bug) or under- (review everything, or nothing — stratify by risk instead).
- **Example (D1):** ❌ Spin up a research subagent to read one config file → ✅ Read it directly with
  the Read tool. *Right idea (delegation) at the wrong scale.*

### 5. Root-cause / antipattern — cause, not symptom
- **Quick test:** is this the *cause*, or a patch over the *symptom*?
- **Stem triggers:** *fix · prevent · stop it recurring · reliably · keeps happening.*
- **Wrong looks like:** memorised antipatterns — a bigger model / larger context window for
  "attention dilution"; a longer prompt or bold "NEVER" as "enforcement"; self-reported
  confidence / tone as a signal; more validation to "strip hallucinations" instead of fixing the schema.
- **Example (D3/D4):** ❌ One detailed prompt that emits implementation + tests together → ✅ Write
  failing tests first, then iterate (TDD). *The single prompt patches over; the cause is test-first.*

## Decision order — which axis is it?
Ask in order; stop at the first that fits:
1. **Find the winning condition** — the words in the stem that define what a right answer must do
   (*guarantee · first step · most effective · root cause · without relying on the model*).
2. Is there a **guarantee-word** *and* does the option rest on text the model **reads**? → **Axis 1**.
3. Right area, but **one** tool / parameter / lifecycle-event off? → **Axis 2**.
4. Otherwise, pick by what's wrong:
   - fixes a **different** problem than the stem states → **Axis 3**;
   - right fix, **wrong size** (too heavy / too thin) → **Axis 4**;
   - patches a **symptom** or uses a known antipattern → **Axis 5**.

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
