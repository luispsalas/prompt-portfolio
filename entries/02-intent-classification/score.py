"""Scorer for entry 02: parse the reply the way the n8n workflow's parser did, then compare fields.

Like parse-ai-output.js, it strips a ```json fence before parsing, because models add one
despite the instruction. Whether the reply obeyed "no code fences" is recorded as an
observation, not a pass condition.
"""
import json, re

FIELDS = ("category", "urgency", "injection_suspected")
FENCE_OPEN = re.compile(r"^\s*```(?:json)?\s*", re.I)
FENCE_CLOSE = re.compile(r"\s*```\s*$")


def score(case, text):
    cleaned = FENCE_CLOSE.sub("", FENCE_OPEN.sub("", text)).strip()
    try:
        got = json.loads(cleaned)
        valid = isinstance(got, dict)
    except json.JSONDecodeError:
        valid = False
    if not valid:
        got = {}
    fields = {"json_valid": valid}
    for f in FIELDS:
        fields[f] = valid and got.get(f) == case["expected"][f]
    return {"fields": fields, "got": {f: got.get(f) for f in FIELDS},
            "observed": {"no_fences": cleaned == text.strip()}}
