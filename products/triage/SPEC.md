# Triage - Product Specification

Version 1. 14 September 2026.

This document defines what correct means. Every test, metric, and CI gate
downstream derives from it. If this document is wrong, everything built on
it measures the wrong thing.

---

## 1. The job

Read one inbound customer support message and decide which team handles it,
how urgent it is, and whether a human must see it immediately.

## 2. Scope

### It does
- Route a message to exactly one team
- Assign one urgency tier
- Raise an escalation flag independently of the above
- Say "I do not know" when the message carries no signal

### It does not
- Reply to the customer
- Resolve anything
- Give advice of any kind
- Look up account data

The narrowness is deliberate. A router that also answers is two products,
and neither can be tested properly.

## 3. Output contract

Every response returns exactly this shape.

    team                 one of the nine values below
    urgency              P1 | P2 | P3 | P4
    escalate             true | false
    secondary_intent     a team name, or null
    confidence           low | medium | high
    reason               one sentence, for the human reading the queue

## 4. Teams

| Team | Handles | Distinct power, training, or duty |
|---|---|---|
| `frontline` | General questions, single-user app problems, fees, praise, spam, out-of-scope requests | None. The default. |
| `fraud_scams` | Money moved without permission. Customers tricked into giving details. | Can freeze a card and recall a payment in real time |
| `disputes` | Chargebacks and merchant disputes | Card scheme rules and fixed 120-day deadlines |
| `payments_ops` | Payments stuck, pending, or failed in the rails | Can see inside the payment rails and unstick money |
| `complaints` | Formal regulated complaints | A regulatory clock. Missing it is reportable. |
| `specialist_care` | Bereavement, serious illness, severe financial difficulty, vulnerability | Trained for these conversations. Others are not. |
| `data_protection` | Statutory data requests | Only group permitted to handle them. Legal deadline. |
| `business_support` | Business account customers | Different contract. Failures affect many people at once. |
| `engineering` | Reproducible bugs affecting many users | The only people who can fix it |

Plus one non-team outcome.

| `needs_clarification` | The message carries no routable signal | Triggers an automatic clarifying question |

### Merges considered and rejected

- **Specialist care into frontline.** Rejected. It is a training boundary,
  not a topic boundary, and the cost of getting it wrong is harm to a person.
- **Data protection into complaints.** Rejected. Two different statutory
  clocks in one queue means one will be missed.
- **Business support into frontline.** Rejected. One business ticket can
  represent fourteen people.

### Merges accepted

- **Trust and safety.** Not a team. Fails all three tests. Spam and abuse
  go to frontline.
- **Account servicing.** Not a team. Closures and account changes go to
  frontline.

## 5. Urgency

Acknowledgement is automatic and instant for every message. These numbers
are for the first human response.

| Tier | First human response | Coverage |
|---|---|---|
| P1 | 15 minutes | Round the clock |
| P2 | 4 hours | Business hours |
| P3 | 24 hours | Business hours |
| P4 | 72 hours | Business hours |

Two tests any tier assignment must pass.

1. P1 means someone is woken at 3am. If it does not justify that, it is not P1.
2. If fewer than 70 percent of messages land in P3 or P4, the tiers are
   inflated and P1 will be ignored.

## 6. Escalation

Escalation is not urgency. Urgency decides the queue. Escalation pages a
named human now, regardless of queue depth.

### Triggers

| Trigger | The signal |
|---|---|
| Vulnerability | Bereavement, serious illness, severe hardship, any sign the person is not coping |
| Active financial loss | Money moving now without permission, card stolen, credentials just given away |
| Regulatory language | Ombudsman, FCA, regulator, "formal complaint", solicitor, legal action |
| Many people affected | Business payroll, outage, anything where one ticket represents many humans |
| Threats or safety | Threats toward staff or others |

### Explicitly not triggers

- **Anger.** Anger is a volume control, not a signal.
- **Stuck payments.** Frustrating and safe.
- **A bug affecting one person.**

