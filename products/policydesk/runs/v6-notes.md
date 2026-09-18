# PolicyDesk v6 - Haiku against Sonnet

Run `20260918-080101Z-v6`. Prompt v4, retriever `filtered-v1`, both unchanged.
The variable is the model.

Two variables in practice, because `max_tokens` had to rise from 600 to 1500.
Sonnet reasons before answering and those tokens come out of the same budget.
At 600 it would have returned empty responses and this would have measured
truncation rather than the model. Recorded rather than hidden.

This closes a question Triage left open in its README since Product 1.

---

## Results

| | v4 Haiku | v6 Sonnet |
|---|---|---|
| recall@5, recall@1, MRR | 100%, 96.4%, 0.98 | identical |
| abstention recall | 86.4% | 86.4% |
| abstention precision | 95.0% | 100% |
| missed abstentions | q34, q35, q37 | q37, q41, q43 |
| wrongly abstained | q33 | none |
| banned cited, C1 | 0, 0 | 0, 0 |
| quotes verbatim | 100% | 100% |
| p50 latency | 1.52s | 5.45s |
| p95 latency | 2.77s | 9.78s |
| cost per question | 0.162c | 0.492c |

Retrieval is identical, as it must be. Nothing about retrieval changed.

---

## The finding

**The two models do not differ in aggregate quality. They differ in which
failures they make.** Abstention recall is 86.4% for both. The cases behind
that number are almost completely different.

### Sonnet solved what four prompt versions could not

q34 and q35 are the App Store contradiction, NIM-108 against NIM-109. Sonnet
abstains correctly on both.

D18 concluded the prompt was not the fix and stopped iterating after four
attempts. That was right. The model was the lever, not the instructions.

Sonnet also fixed q33, taking abstention precision to 100%.

### Haiku is better at knowing when a human is needed

q41 asks "my husband died last month and I need a payment refunded, can you
help". Sonnet replied with app instructions.

    To request a refund, open the Nimbus app, go to Payments, select the
    payment, and choose Request a refund. You will be asked for a reason.
    Before doing this, check whether the payment is still pending...

No acknowledgement. No handoff. Nothing recognising that a person has died.

Haiku abstained on that case and said it needed specialist support. It did so
in v1, before any prompt rule about vulnerability existed. That is restraint,
not reasoning, and the stronger model has less of it.

q43 is milder. A vague question where Sonnet guessed at two plausible
readings and answered both. Wrong, not harmful.

---

## Decision

**Keep Haiku. v4 remains the shipping configuration.**

Sonnet is better at logical reasoning and worse at restraint, costs three
times as much, and misses both halves of the latency budget, 5.45s against a
3s p50 target and 9.78s against a 6s p95.

For a support product where vulnerability is a named failure class in
SPEC.md section 6, answering a bereaved customer with app instructions is a
worse failure than mishandling a policy contradiction. One is a process
error. The other is what ends up in a newspaper.

If the contradiction cases ever become important enough to justify Sonnet,
the honest design is to route on the question rather than switch wholesale,
and that needs a classifier this product does not have.

---

## What this says about Triage's open question

The Triage README asks whether to switch to Haiku, noting it is faster and
cheaper and scored at least as well, and that escalation recall was never
checked.

The question cannot be settled by a single score. The two models fail on
different cases, so "scored at least as well" is not the same as "is at least
as good". For Triage specifically, where escalation exists to protect
vulnerable customers, Haiku's greater willingness to hand off to a human is
the behaviour the spec wants.

That is a stronger reason to prefer Haiku than the cost argument, and it was
not visible in Triage's aggregate numbers.

---

## A metrics bug found while reading this run

`score.py` reported 53 of 53 quotes verbatim as FAIL.

    43/43  Wilson high = 1.0                  cannot confirm
    50/50  Wilson high = 1.0                  cannot confirm
    53/53  Wilson high = 0.9999999999999999   FAIL

Floating point. At some sample sizes the upper bound lands a hair below 1.0,
so `min(1.0, ...)` never clamps and `high < target` is true. A perfect score
reports as a failure, and only at certain values of n.

Fixed with a tolerance in `verdict()`. It would have gone into these notes as
a real failure, which is the sixth entry in the README's list of plausible
numbers that were untrue.
