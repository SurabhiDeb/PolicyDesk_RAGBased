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