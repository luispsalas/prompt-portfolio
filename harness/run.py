"""Run each entry's test set against a Claude model and save a results table.

Usage (from the repo root):
  .venv/bin/python harness/run.py                      # every entry, default model
  .venv/bin/python harness/run.py 02-intent-classification --model claude-haiku-4-5-20251001
Options:
  --model ID          model to test (must have settings in the entry's entry.json)
  --prompt NAME       which prompt version from entry.json "prompts" (default: the entry's default_prompt)
  --set NAME          which test set from entry.json "cases" (default: the first one listed)
  --system-file PATH  use this system prompt instead (for fault tests)
  --limit N           run only the first N cases
  --max-cost USD      stop before spending more than this (default 0.50)

Exit status: 0 = every entry met its thresholds; 1 = an entry fell short;
2 = the run could not be completed (setup problem, API error, spend cap reached).
An API error is never counted as a model failure: the run is reported as incomplete.

Each entry folder holds entry.json, its prompt files, cases.jsonl and score.py, where
score(case, text) returns {"fields": {name: bool, ...}, "got": {...}} and optionally
"observed": {name: bool} for things worth counting that are not pass conditions.
A case passes when every field is True.
"""
import argparse, csv, hashlib, importlib.util, json, logging, sys, time
from datetime import datetime, timezone
from pathlib import Path

import anthropic

ROOT = Path(__file__).resolve().parent.parent
ENTRIES = ROOT / "entries"
RESULTS = ROOT / "results"
KEY_FILE = Path.home() / ".config/anthropic/prompt-portfolio.env"
DEFAULT_MODEL = "claude-haiku-5-5"

# USD per million tokens (input, output), from Anthropic's published rates as of 2026-10-06.
PRICES = {
    "claude-haiku-5-5": (0.10, 0.50),
    "claude-haiku-4-5-20251001": (1.00, 5.00),
}

# HTTP libraries log request details at INFO; keep them quiet so nothing sensitive is ever logged.
for name in ("httpx", "httpx2", "httpcore", "httpcore2", "anthropic"):
    logging.getLogger(name).setLevel(logging.WARNING)


def die(msg):
    print(msg, file=sys.stderr)
    sys.exit(2)


def load_key():
    if not KEY_FILE.exists():
        die(f"setup: key file not found: {KEY_FILE}")
    for line in KEY_FILE.read_text().splitlines():
        if line.startswith("ANTHROPIC_API_KEY="):
            key = line.split("=", 1)[1].strip()
            if key and key != "paste-your-key-here":
                return key
    die(f"setup: no ANTHROPIC_API_KEY value in {KEY_FILE}")


def render(template, values):
    for k, v in values.items():
        template = template.replace("{{" + k + "}}", str(v))
    if "{{" in template:
        raise ValueError(f"unfilled placeholder in: {template[:80]}")
    return template


