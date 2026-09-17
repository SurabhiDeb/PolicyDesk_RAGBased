"""Run a few named cases against the current prompt, without recording a run.

For iterating on a prompt fix before spending on all 50. Deliberately writes
no run file, so score.py and the eval tests keep reading the last real run.
"""

import json
import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from shared.tracing import flush  # noqa: E402

from ask import PROMPT, answer  # noqa: E402

QUESTIONS = Path(__file__).parent / "data" / "questions.jsonl"


def main():
    if len(sys.argv) < 2:
        sys.exit("Usage: python3 try_cases.py q06 q36 q44 q47")

    wanted = set(sys.argv[1:])
    cases = [
        json.loads(line) for line in QUESTIONS.read_text().splitlines()
        if line.strip() and json.loads(line)["id"] in wanted
    ]

    missing = wanted - {c["id"] for c in cases}
    if missing:
        sys.exit(f"No such case: {sorted(missing)}")

    print(f"prompt {PROMPT.name}\n")
    for c in cases:
        out = answer(c["question"], c["audience"], question_id=c["id"])
        ok = out["status"] == c["expected_status"]
        print(f"{'ok  ' if ok else 'WRONG'} {c['id']}  "
              f"expected {c['expected_status']}, got {out['status']}"
              f"{'  (cached)' if out['cached'] else ''}")
        print(f"      Q: {c['question']}")
        body = out["answer"] or out.get("handoff_reason") or ""
        print(textwrap.indent(textwrap.fill(body, 88), "      "))
        if out["citations"]:
            print(f"      cites {[x['article_id'] for x in out['citations']]}")
        if out["problem"]:
            print(f"      PROBLEM: {out['problem']}")
        print()

    flush()


if __name__ == "__main__":
    main()