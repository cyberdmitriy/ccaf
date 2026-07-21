# Shared build recipe — the CCAF study app (`ccaf-exam.html`)

Both `/ccaf:dashboard` and `/ccaf:dashboard` build the **same** self-contained offline app from
`app-template.html` + the user's progress store, then open it. This file is the single source of
truth for that build so the two skills stay in sync. Follow it verbatim.

> **ALWAYS REBUILD — never open a stale file.** `ccaf-exam.html` is a disposable build artifact.
> On **every** `/ccaf:dashboard` and `/ccaf:dashboard`, run Steps 1–4 in full and **overwrite** any existing
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
Do NOT hand-copy the question bank or hand-edit the template. Run this Python verbatim (no values to
edit). It reads the bank + `stats.json` + `profile.md`, composes the authoritative `HISTORY` object
exactly as the template expects, injects all three placeholders (bank, history, reference), writes the single app file, and validates it.

```bash
python3 - <<'PY'
import json, os, re
ROOT = os.environ["CLAUDE_PLUGIN_ROOT"]
HOME = os.environ["HOME"]
STORE = f"{HOME}/.claude/ccaf-progress"

# ---- explicit focus domains, parsed straight from profile.md's "## Focus domains" section ----
def parse_profile_focus(path):
    try:
        txt = open(path).read()
    except FileNotFoundError:
        return []
    m = re.search(r'##\s*Focus domains(.*?)(?:\n##\s|\Z)', txt, re.S | re.I)
    if not m:
        return []
    seg = m.group(1)
    out = []
    for mm in re.finditer(r'\bD?([1-5])\b', seg):   # "D3", "3", etc.; placeholder text has no 1–5
        d = int(mm.group(1))
        if d not in out:
            out.append(d)                            # preserve written order (weakest first)
    return out
PROFILE_FOCUS = parse_profile_focus(f"{STORE}/profile.md")
# ---------------------------------------------------------------------------------------------

bank = json.load(open(f"{ROOT}/data/questions.json"))["questions"]
try:
    REFERENCE = json.load(open(f"{ROOT}/data/quick-reference.json"))  # bundled see→answer map
except Exception:
    REFERENCE = {}   # graceful: the Reference tab shows a hint if the file is missing/unreadable
stats = json.load(open(f"{STORE}/stats.json"))

# ---- learning-progress (tutor task-statement coverage + drills); READ-ONLY here, never written ----
# Distinguish ABSENT (expected first run -> skeleton, no warning) from PRESENT-BUT-CORRUPT
# (surface it -> the app shows a warning instead of silently rendering zero progress).
def load_learning(path):
    skel = {"schema": 1,
            "domains": {str(d): {"status": "not_started", "last_visited": None,
                                 "task_total": None, "task_statements": {}, "drills": []} for d in range(1, 6)},
            "axis_mastery": {str(a): {"seen": 0, "correct": 0} for a in range(1, 6)}}
    if not os.path.exists(path):
        return skel, False                 # absent -> expected first run
    try:
        obj = json.load(open(path))
    except ValueError:
        return skel, True                  # present but unparseable -> surface, don't pretend it's empty
    if not isinstance(obj, dict):
        return skel, True
    obj.setdefault("domains", skel["domains"])
    obj.setdefault("axis_mastery", skel["axis_mastery"])
    return obj, False
LEARNING, LEARNING_UNREADABLE = load_learning(f"{STORE}/learning-progress.json")

# ---- cheatsheet (miss-driven "trigger -> rule" table); READ-ONLY here, never written ----
# Same ABSENT vs PRESENT-BUT-CORRUPT discipline as load_learning: absent -> empty skeleton, no
# warning (expected first run); present but unparseable -> surface it so the app shows a banner
# instead of silently rendering an empty cheatsheet.
def load_cheatsheet(path):
    skel = {"schema": 1, "entries": {}}
    if not os.path.exists(path):
        return skel, False
    try:
        obj = json.load(open(path))
    except ValueError:
        return skel, True
    if not isinstance(obj, dict):
        return skel, True
    if "entries" in obj and not isinstance(obj["entries"], dict):
        return skel, True                  # present but wrong type -> surface
    obj.setdefault("schema", 1)
    obj.setdefault("entries", {})          # missing key tolerated, mirrors load_learning
    return obj, False
CHEATSHEET, CHEATSHEET_UNREADABLE = load_cheatsheet(f"{STORE}/cheatsheet.json")

# answered: transform the store's {attempts:[...], last_correct} -> {last_correct, attempts:<count>, last_ts}
# last_ts (ISO ts of the MOST RECENT attempt) drives the app's spaced-repetition "due" term in weak mode.
answered = {}
for qid, rec in (stats.get("answered") or {}).items():
    att = rec.get("attempts")
    if isinstance(att, list):
        count = len(att)
        last = att[-1] if att else None
        last_ts = last.get("ts") if isinstance(last, dict) else None
    else:
        count = att if isinstance(att, int) else 1
        last_ts = rec.get("last_ts")  # fallback for a compact/older record shape
    answered[str(qid)] = {"last_correct": bool(rec.get("last_correct")), "attempts": count, "last_ts": last_ts}

per_domain = stats.get("per_domain") or {str(d): {"seen":0,"correct":0} for d in range(1,6)}
exam_history = stats.get("exam_history") or []
recorded = [e["exam_id"] for e in exam_history if e.get("exam_id")]

# focus: profile's explicit list wins; else the up-to-2 lowest-accuracy domains with data; else []
focus = list(PROFILE_FOCUS or [])
if not focus:
    accs = []
    for d in range(1,6):
        pd = per_domain.get(str(d), {}); seen = pd.get("seen",0)
        if seen: accs.append((pd.get("correct",0)/seen, d))
    accs.sort()
    focus = [d for _,d in accs[:2]]

counts = {}
for q in bank: counts[str(q["domain"])] = counts.get(str(q["domain"]),0)+1

# Note: blueprint weights and per-domain accuracy are NOT injected — the app owns the blueprint
# (constant CCAF data) and recomputes per-domain accuracy client-side from `answered` (latest attempt
# + any unrecorded local sittings), so injecting them would just be stale duplicate data.
# `learning` IS injected (read-only) — the tutors' learning-progress.json, powering the dashboard's
# "Learning progress" card; the app only reads it, never writes back.
HISTORY = {
    "generated_at": "",  # optional label; leave "" (no clock available here)
    "bank_total": len(bank),
    "domain_totals": counts,
    "focus_domains": focus,
    "answered": answered,
    "axis_tally": stats.get("axis_tally") or {"1":0,"2":0,"3":0,"4":0,"5":0},
    "exam_history": exam_history,
    "recorded_exam_ids": recorded,
    "learning": LEARNING,
    "learning_unreadable": LEARNING_UNREADABLE,
    "cheatsheet": CHEATSHEET,
    "cheatsheet_unreadable": CHEATSHEET_UNREADABLE,
}

tpl = open(f"{ROOT}/data/app-template.html").read()
# The bank + HISTORY + REFERENCE are injected inside a <script> tag, so escape any "</" (e.g. a stray
# "</script>" in a question or an external result's free-text label) — "<\/" is an identical
# JS string but can't terminate the script early. Also neutralise "<!--".
def js_safe(obj):
    return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/").replace("<!--", "<\\!--")
out = tpl.replace("/*__BANK__*/[]", js_safe(bank))
out = out.replace("/*__HISTORY__*/{}", js_safe(HISTORY))
out = out.replace("/*__REFERENCE__*/{}", js_safe(REFERENCE))
assert "/*__BANK__*/[]" not in out and "/*__HISTORY__*/{}" not in out \
    and "/*__REFERENCE__*/{}" not in out, "placeholder not replaced"
dest = f"{STORE}/ccaf-exam.html"
open(dest, "w").write(out)
print("wrote", dest, "| questions:", len(bank), "| answered:", len(answered),
      "| exams:", len(exam_history), "| focus:", focus)
PY
```

## Step 4 — Open the app
macOS: `open "$HOME/.claude/ccaf-progress/ccaf-exam.html"`  ·  Linux: `xdg-open …`.
If opening fails, print the path and tell the user to open it manually.

## Notes / invariants
- **Single file, overwritten** each build (`ccaf-exam.html`). No per-exam files, no archive.
- The app **never** writes to the store — it holds in-progress + unrecorded sittings in
  `localStorage` and hands results back via copy-JSON for `/ccaf:result` to record.
- Unrecorded sittings are reconciled on the next build via `recorded_exam_ids` (the page drops any
  local sitting whose `exam_id` is already recorded), so nothing is double-counted.
- Focus is **data-driven** (profile's explicit list, else lowest-accuracy domains) — never hardcode
  a person's results.
