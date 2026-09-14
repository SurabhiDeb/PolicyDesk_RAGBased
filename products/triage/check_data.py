"""Check that seed.csv agrees with what SPEC.md says is allowed."""

import csv
from pathlib import Path

VALID_TEAMS = {
    "frontline",
    "fraud_scams",
    "disputes",
    "payments_ops",
    "complaints",
    "specialist_care",
    "data_protection",
    "business_support",
    "engineering",
    "needs_clarification",
}
VALID_URGENCY = {"P1", "P2", "P3", "P4"}
VALID_ESCALATE = {"true", "false"}

DATA_FILE = Path(__file__).parent / "data" / "seed.csv"


def main():
    with DATA_FILE.open() as f:
        rows = list(csv.DictReader(f))

    problems = []
    for row in rows:
        if row["team"] not in VALID_TEAMS:
            problems.append(f"row {row['id']}: unknown team '{row['team']}'")
        if row["urgency"] not in VALID_URGENCY:
            problems.append(f"row {row['id']}: unknown urgency '{row['urgency']}'")
        if row["escalate"] not in VALID_ESCALATE:
            problems.append(f"row {row['id']}: escalate is '{row['escalate']}'")

    print(f"Checked {len(rows)} rows from {DATA_FILE.name}")
    print()

    counts = {}
    for row in rows:
        counts[row["team"]] = counts.get(row["team"], 0) + 1

    print("Messages per team:")
    for team in sorted(counts, key=lambda t: -counts[t]):
        flag = "   <-- too few to test" if counts[team] < 3 else ""
        print(f"  {counts[team]:2}  {team}{flag}")

    escalated = sum(1 for row in rows if row["escalate"] == "true")
    print()
    print(f"Escalated: {escalated} of {len(rows)}")
    print()

    if problems:
        print(f"FOUND {len(problems)} PROBLEMS")
        for p in problems:
            print(f"  {p}")
    else:
        print("No problems found.")


main()