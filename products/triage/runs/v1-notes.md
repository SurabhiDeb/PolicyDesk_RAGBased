# Error analysis, prompt v1, 20 seed messages

Run: 20260915-121332Z-v1
Model: anthropic/claude-sonnet-5
Analyst: Surabhi, with review

## Scoreboard

| Axis | Result | Target | Notes |
|---|---|---|---|
| Team | 19/20 (95%) | 85% | 95% CI is 76% to 99%. Cannot confirm the target is met. |
| Urgency | 15/20 (75%) | none set | Weakest axis. One dominant cause. |
| Escalate | 20/20 | 99% recall | All 7 cases are obvious. Metric is untested. |
| Contract parses | 20/20 | 100% | JSON format is reliable. No v2 spend needed here. |
| Latency | 3.35s to 9.39s | p50 1s, p95 3s | Failed on every case. |

## Failure modes

### F1. Urgency assigned with no rules
Cases 3, 5, 13, 16, 18. Five of twenty.
The prompt lists response times for P1 to P4 but never says which
situations map to which tier. The model has nothing to reason from and
guesses. My labels are not obviously more correct than its answers,
because neither of us wrote the rule down.

### F2. Escalation pulls urgency to P1
Cases 5 and 16.
Six of seven escalated cases became P1. Case 4 is the only escalation
that did not. The spec treats escalation and urgency as independent
decisions. Nothing in the prompt says so, so the model fused them.
Cases 5 and 16 are two symptoms of this one cause, not two findings.

### F3. Second intent silently dropped
Case 6.
Customer asked for a card block and an account closure. Routed to
fraud_scams correctly. The closure vanished with no error. SPEC section 8
requires secondary_intent; the prompt never asks for it. Silent loss of a
customer request is worse than a misroute because nobody notices it.

### F4. Output contract incomplete
All 20 cases.
SPEC section 3 specifies six fields. The prompt asks for four.
secondary_intent and confidence are missing. classify.py reported no
problems because it validates only the fields the prompt requests, so the
validator agrees with the prompt and both disagree with the spec.
Case 10 ("cant log in") shows the cost: routed confidently with no way to
tell a sure answer from a guess.

### F5. Team boundary undefined
Case 2.
Prompt line reads "payments_ops - payments stuck, pending, or failed". A
declined card is a failed payment, so the prompt invited the routing. The
spec's real distinction is whether money is stuck in the rails, which the
prompt does not carry.
DECISION NEEDED: does payments_ops own declined cards, or frontline?
Whichever is chosen, SPEC and seed.csv row 2 must both be updated.

### F6. Latency over budget
All 20 cases. 3.35s to 9.39s against p50 1s and p95 3s.
Not yet investigated. Could be the gateway, the model, or the budget being
unrealistic. Needs measurement before any fix.

### F0. Dataset too small and too easy (not a bot failure)
20 cases. Five teams have a single example. No hard escalation cases. Team
accuracy of 95% carries a confidence interval of 76% to 99%, which spans
the 85% target. Nothing here can be concluded with confidence.

## Latent successes worth keeping

- Case 9 shouts in capitals and was correctly NOT treated as a formal
  complaint. Anger was not mistaken for severity.
- Case 8 routed to data_protection correctly with no deterministic rule
  helping it. Encouraging, but one example of a class that is 0.1% of real
  traffic proves nothing. Keep the rule planned.
- Case 14, the hardest and highest-stakes message, was handled correctly.

## Open experiment

Case 13 was given P3 where I labelled P2. I initially assumed the Hindi
caused it. There is no evidence for that; the reason field never mentions
language. Ablation to run: submit the same message in English, change
nothing else. Same answer means F1 explains it. Different answer means
language affects routing, which would be a serious new finding.
RESOLVED. Both Hindi and English return P3. Language is not the cause.
F1 explains case 13. My original theory was wrong.

## What v2 must fix, in priority order

1. F1 and F2. Urgency rules, and an explicit statement that escalation and
   urgency are independent decisions.
2. F4 and F3. Complete the output contract, and update classify.py to
   validate all six fields.
3. F5. Decide the payments_ops boundary and write it into both the spec
   and the prompt.
4. F6. Measure properly before attempting a fix.
5. F0. Grow the dataset to 60-100 cases, weighted toward hard escalation
   cases rather than easy ones.

Nothing in v2 needs to address output format. v1 is already reliable there,
and spending prompt on a solved problem is how prompts get bloated.