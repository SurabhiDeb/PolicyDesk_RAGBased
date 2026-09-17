# PolicyDesk v1 - error analysis

Run `20260917-071445Z-v1`. Prompt v1, Haiku 4.5, 50 questions, k=5.
Read by hand in Langfuse, 10 by Surabhi and 40 by Claude, cross-checked
against the run record.

Two of the ten hand reads were corrected on review. q34 was scored clean but
the contradicting article was in its retrieved list. q41 was scored as a
failure but is the best answer in the run.

---

## Headline

34 of 50 clean. 16 cases carry at least one failure.

Every one of the 16 traces back to four missing things, and not one of them
is a hallucination in the usual sense. The model rarely invented facts. It
was handed material it should never have seen, and given no rules about
scope, contradiction or when to stop.

---

## Failure modes, by occurrence

A case can carry more than one, so these sum to more than 16.

| Mode | Count | Cases |
|---|---|---|
| `should_have_abstained` | 8 | q28, q34, q35, q37, q38, q42, q43, q50 |
| `stale_source` (C3) | 5 | q31, q32, q42, q43, q49 |
| `contradiction_blended` | 4 | q31, q32, q43, q49 |
| `internal_leak` (C1) | 3 | q28, q39, q40 |
| `wrongly_abstained` | 3 | q18, q33, q36 |
| `invented_distinction` | 1 | q35 |
| `poisoned_abstention` | 1 | q36 |
| `uncited_claim` | 0 | none |
| `fabricated_quote` | 0 | none |

Two modes were not in the starting taxonomy and were added after reading.

**`invented_distinction`.** Given two articles that contradict, the model
manufactured a condition under which both could be true. q35 split Google
Play refunds into "purchased with your Nimbus card" and "billed by a third
party" as if those were different situations. They are the same situation.
More dangerous than blending, because the answer reads like expertise.

**`poisoned_abstention`.** A banned article caused a refusal instead of a
wrong answer. q36 refused to answer a crypto question because the draft
article told it not to rely on the draft article, while the live NIM-106
answered it plainly. A banned source did damage without ever being cited,
so the citation check could never have caught it.

---

## Root causes, and what each one costs

### 1. Retrieval applies no filter. 9 cases

The index contains every article regardless of `visibility`, `status` or
`supersedes`. 15 of 43 chunks are banned for a customer, so 35% of the index
is poison.

A banned article reached the model in **37 of 50** cases. It declined to use
it 29 times. The 8 that got through are q28, q31, q32, q39, q40, q42, q43
and q49, of which q28, q39 and q40 are C1 breaches. q36 is the ninth, where
a banned article caused a wrong refusal.

Drawing 5 of 43 chunks at random would hit a banned one about 88% of the
time. At 74%, retrieval is barely better than chance at avoiding them,
because it was never asked to be.

NIM-103 is the worst single offender, appearing in 20 of the 37. It says
almost exactly what the live NIM-113 says, so similarity cannot separate
them. No better embedding model fixes this. A `WHERE` clause does.

### 2. The prompt says nothing about scope. 2 cases

q37 and q38 answered chargeback questions from NIM-120. Section 2 of the
spec puts chargebacks out of scope, but v1 never mentions it, so the model
had no way to know. Not a retrieval failure and not a hallucination. A
missing instruction.

### 3. The prompt says nothing about contradiction. 3 cases

q34, q35 and q50 all had both NIM-108 and NIM-109 in front of them. q34 and
q50 picked a side silently. q35 invented a distinction. Section 5 says two
live articles that contradict should return `no_answer`, and v1 never says so.

### 4. The prompt pushes too hard toward refusal. 2 cases

q18 and q33 found the answer, wrote it inside the refusal, then refused.
q33 was asked whether there is a deadline and replied that the articles "do
not contain information about a deadline; they only mention that payments
older than 180 days cannot be refunded through the app". That is the
deadline.

---

## What retrieval got wrong on its own

Separate from the answer layer, and measured properly in Beat 4.

**No relevance bar.** `retrieve.py` always returns exactly k rows however
bad the match. q19, "where is my order", got refund timescale articles.
Section 5 says a case abstains when nothing clears the relevance bar, and no
bar exists in the code. The spec and the implementation disagree.

**The bereavement miss.** q41, "my husband died last month", did not
retrieve NIM-203, the article written for that situation. q29, "can my
husband request a refund on my behalf", did. The right article surfaced for
the question that did not need it and missed the one that did.

**Rank is not relevance.** q28 cited NIM-201 at rank 2 over NIM-202 at rank
1, and was right to. NIM-202 is about approval thresholds and does not
answer the question. The model reranked using comprehension, which
similarity search cannot do. This is why recall@5 matters more than
recall@1 for answer quality, and why rerankers exist.

---

## Things that worked

Worth recording so we do not "fix" them.

q17 hit the same three-way timescale trap as q31 and got it right, using the
live 10 day figure. The failure is not universal, which makes it harder to
catch and easier to regress.

q41 abstained, handed off, gave a reason about specialist support, and did
not quote the internal vulnerability guidance at a grieving customer. No
rule told it to. Best answer in the run.

Zero contract failures. All 50 parsed. No fabricated quotes, no uncited
claims in this run.

Yesterday's hand run of the same q31 question produced an uncited claim.
This run cited it. Same prompt, same model, temperature 0. Temperature 0 is
not deterministic, again.

---

## What this means for the next two runs

The 16 failures split cleanly into two independent fixes, which means two
runs, one variable each.

**v2, retrieval filter only.** Filter on `visibility`, `status` and
`supersedes` at query time. Expected to fix 9 cases and to change nothing
about the prompt. If the number moves by more or less than 9, we have
learned something.

**v3, prompt only.** Add scope, contradiction and abstention rules. Expected
to fix the remaining 7.

A relevance bar and a reranker come after both, once we can see what is left.

Do not do them together. Changing both means neither can be attributed.
