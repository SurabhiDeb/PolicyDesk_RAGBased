"""Fail the build if the latest recorded run misses the bar in SPEC.md.

Makes no model calls. It re-checks committed evidence, which is why it can run
in CI for free.
"""

import json
import sys
from pathlib import Path

RUNS_DIR = Path(__file__).parent / "runs"
MIN_TEAM_ACCURACY = 0.85


def main():
    files = sorted(RUNS_DIR.glob("*-v*.json"))
    if not files:
        sys.exit("No run files found.")

    record = json.loads(files[-1].read_text())
    results = record["results"]
    n = len(results)

    broken = [r["id"] for r in results if r["problem"]]
    team_ok = sum(1 for r in results if r["team"] == r["labelled_team"])
    missed = sum(
        1
        for r in results
        if r["labelled_escalate"] == "true" and not r["escalate"]
    )

    failures = []
    if missed:
        failures.append(f"{missed} missed escalation(s), must be zero")
    if broken:
        failures.append(f"contract invalid on cases {broken}, must be none")
    if team_ok / n < MIN_TEAM_ACCURACY:
        failures.append(f"team accuracy {team_ok / n:.0%} below {MIN_TEAM_ACCURACY:.0%}")

    print(f"Gate on {record['meta']['run_id']}  ({n} cases)")
    if failures:
        for f in failures:
            print(f"  FAIL  {f}")
        sys.exit(1)

    print("  PASS  all gates met")


if __name__ == "__main__":
    main()