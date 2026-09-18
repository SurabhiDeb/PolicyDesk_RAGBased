# Progress

Last updated: 14 September 2026

## Where we are right now

Product 1 (Triage) is COMPLETE at a deliberately limited scope.
Ready to start Product 2 (PolicyDesk, RAG).

## Next step

Beat 8 done. Start project 3.

## Note on ordering

Beats 1 to 6 ran in sequence and that is the pattern that carries to
Products 3 and 4. Beats 7 and 8 are additions to the six-beat rhythm, not
part of it. 6a and 6b are Beat 6 work finished late.

## Product 2 service layer, Beat 7 done
  POST /ask with API key auth, 20/min rate limit, 422 on bad input
  GET /health returning 503 when degraded
  PII redacted in logs and in Langfuse traces
  Dockerfile, non-root, no secrets in the image
  Known limits: in-memory rate limiter, Postgres and Langfuse not in compose
## Product 2 current, prompt v4, retriever filtered-v1, Haiku 4.5
  recall@5 100%, recall@1 96.4%, MRR 0.98
  abstention recall 86.4% (target 95%), precision 95.0%
  banned cited 0, C1 leaks 0, unparseable none
  groundedness unmeasured on v4, last known 75% on v2
  three known failures: q34, q35 contradiction, q37 scope
  notes in runs/v1-notes.md, v2-notes.md, v4-notes.md

## Product 2 baseline, prompt v1, Haiku 4.5, 50 cases
  recall@5   96.4%, recall@1 71.4%, MRR 0.84
  abstention recall 54.5% against a 95% target
  groundedness 83% against 98%, judge Sonnet 5
  8 cases cite a banned article, 3 of them C1
  30 of 50 clean, taxonomy in runs/v1-notes.md

## Product 1, Triage - done

Built, evaluated, and gated in CI.

Final numbers, prompt v2, Sonnet 5, 20 seed cases:
  team      95%  (19/20)   target 85%
  urgency   85%  (17/20)   up from 75% on v1
  escalate  7/7, zero missed
  contract  100%
  latency   p50 4.18s, p95 6.67s   FAILS the 1s / 3s budget
  cost      $0.052 per full run, about 0.26p per message

What exists:
  products/triage/SPEC.md            the product definition
  products/triage/data/seed.csv      20 labelled messages
  products/triage/prompts/v1.md,v2.md  versioned, never edited in place
  products/triage/classify.py        the classifier
  products/triage/score.py           the metrics report
  products/triage/gate.py            CI pass/fail
  products/triage/runs/              every run, with full provenance
  shared/llm.py                      provider wrapper with disk cache
  shared/stats.py                    Wilson intervals
  .github/workflows/ci.yml           gate runs on every push

Known limitations, accepted deliberately:
  - 20 cases only. Team accuracy CI is 76-99%, too wide to confirm the
    target. Needs 60-100 cases, weighted to hard escalation cases.
  - Case 14 (severe distress) gets P2, should be P1. Still escalates, so a
    human sees it, but the tier is wrong. Fix in v3.
  - Case 2 (declined card) team boundary never decided.
  - Case 7 gets P3, should be P4.
  - Latency fails the budget on every call. Not investigated.
  - Output contract is missing secondary_intent and confidence.
  - Case 6's second intent is silently dropped.

## Things learned that apply to every product

1. Do error analysis before writing evals. v1 was deliberately crude so it
   would fail in ways worth studying.
2. When the bot disagrees with your label, three things could be true: the
   bot is wrong, the label is wrong, or the spec never decided.
3. A pass rate without a confidence interval is a rumour. 19/20 is "76% to
   99%", which straddles an 85% target.
4. On small datasets the case-level flip list beats the aggregate. 75% to
   80% proved nothing; five specific cases flipping proved the mechanism.
5. Change one variable per run or you cannot attribute the change.
6. Test your theory before fixing it. The Hindi ablation cost 0.1p and
   saved a wasted prompt change.
7. Fail safe. An unparseable response must default to escalate, never to
   silence.
8. Temperature 0 is not deterministic. Case 13 gave different answers to
   identical input on two runs.
9. Prompt improvements cost tokens, money, and latency. v2 was 42% more
   expensive than v1.
10. Watch out for plausible numbers that are untrue. We shipped four:
    TRUE vs true, cached seconds, the price lookup, and the dirty git flag.
    None of them crashed. All of them lied.

## Session log

### Session 1 - Setup
Created the repo, cloned with GitHub Desktop, confirmed VS Code and
Python 3.13.5. Learned: repository, clone, commit, push, terminal, markdown.

### Session 2 - Memory system
Created the CONTEXT folder and did the full write-commit-push loop for the
first time.

### Session 3 - CI
Built .github/workflows/hello.yml, saw it pass and fail on purpose.
Learned: CI, workflow, runner, YAML, exit codes, fail fast.

