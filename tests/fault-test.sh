#!/bin/sh
# Proves the harness can fail: a deliberately broken prompt must score below threshold (exit 1),
# and a spend cap of 0 must stop the run as incomplete (exit 2). Costs about $0.001 on Haiku 5.5.
cd "$(dirname "$0")/.." || exit 2
PY=.venv/bin/python
ENTRY=02-intent-classification
BROKEN=$(mktemp)
# Fault: replace the JSON output instruction with a plain-English one.
$PY -I - "$BROKEN" <<'PYEOF'
import sys
t = open("entries/02-intent-classification/system-v1.txt").read()
marker = "Reply with exactly one JSON object"
assert t.count(marker) == 1, "fault anchor not found"
open(sys.argv[1], "w").write(t[: t.index(marker)] + "Reply in one short plain-English sentence naming the category and urgency.\n")
PYEOF
[ $? -eq 0 ] || { echo "FAIL: could not build the broken prompt"; exit 2; }
$PY harness/run.py $ENTRY --limit 3 --system-file "$BROKEN" >/dev/null; got=$?
rm -f "$BROKEN"
[ $got -eq 1 ] && echo "ok: broken prompt fails (exit 1)" || { echo "FAIL: broken prompt gave exit $got, expected 1"; exit 1; }
$PY harness/run.py $ENTRY --max-cost 0 >/dev/null; got=$?
[ $got -eq 2 ] && echo "ok: spend cap stops the run (exit 2)" || { echo "FAIL: spend cap gave exit $got, expected 2"; exit 1; }
echo "fault test passed"
