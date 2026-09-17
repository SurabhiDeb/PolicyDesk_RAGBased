"""Score groundedness with an LLM judge, against the spec's definition.

Every claim must be supported by one of the answer's OWN citations, not by
whatever happened to be retrieved. That is stricter than ragas faithfulness
and it is what SPEC.md section 6 rule 1 actually says.

The judge is a second opinion you have not checked. Nothing here is trusted
until validate_judge.py measures it against hand labels.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from shared.llm import ask as ask_model  # noqa: E402
from shared.tracing import flush, observation, trace_attributes  # noqa: E402

from text import strip_fences  # noqa: E402

HERE = Path(__file__).parent
RUNS = HERE / "runs"
PROMPT = HERE / "prompts" / "judge-v1.md"

# A stronger model than the one being judged. Standard practice, because a
# judge no better than the generator mostly agrees with it.
JUDGE_MODEL = "anthropic/claude-sonnet-5"


def judge_one(answer: str, citations: list[dict]) -> dict:
    """One verdict. Cached by shared/llm.py, so re-runs are free."""
    quotes = "\n".join(f"- {c.get('quote', '')}" for c in citations) or "(none)"
    user = f"ANSWER:\n{answer}\n\nQUOTES:\n{quotes}"

    with observation(
        "judge", "evaluator", input=user, model=JUDGE_MODEL
    ) as span:
        reply = ask_model(
            user,
            system=PROMPT.read_text(),
            model=JUDGE_MODEL,
            max_tokens=2000,
        )
        raw = (reply.text or "").strip()
        if not raw:
            # Empty is not the same as malformed, and both fail safe.
            verdict = {
                "grounded": False,
                "unsupported": [],
                "problem": f"empty judge response, finish_reason={reply.finish_reason}",
            }
        else:
            try:
                verdict = json.loads(strip_fences(raw))
                verdict.setdefault("unsupported", [])
            except json.JSONDecodeError as e:
                verdict = {
                    "grounded": False,
                    "unsupported": [],
                    "problem": f"unparseable judge ({reply.finish_reason}): {e}",
                }
        span.update(output=verdict)

    verdict["cached"] = reply.cached
    verdict["input_tokens"] = reply.input_tokens
    verdict["output_tokens"] = reply.output_tokens
    return verdict


def main():
    files = sorted(RUNS.glob("*-v*.json"))
    if not files:
        sys.exit(f"No run record in {RUNS}")

    record = json.loads(files[-1].read_text())
    run_id = record["meta"]["run_id"]

    with trace_attributes(trace_name="policydesk.judge", session_id=run_id,
                          tags=["judge", "groundedness"]):
        verdicts = []
        for r in record["results"]:
            if r["status"] != "answered":
                continue
            v = judge_one(r["answer"], r.get("citations") or [])
            verdicts.append({"id": r["id"], **v})
            mark = "." if v["grounded"] else "!"
            print(f"{mark} {r['id']}")

    flush()

    grounded = sum(1 for v in verdicts if v["grounded"])
    out = {
        "run_id": run_id,
        "judge_model": JUDGE_MODEL,
        "judge_prompt": PROMPT.name,
        "cases": len(verdicts),
        "grounded": grounded,
        "verdicts": verdicts,
    }
    path = RUNS / f"{run_id}-groundedness.json"
    path.write_text(json.dumps(out, indent=2))

    print(f"\ngroundedness {grounded}/{len(verdicts)} "
          f"= {grounded / len(verdicts):.0%}   target 98%")
    print(f"not grounded: {[v['id'] for v in verdicts if not v['grounded']]}")
    print(f"saved {path}")


if __name__ == "__main__":
    main()
