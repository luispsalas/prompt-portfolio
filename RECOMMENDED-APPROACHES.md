# Recommended approaches

**What current published guidance recommends for the problems in this portfolio, and where each entry stands against it.**

**As of 2026-10-09** (created and extended that day). Each practice is cited to the source that makes it. Each entry links here for the practices it applies or tests, and keeps its own measured evidence; this file holds the practices, the sources and how disagreements were resolved.

## How this file is maintained

This is one living synthesis, following the [persistent synthesis](https://luispsalas.github.io/applied-ai-concepts/concepts/persistent-synthesis.html) principle of the Applied AI Concepts wiki: new sources and new results are merged into the existing practices, not added beside them.

- **A practice is updated in place** when a source or a result changes it, and the change is recorded in the log at the foot.
- **A disagreement is recorded where it arises**: what the guidance says, what an entry measured, and how the two were reconciled (or that they were not).
- **Practice IDs are permanent.** Entries link to them, so an ID is never reused or renumbered; a retired practice keeps its ID and says what replaced it.
- **Primary sources only for recommendations.** A vendor overview may frame a topic but is not cited as evidence.

**For a plain-language explanation of each risk**, see the wiki entries linked under each practice.

## Practices

### The model's authority

<a id="p-01"></a>
#### P-01 · Keep the model's authority small

- **Recommendation:** give the model only the decisions that need judgment; decide anything consequential in code, and require a person's approval for high-risk actions.
- **Sources:** OWASP LLM01:2025 (least privilege; human approval for high-risk actions). IBM's overview frames this as one layer of defense in depth.
- **In this portfolio:** applied by design in entries [02](entries/02-intent-classification/), [03](entries/03-structured-output/) and [04](entries/04-injection-resistance/). The model routes requests; amounts and approvals are fixed rules it never sees. In entry 04, this is what limits the damage an obeyed injection could do: a misrouted request, never an approval.
- **Wiki:** [Permission model](https://luispsalas.github.io/applied-ai-concepts/concepts/permission-model-ai.html) · [Human-in-the-loop](https://luispsalas.github.io/applied-ai-concepts/concepts/human-in-the-loop.html)

### Output format

<a id="p-02"></a>
#### P-02 · Define the output format and validate it in code

- **Recommendation:** specify the output format, and check every reply with deterministic code before anything uses it.
- **Sources:** OWASP LLM01:2025 (define and validate expected output formats); OWASP LLM05:2025 (treat the model like any other user, and validate its output before it reaches other systems); Tam et al. 2024 (format restrictions are task-dependent: in their tests, strict formats such as JSON mode hurt reasoning tasks but helped or matched accuracy on classification tasks, and accuracy dropped when JSON mode put the answer before the reasoning).
- **In this portfolio:** tested in [entry 03](entries/03-structured-output/): a checker tested on 33 fixed replies, every rejected reply sent to a person, and API-enforced structured output compared with a prompt-only instruction (84 of 84 against 83 of 84 accepted, a difference too small to rank them). Applied in [entry 04](entries/04-injection-resistance/), where the schema leaves no field for an approval or an amount.
- **Consistent with the sources so far, with a condition:** entry 03 is a classification task, and its accuracy was unchanged with the schema (14 of 16 either way), as Tam et al. would predict. An entry that needs reasoning should measure accuracy with and without the schema rather than assume the same.
- **Wiki:** [Structured output](https://luispsalas.github.io/applied-ai-concepts/concepts/structured-output.html) · [Guardrails](https://luispsalas.github.io/applied-ai-concepts/concepts/guardrails-ai-systems.html)

### Untrusted input

<a id="p-03"></a>
#### P-03 · Mark untrusted content and keep it structurally apart from instructions

- **Recommendation:** tell the model what the content is and where it came from, and keep it out of the instruction channel: deliver it as a tool result, and encode it as JSON so it cannot close a tag and break out.
- **Sources:** OWASP LLM01:2025 (segregate and identify external content); Anthropic, *Mitigate jailbreaks and prompt injections*; Hines et al. 2024 (spotlighting: in their tests with GPT-family models, attack success fell from over 50% to under 2%).
- **In this portfolio:** partly applied in [entry 04](entries/04-injection-resistance/). The request sits inside `<request>` tags in the user message; two cases faked a closing tag and changed nothing on that model. JSON encoding and tool-result delivery are not used yet (listed in entry 04's Potential improvements).
- **Wiki:** [Prompt injection](https://luispsalas.github.io/applied-ai-concepts/concepts/prompt-injection.html)

<a id="p-04"></a>
#### P-04 · Tell the model to treat embedded instructions as data

- **Recommendation:** state in the system prompt that instructions inside the content are not to be followed.
- **Sources:** OWASP LLM01:2025 (constrain model behavior); Anthropic, *Mitigate jailbreaks and prompt injections* (state the policy in the system prompt). IBM's overview lists the same under strengthening internal prompts. **Qualified by** OWASP LLM07:2025, which advises against relying on system prompts for strict behavior control and says security controls must be enforced outside the model.
- **In this portfolio:** tested in [entry 04](entries/04-injection-resistance/).
- **Disagreement, and how it was resolved:** on `claude-haiku-5-5` with a schema, removing this paragraph changed nothing measurable in resistance (no version obeyed any of 216 injection replies) and removed false alarms, because the paragraph's wording made harmless requests such as "mark the invoice for the attention of accounts payable" look like instructions. Read narrowly, this does not contradict the guidance: the paragraph is one layer among several, the test used one model, and its attacks never broke that model. Anthropic's page describes Claude as resilient to such attacks, which may be what was measured; Wallace et al. 2024 show one way such behavior is trained in (an instruction hierarchy that teaches a model to give system instructions priority over lower-privileged text, demonstrated on GPT-3.5), though the sources read do not say whether the model tested here was trained that way. OWASP's own LLM07 points the same way: the prompt instruction is a soft layer, and the hard control is P-01. **Resolution: keep the instruction, scope it to text aimed at the model, and measure its false alarms** (entry 04's v3, which kept every catch and cleared all but one false alarm). Re-test when the model changes.
- **Wiki:** [Prompt injection](https://luispsalas.github.io/applied-ai-concepts/concepts/prompt-injection.html) · [System prompt](https://luispsalas.github.io/applied-ai-concepts/concepts/system-prompt.html)

<a id="p-05"></a>
#### P-05 · For systems with tools, limit by design what injected text can trigger

- **Recommendation:** when a model can call tools, use designs that constrain which actions untrusted content can reach, rather than relying on the model to resist.
- **Sources:** Beurer-Kellner et al. 2025 (design patterns for agents with provable resistance); Chen et al. 2024 (StruQ: separate prompt and data channels, with a model fine-tuned to follow only the prompt channel).
- **In this portfolio:** not applicable yet; no entry's model calls tools. Relevant to entry 09 (tool use).
- **Wiki:** [Permission model](https://luispsalas.github.io/applied-ai-concepts/concepts/permission-model-ai.html)

### Prompt content

<a id="p-06"></a>
#### P-06 · Write expert judgment as explicit rules, then test them

- **Recommendation:** give the model the distinctions an experienced reviewer would make, as rules and definitions, rather than telling it that it is an expert; and test each addition, because expert elements can help some cases and hurt others.
- **Sources:** Prompting Science Report 4 (in a controlled test on six models, expert personas did not improve factual accuracy); Steging, van Leeuwen and Zbiegień 2026 (prompt elements built with a legal expert improved some cases and degraded others, with no combination best everywhere).
- **In this portfolio:** tested in [entry 02](entries/02-intent-classification/). v2 added rules, not a persona. On unseen requests the urgency rules generalized (16 of 16 in every run), while the category definitions traded two fixes for two new errors: the pattern the second source describes.
- **Wiki:** [Prompt engineering](https://luispsalas.github.io/applied-ai-concepts/concepts/prompt-engineering.html)

### Testing

<a id="p-07"></a>
#### P-07 · Set success criteria first, and judge changes on cases the prompt was not written from

- **Recommendation:** define specific, measurable success criteria before testing; build test cases that include edge cases; refine the prompt on them, then test against held-out cases before shipping.
- **Sources:** Anthropic, *Define success criteria and build evaluations*.
- **In this portfolio:** applied in every entry: pass marks are set before any run, and the harness fails a run that falls short. In [entry 02](entries/02-intent-classification/), 15 of 15 on the dev set did not transfer to the held-out set. In [entry 04](entries/04-injection-resistance/), a fresh set was written and frozen before v3, because the held-out results had been seen.
- **Gap:** the same source advises more automatically graded cases over fewer hand-graded ones. The sets here hold 12 to 31 cases, which limits what any one result can show; every entry states its *n*.
- **Wiki:** [Evaluation](https://luispsalas.github.io/applied-ai-concepts/concepts/evaluation.html)

<a id="p-08"></a>
#### P-08 · Measure false alarms, not only catches

- **Recommendation:** when testing a detector or a defense, count the harmless inputs it flags as well as the attacks it catches.
- **Sources:** Li and Liu 2024 (InjecGuard: prompt-injection guard models over-flag benign inputs that contain trigger words, with accuracy near 60%, close to random, on their benign set). IBM's overview notes that filters can block benign inputs.
- **In this portfolio:** measured in [entry 04](entries/04-injection-resistance/): false alarms were the defended prompt's only failure, on the same kind of trigger words ("ignore", "mark", "skip"). Their study is of separate guard models, not a flag in the classifier's own prompt, so this is a parallel finding, not a replication.
- **Wiki:** [Guardrails](https://luispsalas.github.io/applied-ai-concepts/concepts/guardrails-ai-systems.html)

<a id="p-09"></a>
#### P-09 · Test adversarially, then keep monitoring and refining

- **Recommendation:** run attack simulations against the system, and in production keep analyzing outputs for signs of a successful attack, refining prompts and checks as you go.
- **Sources:** OWASP LLM01:2025 (adversarial testing and attack simulations); Anthropic, *Mitigate jailbreaks and prompt injections* (continuous monitoring). For attacks stronger than hand-written ones: Liu et al. 2023 (a framework that formalizes prompt injection, a combined attack built from existing ones, and a benchmark of 5 attacks and 10 defenses across 10 models) and Debenedetti et al. 2024 (AgentDojo, an extensible environment with adaptive attacks, 97 tasks and 629 security test cases for agents). NIST AI 100-2 E2025 provides a taxonomy and terminology for attacks and mitigations, useful for classifying what a test set covers.
- **In this portfolio:** one round applied: [entry 03](entries/03-structured-output/)'s stress set aimed at the format, and [entry 04](entries/04-injection-resistance/)'s injection sets. Synthetic, written by one author, with no production monitoring. Entry 04's attacks never broke the model, so stronger attacks are listed among its improvements; the benchmarks above are where they would come from.
- **Wiki:** [Red teaming](https://luispsalas.github.io/applied-ai-concepts/concepts/red-teaming.html)

<a id="p-10"></a>
#### P-10 · Report results across plausible prompt formats

- **Recommendation:** treat formatting as a variable. Small meaning-preserving changes (spacing, separators, line breaks) can change results, so report a range across plausible formats rather than one number from one format.
- **Sources:** Sclar et al. 2023 (on several open-source models, meaning-preserving formatting changes moved few-shot accuracy by up to 76 points on one model; they recommend reporting a range across formats).
- **In this portfolio:** observed in [entry 02](entries/02-intent-classification/): the same prompt with its line breaks collapsed gave a different urgency on one request (on Haiku 4.5). Not yet tested systematically; listed in entry 02's improvements.
- **Wiki:** [Evaluation](https://luispsalas.github.io/applied-ai-concepts/concepts/evaluation.html)

<a id="p-11"></a>
#### P-11 · Report uncertainty, and compare on the same cases

- **Recommendation:** give every score a standard error. When cases come in related groups, use clustered errors; when the model is sampled several times, average per question before computing the error; compare two systems on question-level paired differences; and use a power analysis to size a test before running it.
- **Sources:** Miller 2024 (*Adding Error Bars to Evals*), whose recommendations include all five.
- **In this portfolio:** partly applied. [Entry 03](entries/03-structured-output/) states that 84 against 83 accepted replies is not significant, that its 84 replies are 28 requests run 3 times rather than independent samples, and estimates how many distinct requests a meaningful comparison would need. Not yet applied: no entry reports standard errors, and [entry 04](entries/04-injection-resistance/)'s twins are related pairs that a clustered analysis would treat as such.
- **Wiki:** [Evaluation](https://luispsalas.github.io/applied-ai-concepts/concepts/evaluation.html)

## For a non-technical team

- **A model reads instructions and content through the same channel**, so text inside a request can act like a command. That is the root of prompt injection, not a bug that will be patched away.
- **The most reliable protection is what the model is allowed to decide**, not the wording of its prompt (P-01).
- **A readable answer is not a right answer.** Checking the format and checking the content are separate jobs (P-02).
- **A score on the examples a prompt was written from proves little.** Ask how it did on cases it never saw (P-07).
- **A warning that cries wolf has a cost.** Ask for both numbers: attacks caught and harmless requests flagged (P-08).
- **A small difference between two results is often noise.** Ask how sure the measurement is, not only what the number was (P-11).

## When to revisit

Re-read the affected practices, rerun the entries that test them, and record the result in the log when:
- the model behind an entry changes;
- OWASP publishes a new edition of its list, or a cited guidance page changes;
- a new entry applies or tests a practice here;
- a real miss or a real false alarm is reported.

## Sources

- Anthropic, [Define success criteria and build evaluations](https://platform.claude.com/docs/en/test-and-evaluate/develop-tests), Claude Platform Docs, read 2026-10-09.
- Anthropic, [Mitigate jailbreaks and prompt injections](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/mitigate-jailbreaks), Claude Platform Docs, read 2026-10-09.
- Basil, Shapiro, Shapiro, Mollick, Mollick and Meincke, [Prompting Science Report 4: Playing Pretend: Expert Personas Don't Improve Factual Accuracy](https://arxiv.org/abs/2512.05858), arXiv 2512.05858, 2025.
- Beurer-Kellner, L. et al., [Design Patterns for Securing LLM Agents against Prompt Injections](https://arxiv.org/abs/2506.08837), arXiv 2506.08837, 2025.
- Chen, S., Piet, J., Sitawarin, C. and Wagner, D., [StruQ: Defending Against Prompt Injection with Structured Queries](https://arxiv.org/abs/2402.06363), arXiv 2402.06363, 2024.
- Debenedetti, E. et al., [AgentDojo: A Dynamic Environment to Evaluate Prompt Injection Attacks and Defenses for LLM Agents](https://arxiv.org/abs/2406.13352), arXiv 2406.13352, 2024.
- Hines, K. et al., [Defending Against Indirect Prompt Injection Attacks With Spotlighting](https://arxiv.org/abs/2403.14720), arXiv 2403.14720, 2024.
- Kosinski, M., [Protect Against Prompt Injection](https://www.ibm.com/think/insights/prevent-prompt-injection), IBM Think, published 2025-02-03, updated 2026-02-27. A vendor overview, used for its framework only.
- Li, H. and Liu, X., [InjecGuard: Benchmarking and Mitigating Over-defense in Prompt Injection Guardrail Models](https://arxiv.org/abs/2410.22770), arXiv 2410.22770, 2024.
- Liu, Y., Jia, Y., Geng, R., Jia, J. et al., [Formalizing and Benchmarking Prompt Injection Attacks and Defenses](https://arxiv.org/abs/2310.12815), arXiv 2310.12815, 2023.
- Miller, E., [Adding Error Bars to Evals: A Statistical Approach to Language Model Evaluations](https://arxiv.org/abs/2411.00640), arXiv 2411.00640, 2024.
- NIST, Vassilev, A. et al., [AI 100-2 E2025, Adversarial Machine Learning: A Taxonomy and Terminology of Attacks and Mitigations](https://csrc.nist.gov/pubs/ai/100/2/e2025/final), March 2025.
- OWASP GenAI Security Project, [LLM01:2025 Prompt Injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/), page updated 2025-04-17.
- OWASP GenAI Security Project, [LLM05:2025 Improper Output Handling](https://genai.owasp.org/llmrisk/llm052025-improper-output-handling/), page updated 2025-05-05.
- OWASP GenAI Security Project, [LLM07:2025 System Prompt Leakage](https://genai.owasp.org/llmrisk/llm072025-system-prompt-leakage/), page updated 2025-04-28.
- Sclar, M., Choi, Y., Tsvetkov, Y. and Suhr, A., [Quantifying Language Models' Sensitivity to Spurious Features in Prompt Design](https://arxiv.org/abs/2310.11324), arXiv 2310.11324, 2023.
- Steging, van Leeuwen and Zbiegień, [Investigating Expert-Based Prompt Engineering for Legal Entailment Tasks](https://doi.org/10.1007/s12626-026-00202-3), The Review of Socionetwork Strategies 20, 2026.
- Tam, Z. R. et al., [Let Me Speak Freely? A Study on the Impact of Format Restrictions on Performance of Large Language Models](https://arxiv.org/abs/2408.02442), arXiv 2408.02442, 2024.
- Wallace, E. et al., [The Instruction Hierarchy: Training LLMs to Prioritize Privileged Instructions](https://arxiv.org/abs/2404.13208), arXiv 2404.13208, 2024.

## Log

- **2026-10-09: created.** Started as entry 04's Recommended approaches section; moved here at the owner's request so that practices shared by several entries have one home. Nine practices: P-01 to P-05 and P-08 to P-09 from entry 04's research, P-06 from the sources entry 02 already cited, P-07 added with Anthropic's evaluation guidance. The P-04 disagreement is recorded from entry 04's results.
- **2026-10-09: additional-sources pass** (the owner's request). Added P-10 (formatting sensitivity, from Sclar et al.) and P-11 (uncertainty and paired comparisons, from Miller). P-02 gained OWASP LLM05 and Tam et al., with the condition that reasoning-heavy entries retest accuracy under a schema. P-04 gained OWASP LLM07 and Wallace et al.; both support its resolution (the prompt instruction is a soft layer, the hard control is P-01). P-09 gained Liu et al., AgentDojo and NIST AI 100-2 E2025 as sources of stronger attacks and a taxonomy. All metadata checked at the source (arXiv API, OWASP and NIST pages); claims taken from abstracts or, for Miller and Tam et al., the full text.