Every item added to this list makes every other item less effective. An
escalation channel that fires 200 times a day gets muted, and then the real
one is missed.

## 7. Deterministic rules

These run before the model and override it. They exist because rare
critical classes cannot be learned from four examples a day.

    RULE 1  data protection
    if the message contains any of
       "subject access request", "SAR", "GDPR", "data protection",
       "copy of all personal data", "right to erasure"
    then team = data_protection, regardless of the model's answer

    RULE 2  regulatory language
    if the message contains any of
       "ombudsman", "FCA", "financial conduct authority", "regulator",
       "formal complaint", "solicitor", "legal action"
    then escalate = true, regardless of the model's answer

Rules handle the rare things we cannot afford to miss. The model handles
the fuzzy majority.

## 8. Ambiguity policy

| Situation | Rule |
|---|---|
| Two intents in one message | Route to the more urgent team. Record the other in `secondary_intent`. |
| No routable signal | Return `needs_clarification`. Do not guess. |
| Not English | Route normally. Language is not a routing signal. |
| Out of scope, for example investment advice | `frontline`, P4, with a do-not-answer note |

Roughly 4 to 6 percent of real traffic landing in `needs_clarification` is
healthy. Zero percent means the bot is guessing.

## 9. Definition of a good answer

1. Exactly one team, from the list, never invented
2. Output matches the contract exactly, every time
3. Urgency consistent with the team and the content
4. Escalation raised whenever a trigger is present
5. `reason` is one sentence a human can act on
6. Deterministic rules always win over the model
7. Any response that cannot be parsed must default to escalate=true, team=frontline, urgency=P2, and record the problem. The system never silently decides not to escalate.

## 10. Unacceptable failures

Each of these becomes a test case tagged `critical`. One failure fails the
build. These are not low scores, they are a different category of thing.

| # | Failure |
|---|---|
| C1 | A vulnerable customer routed to a normal queue |
| C2 | Active fraud routed anywhere but `fraud_scams` |
| C3 | Regulatory language present and `escalate` is false |
| C4 | A statutory data request not routed to `data_protection` |
| C5 | Bereavement routed anywhere but `specialist_care` |
| C6 | A business-critical failure treated as one consumer ticket |
| C7 | Output that does not match the contract |

## 11. Success metrics

| Metric | Target | Why this number |
|---|---|---|
| Overall team accuracy | 85% | Misroutes cost hours, not harm |
| Escalation recall | 99% | Missing a real one is the worst outcome available |
| Escalation precision | 70% | Deliberately low. See below. |
| Critical cases (C1 to C7) | 100% | No tolerance |
| Contract validity | 100% | A malformed response cannot be routed at all |
| `needs_clarification` rate | 3% to 8% | Too low means guessing, too high means useless |

### On the recall and precision asymmetry

This is the most important line in the document.

Recall is set brutally high and precision deliberately low. We are stating
out loud that we would rather wake someone unnecessarily thirty times than
miss one real case. That is a product decision, not a technical one, and it
is the reason a single accuracy number would be the wrong headline metric.

## 12. Budget

Volume is roughly 4,000 messages per day.

| | Target |
|---|---|
| p50 latency | under 1 second |
| p95 latency | under 3 seconds |
| Cost per message | under 1 penny |
| Cost per month | under £1,200 |

## 13. Known hard cases

Recorded before building, so they can be checked against later.

1. "it's not working" and similar. No signal exists. Must abstain.
2. Fraud against ordinary payment trouble. The distinguishing signal is
   whether the customer recognises the transaction.
3. A formal complaint against ordinary anger. Anger alone is not a complaint.
4. A bug affecting everyone against a problem affecting one person.
5. Fraud against a dispute. Did the customer authorise it originally.

---

## Appendix. Where this came from

Derived from 20 seed messages, labelled in `data/seed.csv`. Those are
synthetic, which is the weakest source of test data and the correct
starting point when no production traffic exists yet. They are replaced by
real messages as soon as any exist.