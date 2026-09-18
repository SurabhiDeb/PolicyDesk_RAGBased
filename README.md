# Chatbot Lab

Four chatbots built from scratch to production standard, as a way of learning
software engineering, product thinking, and testing.

Owner: Surabhi. Started September 2026.

| # | Product | What it does | Status |
|---|---|---|---|
| 1 | **Triage** | Routes a customer support message to a team, urgency, escalation | **Done** |
| 2 | PolicyDesk | Answers refund questions from help docs (RAG) | **Done** |
| 3 | OpsAgent | Looks up orders and issues refunds (tool use) | Not started |
| 4 | Coach | Multi-turn assistant with a fixed persona | Not started |

---

## How to run it

```bash
source .venv/bin/activate              # every new terminal
python3 products/triage/check_data.py  # validate the dataset
python3 products/triage/classify.py 20 # run the classifier
python3 products/triage/score.py       # read the metrics
python3 products/triage/gate.py        # pass/fail, same as CI
promptfoo eval && promptfoo view       # prompt x model matrix

.env holds AICREDITS_API_KEY, AICREDITS_BASE_URL, and OPENAI_API_KEY
(same key, promptfoo needs that name). Never committed.

Layout:

CONTEXT/              project memory, readable by any new Claude session
  START-HERE.md       paste into a new chat to resume work
  PROGRESS.md         where we are, updated when pausing
  DECISIONS.md        choices made and why
  GLOSSARY.md         every term, plain English

shared/
  llm.py              the ONLY file that knows the provider. Caches to disk.
  stats.py            Wilson confidence intervals

products/triage/
  SPEC.md             the product definition. Everything downstream inherits.
  data/seed.csv       20 labelled messages
  prompts/v1.md v2.md versioned, never edited in place
  classify.py         the classifier
  score.py            metrics report
  gate.py             CI pass/fail
  runs/               every run, with full provenance
  runs/v1-notes.md    the error analysis and failure taxonomy

promptfoo/            matrix comparison config
.github/workflows/    CI, runs the gate on every push


Product 1 results:

Prompt v2, Sonnet 5, 20 seed cases.

Metric	Result	Target
Team accuracy	95% (19/20), CI 76-99%	85%
Urgency	85% (17/20), up from 75% on v1	none set
Escalation recall	7/7, zero missed	99%
Contract valid	100%	100%
Latency	p50 4.18s, p95 6.67s	FAILS 1s / 3s
Cost	$0.052 per run, 0.26p per message	under 1p

The failure taxonomy that produced v2 is in products/triage/runs/v1-notes.md.
Six failure modes, found by reading all 20 outputs by hand.

The rules this repo runs on:
1. Pinned model ids, never an alias containing "latest"
2. Prompts are immutable versioned files. A change creates a new file.
3. Every run records prompt sha, model, dataset sha, git sha, cost
4. One variable per run, or you cannot attribute the change
5. Report per-failure-mode, never a bare aggregate
6. Fail safe. An unparseable response escalates, never falls silent.
7. Never tune against the split you report on

What we learned:
The engineering lessons, in the order we hit them.

1. Do error analysis before writing evals. Prompt v1 was deliberately
crude so it would fail in ways worth studying. You cannot analyse a bot that
does not make mistakes.

2. When the bot disagrees with your label, three things could be true.
The bot is wrong, the label is wrong, or the spec never decided. Work out
which before changing anything. Most of our "failures" were spec gaps.

3. A pass rate without a confidence interval is a rumour. 19/20 is
"somewhere between 76% and 99%", which straddles an 85% target. You cannot
claim you meet it.

4. On small datasets the flip list beats the aggregate. 75% to 80% proved
nothing. Five named cases flipping proved the mechanism worked.

5. Change one variable per run. v2 fixed urgency only. That is why we
know the urgency rules were what helped.

6. Test your theory before fixing it. The Hindi ablation cost 0.1p and
saved a wasted prompt change. The language was never the cause.

7. Fail safe. A truncated response silently became "no escalation" on the
most important case in the dataset. Systems that cannot understand their own
output must take the least costly action, not the quietest one.

8. Temperature 0 is not deterministic. Case 13 gave different answers to
identical input on two runs. Caching is what makes scores reproducible.

9. Prompt improvements cost tokens, money, and latency. v2 was 42% more
expensive and 22% slower than v1.

10. Watch for plausible numbers that are untrue. We shipped five, and not
one of them crashed:

Bug	What it claimed
TRUE vs true	0 escalations out of 20, when there were 7
Cached seconds	1.16s for a call that read a local file
Price lookup	$0.0000 for every run
Git dirty flag	Dirty on every run, from untracked output files
max_tokens 300	A truncation reported as a JSON syntax error

11. Two tools disagreeing means one is wrong. Promptfoo scored v2/Sonnet
at 10/20 where our harness scored 16/20. Unresolved. Do not average them and
do not pick the one you prefer.

Known limitations of Product 1:
Accepted deliberately, not forgotten.

20 cases only. Confidence intervals are too wide to confirm any target.
Needs 60-100, weighted toward hard escalation cases. Evidencing 99%
escalation recall would need roughly 400 escalation cases.
Case 14 (severe distress) gets P2, should be P1. Still escalates.
Case 2 (declined card) team boundary never decided.
Latency fails the budget on every call. Not investigated.
Output contract is missing secondary_intent and confidence.
Case 6's second intent is silently dropped.

Open questions
Haiku 4.5 is 3x faster (1.3s vs 4.2s) and half the price, and scored at
least as well as Sonnet on prompt v2. Not switched. Needs an
escalation-recall check first.
The promptfoo v2/Sonnet discrepancy. Suspected cause is reasoning tokens
consuming the max_tokens budget and truncating output.

Answered in PolicyDesk, see products/policydesk/runs/v6-notes.md. The two
models fail on different cases rather than at different rates, and Haiku hands
off to a human more readily, which is what escalation exists for.

---

## Product 2 results

Prompt v4, retriever filtered-v1, Haiku 4.5, 50 questions, 28 with a gold
article. Numbers from runs/20260917-153710Z-v4.json.

Metric                  Result              Target
recall@5                100%                none set
recall@1                96.4%               80%
MRR                     0.98                none set
Abstention recall       86.4%               FAILS the 95% target
Abstention precision    95.0%               70%
Banned articles cited   0                   0
C1 internal leaks       0                   0
Unparseable             0                   0
Cost                    $0.0811 per run     none set
Latency                 p50 1.53s, p95 2.77s   under the 6s budget

Three known failures, q34 and q35 on contradiction and q37 on scope. They
are deliberate and the articles causing them stay in the corpus. See D17.

## What Product 2 added

1. A filter in the prompt is advice. A filter in SQL is a rule. The prompt
   version was ignored 8 times in 50. Moving it into the query fixed C1
   breaches and unexpectedly lifted recall@1 from 71% to 93%, because a
   superseded article had been outranking the live one.
2. Scope is decided by the question, not by the answer. A refund question is
   still ours when the answer is no.
3. Do not delete the test to pass the test. Three failures would vanish if
   we removed the contradictory articles, and the number left behind would
   mean nothing.
4. Prompt iteration has an end. Four versions, each trading one case for
   another. The remaining failures need a different kind of fix.
5. The audience comes from the API key, never from the request. The first
   version let any caller declare itself an agent and read internal
   articles, which bypassed every visibility rule with one word of JSON.
6. Redaction protects only what you collect next. The logs were clean and
   the tracer was storing every question in full.
7. A better model is not automatically a safer one. Sonnet and Haiku scored
   identically on abstention recall but failed on different cases, and
   Sonnet answered a bereaved customer with app instructions. Shipped on
   failure mode, not on score.
8. Build the real shape even when the data is small. Hybrid retrieval was
   built properly and then rejected on measurement, not on taste.
9. An upsert can add and update and it can never remove. An incremental
   sync can neither see a deletion nor heal one, proved by breaking the
   source on purpose.

## Known limitations of Product 2

Accepted deliberately, not forgotten.

Abstention recall is 86.4% against a 95% target. q34 and q35 contradict,
q37 is a scope boundary. The articles causing them stay, see D17.
Groundedness is unmeasured on prompt v4. Last measured at 75% on v2.
Fixed: """The CI gate reads the newest run file, which is currently the Sonnet
comparison rather than the shipping Haiku configuration.
corpus_sha and the C2 verbatim check read articles.jsonl, which is no
longer what retrieval serves. 3 of 53 quotes differ, all one sentence in
NIM-106. See D28."""
A full sync against an empty source deletes the whole index and reports
success. Harmless with a local file, real against a live API.
The high water mark is recomputed each run and can move backwards.
Incremental fetches the whole corpus to compute that watermark, so it is
not actually incremental in cost.
50 questions, 28 with a gold article. The intervals are still wide.

## Open questions

Whether hybrid retrieval pays once the corpus is thousands of articles
rather than 43 chunks. The theory held, the data was too clean to show it.
Groundedness on prompt v4, never measured.