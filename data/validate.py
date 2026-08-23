#!/usr/bin/env python3
"""Validate data/questions.json against the schema + authoring invariants in CLAUDE.md.

Usage:  python3 data/validate.py                     (validate the question bank)
        python3 validate.py                          (same, run from data/)
        python3 data/validate.py --learning <path>   (validate a learning-progress.json shape)

Exits 0 if valid, 1 otherwise. Read-only — never mutates the file.
Bank checks: unique sequential ids · A–D options · valid `correct` · `axis` 1–5 on every entry ·
canonical `task` (a key in task-statements.json, domain-prefix matching `domain`) on every entry ·
meta.total and meta.per_domain match reality · reports the correct-answer-letter distribution
(overall + per domain) and warns on a heavy skew · flags any `</script>`/`<!--` that would break
the injected HTML app · flags empty explanations. Also shape-checks task-statements.json itself.
`--learning`: shape-checks a per-user learning-progress.json (schema · domains 1–5 with the right
keys and a valid status · axis_mastery 1–5 with int seen/correct · drills/task_statements shape).
Useful in the maintenance runbook and after hand-off writes.
"""
import json, os, sys, collections

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(HERE, "questions.json")

def main():
    try:
        d = json.load(open(PATH))
    except Exception as e:
        print(f"FAIL: cannot read/parse {PATH}: {e}")
        return 1
    qs = d.get("questions", [])
    meta = d.get("meta", {})
    errors, warnings = [], []

    # canonical task-statement map (single source of truth for the per-question `task` tag)
    ts_path = os.path.join(HERE, "task-statements.json")
    task_keys = set()
    try:
        tsdoc = json.load(open(ts_path))
        statements = tsdoc.get("statements", {})
        if not isinstance(statements, dict) or not statements:
            errors.append("task-statements.json: 'statements' missing or empty")
        else:
            task_keys = set(statements)
            for k, v in statements.items():
                parts = str(k).split(".")
                if len(parts) != 2 or parts[0] not in {"1", "2", "3", "4", "5"} or not parts[1].isdigit():
                    errors.append(f"task-statements.json: bad key {k!r} (want <d>.<n>)")
                if not (isinstance(v, str) and v.strip()):
                    errors.append(f"task-statements.json: {k} has empty label")
            ts_pd = collections.Counter(str(k).split(".")[0] for k in statements)
            expected_ts_pd = {"1": 7, "2": 6, "3": 7, "4": 6, "5": 6}
            if dict(ts_pd) != expected_ts_pd:
                errors.append(f"task-statements.json: per-domain counts {dict(sorted(ts_pd.items()))} != {expected_ts_pd}")
    except Exception as e:
        errors.append(f"task-statements.json: cannot read/parse: {e}")

    # ids: unique + sequential 1..N
    ids = [q.get("id") for q in qs]
    if len(set(ids)) != len(ids):
        dupes = [i for i, c in collections.Counter(ids).items() if c > 1]
        errors.append(f"duplicate ids: {dupes}")
    if ids != list(range(1, len(qs) + 1)):
        errors.append("ids are not sequential 1..N (append-only, never renumber)")

    # per-question shape
    for q in qs:
        qid = q.get("id")
        if set(q.get("options", {})) < {"A", "B", "C", "D"}:
            errors.append(f"q{qid}: options missing one of A–D")
        if q.get("correct") not in q.get("options", {}):
            errors.append(f"q{qid}: correct {q.get('correct')!r} not in options")
        if q.get("axis") not in (1, 2, 3, 4, 5):
            errors.append(f"q{qid}: axis {q.get('axis')!r} not in 1–5")
        if q.get("domain") not in (1, 2, 3, 4, 5):
            errors.append(f"q{qid}: domain {q.get('domain')!r} not in 1–5")
        t = q.get("task")
        if not t:
            errors.append(f"q{qid}: missing task")
        elif task_keys and t not in task_keys:
            errors.append(f"q{qid}: task {t!r} not in task-statements.json")
        elif str(t).split(".")[0] != str(q.get("domain")):
            errors.append(f"q{qid}: task {t!r} domain-prefix != domain {q.get('domain')}")
        if not q.get("explanation"):
            warnings.append(f"q{qid}: empty explanation")
        for field in ("stem", "explanation", *q.get("options", {}).values()):
            s = str(field)
            if "</script" in s.lower() or "<!--" in s:
                errors.append(f"q{qid}: contains '</script>' or '<!--' (breaks the injected HTML app)")

    # meta counts match reality
    actual_pd = collections.Counter(str(q.get("domain")) for q in qs)
    if meta.get("total") != len(qs):
        errors.append(f"meta.total {meta.get('total')} != actual {len(qs)}")
    meta_pd = {str(k): v for k, v in (meta.get("per_domain") or {}).items()}
    if meta_pd != dict(actual_pd):
        errors.append(f"meta.per_domain {meta_pd} != actual {dict(sorted(actual_pd.items()))}")

    # quick-reference.json (curated see→answer map): domains 1–5, non-empty see/answer,
    # q_ids a list of ids that exist in the bank. No axis field (axis lives in questions.json).
    # Each section IS a task statement — its title must start with a valid "<d>.<n>" of that domain.
    ref_path = os.path.join(HERE, "quick-reference.json")
    ref_rows = None
    if os.path.exists(ref_path):
        ref_rows = 0
        try:
            ref = json.load(open(ref_path))
        except Exception as e:
            errors.append(f"reference: cannot parse quick-reference.json: {e}")
            ref = None
        if ref is not None:
            bank_ids = set(ids)
            for dk, dv in (ref.get("domains") or {}).items():
                if dk not in {"1", "2", "3", "4", "5"}:
                    errors.append(f"reference: bad domain key {dk!r}")
                if not dv.get("title"):
                    errors.append(f"reference: domain {dk} missing title")
                for si, sec in enumerate(dv.get("sections", [])):
                    title = sec.get("title")
                    if not title:
                        errors.append(f"reference: domain {dk} section {si} missing title")
                    else:
                        # each section IS a task statement: title starts with its "<d>.<n>" (matching
                        # task-statements.json) so the Cheatsheet tab lines up with the tutors + the bank `task`.
                        head = str(title).split(" ", 1)[0]
                        if task_keys and head not in task_keys:
                            errors.append(f"reference: D{dk} section {si} title must start with a task-statement number, got {head!r}")
                        elif head.split(".")[0] != dk:
                            errors.append(f"reference: D{dk} section {si} title number {head!r} is not a domain-{dk} task statement")
                    for ri, row in enumerate(sec.get("rows", [])):
                        ref_rows += 1
                        loc = f"reference: D{dk} sec{si} row{ri}"
                        if not row.get("see") or not row.get("answer"):
                            errors.append(f"{loc}: missing see/answer")
                        q_ids = row.get("q_ids", [])
                        if not isinstance(q_ids, list):
                            errors.append(f"{loc}: q_ids must be a list")
                        else:
                            for qid in q_ids:
                                if qid not in bank_ids:
                                    errors.append(f"{loc}: q_id {qid} not in bank")

    # correct-answer-letter balance (report; warn on heavy skew)
    letters = collections.Counter(q.get("correct") for q in qs)
    hi, lo = max(letters.values()), min(letters.values())
    if hi - lo > max(8, 0.15 * len(qs)):
        warnings.append(f"correct-letter distribution is skewed: {dict(sorted(letters.items()))}")

    print(f"bank: {len(qs)} questions | per_domain: {dict(sorted(actual_pd.items()))}")
    print(f"correct-letter: {dict(sorted(letters.items()))}")
    print("axis: " + str(dict(sorted(collections.Counter(q.get('axis') for q in qs).items()))))
    print("task: " + str(dict(sorted(collections.Counter(q.get('task') for q in qs).items(), key=lambda kv: (str(kv[0]))))))
    if ref_rows is not None:
        print(f"reference: {ref_rows} rows")
    for w in warnings:
        print(f"WARN: {w}")
    if errors:
        for e in errors:
            print(f"FAIL: {e}")
        print(f"\n{len(errors)} error(s).")
        return 1
    print("\nok — bank is valid.")
    return 0

