# Learning-Progress Tracking Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add durable learning-progress tracking (task-statement coverage, in-tutor drill scores, last-visited, per-axis mastery) written by the domain tutors and surfaced in `/ccaf:init` (text) and `/ccaf:stats` (a dashboard card).

**Architecture:** A new per-user `learning-progress.json` (separate from `stats.json`) is bootstrapped from the plugin template via the existing `cp -rn` Step-0, written read-modify-write by each `dN-teacher` at hand-off, read-only by `init` (text summary) and by the app builder (`app-build.md` → `HISTORY.learning` → a new dashboard card in `app-template.html`). No new command; `/ccaf:result` is untouched.

**Tech Stack:** Markdown skill/command files, JSON data file, Python 3 build script (in `app-build.md`), vanilla-JS single-file HTML app (`app-template.html`).

## Global Constraints

Copied verbatim from the spec and plugin maintainer `CLAUDE.md`; every task's requirements implicitly include this section.

- Progress lives ONLY in `~/.claude/ccaf-progress/`, never in the plugin dir. Bundled path refs use `${CLAUDE_PLUGIN_ROOT}/data/...`; progress refs use `$HOME/.claude/ccaf-progress/...`.
- Bootstrap is `cp -rn "${CLAUDE_PLUGIN_ROOT}/data/progress-template/." "$HOME/.claude/ccaf-progress/"` — copies MISSING files, never overwrites. The new template file must be additive for existing stores.
- `disable-model-invocation: true` stays on every skill/command; never set `user-invocable: false`.
- No skill→skill calls. Tutors WRITE `learning-progress.json`; `init`/`stats` READ & display; hand-offs stay as instructions to the user.
- `learning-progress.json` is separate from `stats.json`. `/ccaf:result` remains the single recorder of exam results and MUST NOT touch learning-progress. This plan does not modify `commands/result.md`.
- One app file (`ccaf-exam.html`), overwritten each build. The `/*__BANK__*/[]` and `/*__HISTORY__*/{}` placeholders must stay valid as empty literals. The card degrades gracefully when `HISTORY.learning` is absent or all-`not_started`.
- JSON the tutors write must be valid — no trailing commas.
- Bump the plugin version (`.claude-plugin/plugin.json` + `.claude-plugin/marketplace.json`) so teachers/app pick up the changes. Target version: **0.6.6 → 0.7.0**.
- `data/validate.py` validates only `questions.json`; the bank is NOT changed here, but run it once as a regression check (see Task 8).

## Data model reference (used across tasks)

`learning-progress.json` shape (per spec "Data model"):

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

Field semantics (authoritative for every task that reads/writes the file):
- `domains[d].task_total` — number of task statements in that domain (tutor knows its own set, e.g. D4 = 6).
- `domains[d].task_statements[<id>]` — `{ "covered": true, "ts": "<YYYY-MM-DD>" }`; set ONLY when fully taught **and** its check-question was attempted.
- `domains[d].drills[]` — `{ "ts": "<YYYY-MM-DD>", "score": <int>, "total": <int> }`, one per 8-question in-tutor drill.
- `domains[d].last_visited` — `YYYY-MM-DD` of the most recent tutor session for that domain.
- `domains[d].status` — derived: `complete` when `len(covered) == task_total` **and** the latest drill passed (`score/total >= 7/8`); else `in_progress` once any activity exists; else `not_started`.
- `axis_mastery[a]` — cumulative `seen`/`correct` over check + drill questions whose axis is known, across all domains.

---

### Task 1: Create `learning-progress.json` template skeleton

**Files:**
- Create: `data/progress-template/learning-progress.json`
- Test: run the JSON-shape assertion in Step 2 (no test file — this repo has no test framework; verification is a `python3 -c` assertion, mirroring how `data/validate.py` is used).

**Interfaces:**
- Consumes: nothing.
- Produces: the on-disk template file that Step-0 `cp -rn` copies to `~/.claude/ccaf-progress/learning-progress.json`. Its exact key set (`schema`, `domains.1..5`, `axis_mastery.1..5`) is relied on by the tutor write contract (Task 2), the app builder default (Task 4), the card renderer (Task 5), and the init summary (Task 7).

- [ ] **Step 1: Write the template file**

Create `data/progress-template/learning-progress.json` with EXACTLY this content (no trailing commas, LF newline at EOF):

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

- [ ] **Step 2: Verify it parses and has the exact shape**

Run:
```bash
python3 -c "import json; d=json.load(open('data/progress-template/learning-progress.json')); assert d['schema']==1; assert set(d['domains'])=={'1','2','3','4','5'}; assert set(d['axis_mastery'])=={'1','2','3','4','5'}; assert all(set(v)=={'status','last_visited','task_total','task_statements','drills'} for v in d['domains'].values()); assert all(d['domains'][k]['status']=='not_started' for k in d['domains']); print('shape ok')"
```
Expected: `shape ok`

