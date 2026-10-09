# Results

Every harness run writes here. Raw model replies go to `raw/`, which is not committed.

| File | What it holds |
|---|---|
| `runs.csv` | One row per run: entry, test set, prompt version and its hash, model and settings, scores, tokens, latency, cost. **The figures cited in each entry's README come from this file.** |
| `<entry>/<time>_<model>_<prompt>_<set>.csv` | Per-case results for one run: what the model answered, what was expected, pass or fail. |
| `runs-2026-10-09-setup.csv` | History from building and testing the harness, kept for transparency. **Not results.** It includes calibration runs on `claude-haiku-4-5-20251001` and the fault tests: prompts deliberately broken to prove the harness fails (`override:system-broken-*`, `override:tmp.*`), runs stopped by a $0 spend cap (`INCOMPLETE`), and one run with the pass-mark check switched off on purpose, which therefore reports `PASS` for a broken prompt. That row is the evidence that the pass marks are needed, not a passing result. |
| `runs-calibration-attempt1.csv` | The first calibration run, scored before the scorer stripped code fences the way the original workflow's parser did. Every reply failed to parse, so the run measured the scorer, not the model. |
