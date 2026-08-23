#!/usr/bin/env python3
"""Deterministic CCAF app builder: bootstrap store -> build ccaf-exam.html -> (optional) open.

Usage: python3 data/build-app.py [--open]
Reads $CLAUDE_PLUGIN_ROOT + $HOME. Read-only w.r.t. the store except writing ccaf-exam.html.
--open opens the file ONLY when stdout is a TTY (so headless/-p/cron never block on a GUI).

This is the single source of truth for the build. The UserPromptSubmit hook (hooks/ccaf-build.sh)
runs it on /ccaf:init and /ccaf:dashboard for a deterministic rebuild; data/app-build.md and the
skills call it as a belt-and-braces fallback.
"""
import json, os, re, sys, shutil, subprocess

ROOT = os.environ.get("CLAUDE_PLUGIN_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOME = os.environ.get("HOME") or os.path.expanduser("~")
STORE = f"{HOME}/.claude/ccaf-progress"

# ---- bootstrap the per-user store from the template, never overwriting (mirrors `cp -rn`) ----
os.makedirs(STORE, exist_ok=True)
_tpl = f"{ROOT}/data/progress-template"
if os.path.isdir(_tpl):
    for dirpath, _, files in os.walk(_tpl):
        rel = os.path.relpath(dirpath, _tpl)
        dest_dir = STORE if rel == "." else f"{STORE}/{rel}"
        os.makedirs(dest_dir, exist_ok=True)
        for fn in files:
            d = f"{dest_dir}/{fn}"
            if not os.path.exists(d):
                shutil.copy2(f"{dirpath}/{fn}", d)

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

# ---- stats.json (authoritative history); READ-ONLY here. Same ABSENT vs PRESENT-BUT-CORRUPT
# discipline as load_learning/load_cheatsheet + God Rule #11: a malformed real file is backed up to
# .bak and SURFACED (never silently skeleton-recreated / never crashing the whole build). ----
def load_stats(path):
    skel = {"answered": {}, "per_domain": {}, "exam_history": [],
            "axis_tally": {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}}
    if not os.path.exists(path):
        return skel, False                 # absent -> expected first run (bootstrap normally copies it)
    try:
        with open(path) as f:
            obj = json.load(f)
    except ValueError:
        try:
            shutil.copy2(path, path + ".bak")   # preserve the corrupt file, don't overwrite it
        except Exception:
            pass
        print(f"WARNING: {path} is malformed — backed up to {path}.bak; building with empty stats.")
        return skel, True
    if not isinstance(obj, dict):
        return skel, True
    return obj, False
stats, STATS_UNREADABLE = load_stats(f"{STORE}/stats.json")

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

# ---- settings: per-user learning_language (READ-ONLY) — drives the Weaknesses tab's localized labels.
# Content is still authored per learning_language by the skills; this only localizes the few chrome LABELS
# that sit directly on that localized content (Invariant #8 carve-out). Free-form string; the app maps the
# ones it has a translation for and falls back to English for any it doesn't.
def load_language(path):
    try:
        lang = (json.load(open(path)) or {}).get("learning_language")
        return lang if isinstance(lang, str) and lang.strip() else "English"
    except Exception:
        return "English"
LANG = load_language(f"{STORE}/settings.json")

# answered: transform the store's {attempts:[...], last_correct} -> {last_correct, attempts:<count>, last_ts, misses:[...]}
# last_ts (ISO ts of the MOST RECENT attempt) drives the app's spaced-repetition "due" term in weak mode.
# misses = the wrong attempts as {exam_id, ts} — lets the Weaknesses tab tie each failed question to the
# exam (date + ordinal) it was missed in. Empty for compact/older records with no per-attempt list.
answered = {}
for qid, rec in (stats.get("answered") or {}).items():
    att = rec.get("attempts")
    misses = []
    right = wrong = 0
    if isinstance(att, list):
        count = len(att)
        last = att[-1] if att else None
        last_ts = last.get("ts") if isinstance(last, dict) else None
        for a in att:
            if isinstance(a, dict):
                if a.get("correct"):
                    right += 1
                else:
                    wrong += 1
                    if a.get("exam_id"):
                        misses.append({"exam_id": a.get("exam_id"), "ts": a.get("ts")})
    else:
        count = att if isinstance(att, int) else 1
        last_ts = rec.get("last_ts")  # fallback for a compact/older record shape (no per-attempt breakdown)
    answered[str(qid)] = {"last_correct": bool(rec.get("last_correct")), "attempts": count, "last_ts": last_ts, "misses": misses, "right": right, "wrong": wrong}

per_domain = stats.get("per_domain") or {str(d): {"seen":0,"correct":0} for d in range(1,6)}
exam_history = stats.get("exam_history") or []
recorded = [e["exam_id"] for e in exam_history if e.get("exam_id")]

# focus: RECENT mock performance drives it — the up-to-2 domains with the highest per-domain error
# RATE over the last few mock sittings — so focus tracks where you're CURRENTLY slipping, not a frozen
# cumulative rank. Cold-start fallbacks (no mock data yet): profile.md "## Focus domains" (written by
# /ccaf:result), then the lowest-accuracy domains over all history, then []. Kept here (never hardcoded)
# per invariant #3. Error RATE (not raw count) is fair across domains of different blueprint size.
_BLUEPRINT = {1: 27, 2: 18, 3: 20, 4: 20, 5: 15}   # CCAF exam weights (constant) — tie-break only
def recent_focus(history, n=5):
    mocks = [e for e in history if e.get("type") == "mock" and e.get("per_domain")]
    mocks.sort(key=lambda e: str(e.get("ts") or ""), reverse=True)   # newest first
    agg = {}                                                          # domain -> [seen, wrong]
    for e in mocks[:n]:                                              # last N mock sittings (3–5 window)
        for d in range(1, 6):
            pd = (e.get("per_domain") or {}).get(str(d)) or {}
            total = pd.get("total", 0) or 0
            if total:
                a = agg.setdefault(d, [0, 0])
                a[0] += total
                a[1] += (total - (pd.get("correct", 0) or 0))
    cands = [(d, s, w) for d, (s, w) in agg.items() if s > 0 and w > 0]   # only domains with actual misses
    # rank: error rate desc, then abs wrong desc, then blueprint weight desc, then domain number asc
    cands.sort(key=lambda t: (-(t[2] / t[1]), -t[2], -_BLUEPRINT.get(t[0], 0), t[0]))
    return [d for d, _, _ in cands[:2]]   # all-correct recent mocks → [] → falls through to profile/accuracy

focus = recent_focus(exam_history) or list(PROFILE_FOCUS or [])
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
    "stats_unreadable": STATS_UNREADABLE,
    "learning_language": LANG,   # localizes only the Weaknesses content-labels; rest of the chrome stays English
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

# open when asked, unless an explicit headless opt-out is set.
# NOTE: do NOT gate on sys.stdout.isatty() — inside Claude Code stdout is ALWAYS a pipe (a hook, or
# the Bash tool), so isatty() is False even in a normal interactive session and would wrongly suppress
# the GUI. `open`/`xdg-open` return immediately and no-op harmlessly when there's no display (true
# headless), so an explicit env opt-out (CCAF_NO_OPEN) is the only guard we need.
if "--open" in sys.argv and not os.environ.get("CCAF_NO_OPEN"):
    try:
        opener = "open" if sys.platform == "darwin" else "xdg-open"
        subprocess.run([opener, dest], check=False)
    except Exception as e:
        print("could not open automatically:", dest, "(", e, ")")
