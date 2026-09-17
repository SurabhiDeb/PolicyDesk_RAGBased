# PolicyDesk v3 and v4 - the prompt

Runs `20260917-150227Z-v3` and `20260917-153710Z-v4`. Retriever
`filtered-v1` unchanged from v2. Prompt is the variable.

v3 and v4 are recorded together because v4 exists to fix a bug v3 introduced.
v3 was never a candidate to ship.

---

## What the prompt was asked to do

Four jobs, from the v2 analysis.

1. Scope. Chargebacks belong to the disputes team.
2. Contradiction. Two live articles that disagree means `no_answer`.
3. Abstention balance. Stop refusing when the answer is present.
4. Citation completeness. Every sentence covered by a quote it provides.

Job 4 was added because the v2 filter made answers longer, which cost
groundedness. It was not in the v1 analysis.

---

## v3, and the bug it introduced

    abstention recall     54.5% -> 100.0%
    abstention precision  88.9% ->  78.6%
    unparseable               0 ->  1  (q06)

Recall hit the target. Everything else got worse.

**Six cases refused that should have answered**, four of them working
correctly in v2. The cause was a scope rule that tested the answer rather
than the question.

"Can I get a refund on gambling" is a refund question whose answer is no.
"How long do I have to raise a chargeback" is a chargeback question. v3
taught the model those were the same thing.

### `answer_in_the_refusal`, a new mode

q36, q44 and q47 were not refusing. They put the correct answer in
`handoff_reason` with `status: no_answer` and no citations.

    q44  This describes an unauthorised payment, which should be reported
         as fraud rather than handled as a refund matter.

That is exactly what NIM-106 says. Right content, wrong field, uncited,
invisible to every test that reads `answer`.

It was present in v1 too. q33's refusal said "they only mention that payments
older than 180 days cannot be refunded through the app", which was the
answer. Nobody spotted it until v3 made it common.

### The q06 parse failure

`Extra data: line 8 column 1` at 224 output tokens, nowhere near the 600
cap. Not truncation, which was the first guess. The model returned valid JSON
and then kept writing its sentence-checking work after the closing brace.

Fixed by parsing with `json.JSONDecoder().raw_decode`, which reads the first
value and ignores the rest, in `text.first_json`.

Because every model response was already cached, the fix was isolated
perfectly. Re-running cost nothing and changed exactly one case. Contract
validity returned to 100% and no other number moved.

It also exposed a second problem hiding under the first. q06's JSON parsed
fine and the model's own verdict was still `no_answer`. The parser bug had
been masking an `answer_in_the_refusal`.

---

## v4

Two edits to the scope section, plus a rule about where citations go.

Scope now tests the question. A refund question is yours even when the answer
is no, even when the answer is report it as fraud, even when the answer is
that another team handles it. Chargebacks named as the explicit exception.

    recall@5              96.4% -> 100.0%
    recall@1              92.9% ->  96.4%
    MRR                    0.95 ->   0.98
    abstention recall    100.0% ->  86.4%
    abstention precision  78.6% ->  95.0%
    unparseable               1 ->  0
    never retrieved        q18 ->  none

### Two label errors found, one corrected

**q18 was never a retrieval failure.** Its gold list named only NIM-106.
It answers perfectly well from NIM-101, which was retrieved every time. Three
runs reported "never retrieved" because of a bad label. NIM-101 added to
`expected_articles`, and recall@5 went to 100%.

**q33 is an open spec question, left alone deliberately.** The model says
there is no deadline for requesting a refund, only a limit on the app route,
and NIM-102 supports that reading. The label says `answered`. Changing a
label to match what the model said is how you overfit to your own test set,
which D10 forbids, so the disagreement is recorded rather than resolved.

### An inline citation regression, caused and fixed

The v4 wording "cite the article that says it" made the model write citations
inside the answer text.

    No, gambling transactions cannot be refunded. {NIM-106, When we cannot
    refund / Payments we cannot refund, "We cannot refund gambling..."}

Fixed by stating that citations go only in the `citations` field. A customer
would have seen that brace soup.

---

## What four prompt versions taught

**v3's 100% abstention recall was luck.** It looked like the contradiction
rule working. It was the over-tight scope rule refusing everything nearby.
When v4 loosened scope to fix q06 and q44, q34 and q35 came back. The
contradiction rule has never worked in any version.

A number can hit its target for the wrong reason, and only the case-level
flip list shows it.

**Every prompt edit traded one case for another.** v3 fixed abstention recall
and broke four working cases. v4 fixed those and lost q34 and q35. Four
rounds of this is the signal to stop prompting.

---

## Three known failures, deliberately not fixed

| Case | Failure | Why it stands |
|---|---|---|
| q34, q35 | Answers the App Store contradiction by picking a side | The prompt rule does not work. A fifth attempt would likely trade another case |
| q37 | Answers a chargeback question from NIM-120 | Scope boundary. Same pattern |

The obvious fix is to edit the corpus, delete NIM-109 or drop NIM-120 from
the index, and all three go green. **Refused.** Those articles were planted
to test contradiction handling and scope. Removing them removes the test and
buys a number that means nothing.

---

## v4 against the spec

    recall@5             100.0%   target 95%    ok
    recall@1              96.4%   target 80%    ok
    MRR                    0.98   target 0.85   ok
    abstention precision  95.0%   target 70%    ok
    abstention recall     86.4%   target 95%    cannot confirm, CI 67% to 95%
    quotes verbatim        100%   target 100%   50/50
    banned cited              0
    C1 leaks                  0
    unparseable            none
    latency p95           2.77s   target 6s     ok
    cost per question    0.162c   target 3p     ok

    groundedness         UNMEASURED on v4. Last known 75% on v2.

Groundedness was skipped on cost. The citation completeness rule is therefore
the one part of the prompt with no evidence either way, and quote validity at
50/50 is adjacent evidence, not the same thing.

---

## Against v1

| | v1 | v4 |
|---|---|---|
| recall@5 | 96.4% | 100% |
| recall@1 | 71.4% | 96.4% |
| MRR | 0.84 | 0.98 |
| abstention recall | 54.5% | 86.4% |
| abstention precision | 80.0% | 95.0% |
| banned cited | 8 | 0 |
| C1 leaks | 3 | 0 |
