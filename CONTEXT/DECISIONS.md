# Decisions

Each entry says what was decided and why. Do not reverse one of these
without adding a new entry explaining the reversal.

## D1. A separate repo, not the existing Claude repo
14 Sept 2026. One repo, one project. Mixing an unrelated project in means
neither is findable later, and automated checks would run against
unrelated files.

## D2. Build order is Triage, PolicyDesk, OpsAgent, Coach
14 Sept 2026. Not the order the source playbook lists. Triage first
because every one of its tests has an exact right answer, so the full
testing loop can be learned before anything fuzzy is introduced. Each
product after it adds exactly one new hard problem.

## D3. Mac, VS Code, GitHub Desktop, Python 3.13.5
14 Sept 2026. VS Code writes and runs code. GitHub Desktop handles
snapshots and syncing. They are not alternatives, they do different jobs.

## D4. Claude teaches, Surabhi does the work
14 Sept 2026. Claude proposes and explains. Nothing gets created without
being asked for first. Reversing this defeats the purpose of the project.

## D5. Project memory lives in the repo, not in a chat
14 Sept 2026. Chat sessions lose their memory. The CONTEXT folder is the
source of truth, so any new session can be brought fully up to speed by
pasting CONTEXT/START-HERE.md.

## D6. AICredits gateway, not the Anthropic API directly
15 Sept 2026. OpenAI-compatible, so we use the openai library. All model
calls go through shared/llm.py, which is the only file that knows this.
Swapping providers is an edit to that one file.

## D7. Responses are cached to disk, keyed by request fingerprint
15 Sept 2026. Makes repeat runs free and makes scores reproducible.
Temperature 0 is not deterministic, so without this a score change could
be noise rather than a real change.

## D8. Prompt v2 shipped, v3 deferred
15 Sept 2026. Urgency 75% to 85%. Known issues recorded in README rather
than fixed, because the dataset is too small to measure further work.

## D9. Promptfoo added for comparison only
15 Sept 2026. It does the matrix. score.py measures, gate.py enforces,
promptfoo compares. Our harness stays for provenance and the CI gate.

## D10. The goal is not a green matrix
15 Sept 2026. Every red cell must be explained, as a harness bug, a wrong
label, or a real model failure. Tuning until everything passes is
overfitting to our own test set.

## D11. Nimbus is one company across all four products
16 Sept 2026. Triage routes, PolicyDesk answers policy, OpsAgent acts,
Coach converses. One world means specs reference each other instead of
re-inventing vocabulary, and the four products compound into something
resembling a real support stack.

## D12. PolicyDesk serves two audiences under one spec
16 Sept 2026. Agent-assist and customer-facing, one retrieval core, two
answer contracts. The cost of this choice is an access-control boundary
inside retrieval, because some articles are internal-only. That boundary is
C1, the most severe failure in the spec.

## D13. Tools do the bookkeeping, hands do the judgement
16 Sept 2026. Product 1 was hand-run to teach the mechanism. From Product 2,
anything that only needs recording or comparing gets a real tool. Anything
requiring a decision stays manual. Specifically manual: writing specs,
labelling the golden set, reading every output in Beat 3, and validating any
LLM judge against hand labels.

## D14. Build the real stack, not the small-data version
16 Sept 2026. Product 2 adds Langfuse tracing, structured outputs, hybrid
retrieval with reranking on LangChain, a FastAPI service layer with auth and
rate limiting, and incremental Zendesk-shaped ingestion. The dataset being
small is not a reason to build a toy. Where live infrastructure genuinely
does not exist, we build the same shape against a local source so switching
is a credentials change, not a redesign.

## D15. Retrieval filters on status, visibility and supersedes
17 Sept 2026. The filter is enforced in SQL at query time, not in the prompt
and not at ingest. In the prompt it would be advice the model can ignore, and
it did ignore it 8 times in 50. At ingest the index could not serve agents
and customers from the same table, and an archived article would be
unrecoverable if it were ever republished.

Measured effect: C1 breaches 3 to 0, banned citations 8 to 0, and
unexpectedly recall@1 71% to 93%, because the superseded article had been
outranking the live one.

## D16. Scope is decided by the question, not by the answer
17 Sept 2026. A refund question is PolicyDesk's even when the answer is no,
or that it must be reported as fraud, or that another team handles it. Only
the question's subject decides scope. The v3 prompt got this backwards and
broke four working cases by treating "the answer is no" as "out of scope".

## D17. Contradictory and out-of-scope articles stay in the corpus
17 Sept 2026. NIM-108 and NIM-109 contradict, and NIM-120 covers chargebacks
which are out of scope. Deleting either would turn q34, q35 and q37 green.
Refused. They were planted to test contradiction handling and scope, so
removing them removes the test and buys a number that means nothing. The
three failures are recorded as known limitations instead.