def validate_learning(path):
    """Shape-check a learning-progress.json. Read-only. Returns 0 if valid, 1 otherwise."""
    try:
        d = json.load(open(path))
    except FileNotFoundError:
        print(f"FAIL: no such file: {path}")
        return 1
    except ValueError as e:
        print(f"FAIL: {path} is not valid JSON: {e}")
        return 1
    errors = []
    if not isinstance(d, dict):
        print("FAIL: top level is not an object")
        return 1
    if d.get("schema") != 1:
        errors.append(f"schema {d.get('schema')!r} != 1")
    domains = d.get("domains")
    if not isinstance(domains, dict) or set(domains) != {"1", "2", "3", "4", "5"}:
        errors.append(f"domains keys must be exactly 1–5, got {sorted(domains) if isinstance(domains, dict) else type(domains).__name__}")
        domains = {}
    for k, v in (domains or {}).items():
        if not isinstance(v, dict):
            errors.append(f"domains[{k}] is not an object"); continue
        if set(v) != {"status", "last_visited", "task_total", "task_statements", "drills"}:
            errors.append(f"domains[{k}] keys {sorted(v)} != status/last_visited/task_total/task_statements/drills")
        if v.get("status") not in ("not_started", "in_progress", "complete"):
            errors.append(f"domains[{k}].status {v.get('status')!r} invalid")
        tt = v.get("task_total")
        if tt is not None and not isinstance(tt, int):
            errors.append(f"domains[{k}].task_total must be int or null")
        ts = v.get("task_statements")
        if not isinstance(ts, dict):
            errors.append(f"domains[{k}].task_statements must be an object")
        else:
            for sid, sv in ts.items():
                if not isinstance(sv, dict) or "covered" not in sv:
                    errors.append(f"domains[{k}].task_statements[{sid}] must be {{covered, ts}}")
        drills = v.get("drills")
        if not isinstance(drills, list):
            errors.append(f"domains[{k}].drills must be a list")
        else:
            for i, dr in enumerate(drills):
                if not (isinstance(dr, dict) and isinstance(dr.get("score"), int) and isinstance(dr.get("total"), int)):
                    errors.append(f"domains[{k}].drills[{i}] must be {{ts, score:int, total:int}}")
    am = d.get("axis_mastery")
    if not isinstance(am, dict) or set(am) != {"1", "2", "3", "4", "5"}:
        errors.append("axis_mastery keys must be exactly 1–5")
    else:
        for k, v in am.items():
            if not (isinstance(v, dict) and isinstance(v.get("seen"), int) and isinstance(v.get("correct"), int)):
                errors.append(f"axis_mastery[{k}] must be {{seen:int, correct:int}}")
    if errors:
        for e in errors:
            print(f"FAIL: {e}")
        print(f"\n{len(errors)} error(s).")
        return 1
    print(f"ok — learning-progress at {path} is valid.")
    return 0

if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "--learning":
        if len(sys.argv) < 3:
            print("usage: python3 validate.py --learning <path-to-learning-progress.json>")
            sys.exit(2)
        sys.exit(validate_learning(sys.argv[2]))
    sys.exit(main())
