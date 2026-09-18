# PolicyDesk v5 - hybrid retrieval, and why it does not ship

Run `20260918-073550Z-v5`. Prompt v4 unchanged. Retriever `hybrid-v1`.

Beat 6 work finished after the service layer. One variable, the retriever.

---

## What was built

A `tsv` column on `chunks`, GENERATED from title, section and text, so
Postgres maintains it and it cannot drift out of sync with the text.

A hybrid query fusing vector search and keyword search with Reciprocal Rank
Fusion. Each half ranks its candidates and each contributes `1 / (60 + rank)`
to a chunk's score. RRF fuses ranks rather than scores, so a cosine distance
and a `ts_rank` never have to be made comparable.

A LangChain `BaseRetriever` wrapper, `lc_retriever.py`.

No index on `tsv`, the same reasoning as the vector index. At 43 rows a
sequential scan wins.

---

## Predicted against actual

| Metric | v4 | Predicted | Actual |
|---|---|---|---|
| recall@5 | 100% | 100%, no headroom | 96.4% |
| recall@1 | 96.4% | same or slightly worse | 92.9% |
| MRR | 0.98 | slightly worse | 0.95 |
| abstention recall | 86.4% | unchanged | 90.9% |
| abstention precision | 95.0% | unchanged | 90.9% |

The prediction was that hybrid would make things marginally worse. It did.

---

## The result

**Hybrid retrieval does not ship.** Three retrieval metrics fell and q44's
gold article, found every time in v4, was missed entirely.

The mechanism is visible in the detail. q44 and q18 both depend on NIM-106
and both got worse. The keyword half promoted chunks sharing common words
with the question and pushed NIM-106 out of the top five.

Vector search already had 100% recall@5 after the v2 filter. There was
nothing for keyword search to add and plenty for it to disturb.

Abstention moved too, recall 86.4% to 90.9% and precision 95.0% to 90.9%.
Those traded rather than improved, and they are downstream of a different
context reaching the model, not of anything the hybrid did on purpose.

`retrieve.py` stays on `filtered-v1`. `retrieve_hybrid.py` stays in the repo
as a measured experiment that lost.

---

## What keyword search actually does, measured

Three queries, run directly against Postgres before any fusion.

**It finds nothing on a natural question.** `plainto_tsquery` ANDs every
term, so q18's question demanded a chunk containing shop AND deliver AND
order AND want. Zero rows.

**It is worse than vector search at vocabulary mismatch.** I predicted
keyword search would rescue q18 because "delivered" and "ordered" are in
NIM-106. They are not. NIM-106 says "if you received what you paid for and
changed your mind" and "the merchant's own returns policy applies". Not one
word overlaps with how the customer phrased it. Vector search at least knows
shop and merchant mean the same thing.

Confirmed in the hybrid run itself, where every keyword column for q18 read
`-`. The keyword half contributed nothing at all.

**It is genuinely better at exact values.** `180 days app` returned exactly
one row, NIM-102, at rank 0.32, twenty times higher than anything the OR
query produced. That is hard case 3 from SPEC.md and it is the half vector
search is weakest at.

So the theory behind hybrid is sound. The corpus is just too small and too
clean for it to pay.

---

## What LangChain is for here

Not the retrieval. The adapter.

Almost nobody's production store matches the shape LangChain's built-in
vector stores expect, and rewriting a working index to fit a library is the
wrong trade. What people do is wrap their own search behind `BaseRetriever`.

`PolicyDeskRetriever` satisfies LangChain's retriever interface, so it drops
into any LangChain chain, agent or pipeline unchanged. The Postgres schema,
the SQL filter and the audience rule are untouched.

Verified that the visibility boundary survives the wrapper. The same question
through `retriever.invoke` returns NIM-201, NIM-202 and NIM-203 for an agent
and none of them for a customer.

---

## Where v5 stands against v4

    recall@5             100.0% -> 96.4%
    recall@1              96.4% -> 92.9%
    MRR                    0.98 -> 0.95
    abstention recall     86.4% -> 90.9%
    abstention precision  95.0% -> 90.9%
    banned cited              0 -> 0
    C1 leaks                  0 -> 0
    unparseable            none -> none
    p50 latency           1.52s -> 1.24s

v4 remains the shipping configuration.
