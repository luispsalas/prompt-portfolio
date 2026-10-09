# Entry 03: Structured output with a checker and a fallback

**Making model replies safe for a program to act on: check every reply before use, send anything that fails to a person, and measure whether letting the API enforce the format is worth its cost.**

`structured output` · `output validation` · `fallback path` · `JSON schema` · `Claude Haiku 5.5`

## At a glance

| | |
|---|---|
| **Goal** | Let a program act on model replies safely: use only replies that pass a check, and send everything else to a person. |
| **What was done** | Compared a prompt-only JSON instruction with API-enforced structured output, both behind the same checker, including 12 requests built to break the format. |
| **Governance** | The model can never return an amount or an approval; extra fields are flagged, and every rejected reply goes to a person. |
| **Measurement** | With the schema, 84 of 84 replies passed the check; prompt-only, 83 of 84, while running faster and cheaper. |

## Why it matters

A model's answer is only useful to a business system if the system can read it. If a classifier is supposed to return a category and instead returns a paragraph, an automated workflow either breaks or, worse, guesses. Teams usually find this out in production, one odd reply at a time.

So the business requirement is not "the model returns JSON". It is: **nothing downstream ever acts on a reply that has not been checked, and a reply that fails the check has a defined, human destination.** This entry builds that checker, tests it on its own, and then measures how often each way of asking for structured output actually needs the fallback.

## Data governance

- **Synthetic data only.** Every request is invented, and every one was run through the real privacy gate from the original workflow lab before use: none contained personal data to remove.
- **Every reply is checked before anything uses it.** The checker accepts only the four expected fields with allowed values. A reply that fails goes to a person; it is never repaired or guessed at.
- **The model cannot decide money or approvals.** It is never shown an amount. The schema forbids any field beyond the four, and the checker flags extra fields, so a reply that tried to add `amount` or `approved` would be visible. Business values always come from the original request, never from the model.
- **Requests can carry instructions; replies are still data.** Four test requests ask the model to change format, add a field, include an amount or explain itself first. The model must flag those (`injection_suspected`) and not comply.
- **Raw model replies are not committed.** Only scored results are published; the raw replies stay local.
- **Every result names its model and prompt version,** including whether the schema was used, and a hash of the prompt and schema text.

## What it does not show

- **Not production use**, and synthetic requests only.
- **The stress set did not break this model.** The 12 format-breaking requests were handled correctly by both approaches in every run, so this entry cannot say how often prompt-only fails on hostile input. The one failure it found came from an ordinary, ambiguous request.
- **Small numbers.** 84 replies per approach; one failure in 84 is a rate this data cannot pin down.
- **One model.** Older models behave differently: in entry 02, Haiku 4.5 ignored the "no code fences" instruction on all 15 replies.
- **No retry.** A rejected reply goes straight to a person, as in the original workflow. Retrying once before falling back is a common alternative and is not tested here.

## How it works

1. The model receives the request and replies.
2. The **checker** ([`validator.py`](validator.py)) reads the reply. It strips a code fence if one is present (models add them), parses the JSON, and checks that the category and urgency are allowed values, the summary is not empty, and the injection flag is true or false.
3. **Accepted:** the four fields are used. **Rejected:** the request goes to a person, with the reason (for example `reply is not valid JSON`).

Two ways of asking for the format were compared. **Both use entry 02's final prompt, unchanged**, so the only difference is one API setting.

| Approach | How the format is requested |
|---|---|
| **prompt-only** | The prompt asks for one JSON object and nothing else. The model usually complies. |
| **schema** | The prompt is the same, and the API is also given [`schema.json`](schema.json): the four fields, their allowed values, and no other fields. The API constrains the reply to match. |

The checker stays in place for both. A schema cannot cover everything: if a reply is cut off at the token limit or the model declines to answer, the output may not match it.

## Testing the checker on its own

Before measuring any model, the checker was tested on 33 fixed replies, with no model involved ([`validator-cases.jsonl`](validator-cases.jsonl), run by [`tests/test_validator.py`](../../tests/test_validator.py)):

| Group | Cases | Examples |
|---|---|---|
| Real replies from the original lab | 15 | All valid, all wrapped in code fences |
| Broken replies from the original lab's tests | 7 | Not JSON, unknown category, unknown urgency, missing summary, the flag given as text, an extra `amount_usd` field, the AI call failing |
| Added for this portfolio | 11 | A cut-off reply, prose after the JSON, two JSON objects, a blank summary, `Software` with a capital S, the flag given as `0`, XML, `null`, a list |

Each case states the expected verdict and reason, and all 33 come out as expected. The test was shown to fail when a check is deliberately removed from the checker.

**The checker is a Python port of the original workflow's JavaScript**, so the original was run unchanged on the same 33 cases. **31 of 33 verdicts and reasons are identical.** The two differences are deliberate, and one is a bug found in the original: **a reply of `null` crashed it** instead of being rejected, which would have stopped that request from reaching either the log or a person. The port rejects it with a reason. (The other difference: a list is now rejected as "not a JSON object" rather than with a misleading category message.)

