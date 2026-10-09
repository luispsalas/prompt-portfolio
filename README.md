# Prompt portfolio

**Prompts treated as engineering: each one versioned, tested on a fixed set, measured with *n* stated, and reported with its failures.**

## At a glance

| | |
|---|---|
| **Goal** | Treat prompts as engineering: each one versioned, tested on a fixed set, and reported with its failures. |
| **What was done** | Ten planned entries on one shared test harness, three finished so far. |
| **Governance** | Synthetic data only, personal data removed before the model, no amounts or approvals decided by it, and no keys in the repo. |
| **Measurement** | A revised prompt scored 15 of 15 on known requests but no better on unseen ones; a schema made 84 of 84 replies readable. |

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
| 04 | [Injection resistance](entries/04-injection-resistance/): hidden instructions, false alarms, a narrowed v3 | done |
| 05 | Grounded answer with citations | planned |
| 06 | A judgment step in a pipeline, against a rubric | planned |
| 07 | Summary for a human reviewer | planned |
| 08 | Quality and safety rubric: model-graded against human scores | planned |
| 09 | Tool use with a typed schema | planned |
| 10 | Teaching prompting: a one-page guide for a non-technical team | planned |

Ten entries are planned; three are finished. Each entry README starts with the business case and data governance, then states what the entry does not show, before the method and results. Near the end, each lists the published practices it tests (see Recommended approaches below), then gives a history, in order, of what was tried and what failed along the way, then with potential improvements: hypotheses not yet tested, with the measurement that would settle each.

## How the entries fit together

Each entry isolates one concern so that it can be measured on its own: whether the answer is right (02), whether a program can read it (03), whether hidden instructions are resisted (04), and so on. A real business use case needs all of them at once, and **doing well on one does not imply doing well on another.** Entry 03's schema made every reply readable, and that says nothing about whether the category in it was right.

So the entries are built as **layers of one pipeline**, not as separate demos. Entry 03 runs entry 02's final prompt unchanged, and entry 04 starts from the same prompt with entry 03's schema. In a combined system, the approach used here is:

1. **Start from the business outcome and what each kind of error costs.** A wrong category that only affects a report is cheap; an approval the model was never meant to give is not. Pass marks come from those costs.
2. **Give each concern to the cheapest layer that handles it reliably.** Fixed rules for money and approvals, a privacy gate before the model, the prompt for judgment, a schema and a checker for format, and a person for whatever fails or is ambiguous. The model is asked to do only what needs judgment.
3. **Change one layer at a time, then rerun every set, not only that layer's.** Layers interact. Entry 03's schema lowered the model's output tokens on the held-out set (about 1,020 against 1,220 to 1,320 per run) while leaving category accuracy unchanged at 14 of 16. Here the answers held; on a harder task they might not, and only rerunning the accuracy set would show it. Each prompt addition also lengthens the prompt and raises the cost: entry 02's v2 cost more per run than v1.
4. **Finish with an end-to-end set scored on every check at once.** Per-entry sets show each layer works; a combined set shows they work together. That set is not built yet.

## Lessons learned

What the entries have taught so far, each with the entry that shows it. Lessons are added as entries finish; earlier ones are not rewritten.

1. **A perfect score on the requests a prompt was written from proves little.** Entry 02's revised prompt scored 15 of 15 on its dev set in every run, and no better than the original on 16 requests it had never seen. Only the held-out set showed that two fixes came with two new errors. ([Entry 02](entries/02-intent-classification/))
2. **Check the measuring tool before the model.** The first calibration run scored 0 of 15 because the scorer, not the model, failed to read replies wrapped in code fences. ([Entry 02](entries/02-intent-classification/), History)
3. **A check must be seen to fail, and seen to be needed.** With the pass marks switched off, a deliberately broken prompt reported PASS. In entry 04, each check was disabled in turn to confirm that nothing else would catch its fault. ([Entry 02](entries/02-intent-classification/), [entry 04](entries/04-injection-resistance/))
4. **Small things change answers.** The same prompt with its line breaks collapsed gave a different urgency on one request. ([Entry 02](entries/02-intent-classification/))
5. **A readable answer is not a right answer.** With the schema, 84 of 84 replies passed the format check, and category accuracy stayed at 14 of 16, exactly as without it. Each concern needs its own test. ([Entry 03](entries/03-structured-output/))
6. **A one-reply difference is not a result.** 84 against 83 accepted replies cannot rank two approaches, and repeat runs of the same requests are not independent samples. ([Entry 03](entries/03-structured-output/))
7. **Changing the harness can quietly relabel past results.** A small change altered the recorded fingerprint of every prompt; comparing an unchanged prompt's fingerprint with earlier runs caught it. ([Entry 03](entries/03-structured-output/), History)
8. **Decide what counts as a failure before the run.** In entry 04, "the model approved it" turned out to be unmeasurable, because the reply has no approval field and a neutral summary uses the same word, so it became a reported observation instead of a pass mark. ([Entry 04](entries/04-injection-resistance/))
9. **A defense can cost more than it buys, and only a false-alarm count shows it.** Entry 04's defensive paragraph stopped nothing extra on this model (no version obeyed any of 216 injection replies), but it flagged harmless requests that used words like "mark" or "ignore". A narrowed version kept every catch and cleared all but one false alarm. ([Entry 04](entries/04-injection-resistance/))

## Recommended approaches

[RECOMMENDED-APPROACHES.md](RECOMMENDED-APPROACHES.md) collects what current published guidance recommends for the problems in this portfolio, each practice cited to its primary source, and says where each entry stands against it. It is kept as one living synthesis: when a new source or a new result disagrees with a practice, the practice is updated and the disagreement recorded, never added as a second opinion. Entries link to its practices by ID and keep their own evidence.

Nine practices so far, in five groups: the model's authority (P-01), output format (P-02), untrusted input (P-03 to P-05), prompt content (P-06) and testing (P-07 to P-09). One records a disagreement: a defensive instruction that published guidance recommends added only false alarms in entry 04, and the file says how that was reconciled. It also has a plain-language summary for a non-technical team, and the events that should trigger a revisit.

## How the testing works

One small harness ([`harness/run.py`](harness/run.py)) runs an entry's test set against the model and writes per-case results and one summary row per run to [`results/`](results/). Each entry's `entry.json` holds its pass marks, set before the model is run. The harness exits 0 when every mark is met, 1 when one falls short, and 2 when the run could not complete; an API error is never counted as a wrong answer. Every result records the model, the prompt version and a hash of the prompt text, and the harness has been shown to fail a deliberately broken prompt ([`tests/fault-test.sh`](tests/fault-test.sh)).

```bash
./setup.sh
.venv/bin/python harness/run.py 02-intent-classification --set heldout --prompt v2
```

The harness reads an Anthropic API key from a local file outside the repository; the key is never printed or logged.

## How it was built

Built with an AI coding assistant (Claude Code), which wrote the harness, the test sets and the entry write-ups. The owner set the scope, confirmed the held-out labels before any prompt was revised, and decided each entry's final version.