- [ ] **Step 3: Verify `cp -rn` is additive (does not overwrite an existing store)**

Run (simulates an existing store that already has other files but not the new one):
```bash
T=$(mktemp -d) && mkdir -p "$T/store" && echo '{"schema":1,"answered":{"7":{}}}' > "$T/store/stats.json" && cp -rn data/progress-template/. "$T/store/" && python3 -c "import json;s=json.load(open('$T/store/stats.json'));assert s['answered']=={'7':{}},'stats.json was clobbered';lp=json.load(open('$T/store/learning-progress.json'));assert lp['schema']==1;print('cp -rn additive ok')" && rm -rf "$T"
```
Expected: `cp -rn additive ok`

- [ ] **Step 4: Commit**

```bash
git add data/progress-template/learning-progress.json
git commit -m "feat(ccaf): add learning-progress.json template skeleton"
```

---

### Task 2: Add the "Recording learning progress" write contract to `teaching-method.md`

**Files:**
- Modify: `data/teaching-method.md` (append a new `##` section after the existing "## Coverage" section at EOF)

**Interfaces:**
- Consumes: the data model + field semantics above.
- Produces: the shared write contract the five `dN-teacher` skills reference by name in Task 3 ("Recording learning progress"). Must instruct read-modify-write of ONLY the current domain's entry plus `axis_mastery`, and valid JSON with no trailing commas.

- [ ] **Step 1: Append the section**

Append this section to the END of `data/teaching-method.md` (after the `## Coverage` section):

```markdown
## Recording learning progress (at hand-off, before you suggest the next command)
Teacher sessions are otherwise stateless — their progress dies on `/clear`. So at hand-off you
persist what this session covered into the per-user file `learning-progress.json`. This is
**separate** from `stats.json` (exam results, owned by `/ccaf:result`) — never touch that here.

Perform this contract as a **read-modify-write**, touching ONLY the current domain's entry and the
shared `axis_mastery` — never clobber the other four domains from a stale copy:

1. The store + file already exist (Step-0 `cp -rn` bootstraps `learning-progress.json` from the
   template on first run). If for any reason the file is missing, recreate it from the template
   skeleton before writing.
2. **Read** `$HOME/.claude/ccaf-progress/learning-progress.json` into memory.
3. In `domains["<d>"]` for YOUR domain only:
   - set `last_visited` = today (`YYYY-MM-DD`, from session context — best effort);
   - set `task_total` = this domain's task-statement count (you know your own set, e.g. D4 = 6 →
     4.1–4.6);
   - for each task statement you **fully taught AND check-questioned** this session, set
     `task_statements["<id>"] = {"covered": true, "ts": "<today>"}` (use the tutor's own ids, e.g.
     `"4.3"`). Do NOT mark a statement you only mentioned.
   - if the 8-question domain drill was taken, append `{"ts": "<today>", "score": <int>, "total": <int>}`
     to `drills`.
   - recompute `status`: `complete` when covered count == `task_total` **and** the latest drill
     passed (`score/total >= 7/8`); else `in_progress` if any activity exists; else leave
     `not_started`.
4. In shared `axis_mastery`: for every check-question / drill question whose axis (1–5) is known,
   increment `axis_mastery["<a>"].seen`, and `.correct` when the learner got it right. This is
   cumulative across sessions and complements the misses-only `stats.json.axis_tally`.
5. **Write** the whole object back as **valid JSON — no trailing commas**. Preserve every other
   domain's data and any pre-existing counts exactly.

Do this silently as part of hand-off; you may tell the user in one line that their progress was
saved. It's a write to the learner's own store, not a skill call — you never invoke another skill.
```

- [ ] **Step 2: Verify the section is present and well-formed**

Run:
```bash
grep -q "^## Recording learning progress" data/teaching-method.md && grep -q "read-modify-write" data/teaching-method.md && grep -q "no trailing commas" data/teaching-method.md && echo "contract present"
```
Expected: `contract present`

- [ ] **Step 3: Commit**

```bash
git add data/teaching-method.md
git commit -m "docs(ccaf): add learning-progress write contract to teaching-method"
```

---

### Task 3: Reference the contract from each `dN-teacher` Hand-off

**Files:**
- Modify: `skills/d1-teacher/SKILL.md` (`## Hand-off` section)
- Modify: `skills/d2-teacher/SKILL.md` (`## Hand-off` section)
- Modify: `skills/d3-teacher/SKILL.md` (`## Hand-off` section)
- Modify: `skills/d4-teacher/SKILL.md` (`## Hand-off` section)
- Modify: `skills/d5-teacher/SKILL.md` (`## Hand-off` section)

