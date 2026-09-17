"""Mechanical checks on the latest run. No judgement, no model calls.

Two different failures, kept apart. Retrieval handing over a banned article
is a retrieval bug. The answer citing one is C1.
"""

import json
from pathlib import Path

RUNS = Path(__file__).parent / "runs"

BANNED = {"NIM-099": "archived", "NIM-103": "superseded", "NIM-210": "draft"}
INTERNAL = {"NIM-201", "NIM-202", "NIM-203"}


def main():
    files = sorted(RUNS.glob("*-v*.json"))
    if not files:
        print("No run files found in", RUNS)
        return

    record = json.loads(files[-1].read_text())
    print(f"{record['meta']['run_id']}\n")

    cited_bad, retrieved_bad = 0, 0
    for r in record["results"]:
        cited = [c.get("article_id") for c in r.get("citations") or []]
        banned_here = dict(BANNED)
        if r["audience"] == "customer":
            banned_here.update({a: "internal" for a in INTERNAL})

        in_cited = sorted({a for a in cited if a in banned_here})
        in_retrieved = sorted({a for a in r["retrieved"] if a in banned_here})

        if in_retrieved:
            retrieved_bad += 1
        if in_cited:
            cited_bad += 1
            print(f"CITED     {r['id']}  {r['audience']:<8} "
                  + ", ".join(f"{a} ({banned_here[a]})" for a in in_cited))
        elif in_retrieved:
            print(f"retrieved {r['id']}  {r['audience']:<8} "
                  + ", ".join(f"{a} ({banned_here[a]})" for a in in_retrieved))

    n = len(record["results"])
    print(f"\nbanned article retrieved: {retrieved_bad}/{n}")
    print(f"banned article cited:     {cited_bad}/{n}")


if __name__ == "__main__":
    main()