"""Check a model reply before anything relies on it.

Python port of the original workflow's output checker (parse-ai-output.js), with the
same verdicts and reasons, plus two additions:
  - a reply that is valid JSON but not an object (e.g. `null`) is rejected with a reason;
    the original crashed on it
  - fields the reply should not contain are reported in `extra_fields` (the original
    ignored them silently; the verdict is unchanged, so they are still never trusted)

A rejected reply goes to the fallback path: a person handles the request.
"""
import json
import re

CATEGORIES = ["software", "hardware", "professional_services", "events", "training", "other"]
URGENCIES = ["low", "normal", "high"]
ALLOWED = {"category", "urgency", "summary", "injection_suspected"}


def _js(v):
    """Render a value the way JavaScript's template strings do, so reasons match the original."""
    if v is None:
        return "undefined"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (dict, list)):
        return json.dumps(v)
    return str(v)


def validate(raw, error=None):
    """Return {"ok": bool, "problem": str, "data": dict, "extra_fields": list}."""
    if error:
        return {"ok": False, "problem": f"AI call failed: {str(error)[:200]}", "data": {}, "extra_fields": []}
    # Models sometimes wrap JSON in ```json fences despite instructions: strip them, as the original did.
    cleaned = re.sub(r"\s*```\s*$", "", re.sub(r"^\s*```(?:json)?\s*", "", str(raw), flags=re.I)).strip()
    try:
        ai = json.loads(cleaned)
    except json.JSONDecodeError:
        return {"ok": False, "problem": "reply is not valid JSON", "data": {}, "extra_fields": []}
    if not isinstance(ai, dict):
        return {"ok": False, "problem": "reply is not a JSON object", "data": {}, "extra_fields": []}
    extra = sorted(set(ai) - ALLOWED)
    problem = ""
    if ai.get("category") not in CATEGORIES:
        problem = f"unknown category: {_js(ai.get('category'))}"
    elif ai.get("urgency") not in URGENCIES:
        problem = f"unknown urgency: {_js(ai.get('urgency'))}"
    elif not isinstance(ai.get("summary"), str) or not ai["summary"].strip():
        problem = "missing summary"
    elif not isinstance(ai.get("injection_suspected"), bool):
        problem = "injection_suspected is not true/false"
    data = {} if problem else {k: ai[k] for k in ALLOWED}
    return {"ok": not problem, "problem": problem, "data": data, "extra_fields": extra}
