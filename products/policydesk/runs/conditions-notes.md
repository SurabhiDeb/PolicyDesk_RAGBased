# PolicyDesk C0-C5 - condition mapping and abstention matrix

Recorded 2026-11-28. Derived from run-file metadata, not from filenames.

The run files are named `v1` to `v6` by prompt iteration. The dossier study
refers to the same runs as conditions `C0` to `C5`. Nothing in the repo
carried that mapping, so it is written down here.

Two naming collisions to know about before reading anything labelled C:

- `C1` to `C5` in `SPEC.md:124-128` are **critical failure classes**, not
  conditions. `C3` there means "answer drawn from an archived or superseded
  article". Result rows carry it as a field value, `"critical": "C3"`.
- `v3` has two run files. They are outcome-identical, see below.

---

## The mapping

Assigned on the triple `(retriever, prompt_sha, chat_model_requested)` from
each file's `meta` block.

| Cond | File | Retriever | Prompt | prompt_sha | Model |
|---|---|---|---|---|---|
| C0 | `20260917-071445Z-v1.json` | *key absent* (unfiltered) | v1.md | `8641fbece1ed` | haiku-4.5 |
| C1 | `20260917-142630Z-v2.json` | `filtered-v1` | v1.md | `8641fbece1ed` | haiku-4.5 |
| C2 | `20260917-151853Z-v3.json` | `filtered-v1` | v3.md | `fab0ee6f7afc` | haiku-4.5 |
| C3 | `20260917-153710Z-v4.json` | `filtered-v1` | v4.md | `ddae903658f5` | haiku-4.5 |
| C4 | `20260918-073550Z-v5.json` | `hybrid-v1` | v4.md | `ddae903658f5` | haiku-4.5 |
| C5 | `20260918-080101Z-v6.json` | `filtered-v1` | v4.md | `ddae903658f5` | sonnet-5 |

Constraints that had to hold, and do:

- C0 and C1 share a prompt hash. Both `8641fbece1ed`. The retriever is the
  only variable between them.
- C3, C4 and C5 share a prompt hash. All `ddae903658f5`. C4 varies the
  retriever, C5 varies the model.
- Anchor: prompt v4 + filtered retriever + Haiku 4.5 is C3. Lands on
  `20260917-153710Z-v4.json`.

`corpus_sha` is `557c9914551a` and `k` is 5 in all six. `embed_model` is
`baai/bge-base-en-v1.5` in all six.

### Why the off-by-one mattered

If the mapping had been shifted by one, so that C0 were a baseline absent
from this directory and C1 through C5 were v1 through v5, then C3 and C5
would be v3 and v5. Those are the two runs that never shipped: `v4-notes.md`
records that "v3 was never a candidate to ship", and `v5-notes.md` is titled
"why it does not ship". The anchor is what rules that reading out.

---

## Three metadata facts that each could have changed a cell

**C0 has no `retriever` key.** The field was added in v2. The condition is
defined as unfiltered, so this was confirmed by behaviour rather than by the
absent key. C0 retrieves a strict superset of C1, 16 distinct articles
against 13, and nothing C1 retrieves is missing from C0. The three extras
are exactly the classes `retrieve.py:29-34` excludes:

| Article | Why filtered |
|---|---|
| NIM-099 | `label_names` includes `archived` |
| NIM-210 | body says "not final and must not be relied on" |
| NIM-103 | another article carries `supersedes:NIM-103` |

**C2 had two candidate files.** `20260917-150227Z-v3.json` and
`20260917-151853Z-v3.json` share `prompt_sha` `fab0ee6f7afc`, and have
identical question text and identical `status` on all 50 rows. The later
file is used. The C2 column is the same either way.

**`questions_sha` changes mid-study**, `2acf1aa6e537` for C0-C2 and
`fa171f2762f7` for C3-C5. This is not a question-set change. All 50 question
strings and all 50 `expected_status` values are identical across the two
shas; the hash moved on annotation fields only. C0-C5 are comparable
question by question.

---

## Encoding

`abstained = 1` iff `status == "no_answer"`, else 0.

Every `no_answer` row carries a populated `handoff_reason`, so refusal and
handoff are not separable by status. Two rows invert that: q37 under C3 and
q44 under C4 have `status: "answered"` with a populated `handoff_reason`.
Both are encoded 0 here, on status alone. Counting handoff as abstention
independently of status would flip q37's C3 cell to 1; q44 is
`expected answered` so it does not appear in Table 1.

No missing results. All six conditions contain all 50 qids, q01 to q50, no
gaps and no duplicates.

---

## Table 1 - abstention decisions, 22 expected-abstain questions

Rows are the questions whose `expected_status` is `no_answer`. 22 rows.

```
qid	C0	C1	C2	C3	C4	C5
q19	1	1	1	1	1	1
q20	1	1	1	1	1	1
q21	1	1	1	1	1	1
q22	1	1	1	1	1	1
q23	1	1	1	1	1	1
q24	1	1	1	1	1	1
q25	1	1	1	1	1	1
q26	1	1	1	1	1	1
q27	1	1	1	1	1	1
q28	0	1	1	1	1	1
q29	1	1	1	1	1	1
q30	1	1	1	1	1	1
q34	0	0	1	0	0	1
q35	0	0	1	0	1	1
q37	0	0	1	0	0	0
q38	0	0	1	1	1	1
q39	0	1	1	1	1	1
q40	0	1	1	1	1	1
q41	1	1	1	1	1	0
q42	0	1	1	1	1	1
q43	0	0	1	1	1	0
q50	0	0	1	1	1	1
```

## Table 2 - C3 against C5, all 50 questions

50 rows.

```
qid	expected_status	c3_abstained	c5_abstained
q01	answered	0	0
q02	answered	0	0
q03	answered	0	0
q04	answered	0	0
q05	answered	0	0
q06	answered	0	0
q07	answered	0	0
q08	answered	0	0
q09	answered	0	0
q10	answered	0	0
q11	answered	0	0
q12	answered	0	0
q13	answered	0	0
q14	answered	0	0
q15	answered	0	0
q16	answered	0	0
q17	answered	0	0
q18	answered	0	0
q19	no_answer	1	1
q20	no_answer	1	1
q21	no_answer	1	1
q22	no_answer	1	1
q23	no_answer	1	1
q24	no_answer	1	1
q25	no_answer	1	1
q26	no_answer	1	1
q27	no_answer	1	1
q28	no_answer	1	1
q29	no_answer	1	1
q30	no_answer	1	1
q31	answered	0	0
q32	answered	0	0
q33	answered	1	0
q34	no_answer	0	1
q35	no_answer	0	1
q36	answered	0	0
q37	no_answer	0	0
q38	no_answer	1	1
q39	no_answer	1	1
q40	no_answer	1	1
q41	no_answer	1	0
q42	no_answer	1	1
q43	no_answer	1	0
q44	answered	0	0
q45	answered	0	0
q46	answered	0	0
q47	answered	0	0
q48	answered	0	0
q49	answered	0	0
q50	no_answer	1	1
```

No statistics are computed here deliberately. These are the raw decisions;
`score.py` owns the metrics.
