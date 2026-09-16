# PolicyDesk - Product Specification

Version 1. 16 September 2026.

This document defines what correct means. Every test, metric, and CI gate
downstream derives from it.

Nimbus. Same company as Triage.

---

## 1. The job

Answer a refund question using Nimbus's own help articles, cite the article,
or say the articles do not cover it and hand off to a human.

## 2. Scope

### It does
- Answer refund questions from published help articles
- Cite the article and the exact text it relied on
- Abstain and hand off when the articles are silent
- Serve two audiences, a support agent and a customer

### It does not
- Decide whether a refund is granted. It states the policy, it does not apply it.
- Read any account, payment, or order. That is OpsAgent, Product 3.
- Answer topics outside refunds.
- Answer when the articles are silent.

An answer traceable to an article can be checked. An answer that decides an
outcome is a promise Nimbus has to honour, and no document can verify it.

## 3. Output contract

Every response returns exactly this shape, for either audience.

    status           answered | no_answer
    answer           text, or null when no_answer
    citations        list of {article_id, section, quote}
                     empty only when no_answer
    audience         agent | customer
    confidence       low | medium | high
    handoff_reason   one sentence, only when no_answer

Citations carry the quote, not just the article id. A link says where it
looked. The quote lets a test check the article actually says what the
answer claims.

`no_answer` is a success state, not a failure. A bot that never hands off
is guessing.

`audience` is recorded on the response, not just the request, so an
internal-content leak can be traced across every affected answer.

## 4. The corpus

Every help article carries this metadata.

    article_id     stable, never reused
    title
    body           markdown
    visibility     public | internal
    status         published | draft | archived
    last_updated   date
    supersedes     article_id, or null

### Visibility rules

- `customer` retrieves `public` and `published` only
- `agent` also retrieves `internal`
- `draft` and `archived` are never retrieved by either

`visibility` is the access-control boundary. A customer seeing an internal
article is worse than a wrong answer, because it is a breach rather than a
mistake.

`status` exists because real help centres are full of drafts and dead
articles nobody deleted. Index everything and the bot cites a policy retired
two years ago.

`supersedes` is how a changed policy is handled. The old article stays for
the audit trail. Retrieval ignores it.

## 5. When it must not answer

Six cases return `no_answer` with a handoff reason.

| Case | Why |
|---|---|
| Nothing retrieved clears the relevance bar | No evidence, no answer |
| Two live articles contradict and neither supersedes | The company has not decided, so the bot cannot |
| The question is about a specific account, order, or payment | Out of scope |
| The question is not about refunds | Out of scope |
| The answer needs a step the articles do not state | The inference trap. Combining two facts into a third is where hallucination is most convincing |
| A customer asks something only `internal` articles answer | Agent gets the answer. Customer gets a handoff, never the internal text |

### Target abstention rate

15% to 35%.

Below 15% it is answering things it should not. Above 35% it is not earning
its place.

This range is a guess. Beat 3 is where we find the real number, with
evidence.

## 6. Definition of a good answer

1. Every claim in the answer is supported by one of its citations
2. Every quote appears verbatim in the article it names
3. Cited articles are `published` and visible to that audience
4. Articles silent, `no_answer`
5. Output matches the contract exactly
6. Anything unparseable becomes `no_answer` with a handoff. Fail toward the human.
7. Agent answers may use internal terms. Customer answers may not.

## 7. Unacceptable failures

Each becomes a test tagged `critical`. One failure fails the build.

| # | Failure |
|---|---|
| C1 | Internal article content reaches a customer |
| C2 | A citation whose quote is not in the article it names |
| C3 | An answer drawn from an `archived` or superseded article |
| C4 | A policy stated with no supporting article |
| C5 | Output that does not match the contract |
| C6 | A refund decision or a promise |

C2 is the one people underestimate. A fabricated citation is worse than no
citation, because it survives review. The reviewer sees a source, assumes
someone checked it, and ships.

## 8. Success metrics

Two separate scoreboards. Retrieval sets the ceiling. If the right article
never came back, no prompt change fixes the answer.

### Retrieval

| Metric | Target | Why |
|---|---|---|
| recall@5 | 95% | The correct article is in the top 5 |
| recall@1 | 80% | How often it is first, which is what a reranker moves |
| MRR | 0.85 | How far down the list the right answer sits, averaged |

MRR is mean reciprocal rank. Right article first scores 1, second 0.5,
third 0.33, averaged across all questions.

### Answer

| Metric | Target | Why |
|---|---|---|
| Citation validity | 100% | Quote appears verbatim. Mechanical, no judge |
| Groundedness | 98% | Every claim traceable to a citation. Needs a judge |
| Abstention recall | 95% | Of the questions it should refuse, how many it refused |
| Abstention precision | 70% | Deliberately low. A needless handoff costs minutes, a wrong answer costs trust |
| Critical C1 to C6 | 100% | No tolerance |
| Contract validity | 100% | A malformed response cannot be served |

Groundedness is the only metric needing an LLM judge. That judge is
validated against hand labels before it is trusted.

## 9. Budget

Roughly 1,200 questions per day.

| | Target |
|---|---|
| p50 latency | under 3s |
| p95 latency | under 6s |
| Cost per question | under 3p |

Higher than Triage on purpose. Two model calls now, retrieval then answer,
and the answer prompt carries several articles inside it.

Set from what is achievable, not what sounds good. Triage set a 1s budget it
never met, which made the number useless.

## 10. Known hard cases

Recorded before building.

1. A superseded policy that still gets cited
2. Two live articles that contradict each other
3. Exact values. "14 days", "£100", "Section 75". Similarity search is worst
   at the terms policy answers depend on.
4. A question needing two articles combined
5. A customer question only an internal article answers
6. A question that sounds like refunds but is a chargeback, which belongs to
   Triage's `disputes` team
7. The customer's words sharing no vocabulary with the article's words

Cases 3 and 7 drive the retrieval work in Beat 6.

---

## Appendix. Where this came from

The corpus is synthetic, written to mirror how real help centres publish.
Synthetic is the weakest source of test data and the correct starting point
when no production traffic exists. It is replaced by real articles as soon
as any exist.