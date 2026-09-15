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


def load_rows():
    """Read the CSV and normalise it, so nothing downstream has to think about case."""
    with DATA_FILE.open() as f:
        rows = list(csv.DictReader(f))

    for row in rows:
        row["team"] = row["team"].strip().lower()
        row["urgency"] = row["urgency"].strip().upper()
        row["escalate"] = row["escalate"].strip().lower()

    return rows


def main():
    rows = load_rows()

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

"""Validate the Triage seed dataset against SPEC.md.

Reads products/triage/data/seed.csv and reports three things.

1. Legality. Every team, urgency, and escalate value is one the spec allows.
   This catches typos and silent corruption, for example a spreadsheet
   rewriting "true" as "TRUE" on save. It does NOT check the labels are
   correct, only that they are valid values.

2. Class balance. How many messages per team. Any team with fewer than
   three examples is flagged, because a class that thin cannot be tested
   meaningfully. You cannot tell a correct answer from a lucky guess.

3. Escalation count. How many messages are flagged for immediate human
   attention. Per SPEC.md section 11, escalation recall is the metric with
   the least tolerance for error, so this number is worth watching directly.

Run it after any change to seed.csv, and before any eval run that uses it.
"""