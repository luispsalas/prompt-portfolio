"""Checks the output checker on 33 fixed replies: real model replies, broken ones, edge cases.
No model and no cost. Usage: .venv/bin/python tests/test_validator.py  (exit 0 = all as expected)"""
import json, sys
from pathlib import Path

ENTRY = Path(__file__).resolve().parent.parent / "entries/03-structured-output"
sys.path.insert(0, str(ENTRY))
from validator import validate  # noqa: E402

cases = [json.loads(l) for l in (ENTRY / "validator-cases.jsonl").read_text().splitlines() if l.strip()]
bad = 0
for c in cases:
    r = validate(c["raw"], c.get("error"))
    ok = r["ok"] == c["expect_ok"] and r["problem"] == c["expect_problem"]
    bad += not ok
    print(f"{'ok  ' if ok else 'FAIL'} {c['id']:22} accepted={str(r['ok']):5} {r['problem'] or ''}"
          + (f"  extra fields: {r['extra_fields']}" if r["extra_fields"] else ""))
print(f"{len(cases)} cases, {bad} unexpected")
sys.exit(1 if bad or len(cases) == 0 else 0)