**Interfaces:**
- Consumes: the "Recording learning progress" section from Task 2 (`data/teaching-method.md`).
- Produces: a one-line instruction in each tutor's Hand-off telling it to run that contract before suggesting the next command. Mirrors the existing "Step 4 — Log new fails" pattern (one line pointing at a shared behaviour). Frontmatter `disable-model-invocation: true` and `allowed-tools: Bash, Read, Write` are unchanged — no skill→skill call is introduced.

Each tutor's current `## Hand-off` body differs slightly. Insert the SAME new first line into each, immediately under the `## Hand-off` heading and before the existing "When done…" sentence.

- [ ] **Step 1: Edit d1**

In `skills/d1-teacher/SKILL.md`, change:
```markdown
## Hand-off
When done, tell the user their next best step (e.g. `/ccaf:exam` for a mock, or another `/ccaf:dN-teacher`). Do not auto-invoke other skills — instruct the user to run them.
```
to:
```markdown
## Hand-off
First **record learning progress** — follow the "Recording learning progress" contract in `${CLAUDE_PLUGIN_ROOT}/data/teaching-method.md` (read-modify-write only D1's entry of `$HOME/.claude/ccaf-progress/learning-progress.json` + shared `axis_mastery`).
When done, tell the user their next best step (e.g. `/ccaf:exam` for a mock, or another `/ccaf:dN-teacher`). Do not auto-invoke other skills — instruct the user to run them.
```

- [ ] **Step 2: Edit d2**

In `skills/d2-teacher/SKILL.md`, change:
```markdown
## Hand-off
When done, suggest the user's next step (e.g. `/ccaf:exam` or another `/ccaf:dN-teacher`). Never auto-invoke; instruct the user.
```
to:
```markdown
## Hand-off
First **record learning progress** — follow the "Recording learning progress" contract in `${CLAUDE_PLUGIN_ROOT}/data/teaching-method.md` (read-modify-write only D2's entry of `$HOME/.claude/ccaf-progress/learning-progress.json` + shared `axis_mastery`).
When done, suggest the user's next step (e.g. `/ccaf:exam` or another `/ccaf:dN-teacher`). Never auto-invoke; instruct the user.
```

- [ ] **Step 3: Edit d3**

In `skills/d3-teacher/SKILL.md`, change:
```markdown
## Hand-off
When done, suggest the next step (e.g. `/ccaf:exam` or another `/ccaf:dN-teacher`). Never auto-invoke; instruct the user.
```
to:
```markdown
## Hand-off
First **record learning progress** — follow the "Recording learning progress" contract in `${CLAUDE_PLUGIN_ROOT}/data/teaching-method.md` (read-modify-write only D3's entry of `$HOME/.claude/ccaf-progress/learning-progress.json` + shared `axis_mastery`).
When done, suggest the next step (e.g. `/ccaf:exam` or another `/ccaf:dN-teacher`). Never auto-invoke; instruct the user.
```

- [ ] **Step 4: Edit d4**

In `skills/d4-teacher/SKILL.md`, change:
```markdown
## Hand-off
When done, suggest the next step (e.g. `/ccaf:exam` or another `/ccaf:dN-teacher`). Never auto-invoke; instruct the user.
```
to:
```markdown
## Hand-off
First **record learning progress** — follow the "Recording learning progress" contract in `${CLAUDE_PLUGIN_ROOT}/data/teaching-method.md` (read-modify-write only D4's entry of `$HOME/.claude/ccaf-progress/learning-progress.json` + shared `axis_mastery`).
When done, suggest the next step (e.g. `/ccaf:exam` or another `/ccaf:dN-teacher`). Never auto-invoke; instruct the user.
```

- [ ] **Step 5: Edit d5**

In `skills/d5-teacher/SKILL.md`, change:
```markdown
## Hand-off
When done, suggest the next step (e.g. `/ccaf:exam` or another `/ccaf:dN-teacher`). Never auto-invoke; instruct the user.
```
to:
```markdown
## Hand-off
First **record learning progress** — follow the "Recording learning progress" contract in `${CLAUDE_PLUGIN_ROOT}/data/teaching-method.md` (read-modify-write only D5's entry of `$HOME/.claude/ccaf-progress/learning-progress.json` + shared `axis_mastery`).
When done, suggest the next step (e.g. `/ccaf:exam` or another `/ccaf:dN-teacher`). Never auto-invoke; instruct the user.
```

- [ ] **Step 6: Verify all five reference the contract and invariants are intact**

Run:
```bash
grep -lc "Recording learning progress" skills/d?-teacher/SKILL.md | wc -l | tr -d ' '   # expect 5
grep -L "disable-model-invocation: true" skills/d?-teacher/SKILL.md || echo "all keep disable-model-invocation"
```
Expected: first line `5`; second line `all keep disable-model-invocation`.

- [ ] **Step 7: Commit**

