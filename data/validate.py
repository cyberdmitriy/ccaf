#!/usr/bin/env python3
"""Validate data/questions.json against the schema + authoring invariants in CLAUDE.md.

Usage:  python3 data/validate.py           (run from the plugin root)
        python3 validate.py                (run from data/)

Exits 0 if the bank is valid, 1 otherwise. Read-only — never mutates the file.
Checks: unique sequential ids · A–D options · valid `correct` · `axis` 1–5 on every entry ·
meta.total and meta.per_domain match reality · reports the correct-answer-letter distribution
(overall + per domain) and warns on a heavy skew · flags any `</script>`/`<!--` that would break
the injected HTML app · flags empty explanations.
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

    # correct-answer-letter balance (report; warn on heavy skew)
    letters = collections.Counter(q.get("correct") for q in qs)
    hi, lo = max(letters.values()), min(letters.values())
    if hi - lo > max(8, 0.15 * len(qs)):
        warnings.append(f"correct-letter distribution is skewed: {dict(sorted(letters.items()))}")

    print(f"bank: {len(qs)} questions | per_domain: {dict(sorted(actual_pd.items()))}")
    print(f"correct-letter: {dict(sorted(letters.items()))}")
    print("axis: " + str(dict(sorted(collections.Counter(q.get('axis') for q in qs).items()))))
    for w in warnings:
        print(f"WARN: {w}")
    if errors:
        for e in errors:
            print(f"FAIL: {e}")
        print(f"\n{len(errors)} error(s).")
        return 1
    print("\nok — bank is valid.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