def load_scorer(entry_dir):
    spec = importlib.util.spec_from_file_location(f"score_{entry_dir.name}", entry_dir / "score.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.score


def run_entry(client, entry_dir, args, spent):
    cfg = json.loads((entry_dir / "entry.json").read_text())
    if args.model not in cfg["models"]:
        print(f"[{entry_dir.name}] skipped: no settings for {args.model}")
        return None, spent
    if args.system_file:
        system_path, prompt_name = Path(args.system_file), "override:" + Path(args.system_file).name
    else:
        prompt_name = args.prompt or cfg.get("default_prompt", "final")
        system_path = entry_dir / cfg["prompts"][prompt_name]
    system = system_path.read_text()
    user_tpl = (entry_dir / cfg["user_template"]).read_text()
    prompt_sha = hashlib.sha256((system + "\0" + user_tpl).encode()).hexdigest()[:12]
    sets = cfg["cases"] if isinstance(cfg["cases"], dict) else {"all": cfg["cases"]}
    set_name = args.set or next(iter(sets))
    if set_name not in sets:
        die(f"setup: {entry_dir.name} has no test set '{set_name}' (has: {', '.join(sets)})")
    cases = [json.loads(l) for l in (entry_dir / sets[set_name]).read_text().splitlines() if l.strip()]
    cases = cases[: args.limit] if args.limit else cases
    score = load_scorer(entry_dir)
    params = cfg["models"][args.model]
    price_in, price_out = PRICES[args.model]

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    (RESULTS / "raw").mkdir(parents=True, exist_ok=True)
    (RESULTS / entry_dir.name).mkdir(parents=True, exist_ok=True)
    raw_path = RESULTS / "raw" / f"{stamp}_{entry_dir.name}_{args.model}.jsonl"

    rows, errors, tok_in, tok_out, latencies, entry_cost = [], 0, 0, 0, [], 0.0
    with raw_path.open("w") as raw:
        for case in cases:
            if spent >= args.max_cost:
                print(f"spend cap ${args.max_cost:.2f} reached; stopping before {case['id']}")
                errors += 1
                break
            row = {"id": case["id"], "tags": " ".join(case.get("tags", [])), "error": ""}
            try:
                t0 = time.perf_counter()
                resp = client.messages.create(
                    model=args.model, max_tokens=cfg["max_tokens"], system=system,
                    messages=[{"role": "user", "content": render(user_tpl, case["vars"])}], **params)
                row["latency_s"] = round(time.perf_counter() - t0, 3)
            except (anthropic.APIStatusError, anthropic.APIConnectionError) as e:
                row["error"] = f"api: {type(e).__name__}"
                errors += 1
                rows.append(row)
                continue
            text = "".join(b.text for b in resp.content if b.type == "text")
            if resp.stop_reason != "end_turn":
                row["error"] = f"stop_reason: {resp.stop_reason}"
            u = resp.usage
            cost = (u.input_tokens * price_in + u.output_tokens * price_out) / 1e6
            spent += cost
            entry_cost += cost
            tok_in += u.input_tokens
            tok_out += u.output_tokens
            latencies.append(row["latency_s"])
            result = score(case, text)
            row.update({"pass": all(result["fields"].values()), "in_tokens": u.input_tokens,
                        "out_tokens": u.output_tokens})
            for f, ok in result["fields"].items():
                row[f"ok_{f}"] = ok
            for f, v in result.get("observed", {}).items():
                row[f"obs_{f}"] = v
            for f, v in result["got"].items():
                row[f"got_{f}"] = v
                if f in case.get("expected", {}):
                    row[f"expected_{f}"] = case["expected"][f]
            rows.append(row)
            raw.write(json.dumps({"id": case["id"], "text": text, "stop_reason": resp.stop_reason,
                                  "model": resp.model, "usage": u.model_dump()}) + "\n")

    scored = [r for r in rows if "pass" in r]
    n = len(scored)
    field_names = [k[3:] for k in scored[0] if k.startswith("ok_")] if scored else []
    acc = {f: sum(r[f"ok_{f}"] for r in scored) for f in field_names}
    obs_names = sorted({k[4:] for r in scored for k in r if k.startswith("obs_")})
    tags = sorted({t for r in scored for t in r["tags"].split()})
    by_tag = {t: (sum(r["pass"] for r in scored if t in r["tags"].split()),
                  sum(1 for r in scored if t in r["tags"].split())) for t in tags}
    short = [f for f, th in cfg.get("thresholds", {}).items() if n == 0 or acc.get(f, 0) / n < th]
    complete = errors == 0 and n == len(cases)
    met = complete and not short

    cols = sorted({k for r in rows for k in r}, key=lambda k: (k != "id", k))
    case_path = RESULTS / entry_dir.name / f"{stamp}_{args.model}_{prompt_name.replace(':', '-')}_{set_name}.csv"
    with case_path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)

    summary = {
        "run_utc": stamp, "entry": entry_dir.name, "set": set_name, "prompt": prompt_name, "prompt_sha": prompt_sha,
        "model": args.model, "params": json.dumps(params, sort_keys=True), "n": n, "errors": errors,
        "cases_passed": f"{sum(r['pass'] for r in scored)}/{n}",
        "fields": "; ".join(f"{f}={acc[f]}/{n}" for f in field_names),
        "observed": "; ".join(f"{o}={sum(bool(r.get('obs_' + o)) for r in scored)}/{n}" for o in obs_names),
        "by_tag": "; ".join(f"{t}={p}/{c}" for t, (p, c) in by_tag.items()),
        "in_tokens": tok_in, "out_tokens": tok_out,
        "mean_latency_s": round(sum(latencies) / len(latencies), 3) if latencies else "",
        "cost_usd": round(entry_cost, 6),
        "result": "PASS" if met else ("INCOMPLETE" if not complete else "BELOW THRESHOLD: " + ", ".join(short)),
        "cases_file": str(case_path.relative_to(ROOT)),
    }
    runs = RESULTS / "runs.csv"
    new = not runs.exists()
    with runs.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(summary))
        if new:
            w.writeheader()
        w.writerow(summary)

    print(f"[{entry_dir.name}] {args.model} prompt={prompt_name} ({prompt_sha}) set={set_name}")
    print(f"  cases passed {summary['cases_passed']} | {summary['fields']}")
    if obs_names:
        print(f"  observed (not scored): {summary['observed']}")
    if by_tag:
        print(f"  by tag: {summary['by_tag']}")
    print(f"  tokens {tok_in} in / {tok_out} out | mean latency {summary['mean_latency_s']} s | cost ${entry_cost:.4f}")
    if errors:
        print(f"  {errors} case(s) not scored (API error or spend cap): see {case_path.name}")
    print(f"  {summary['result']}")
    return ("pass" if met else "incomplete" if not complete else "fail"), spent


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("entries", nargs="*")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--prompt")
    ap.add_argument("--set")
    ap.add_argument("--system-file")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--max-cost", type=float, default=0.50)
    args = ap.parse_args()
    if args.model not in PRICES:
        die(f"setup: no price for {args.model}; add it to PRICES so the spend cap can work")
    dirs = [ENTRIES / e for e in args.entries] if args.entries else sorted(p for p in ENTRIES.iterdir() if (p / "entry.json").exists())
    for d in dirs:
        if not (d / "entry.json").exists():
            die(f"setup: no entry.json in {d}")
    client = anthropic.Anthropic(api_key=load_key())
    outcomes, spent = [], 0.0
    for d in dirs:
        outcome, spent = run_entry(client, d, args, spent)
        if outcome:
            outcomes.append(outcome)
    print(f"total spend this run: ${spent:.4f}")
    if not outcomes or "incomplete" in outcomes:
        sys.exit(2)
    sys.exit(1 if "fail" in outcomes else 0)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # a crash is "could not complete" (2), never "below threshold" (1)
        print(f"harness error: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(2)