```bash
git add skills/d1-teacher/SKILL.md skills/d2-teacher/SKILL.md skills/d3-teacher/SKILL.md skills/d4-teacher/SKILL.md skills/d5-teacher/SKILL.md
git commit -m "feat(ccaf): tutors record learning progress at hand-off"
```

---

### Task 4: Load `learning-progress.json` into `HISTORY.learning` (`app-build.md`)

**Files:**
- Modify: `data/app-build.md` (the Python build block: add a loader + one `HISTORY` key + a doc note)
- Test: scratchpad build harness `/private/tmp/claude-501/-Users-dmitryantonenko-exam-ccaf-plugin/ea5bbbaf-e220-496d-9b17-485c1717a1ef/scratchpad/build_check.sh`

**Interfaces:**
- Consumes: `learning-progress.json` (Task 1 shape) from the store; the default skeleton when the file is absent.
- Produces: `HISTORY.learning` = the parsed object (or default skeleton), injected into the app via the existing `js_safe()` + `/*__HISTORY__*/{}` replacement. Task 5's renderer reads `HISTORY.learning.domains["<d>"]` and `HISTORY.learning.axis_mastery["<a>"]`.

- [ ] **Step 1: Add the loader after `stats` is loaded**

In `data/app-build.md`, inside the Python block, find:
```python
bank = json.load(open(f"{ROOT}/data/questions.json"))["questions"]
stats = json.load(open(f"{STORE}/stats.json"))
```
and insert immediately AFTER it:
```python

# ---- learning-progress (tutor task-statement coverage + drills); READ-ONLY here, never written ----
def load_learning(path):
    try:
        obj = json.load(open(path))
    except (FileNotFoundError, ValueError):
        obj = None
    skel = {"schema": 1,
            "domains": {str(d): {"status": "not_started", "last_visited": None,
                                 "task_total": None, "task_statements": {}, "drills": []} for d in range(1, 6)},
            "axis_mastery": {str(a): {"seen": 0, "correct": 0} for a in range(1, 6)}}
    if not isinstance(obj, dict):
        return skel
    obj.setdefault("domains", skel["domains"])
    obj.setdefault("axis_mastery", skel["axis_mastery"])
    return obj
LEARNING = load_learning(f"{STORE}/learning-progress.json")
```

- [ ] **Step 2: Add the `learning` key to the `HISTORY` dict**

In the same block, find the `HISTORY = { ... }` literal and add a `learning` entry (place it after `"recorded_exam_ids": recorded,`):
```python
    "recorded_exam_ids": recorded,
    "learning": LEARNING,
```

- [ ] **Step 3: Update the surrounding doc note**

Directly above `HISTORY = {`, the comment currently explains why blueprint/accuracy aren't injected. Append one sentence to that comment block so maintainers know `learning` is read-only here. Change:
```python
# Note: blueprint weights and per-domain accuracy are NOT injected — the app owns the blueprint
# (constant CCAF data) and recomputes per-domain accuracy client-side from `answered` (latest attempt
# + any unrecorded local sittings), so injecting them would just be stale duplicate data.
```
to:
```python
# Note: blueprint weights and per-domain accuracy are NOT injected — the app owns the blueprint
# (constant CCAF data) and recomputes per-domain accuracy client-side from `answered` (latest attempt
# + any unrecorded local sittings), so injecting them would just be stale duplicate data.
# `learning` IS injected (read-only) — the tutors' learning-progress.json, powering the dashboard's
# "Learning progress" card; the app only reads it, never writes back.
```

- [ ] **Step 4: Write the build harness (reuses the real Python block from `app-build.md`)**

