"""Write the Beat 3 verdicts back to Langfuse, one score per trace.

Deliberately uses new score names. Your hand annotations under `correct` and
`failure_mode` stay untouched, so you can compare what you judged against
what the review concluded. Langfuse also records these as source API rather
than ANNOTATION, so machine-written scores can never be mistaken for human
ones.
"""

import json
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
load_dotenv()

from langfuse import get_client  # noqa: E402

RUNS = Path(__file__).parent / "runs"

# Primary failure mode per case, most severe first where a case has several.
# Everything not listed here is clean.
FAILURES = {
    "q18": "wrongly_abstained",
    "q28": "internal_leak",
    "q31": "stale_source",
    "q32": "stale_source",
    "q33": "wrongly_abstained",
    "q34": "should_have_abstained",
    "q35": "invented_distinction",
    "q36": "poisoned_abstention",
    "q37": "should_have_abstained",
    "q38": "should_have_abstained",
    "q39": "internal_leak",
    "q40": "internal_leak",
    "q42": "should_have_abstained",
    "q43": "stale_source",
    "q49": "stale_source",
    "q50": "should_have_abstained",
}

# Cases carrying more than one mode. Recorded so the counts stay honest.
SECONDARY = {
    "q28": ["should_have_abstained"],
    "q31": ["contradiction_blended"],
    "q32": ["contradiction_blended"],
    "q35": ["should_have_abstained"],
    "q42": ["stale_source"],
    "q43": ["contradiction_blended", "should_have_abstained"],
    "q49": ["contradiction_blended"],
}

BY_HAND = {"q19", "q28", "q31", "q34", "q38", "q39", "q40", "q41", "q42", "q43"}
CORRECTED = {"q34", "q41"}


def main():
    record = json.loads(sorted(RUNS.glob("*-v*.json"))[-1].read_text())
    lf = get_client()

    for r in record["results"]:
        trace_id = r["trace_url"].rsplit("/", 1)[-1]
        mode = FAILURES.get(r["id"], "none")

        judge = "surabhi" if r["id"] in BY_HAND else "claude"
        note = f"judged by {judge}"
        if r["id"] in CORRECTED:
            note += ", corrected on review"

        lf.create_score(
            name="v1_verdict",
            value=mode == "none",
            trace_id=trace_id,
            data_type="BOOLEAN",
            comment=note,
        )
        lf.create_score(
            name="v1_failure_mode",
            value=mode,
            trace_id=trace_id,
            data_type="CATEGORICAL",
            comment=", ".join(SECONDARY.get(r["id"], [])) or note,
        )

    lf.flush()
    clean = sum(1 for r in record["results"] if r["id"] not in FAILURES)
    print(f"scored {len(record['results'])} traces, {clean} clean")


if __name__ == "__main__":
    main()