### Session 4 - Triage spec and first script
Wrote SPEC.md and seed.csv. Set up .venv and .gitignore. Wrote
check_data.py, which found a real bug on its first run (a spreadsheet had
rewritten true as TRUE).

### Session 5 - Provider setup
Switched from the Anthropic API to the AICredits gateway
(https://api.aicredits.in/v1, OpenAI-compatible, use the openai library).
Queried the gateway for its real model ids rather than guessing. They are
prefixed, e.g. anthropic/claude-sonnet-5.

### Session 6 - The wrapper
Built shared/llm.py. One file knows the provider; nothing else does. Every
response is cached to disk by request fingerprint, so repeat runs are free
and reproducible.

### Session 7 - The crude classifier
Prompt v1, deliberately mediocre so it would produce failures worth
studying. Ran all 20, saved a run record with full provenance.

### Session 8 - Error analysis and baseline
Read all 20 outputs by hand and built a six-mode failure taxonomy in
runs/v1-notes.md. Built shared/stats.py and score.py. Baseline recorded.

### Session 9 - v2, the fail-safe fix, and the CI gate
Prompt v2 fixed urgency rules only, one variable. Urgency 75% to 85%.
Found and fixed a truncation bug that silently turned the most important
case into a missed escalation. Added gate.py and wired it into CI, then
proved it blocks by deliberately breaking a run file.


Open question: Haiku 4.5 is 3x faster (1.3s vs 4.2s) and half the price
than Sonnet 5, and scored at least as well on prompt v2 in a promptfoo
matrix. Not switched. Needs an escalation-recall check first.

## Note on ordering

Beats 1 to 6 ran in sequence. Two items planned for Beat 6, hybrid retrieval
on LangChain and the Haiku against Sonnet matrix, were not done before the
service layer and are being finished after it. Beats 7 and 8 are additions to
the original six-beat rhythm, not part of it.

## Product 2 ingestion, Beat 8 known limits

  A full sync against an empty source deletes the entire index and reports
  it as a success. `article_id <> ALL(empty array)` is true for every row,
  so PRUNE_ARTICLES matches everything. Verified against Postgres, not
  reasoned about. Harmless while the source is a local JSON file, because
  emptying it takes a deliberate act. It becomes real the day
  source_zendesk.py points at the live API, where an empty result is an
  ordinary failure, an expired token, a wrong locale, a filter matching
  nothing. Guard it before going live, not before.

  The high water mark is recomputed from the source every run rather than
  carried forward, so it can move backwards. Restoring an older copy of the
  source rewound it from 2026-09-18 to 2026-03-14, seen in the restore run.
  Against a live Zendesk a restored backup would silently re-sync months of
  articles.

  The incremental path fetches the whole corpus anyway, only to compute the
  high water mark. It is O(entire help centre) per run, which defeats the
  incremental endpoint it exists to use. The watermark should come from the
  changed set with the previous value as its floor.

  ## Where we are right now

Product 1 (Triage) is COMPLETE at a deliberately limited scope.
Product 2 (PolicyDesk) is COMPLETE, Beats 1 to 8.
Ready to start Product 3 (OpsAgent, tool use).

## Next step

Product 3, OpsAgent. Beat 1, the spec.

## Product 2 ingestion, Beat 8 done
  source_zendesk.py translates Zendesk's article shape into ours and is the
  only file that knows the source system
  html_sections.py chunks real help centre HTML instead of markdown
  sync.py upserts on (article_id, section), prunes dead sections on every
  run, and prunes dead articles on --full only
  sync_state holds the high water mark so a run knows where the last got to
  Proved by breaking the source on purpose, see D27
  Index is 16 articles, 43 chunks, unchanged from the ingest.py corpus

## Product 2 ingestion, Beat 8 known limits

  The gate does not measure the shipping configuration. test_eval.py and
  score.py both read the newest run file, which is now the v6 Sonnet
  comparison. PolicyDesk ships on Haiku, D24, whose numbers are in the v4
  run. Every experiment that runs last silently becomes what CI gates on.

  A full sync against an empty source deletes the entire index and reports
  it as a success. `article_id <> ALL(empty array)` is true for every row,
  so PRUNE_ARTICLES matches everything. Verified against Postgres, not
  reasoned about. Harmless while the source is a local JSON file, because
  emptying it takes a deliberate act. It becomes real the day
  source_zendesk.py points at the live API, where an empty result is an
  ordinary failure, an expired token, a wrong locale, a filter matching
  nothing. Guard it before going live, not before.

  The high water mark is recomputed from the source every run rather than
  carried forward, so it can move backwards. Restoring an older copy of the
  source rewound it from 2026-09-18 to 2026-03-14, seen in the restore run.
  Against a live Zendesk a restored backup would silently re-sync months of
  articles.

  The incremental path fetches the whole corpus anyway, only to compute the
  high water mark. It is O(entire help centre) per run, which defeats the
  incremental endpoint it exists to use. The watermark should come from the
  changed set with the previous value as its floor.

  corpus_sha and the C2 quote check still read articles.jsonl. See D28.