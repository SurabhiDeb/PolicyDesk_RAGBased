# Progress

Last updated: 14 September 2026

## Where we are right now

Product 1 (Triage) is COMPLETE at a deliberately limited scope.
Ready to start Product 2 (PolicyDesk, RAG).

## Next step

Product 2, Beat 4. Retrieval metrics, pytest, structured outputs, ragas.
Do not touch retrieval or the prompt yet, v1 is the baseline.

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