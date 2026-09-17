"""Print the metrics report for the latest run. Makes no model calls.

Every rate carries a Wilson confidence interval, so a target that sits
inside the interval is reported as "cannot confirm" rather than as a pass.
19 of 20 and 190 of 200 are both 95% and they are not the same claim.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from shared.stats import percentile, rate  # noqa: E402

from metrics import abstention, exposure, first_gold_rank, quotes  # noqa: E402

HERE = Path(__file__).parent
RUNS = HERE / "runs"
ARTICLES = HERE / "data" / "articles.jsonl"


def verdict(r, target: float) -> str:
    """A target inside the interval is not a pass. It is a bigger dataset."""
    if r.low >= target:
        return "ok"
    if r.high < target:
        return "FAIL"
    return "cannot confirm"


def line(label: str, r, target: float):
    print(f"  {label:<22} {r}   target {target:.0%}   {verdict(r, target)}")


def main():
    files = sorted(p for p in RUNS.glob("*-v*.json")
                   if "groundedness" not in p.name)
    if not files:
        sys.exit(f"No run files in {RUNS}")

    record = json.loads(files[-1].read_text())
    results = record["results"]
    meta = record["meta"]
    articles = {
        json.loads(l)["article_id"]: json.loads(l)["body"]
        for l in ARTICLES.read_text().splitlines() if l.strip()
    }

    print(f"\n{meta['run_id']}   {meta['chat_model_served']}   k={meta['k']}")
    print(f"prompt {meta['prompt_file']} @ {meta['prompt_sha']}   "
          f"corpus {meta['corpus_sha']}   git {meta['git']['commit']}")

    gold = [r for r in results if r["expected_articles"]]
    ranks = [first_gold_rank(r) for r in gold]
    n = len(gold)

    print(f"\nRETRIEVAL   ({n} cases with a known right article)")
    line("recall@5", rate(sum(1 for x in ranks if x and x <= 5), n), 0.95)
    line("recall@1", rate(sum(1 for x in ranks if x == 1), n), 0.80)
    found = [x for x in ranks if x]
    print(f"  {'MRR':<22} {sum(1 / x for x in found) / n:6.2f}"
          f"{'':<26} target  0.85")
    missed = [r["id"] for r, x in zip(gold, ranks) if x is None]
    print(f"  {'never retrieved':<22} {missed or 'none'}")

    e = exposure(results)
    print("\nEXPOSURE")
    print(f"  {'banned retrieved':<22} {e['retrieved_banned']:6.0%}")
    print(f"  {'banned cited':<22} {e['cited_banned']:6.0%}   {e['cited_cases']}")

    a = abstention(results)
    expected_abstain = sum(1 for r in results if r["expected_status"] == "no_answer")
    actual_abstain = sum(1 for r in results if r["status"] == "no_answer")
    correct_abstain = sum(1 for r in results if r["expected_status"] == "no_answer"
                          and r["status"] == "no_answer")

    print("\nABSTENTION")
    line("recall", rate(correct_abstain, expected_abstain), 0.95)
    line("precision", rate(correct_abstain, actual_abstain), 0.70)
    print(f"  {'should have abstained':<22} {a['should_have_abstained']}")
    print(f"  {'wrongly abstained':<22} {a['wrongly_abstained']}")

    q = quotes(results, articles)
    valid = sum(len(r.get("citations") or []) for r in results) - len(q["invalid"])
    total_cites = sum(len(r.get("citations") or []) for r in results)

    print("\nCONTRACT AND CITATIONS")
    line("quote is verbatim", rate(valid, total_cites), 1.0)
    print(f"  {'unparseable':<22} "
          f"{[r['id'] for r in results if r['problem']] or 'none'}")

    print("\nCRITICAL")
    print(f"  {'C1 internal to customer':<22} "
          f"{e['c1_internal_leaks'] or 'none'}   must be none")

    seconds = [r["model_seconds"] for r in results]
    print("\nBUDGET")
    print(f"  {'p50 latency':<22} {percentile(seconds, 50):6.2f}s   target  3s")
    print(f"  {'p95 latency':<22} {percentile(seconds, 95):6.2f}s   target  6s")
    per_q = (meta["cost_usd"] or 0) / len(results)
    print(f"  {'cost per question':<22} {per_q * 100:6.3f}c   target  3p")
    print()


if __name__ == "__main__":
    main()
