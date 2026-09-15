"""Classify one support message into a team, urgency, and escalation flag.

Deliberately crude. See prompts/v1.md. The point of v1 is to produce failures
we can study, not to be good.

Every result carries the prompt version, the model that answered, and the token
counts, so a score can always be traced back to what produced it.
"""

from __future__ import annotations

import csv
import json
import sys
import hashlib
import subprocess
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from shared.llm import ask

PROMPT_VERSION = "v2"
PROMPT_PATH = Path(__file__).parent / "prompts" / f"{PROMPT_VERSION}.md"
DATA_FILE = Path(__file__).parent / "data" / "seed.csv"

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

# Approximate list prices in USD per million tokens, input then output.
# Your gateway adds a margin, so treat these as a floor, not a bill.
PRICES = {
    "claude-haiku-4-5": (1.0, 5.0),
    "claude-sonnet-5": (2.0, 10.0),
    "claude-opus-5": (5.0, 25.0),
}


def _sha(text):
    return hashlib.sha256(text.encode()).hexdigest()[:12]


def _git_sha():
    """Which commit produced this run. 'dirty' means uncommitted changes."""
    try:
        sha = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        changed = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=no"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        return f"{sha}-dirty" if changed else sha
    except Exception:
        return "unknown"


def _estimate_usd(results, billed_only):
    total = 0.0
    for r in results:
        if billed_only and r["cached"]:
            continue
        model = r["model"] or ""
        bare = model.split("/")[-1]
        match = next((k for k in PRICES if bare.startswith(k)), None)
        if match is None and model:
            print(f"  WARNING: no price known for {model!r}, cost is understated")
        if match is None:
            continue
        price_in, price_out = PRICES[match]
        total += r["input_tokens"] / 1e6 * price_in
        total += r["output_tokens"] / 1e6 * price_out
    return round(total, 6)


def classify(message):
    """Route one message. Never raises. Records what went wrong instead."""
    answer = ask(message, system=PROMPT_PATH.read_text(), max_tokens=500)

    result = {
        "team": None,
        "urgency": None,
        "escalate": None,
        "reason": None,
        "problem": None,
        "raw": answer.text,
        "model": answer.model,
        "prompt_version": PROMPT_VERSION,
        "input_tokens": answer.input_tokens,
        "output_tokens": answer.output_tokens,
        "model_seconds": answer.model_seconds,
        "cached": answer.cached,
        "finish_reason": answer.finish_reason,
    }
    if answer.finish_reason == "length":
        result["problem"] = f"truncated at max_tokens ({answer.output_tokens})"
        result["escalate"] = True
        result["team"] = "frontline"
        result["urgency"] = "P2"
        return result
    try:
        parsed = json.loads(answer.text)
        
    except json.JSONDecodeError as exc:
        result["problem"] = f"not valid JSON ({exc.msg})"
        result["escalate"] = True
        result["team"] = "frontline"
        result["urgency"] = "P2"
        return result

    result["team"] = parsed.get("team")
    result["urgency"] = parsed.get("urgency")
    result["escalate"] = parsed.get("escalate")
    result["reason"] = parsed.get("reason")

    if result["team"] not in VALID_TEAMS:
        result["problem"] = f"team not in the allowed list: {result['team']!r}"
    elif result["urgency"] not in VALID_URGENCY:
        result["problem"] = f"urgency not allowed: {result['urgency']!r}"
    elif not isinstance(result["escalate"], bool):
        result["problem"] = f"escalate is not true or false: {result['escalate']!r}"

    return result


def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 3

    with DATA_FILE.open() as f:
        rows = list(csv.DictReader(f))[:limit]

    results = []
    for row in rows:
        got = classify(row["message"])
        expected_team = row["team"].strip().lower()
        expected_escalate = row["escalate"].strip().lower()
        results.append(
            {
                **got,
                "id": row["id"],
                "message": row["message"],
                "labelled_team": expected_team,
                "labelled_urgency": row["urgency"],
                "labelled_escalate": expected_escalate,
            }
        )

        print("=" * 70)
        print(f"#{row['id']}  {row['message'][:100]}")
        print()
        print(f"  raw output : {got['raw']}")
        print()
        print(f"  team       : {got['team']}   (labelled {expected_team})")
        print(f"  urgency    : {got['urgency']}   (labelled {row['urgency']})")
        print(f"  escalate   : {got['escalate']}   (labelled {expected_escalate})")
        if got["problem"]:
            print(f"  PROBLEM    : {got['problem']}")
        print(
            f"  cost       : in={got['input_tokens']} out={got['output_tokens']} "
            f"{got['model_seconds']}s cached={got['cached']}"
        )
        print()

        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%SZ")
        prompt_text = PROMPT_PATH.read_text()

        record = {
            "meta": {
                "run_id": f"{stamp}-{PROMPT_VERSION}",
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "prompt_version": PROMPT_VERSION,
                "prompt_sha": _sha(prompt_text),
                "dataset": DATA_FILE.name,
                "dataset_sha": _sha(DATA_FILE.read_text()),
                "git_sha": _git_sha(),
                "cases": len(results),
                "models_served": sorted({r["model"] for r in results if r["model"]}),
                "cached_cases": sum(1 for r in results if r["cached"]),
                "input_tokens": sum(r["input_tokens"] for r in results),
                "output_tokens": sum(r["output_tokens"] for r in results),
                "usd_if_all_fresh": _estimate_usd(results, billed_only=False),
                "usd_billed_this_run": _estimate_usd(results, billed_only=True),                
            },
            "prompt": prompt_text,
            "results": results,
        }

        out = Path(__file__).parent / "runs" / f"{stamp}-{PROMPT_VERSION}.json"
        out.parent.mkdir(exist_ok=True)
        out.write_text(json.dumps(record, indent=2))

        print(f"Saved run {record['meta']['run_id']} to {out}")
        print(
            f"  billed this run ${record['meta']['usd_billed_this_run']:.4f}   "
            f"(would have been ${record['meta']['usd_if_all_fresh']:.4f} without the cache)"
        )


if __name__ == "__main__":
    main()