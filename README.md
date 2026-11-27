Chatbot Lab

Two customer-support chatbots, each built end to end with its own spec, evaluation set and CI gate.

#	Product	What it does	Status
1	Triage	Routes an inbound support message to a team, assigns urgency, decides whether to escalate	Shipped, 2 targets unmet
2	PolicyDesk	Answers refund policy questions from help-centre articles, with citations and human handoff	Shipped, 1 target unmet

Requires Python 3 and a .env holding AICREDITS_API_KEY, AICREDITS_BASE_URL and OPENAI_API_KEY (the same key, under the name promptfoo expects). Never committed.

Quickstart
bash
source .venv/bin/activate              # every new terminal

Triage

bash
python3 products/triage/check_data.py  # validate the dataset
python3 products/triage/classify.py 20 # run the classifier
python3 products/triage/score.py       # metrics report
python3 products/triage/gate.py        # pass/fail, same as CI
promptfoo eval && promptfoo view       # prompt x model matrix

PolicyDesk

bash
# TODO: fill in the equivalent commands
Layout
shared/
  llm.py              the only file that knows the provider, caches to disk
  stats.py            Wilson confidence intervals

products/<name>/
  SPEC.md             the product definition
  data/               labelled cases
  prompts/            versioned, never edited in place
  runs/               every run, with full provenance
  runs/*-notes.md     error analysis and failure taxonomy
  gate.py             CI pass/fail

promptfoo/            matrix comparison config
docs/LESSONS.md       what each product taught, and the bugs that shipped
CONTEXT/              working notes
.github/workflows/    CI, runs the gate on every push
1. Triage

Classifies an inbound support message into a team, an urgency level and an escalation decision, returning a fixed JSON contract. An unparseable response escalates rather than failing silently.

Prompt v2, Sonnet 5, 20 seed cases.

Metric	Result	Target
Team accuracy	95% (19/20), CI 76 to 99%	85%
Urgency	85% (17/20), up from 75% on v1	none set
Escalation recall	7/7, zero missed	99%
Contract valid	100%	100%
Latency	p50 4.18s, p95 6.67s	fails 1s / 3s
Cost	$0.052 per run, 0.26p per message	under 1p

Six failure modes, found by reading all 20 outputs by hand, are in products/triage/runs/v1-notes.md.

Known limitations

20 cases. The intervals are too wide to confirm any target. 95% on 19 of 20 spans 76 to 99%, which straddles the 85% bar. Needs 60 to 100 cases weighted toward hard escalation. Evidencing the 99% escalation recall target would take roughly 400 escalation cases, so that target is not reachable by this suite at any pass rate.
Case 14, severe distress, gets P2 and should be P1. It still escalates.
Case 2, declined card, team boundary never decided in the spec.
Latency fails the budget on every call. Not investigated.
Output contract is missing secondary_intent and confidence. Case 6's second intent is silently dropped.
No held-out set. Every case informed development.
2. PolicyDesk

Answers refund policy questions from help-centre articles, cites the sentence it relied on, and hands off to a human when the corpus does not cover the question. Serves an internal agent and a customer from one retrieval core, with admissibility rules (visibility, status, supersession) applied as predicates in SQL rather than as prompt instructions. The audience is derived from the API key, never from the request body.

Prompt v4, retriever filtered-v1, Haiku 4.5, 50 questions, 28 with a gold article. Run runs/20260917-153710Z-v4.json.

Metric	Result	Target
recall@5	100%	none set
recall@1	96.4%	80%
MRR	0.98	none set
Abstention recall	86.4%	fails 95%
Abstention precision	95.0%	70%
Banned articles cited	0	0
Internal leaks to customers	0	0
Unparseable	0	0
Cost	$0.0811 per run	none set
Latency	p50 1.53s, p95 2.77s	under 6s

Three known failures, q34 and q35 on contradiction and q37 on scope. They are deliberate and the articles causing them stay in the corpus. See D17.

Known limitations

Abstention recall is 86.4% against a 95% target, and at this n no two configurations are statistically separable on it.
Groundedness is unmeasured on prompt v4. Last measured at 75% on v2.
A full sync against an empty source deletes the whole index and reports success. Harmless against a local file, real against a live API.
The high water mark is recomputed each run and can move backwards. The incremental path fetches the whole corpus to compute it, so it is not incremental in cost.
50 questions, 28 with a gold article. Every answer-layer number is a development-set number.
Conventions
Pinned model ids, never an alias containing "latest".
Prompts are immutable versioned files. A change creates a new file.
Every run records prompt sha, model, dataset sha, git sha, cost.
One variable per run.
Report per failure mode, never a bare aggregate.
Fail safe. An unparseable response escalates, it never falls silent.
Never tune against the split you report on. This is the rule the repo currently breaks, recorded under each product above.
Related

The next product in the sequence, a refund agent that writes to a transactional database rather than producing text, is in its own repository. See [TODO: link].

Stack

Python, Postgres with pgvector, bge-base-en-v1.5, Langfuse, promptfoo, GitHub Actions.