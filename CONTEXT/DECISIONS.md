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