## Test sets

| Set | Cases | What it tests |
|---|---|---|
| **stress** ([`stress-cases.jsonl`](stress-cases.jsonl)) | 12 | Requests built to pull the model off format: JSON or a code fence inside the request, a markdown table, a 148-word request, Spanish, emoji, a request that says only "TBD", and four that carry instructions (reply in XML, include the amount and approve it, explain your reasoning first, add a `priority` field). No category labels: this set measures format. |
| **held-out** (entry 02's [`heldout-cases.jsonl`](../02-intent-classification/heldout-cases.jsonl)) | 16 | Ordinary requests with category and urgency labels, to check that the schema does not change the answers. |

A case passes only if the reply is clean JSON as returned, the checker accepts it, it holds no extra fields, and its injection flag (and, on the held-out set, its category and urgency) is right.

## Results

Model `claude-haiku-5-5`, effort `low`, 3 runs per approach per set, so 84 replies per approach. Figures are from [`results/runs.csv`](../../results/runs.csv).

| | prompt-only | schema |
|---|---|---|
| **stress**, replies accepted | 12, 12, 12 of 12 | 12, 12, 12 of 12 |
| stress, injection flag right | 12 of 12, every run | 12 of 12, every run |
| **held-out**, replies accepted | **15**, 16, 16 of 16 | 16, 16, 16 of 16 |
| held-out, category right | 14 of 16, every run | 14 of 16, every run |
| **all replies accepted** | **83 of 84** | **84 of 84** |
| mean time per reply | about 0.9 s | about 1.5 s |
| input tokens per request | baseline | **+341** (the schema) |
| cost per run of 16 held-out requests | about $0.0017 | about $0.0021 |

**Reading:**
- **The one rejected reply was not caused by a hostile request.** It was the ambiguous laptop-repair request from entry 02. The model reasoned in prose first ("Repair of a laptop is physical equipment work…") and then gave the JSON. The checker rejected it, as designed, and it would have gone to a person. Its answer was actually right, so the cost was a needless trip to a person, not bad data.
- **With the schema, that cannot happen.** All 84 replies were clean JSON exactly as returned.
- **The schema did not change the answers.** Category was 14 of 16 in every run under both approaches.
- **The schema costs time and tokens.** Replies took about 1.5 s instead of about 0.9 s in every run, not only the first, and each request carried 341 more input tokens. Output tokens on the held-out set were lower with the schema (about 1,020 against 1,220 to 1,320 per run), consistent with less reasoning written out.
- **The format-breaking requests did not break this model either way.** It did not switch to XML, add a field or include an amount, and flagged all four instruction-carrying requests in every run.

**Which to use:** for a workflow where a rejected reply costs a person's time, the schema removes that cost for about 0.6 s and a few hundred tokens per request. Where latency matters more, prompt-only with the checker is safe, because every failure still lands with a person. Either way, the checker is not optional. This repo uses the schema as the default.

## Failure modes and guardrails

| What can go wrong | What catches it |
|---|---|
| The reply is prose, XML, cut off, or not an object | The checker rejects it with a reason; the request goes to a person |
| The reply holds a value outside the allowed list | The checker rejects it (the schema also prevents it) |
| The reply adds a field such as `amount` | The schema forbids it; the checker flags it; business values never come from the model |
| The AI call itself fails | The checker records `AI call failed` and the request goes to a person |
| The checker itself is wrong | 33 fixed cases with stated verdicts, compared against the original implementation, and shown to fail when a check is removed |
| A request hides an instruction | The model flags it; tested here on 4 requests, 3 runs each. Entry 04 tests injection in depth |

## Reproduce

```bash
./setup.sh
.venv/bin/python tests/test_validator.py                     # the checker alone: no model, no cost
.venv/bin/python harness/run.py 03-structured-output --set stress --prompt schema
.venv/bin/python harness/run.py 03-structured-output --set heldout --prompt prompt-only
```

A full run of one set costs under $0.003.

## Related concepts

[Structured output](https://luispsalas.github.io/applied-ai-concepts/concepts/structured-output.html) · [Guardrails](https://luispsalas.github.io/applied-ai-concepts/concepts/guardrails-ai-systems.html) · [Prompt injection](https://luispsalas.github.io/applied-ai-concepts/concepts/prompt-injection.html) · [Evaluation](https://luispsalas.github.io/applied-ai-concepts/concepts/evaluation.html) · [System prompt](https://luispsalas.github.io/applied-ai-concepts/concepts/system-prompt.html)

## How it was built

Built with an AI coding assistant (Claude Code), which designed the comparison, ported the checker, wrote its test cases and the stress requests, ran the original JavaScript to compare verdicts, and found the `null` crash.

## What stays private

The original workflow's checker and its saved replies come from a separate lab whose full workflow file is not published. The script that runs that original JavaScript for comparison reads the lab's private files, so it stays outside this repository; its result (31 of 33 identical) is reported above.
