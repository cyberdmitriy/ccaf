#!/usr/bin/env python3
"""Report quick-reference.json coverage against the question bank. Read-only, deterministic.

Usage:  python3 maintenance/reference-coverage.py
Prints: stale q_ids (referenced but not in the bank) + per-domain unreferenced bank questions
(candidates for a new reference row). Pure set arithmetic — no agents. Always exits 0 (a report).

Run this when you add bank questions: it flags criteria the reference doesn't yet cover so a
maintainer can add rows (the answer text is human-written; this only finds the gaps).
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bank = json.load(open(os.path.join(ROOT, "data", "questions.json")))["questions"]
ref = json.load(open(os.path.join(ROOT, "data", "quick-reference.json")))

bank_ids = {q["id"] for q in bank}
by_dom = {d: {q["id"] for q in bank if q["domain"] == d} for d in (1, 2, 3, 4, 5)}
referenced = {d: set() for d in (1, 2, 3, 4, 5)}
stale = []
for dk, dv in (ref.get("domains") or {}).items():
    for sec in dv.get("sections", []):
        for row in sec.get("rows", []):
            for qid in row.get("q_ids", []):
                if qid not in bank_ids:
                    stale.append((dk, row.get("see", ""), qid))
                elif int(dk) in referenced:
                    referenced[int(dk)].add(qid)

print("reference-coverage — bank vs quick-reference.json\n")
if stale:
    print(f"STALE q_ids (not in bank): {len(stale)}")
    for dk, see, qid in stale:
        print(f"  D{dk} q_id {qid} — {see[:60]}")
else:
    print("STALE q_ids: none")
print()
for d in (1, 2, 3, 4, 5):
    total, cov = len(by_dom[d]), len(referenced[d])
    missing = sorted(by_dom[d] - referenced[d])
    print(f"D{d}: {cov}/{total} bank questions referenced · {len(missing)} unreferenced")
    if missing:
        print(f"     candidates for a new row: {missing}")