## D18. Prompt iteration stops at v4
17 Sept 2026. Four prompt versions, and every edit traded one case for
another. v3 fixed abstention recall and broke four working cases, v4 fixed
those and lost two others. Diminishing returns. The remaining three failures
need a different kind of fix, not a fifth prompt.

## D19. The audience comes from the API key, never from the request
17 Sept 2026. The first /ask took `audience` as a body field, which meant
any caller could declare itself an agent and read internal articles. Every
visibility rule from D15 was bypassable with one word of JSON. A key now maps
to an audience and the caller never chooses. C1 is enforced in three places:
the SQL filter, the key mapping, and the CI gate.

## D20. Redaction is applied to traces as well as logs
17 Sept 2026. The access log never contained the question, but Langfuse was
storing every one in full. Logs feel like the risky place and the tracer does
not, which is how this is usually missed. shared/redact.py is wired into the
Langfuse client's mask hook. Traces created before this still hold real card
numbers, because redaction only protects what you collect next.

## D21. Secrets never enter the image
17 Sept 2026. .env is in .dockerignore. Images go to registries, get pulled
by anyone with access, and their layers are readable. Configuration arrives
at runtime as environment variables, which is also why shared/db.py has read
its DSN from the environment since Beat 2.

## D22. Hybrid retrieval was built, measured, and rejected
18 Sept 2026. Vector plus Postgres full-text, fused with Reciprocal Rank
Fusion. recall@5 fell 100% to 96.4%, recall@1 96.4% to 92.9%, MRR 0.98 to
0.95, and q44's gold article was missed entirely. The v2 filter had already
taken all the headroom, so keyword search had nothing to add and pushed
NIM-106 out of the top five on the cases that needed it. retrieve.py stays
on filtered-v1. retrieve_hybrid.py stays in the repo as the record.

The theory is still sound. Keyword search is measurably better at exact
values, which is hard case 3 in SPEC.md. The corpus is 43 chunks and too
clean for that to pay. Revisit when the corpus is thousands of articles.

## D23. LangChain is an adapter over our own retrieval, not a replacement
18 Sept 2026. lc_retriever.py wraps retrieve.search behind BaseRetriever.
LangChain's built-in vector stores expect their own schema, and rewriting a
working pgvector index with visibility filtering to fit a library is the
wrong trade. Verified the audience boundary survives the wrapper.

## D24. PolicyDesk ships on Haiku 4.5, chosen on failure mode not on score
18 Sept 2026. Sonnet 5 scored identically on abstention recall, 86.4% for
both, but on different cases. Sonnet fixed the App Store contradiction that
four prompt versions could not, and broke q41, answering a bereaved customer
with app instructions instead of handing off. Add 3x cost and a latency
budget missed on both p50 and p95.

For a product where vulnerability is a named failure class, Haiku's failure
mode is the safer one. A stronger model reasons better and holds back less.

## D25. Triage's open model question is answered, differently than asked
18 Sept 2026. The Triage README asks whether Haiku is good enough to switch
to. The question cannot be settled by one score, because the models fail on
different cases. "Scored at least as well" is not "is at least as good".
Where escalation exists to protect vulnerable customers, Haiku's greater
willingness to hand off is the behaviour the spec wants. That is a better
argument for Haiku than cost, and it was invisible in the aggregate.

## D26. The index is maintained, never rebuilt
18 Sept 2026. sync.py replaces ingest.py. A rebuild drops the table, which
leaves the index empty while it runs and pays for every embedding a second
time. Sync upserts on (article_id, section) and deletes in two places,
sections that no longer exist in a synced article, and on a full sync
articles that no longer exist in the source. Incremental is the default and
full is explicit, because only a full sync knows the article list is
complete enough to delete against.

## D27. Deletion was proved by breaking the source on purpose
18 Sept 2026. A claim about deletion is worth nothing untested. NIM-101 had
its last section dropped and its timestamp bumped, NIM-105 was removed
entirely, and both syncs were run against the damage.

Incremental caught the section and missed the article, 43 chunks to 42. Full
caught the article, 42 to 39. Restoring the source and running incremental
again left the index at 39, because restored articles carry their old
timestamps and never beat the watermark. Only full brought it back to 43.

An incremental sync can neither see a deletion nor heal one. That is the
failure naive syncs ship with, and it is now demonstrated rather than
asserted.

## D28. articles.jsonl stays as the measurement corpus for now
18 Sept 2026. Retrieval serves the index built from zendesk_articles.json,
but run.py, score.py and test_eval.py still read data/articles.jsonl. So
corpus_sha fingerprints a file that no longer decides what was retrieved, and
the C2 verbatim check compares quotes against wording the model was never
shown.

Measured before deciding. 3 of 53 quotes in the v6 run fail against the
Zendesk text, and all three are the same sentence in NIM-106, which is one
prose line in the old corpus and a bulleted list in the new one. One
article's wording, not a broken corpus.

Switching now turns a passing build red for something that is not a product
failure. Recorded as a known limitation instead, and left for whoever wires
up the live API, because that is the point at which the old file has to go.