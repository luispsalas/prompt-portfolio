# Prompt portfolio

**Prompts treated as engineering: each one versioned, tested on a fixed set, measured with *n* stated, and reported with its failures.**

## Why it exists

A prompt that works on the examples someone tried is not evidence of anything. A team that relies on a model needs to know how often it is right, what it does when it is wrong, and whether a change to the prompt made things better or only different. Each entry here takes one prompting problem and answers those questions with a test set, pass marks set before any run, and results that anyone can reproduce.

## What it does not show

- **Not production use.** Every entry is a lab exercise on synthetic data.
- **Small samples.** Test sets hold 12 to 33 cases. Every figure gives its *n*, and runs are repeated to show the spread.
- **One model at a time.** Results are for the model named beside them (mostly `claude-haiku-5-5`) and may not hold for another.

## Entries

| # | Entry | Status |
|---|---|---|
| 01 | Plain-language explanation for a non-technical reader | planned |
| 02 | [Intent classification](entries/02-intent-classification/): category and urgency, v1 to v2, held-out test | done |
| 03 | [Structured output](entries/03-structured-output/) with a checker and a fallback path | done |
| 04 | Injection-resistant system prompt | in progress |
| 05 | Grounded answer with citations | planned |
| 06 | A judgment step in a pipeline, against a rubric | planned |
| 07 | Summary for a human reviewer | planned |
| 08 | Quality and safety rubric: model-graded against human scores | planned |
| 09 | Tool use with a typed schema | planned |
| 10 | Teaching prompting: a one-page guide for a non-technical team | planned |

Each entry README starts with the business case and data governance, then states what the entry does not show, before the method and results. Each ends with a history, in order, of what was tried and what failed along the way, then with potential improvements: hypotheses not yet tested, with the measurement that would settle each.

## How the entries fit together

Each entry isolates one concern so that it can be measured on its own: whether the answer is right (02), whether a program can read it (03), whether hidden instructions are resisted (04), and so on. A real business use case needs all of them at once, and **doing well on one does not imply doing well on another.** Entry 03's schema made every reply readable, and that says nothing about whether the category in it was right.

So the entries are built as **layers of one pipeline**, not as separate demos. Entry 03 runs entry 02's final prompt unchanged, and entry 04 starts from the same prompt with entry 03's schema. In a combined system, the approach used here is:

1. **Start from the business outcome and what each kind of error costs.** A wrong category that only affects a report is cheap; an approval the model was never meant to give is not. Pass marks come from those costs.
2. **Give each concern to the cheapest layer that handles it reliably.** Fixed rules for money and approvals, a privacy gate before the model, the prompt for judgment, a schema and a checker for format, and a person for whatever fails or is ambiguous. The model is asked to do only what needs judgment.
3. **Change one layer at a time, then rerun every set, not only that layer's.** Layers interact. Entry 03's schema lowered the model's output tokens on the held-out set (about 1,020 against 1,220 to 1,320 per run) while leaving category accuracy unchanged at 14 of 16. Here the answers held; on a harder task they might not, and only rerunning the accuracy set would show it. Each prompt addition also lengthens the prompt and raises the cost: entry 02's v2 cost more per run than v1.
4. **Finish with an end-to-end set scored on every check at once.** Per-entry sets show each layer works; a combined set shows they work together. That set is not built yet.

## How the testing works

One small harness ([`harness/run.py`](harness/run.py)) runs an entry's test set against the model and writes per-case results and one summary row per run to [`results/`](results/). Each entry's `entry.json` holds its pass marks, set before the model is run. The harness exits 0 when every mark is met, 1 when one falls short, and 2 when the run could not complete; an API error is never counted as a wrong answer. Every result records the model, the prompt version and a hash of the prompt text, and the harness has been shown to fail a deliberately broken prompt ([`tests/fault-test.sh`](tests/fault-test.sh)).

```bash
./setup.sh
.venv/bin/python harness/run.py 02-intent-classification --set heldout --prompt v2
```

The harness reads an Anthropic API key from a local file outside the repository; the key is never printed or logged.

## How it was built

Built with an AI coding assistant (Claude Code), which wrote the harness, the test sets and the entry write-ups. The owner set the scope, confirmed the held-out labels before any prompt was revised, and decided each entry's final version.