Write `/private/tmp/claude-501/-Users-dmitryantonenko-exam-ccaf-plugin/ea5bbbaf-e220-496d-9b17-485c1717a1ef/scratchpad/build_check.sh`:
```bash
#!/usr/bin/env bash
set -euo pipefail
REPO="/Users/dmitryantonenko/exam/ccaf-plugin"
SCRATCH="/private/tmp/claude-501/-Users-dmitryantonenko-exam-ccaf-plugin/ea5bbbaf-e220-496d-9b17-485c1717a1ef/scratchpad"
export CLAUDE_PLUGIN_ROOT="$REPO"
export HOME="$SCRATCH/fakehome"
STORE="$HOME/.claude/ccaf-progress"
rm -rf "$HOME"; mkdir -p "$STORE"
# bootstrap the store exactly like Step-0 does
cp -rn "$CLAUDE_PLUGIN_ROOT/data/progress-template/." "$STORE/"
# populate a realistic learning-progress.json (D4 partially done, drill taken)
cat > "$STORE/learning-progress.json" <<'JSON'
{ "schema": 1,
  "domains": {
    "1": { "status": "not_started", "last_visited": null, "task_total": null, "task_statements": {}, "drills": [] },
    "2": { "status": "not_started", "last_visited": null, "task_total": null, "task_statements": {}, "drills": [] },
    "3": { "status": "not_started", "last_visited": null, "task_total": null, "task_statements": {}, "drills": [] },
    "4": { "status": "in_progress", "last_visited": "2026-07-18", "task_total": 6,
           "task_statements": {"4.1": {"covered": true, "ts": "2026-07-18"}, "4.2": {"covered": true, "ts": "2026-07-18"}},
           "drills": [{"ts": "2026-07-18", "score": 6, "total": 8}] },
    "5": { "status": "not_started", "last_visited": null, "task_total": null, "task_statements": {}, "drills": [] }
  },
  "axis_mastery": {
    "1": { "seen": 4, "correct": 3 }, "2": { "seen": 2, "correct": 2 }, "3": { "seen": 0, "correct": 0 },
    "4": { "seen": 5, "correct": 3 }, "5": { "seen": 1, "correct": 1 }
  } }
JSON
# extract the fenced python from app-build.md (the block between ```bash python3 - <<'PY' ... PY) and run it
python3 - "$REPO/data/app-build.md" <<'PYX'
import sys, re, subprocess, os
md = open(sys.argv[1]).read()
m = re.search(r"python3 - <<'PY'\n(.*?)\nPY", md, re.S)
assert m, "could not find the PY heredoc in app-build.md"
open(os.path.join(os.environ["HOME"], "build.py"), "w").write(m.group(1))
PYX
python3 "$HOME/build.py"
echo "--- checking output ---"
python3 - <<'PYC'
import os
html = open(os.path.join(os.environ["HOME"], ".claude/ccaf-progress/ccaf-exam.html")).read()
assert "/*__BANK__*/[]" not in html and "/*__HISTORY__*/{}" not in html, "placeholder not replaced"
assert '"learning"' in html, "HISTORY.learning missing from output"
assert '"in_progress"' in html, "learning payload not injected"
print("app-build integration ok")
PYC
```
Make it executable: `chmod +x "/private/tmp/claude-501/-Users-dmitryantonenko-exam-ccaf-plugin/ea5bbbaf-e220-496d-9b17-485c1717a1ef/scratchpad/build_check.sh"`

- [ ] **Step 5: Run the harness — expect the build to embed `HISTORY.learning`**

Run:
```bash
bash "/private/tmp/claude-501/-Users-dmitryantonenko-exam-ccaf-plugin/ea5bbbaf-e220-496d-9b17-485c1717a1ef/scratchpad/build_check.sh"
```
Expected: build prints its `wrote … | questions: … | focus: …` line, then `app-build integration ok`.

- [ ] **Step 6: Commit**

```bash
git add data/app-build.md
git commit -m "feat(ccaf): build injects learning-progress into HISTORY.learning"
```

---

### Task 5: Render the "Learning progress" dashboard card + axis-mastery mini-view (`app-template.html`)

**Files:**
- Modify: `data/app-template.html` — add CSS (near the domain-bars block ~line 134) + JS helpers and a dashboard section (in `renderDashboard`, before the axis-tally section ~line 604) + an axis-mastery line inside the existing axis loop (~line 615).

**Interfaces:**
- Consumes: `HISTORY.learning` (Task 4). Reads `HISTORY.learning.domains["1".."5"]` (`status`, `task_total`, `task_statements`, `drills`, `last_visited`) and `HISTORY.learning.axis_mastery["1".."5"]` (`seen`, `correct`). Reuses existing constants `DOMAIN_VAR`, `DOMAIN_SHORT`, `esc`, and CSS classes `.block`, `.card`, `.pad`, `.dbar-row`, `.dbar-top`, `.dname`, `.dn-full`, `.dot`, `.dval`, `.track`, `.fill`, `.axis-row`, `.axis-desc`.
- Produces: a new "Learning progress" section and per-axis "Tutor recognition N/M" lines. Both must not render (or render an empty-state hint) when there is no learning activity. Placeholders `/*__BANK__*/[]` and `/*__HISTORY__*/{}` stay untouched.

- [ ] **Step 1: Add CSS for the status chip and axis-mastery line**

In `data/app-template.html`, find (line ~134):
```css
  .focus-flag{font-size:.66rem;background:var(--accent);color:#fff;border-radius:999px;padding:.05rem .45rem;letter-spacing:.04em;text-transform:uppercase}
```
and insert immediately AFTER it:
```css
  /* ---------- learning-progress card ---------- */
  .lp-status{font-size:.66rem;font-weight:700;border-radius:999px;padding:.05rem .5rem;letter-spacing:.04em;text-transform:uppercase;white-space:nowrap}
  .lp-status.lp-not_started{background:var(--paper2);color:var(--muted)}
  .lp-status.lp-in_progress{background:var(--accent-soft);color:var(--accent2)}
  .lp-status.lp-complete{background:var(--ok-soft);color:var(--ok)}
  .axis-mastery{font-size:.82rem;color:var(--ink2);margin:.1rem 0 .2rem 1.4rem}
  .axis-mastery b{color:var(--ink);font-variant-numeric:tabular-nums}
```

- [ ] **Step 2: Add JS helpers just before `renderDashboard`**

Find (line ~497):
```javascript
/* ================= DASHBOARD ================= */
function renderDashboard(){
```
and insert BEFORE the `/* ================= DASHBOARD ================= */` comment:
```javascript
/* ---- learning progress (tutor sessions, read-only from HISTORY.learning) ---- */
const LEARNING = HISTORY.learning || null;
const LP_STATUS_LABEL = {not_started:"not started", in_progress:"in progress", complete:"complete"};
function learningDomain(d){ return (LEARNING && LEARNING.domains && LEARNING.domains[String(d)]) || null; }
function lpCovered(ld){ if(!ld||!ld.task_statements) return 0;
  return Object.values(ld.task_statements).filter(t=>t&&t.covered).length; }
function lpLatestDrill(ld){ return (ld&&ld.drills&&ld.drills.length)? ld.drills[ld.drills.length-1] : null; }
function lpAnyActivity(){ if(!LEARNING||!LEARNING.domains) return false;
  return [1,2,3,4,5].some(d=>{ const ld=LEARNING.domains[String(d)];
    return ld && ((ld.status && ld.status!=="not_started") || lpCovered(ld)>0 || (ld.drills&&ld.drills.length)); }); }
function lpAxisAny(){ const m=LEARNING&&LEARNING.axis_mastery; if(!m) return false;
  return [1,2,3,4,5].some(a=>Number((m[String(a)]||{}).seen||0)>0); }

```

- [ ] **Step 3: Add the "Learning progress" section in `renderDashboard`**

Find the end of the exam-history section (line ~602):
```javascript
  html+=`</section>`;

  /* axis tally — computed client-side from per-question axis over the user's misses (always correct
     against the current bank); HISTORY.axis_tally is only a fallback when the bank carries no axis. */
```
and insert the new section BETWEEN `html+=\`</section>\`;` and the `/* axis tally …` comment:
```javascript

  /* learning progress — tutor task-statement coverage + in-tutor drills (read-only) */
  if(lpAnyActivity()){
    html+=`<section class="block"><h2>Learning progress <span class="count">tutor task-statement coverage · in-tutor drills</span></h2><div class="card pad">`;
    for(let d=1;d<=5;d++){
      const ld=learningDomain(d);
      const status=(ld&&ld.status)||"not_started";
      const total=(ld&&ld.task_total)||null;
      const cov=lpCovered(ld);
      const pct=total?Math.round(100*cov/total):0;
      const drill=lpLatestDrill(ld);
      const lv=(ld&&ld.last_visited)||null;
      html+=`<div class="dbar-row">
        <div class="dbar-top">
          <span class="dot" style="background:var(${DOMAIN_VAR[d]})"></span>
          <span class="dname"><b>D${d}</b> <span class="dn-full">${DOMAIN_SHORT[d]}</span></span>
          <span class="lp-status lp-${status}">${LP_STATUS_LABEL[status]||esc(status)}</span>
          <span class="dval">${total?cov+"/"+total+" <small>statements</small>":"<small>not started</small>"}${drill?` <small>· drill ${drill.score}/${drill.total}</small>`:""}${lv?` <small>· seen ${esc(lv)}</small>`:""}</span>
        </div>
        <div class="track"><div class="fill" style="width:${pct}%;background:var(${DOMAIN_VAR[d]})"></div></div>
      </div>`;
    }
    html+=`</div></section>`;
  }
```

- [ ] **Step 4: Add the per-axis "Tutor recognition" line inside the axis loop**

Find, inside the axis loop (line ~615):
```javascript
      <div class="axis-desc">${AXIS_DESC[a]}</div>
      ${hasAxis?`<div class="track"><div class="fill" style="width:${Math.round(100*val/axisMax)}%;background:var(--accent)"></div></div>`:""}
    </div>`;}
```
and change it to (adds a mastery line that reads "beside" the misses tally, only when the tutor has recorded recognition for that axis):
```javascript
      <div class="axis-desc">${AXIS_DESC[a]}</div>
      ${(function(){ const m=LEARNING&&LEARNING.axis_mastery&&LEARNING.axis_mastery[String(a)];
        if(!m||!Number(m.seen)) return ""; const s=Number(m.seen), c=Number(m.correct||0);
        return `<div class="axis-mastery">Tutor recognition: <b>${c}/${s}</b> correct · ${Math.round(100*c/s)}%</div>`; })()}
      ${hasAxis?`<div class="track"><div class="fill" style="width:${Math.round(100*val/axisMax)}%;background:var(--accent)"></div></div>`:""}
    </div>`;}
```

- [ ] **Step 5: Verify the injected script is syntactically valid (extract + `node --check`)**

Run:
```bash
python3 - "data/app-template.html" > "/private/tmp/claude-501/-Users-dmitryantonenko-exam-ccaf-plugin/ea5bbbaf-e220-496d-9b17-485c1717a1ef/scratchpad/app_script.js" <<'PYX'
import sys, re
html = open(sys.argv[1]).read()
# grab the first <script>…</script> that carries the placeholders (the app logic)
blocks = re.findall(r"<script>(.*?)</script>", html, re.S)
src = next(b for b in blocks if "/*__BANK__*/" in b)
# neutralise the empty-literal placeholders so it's parseable standalone
src = src.replace("/*__BANK__*/[]", "[]").replace("/*__HISTORY__*/{}", "{}")
sys.stdout.write(src)
PYX
node --check "/private/tmp/claude-501/-Users-dmitryantonenko-exam-ccaf-plugin/ea5bbbaf-e220-496d-9b17-485c1717a1ef/scratchpad/app_script.js" && echo "script syntax ok"
```
Expected: `script syntax ok`. (If `node --check` prints a parse error, fix the JS before continuing.)

- [ ] **Step 6: Verify placeholders are still intact in the template**

Run:
```bash
grep -c "/\*__BANK__\*/\[\]" data/app-template.html   # expect 1
grep -c "/\*__HISTORY__\*/{}" data/app-template.html   # expect 1
```
Expected: `1` and `1`.

- [ ] **Step 7: End-to-end — rebuild with the populated fixture and confirm the card renders**

Re-run the build harness (it rebuilds `ccaf-exam.html` from the now-updated template), then confirm the card + mastery markup is present in the output:
```bash
bash "/private/tmp/claude-501/-Users-dmitryantonenko-exam-ccaf-plugin/ea5bbbaf-e220-496d-9b17-485c1717a1ef/scratchpad/build_check.sh"
grep -q "Learning progress" "/private/tmp/claude-501/-Users-dmitryantonenko-exam-ccaf-plugin/ea5bbbaf-e220-496d-9b17-485c1717a1ef/scratchpad/fakehome/.claude/ccaf-progress/ccaf-exam.html" && echo "card markup present"
```
Expected: `app-build integration ok` then `card markup present`.

- [ ] **Step 8 (manual, best-effort): Open the built app and confirm no console errors**

Open `…/scratchpad/fakehome/.claude/ccaf-progress/ccaf-exam.html` in a browser (or via the claude-in-chrome tools), land on the Dashboard, confirm: a "Learning progress" card with D4 showing `2/6 statements`, an `in progress` chip, `drill 6/8`, `seen 2026-07-18`; and "Tutor recognition" lines under the axes that have mastery data. Check the console is clean. (This is the spec's "no console errors" acceptance; the `node --check` gate in Step 5 is the automated proxy.)

- [ ] **Step 9: Commit**

```bash
git add data/app-template.html
git commit -m "feat(ccaf): learning-progress dashboard card + axis-mastery mini-view"
```

---

### Task 6: Mention the new card in `skills/stats/SKILL.md`

**Files:**
- Modify: `skills/stats/SKILL.md` (the "## Build & open" paragraph that lists what the dashboard shows)

**Interfaces:**
- Consumes: nothing (doc only).
- Produces: user-facing note that the dashboard now shows learning progress. No logic change (the build recipe is shared and already updated in Tasks 4–5).

- [ ] **Step 1: Edit the dashboard-contents sentence**

In `skills/stats/SKILL.md`, find:
```markdown
`/ccaf:exam` — it opens on the Dashboard). The dashboard shows overall accuracy, per-domain
accuracy vs blueprint weight with focus markers, coverage (answered vs remaining), exam history
(mock and external kept **separate**, never averaged), the 5-axis trap tally, and recurring misses.
```
and change the last line to add the learning-progress card:
```markdown
`/ccaf:exam` — it opens on the Dashboard). The dashboard shows overall accuracy, per-domain
accuracy vs blueprint weight with focus markers, coverage (answered vs remaining), exam history
(mock and external kept **separate**, never averaged), a **Learning progress** card (tutor
task-statement coverage + in-tutor drill scores + per-axis mastery, from `learning-progress.json`),
the 5-axis trap tally, and recurring misses.
```

- [ ] **Step 2: Verify**

Run:
```bash
grep -q "Learning progress" skills/stats/SKILL.md && echo "stats skill mentions card"
```
Expected: `stats skill mentions card`

- [ ] **Step 3: Commit**

```bash
git add skills/stats/SKILL.md
git commit -m "docs(ccaf): stats skill notes the learning-progress card"
```

---

### Task 7: Print a learning-progress summary in `/ccaf:init`

**Files:**
- Modify: `commands/init.md` (add a new step after Step 3, before Step 4)

**Interfaces:**
- Consumes: `learning-progress.json` (Task 1 shape) from `$HOME/.claude/ccaf-progress/`.
- Produces: a per-domain + axis-mastery text summary during onboarding. Reads only; never writes. Says so plainly when the file is missing/empty (never fabricates). `disable-model-invocation: true` unchanged; no skill call.

- [ ] **Step 1: Insert a new "Learning progress" step**

In `commands/init.md`, find:
```markdown
## Step 4 — Prior result? (first run, or on request)
```
and insert this new step immediately BEFORE it:
```markdown
## Step 3.5 — Show learning progress (from tutor sessions)
Read `$HOME/.claude/ccaf-progress/learning-progress.json` (read-only; never write it here). If it
is missing, or every domain is `not_started` with no drills, say plainly that no tutor sessions are
recorded yet and point them at `/ccaf:d1-teacher`…`/ccaf:d5-teacher` — do NOT invent progress.

Otherwise print one line per domain that has any activity, e.g.:
`D4: task statements 2/6 · last drill 6/8 · last visited 2026-07-18 · in progress`
(omit the drill part if `drills` is empty; show `task statements 0/6` when `task_total` is known but
none covered). Then print one `axis_mastery` line summarising recognition across all domains, e.g.:
`Axis recognition — 1:3/4 · 2:2/2 · 4:3/5` (show only axes with `seen > 0`; say "none yet" if all
zero). This is separate from `stats.json`'s misses-based axis tally — it's where the tutors saw you
get traps *right*.
```

- [ ] **Step 2: Verify**

Run:
```bash
grep -q "Step 3.5 — Show learning progress" commands/init.md && grep -q "learning-progress.json" commands/init.md && grep -q "disable-model-invocation: true" commands/init.md && echo "init step added, invariant intact"
```
Expected: `init step added, invariant intact`

- [ ] **Step 3: Commit**

```bash
git add commands/init.md
git commit -m "feat(ccaf): init prints learning-progress summary"
```

---

### Task 8: Version bump + regression check

**Files:**
- Modify: `.claude-plugin/plugin.json` (`version`)
- Modify: `.claude-plugin/marketplace.json` (`plugins[0].version`)

**Interfaces:**
- Consumes: nothing.
- Produces: version `0.7.0` so installed teachers/app pick up the new files.

- [ ] **Step 1: Bump `plugin.json`**

In `.claude-plugin/plugin.json`, change `"version": "0.6.6",` to `"version": "0.7.0",`.

- [ ] **Step 2: Bump `marketplace.json`**

In `.claude-plugin/marketplace.json`, change `"version": "0.6.6"` (under `plugins[0]`) to `"version": "0.7.0"`.

- [ ] **Step 3: Regression — bank validator still passes (bank unchanged, but per Global Constraints)**

Run:
```bash
python3 data/validate.py
```
Expected: validator reports OK (unique/sequential ids, valid axis/domain, meta matches) — the bank was not touched, so this must still pass.

- [ ] **Step 4: Verify versions match**

Run:
```bash
grep -q '"version": "0.7.0"' .claude-plugin/plugin.json && grep -q '"version": "0.7.0"' .claude-plugin/marketplace.json && echo "version bumped to 0.7.0"
```
Expected: `version bumped to 0.7.0`

- [ ] **Step 5: Commit**

```bash
git add .claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "chore(ccaf): bump plugin to 0.7.0 (learning-progress tracking)"
```

---

## Self-review

**Spec coverage:**
- Data model `learning-progress.json` → Task 1. ✓
- Write path "Recording learning progress" contract in `teaching-method.md` → Task 2. ✓
- One-line Hand-off reference in d1–d5 → Task 3. ✓
- `app-build.md` → `HISTORY.learning` → Task 4. ✓
- `app-template.html` "Learning progress" card + axis-mastery mini-view + graceful degrade + placeholders intact → Task 5. ✓
- `stats/SKILL.md` mention → Task 6. ✓
- `commands/init.md` text summary (per-domain + axis_mastery, plain "empty" message) → Task 7. ✓
- Version bump + validator → Task 8. ✓
- `/ccaf:result` untouched (invariant) → stated in Global Constraints; no task edits `result.md`. ✓

**Placeholder scan:** every code/JSON/markdown step contains the literal content to write; no "TBD"/"add validation"/"similar to Task N". ✓

**Type consistency:** helper names used consistently — `learningDomain`, `lpCovered`, `lpLatestDrill`, `lpAnyActivity`, `LP_STATUS_LABEL`, `LEARNING` (Task 5) all defined in Task 5 Step 2 and used in Steps 3–4. Python `LEARNING`/`load_learning` (Task 4) and JSON keys (`domains`, `task_total`, `task_statements`, `drills`, `last_visited`, `status`, `axis_mastery`, `seen`, `correct`) match the Data model reference and Task 1 skeleton throughout. ✓
```
