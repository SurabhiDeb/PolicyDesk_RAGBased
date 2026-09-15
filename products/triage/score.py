"""Score a saved run against the labels in seed.csv.

Reports one headline rate per axis plus the exact cases that failed. A single
aggregate number hides whether the 5 percent is cosmetic or catastrophic, so
this never prints one on its own.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from shared.stats import percentile, rate

RUNS_DIR = Path(__file__).parent / "runs"


def newest_run():
    files = sorted(RUNS_DIR.glob("*-v*.json"))
    if not files:
        raise SystemExit("No run files in runs/. Run classify.py first.")
    return files[-1]


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else newest_run()
    record = json.loads(path.read_text())
    meta, results = record["meta"], record["results"]

    team_wrong, urgency_wrong, escalate_wrong, broken = [], [], [], []
    true_pos = false_pos = false_neg = 0

    for r in results:
        rid = r["id"]
        labelled_escalate = r["labelled_escalate"] == "true"

        if r["problem"]:
            broken.append(f"{rid} ({r['problem']})")
        if r["team"] != r["labelled_team"]:
            team_wrong.append(f"{rid} got {r['team']}, labelled {r['labelled_team']}")
        if r["urgency"] != r["labelled_urgency"]:
            urgency_wrong.append(
                f"{rid} got {r['urgency']}, labelled {r['labelled_urgency']}"
            )
        if r["escalate"] != labelled_escalate:
            escalate_wrong.append(f"{rid} got {r['escalate']}")

        if r["escalate"] and labelled_escalate:
            true_pos += 1
        elif r["escalate"] and not labelled_escalate:
            false_pos += 1
        elif not r["escalate"] and labelled_escalate:
            false_neg += 1

    n = len(results)
    latencies = [r["model_seconds"] for r in results]

    print(f"Run       {meta['run_id']}")
    print(f"Prompt    {meta['prompt_version']}  sha {meta['prompt_sha']}")
    print(f"Model     {', '.join(meta['models_served'])}")
    print(f"Git       {meta['git_sha']}")
    print(f"Dataset   {meta['dataset']}  sha {meta['dataset_sha']}  ({n} cases)")
    print()

    print("ACCURACY")
    print(f"  team             {rate(n - len(team_wrong), n)}   target 85%")
    print(f"  urgency          {rate(n - len(urgency_wrong), n)}")
    print(f"  escalate         {rate(n - len(escalate_wrong), n)}")
    print(f"  contract valid   {rate(n - len(broken), n)}   target 100%")
    print()

    print("ESCALATION, the metric with the least tolerance for error")
    if true_pos + false_neg:
        print(f"  recall           {rate(true_pos, true_pos + false_neg)}   target 99%")
    if true_pos + false_pos:
        print(f"  precision        {rate(true_pos, true_pos + false_pos)}   target 70%")
    print(f"  missed           {false_neg}   <-- must be zero")
    print()

    print("LATENCY")
    print(f"  p50              {percentile(latencies, 50):.2f}s   target 1.00s")
    print(f"  p95              {percentile(latencies, 95):.2f}s   target 3.00s")
    print(f"  worst            {max(latencies):.2f}s")
    print()

    print("FAILURES")
    for title, items in (
        ("contract", broken),
        ("team", team_wrong),
        ("urgency", urgency_wrong),
        ("escalate", escalate_wrong),
    ):
        print(f"  {title}:")
        for item in items or ["none"]:
            print(f"    {item}")
    print()

    print(f"Cost      ${meta['usd_if_all_fresh']:.4f} if run fresh")


if __name__ == "__main__":
    main()