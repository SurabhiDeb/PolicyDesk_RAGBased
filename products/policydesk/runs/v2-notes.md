# PolicyDesk v2 - retrieval filter

Run `20260917-142630Z-v2`. Prompt v1 unchanged. Retriever `filtered-v1`.

One variable. `retrieve.py` now filters on `status`, `visibility` and
`supersedes` at query time. Nothing else moved.

---

## Predicted against actual

Written down before the run, which is the only way to tell measuring from
rationalising.

| Metric | v1 | Predicted | Actual |
|---|---|---|---|
| banned cited | 8 | 0 | 0 |
| C1 leaks | 3 | 0 | 0 |
| abstention recall | 54.5% | ~77% | 72.7% |
| recall@5 | 96.4% | same | 96.4% |
| recall@1 | 71.4% | not predicted | 92.9% |
| MRR | 0.84 | not predicted | 0.95 |
| groundedness | 83% | roughly flat | 75% |

Two predictions missed, in opposite directions.

---

## The unpredicted win

recall@1 rose 21 points and MRR went from 0.84 to 0.95.

NIM-103 said almost exactly what the live NIM-113 says. It was not merely
dangerous, it was **outranking the right answer**. Removing 15 banned chunks
removed 15 competitors.

Cleaning the index is a retrieval quality improvement, not only a compliance
one. That was not in the analysis and it should have been.

It also changes the plan. recall@1 at 92.9% already clears its 80% target, so
the reranker in v4 has far less to do than assumed. Still worth measuring,
but expect little.

---

## The unpredicted loss

Groundedness fell from 83% to 75%.

First check was whether the judge had simply changed its mind. It had not.
Every newly flagged case has a different answer and a different retrieved
set. The two cases whose answers were byte-identical across runs, q44 and
q47, got identical verdicts, which is reasonable evidence the judge is
stable.

**Retrieval changed even for cases that never touched a banned article.**
q13 pulled NIM-099 and NIM-103 in v1. With those gone, three NIM-113 chunks
and a NIM-101 moved up to fill the slots. Removing chunks reshuffles the top
k for everything.

**And with less rubbish in context, the model became more helpful.**

    v1  No, Nimbus cannot refund a payment because you changed your mind.
    v2  No, Nimbus cannot refund a payment simply because you changed your
        mind. Refunds are only available for specific circumstances such as
        payments made in error, subscriptions cancelled within their cooling
        off period, or duplicate payments.

Longer, better, and more sentences means more chances one of them has no
quote behind it. Improving retrieval made groundedness worse. Two quality
axes traded against each other and neither of us saw it coming.

### The eight flagged cases

| Group | Cases | What it is |
|---|---|---|
| `uncited_support` | q03, q13, q47 | The claim is in the article. The quote given does not contain it |
| Applying policy, not stating it | q04, q11, q12 | "a payment that is two years old" where the quote says 180 days. Section 2 forbids this |
| Genuine invention | q37, q44 | q37 invents "contact the merchant about their returns policy first" |

Only one of eight is invention in the usual sense.

---

## Flip list

Aggregates hide mechanisms. These are the named cases that moved.

**Fixed, stopped answering when they should not.** q28, q39, q40, q42.
All four were answering from articles that no longer reach the model.

**Fixed, stopped refusing when they should not.** q36. The draft crypto
article that told it not to rely on the draft crypto article is gone, so the
live NIM-106 answers plainly. `poisoned_abstention` resolved by the filter,
as predicted.

**Fixed on groundedness.** q31, q49. The blended timescale sentence had
nothing left to blend.

**Still wrong, all in the prompt's column.** q34, q35, q50 are the App Store
contradiction. q37, q38 are chargebacks, out of scope. q43 is the vague
question. q33 still refuses when NIM-102 answers it. q18's gold article is
still never retrieved.

---

## Where v2 stands

    recall@5            96.4%   cannot confirm, 27/28
    recall@1            92.9%   passes on paper, CI 77% to 98%
    MRR                  0.95
    abstention recall   72.7%   FAIL, target 95%
    groundedness          75%   FAIL, target 98%
    banned cited            0
    C1 leaks                0
    quotes verbatim      100%
    latency p95          2.90s   passes
    cost per question   0.114c   passes

CI went green on C1 and two xfail markers became lies and were deleted.

---

## What v3 must do

The prompt, one variable, and it now has four jobs rather than three.

1. **Scope.** Chargebacks belong to Triage disputes. q37, q38.
2. **Contradiction.** Two live articles that disagree means `no_answer`.
   q34, q35, q50.
3. **Abstention balance.** Stop refusing when the answer is present. q33.
4. **Citation completeness.** Every sentence must be covered by a quote the
   answer actually provides. This is new, and it exists because v2 made the
   answers longer.

Job 4 was not in the v1 analysis. It arrived because fixing retrieval
changed how the model writes.
