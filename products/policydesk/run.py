"""Run every question in the golden set and save one run record.

The record is the evidence. score.py and gate.py read it and never call a
model, which is what lets the gate run in CI for free.
"""

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from shared.embed import EMBED_MODEL  # noqa: E402
from shared.tracing import flush  # noqa: E402
from retrieve import RETRIEVER  # noqa: E402
from ask import MODEL, PROMPT, answer  # noqa: E402

HERE = Path(__file__).parent
QUESTIONS = HERE / "data" / "questions.jsonl"
ARTICLES = HERE / "data" / "articles.jsonl"
RUNS = HERE / "runs"
RUN_LABEL = "v4"  # bump whenever the prompt or the retriever changes

# List prices per million tokens. If the model id is not here we say so
# rather than quietly reporting zero.
PRICES = {
    "haiku-4-5": (1.00, 5.00),
    "sonnet-5": (2.00, 10.00),
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def git_state() -> dict:
    """Commit and whether TRACKED files differ. Untracked output is not dirt."""
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], text=True
        ).strip()
        changed = subprocess.check_output(
            ["git", "status", "--porcelain", "--untracked-files=no"], text=True
        ).strip()
        return {"commit": commit, "dirty": bool(changed)}
    except Exception as e:
        return {"commit": None, "dirty": None, "error": str(e)}


def price_for(model_id: str) -> tuple[float, float] | None:
    for key, rates in PRICES.items():
        if key in model_id:
            return rates
    return None


def main():
    k = int(sys.argv[1]) if len(sys.argv) > 1 else 5

    questions = [
        json.loads(line) for line in QUESTIONS.read_text().splitlines() if line.strip()
    ]
    started = datetime.now(timezone.utc)
    run_id = started.strftime("%Y%m%d-%H%M%SZ") + f"-{RUN_LABEL}"

    results = []
    for i, q in enumerate(questions, start=1):
        out = answer(q["question"], q["audience"], k, question_id=q["id"], run_id=run_id)
        results.append({**q, **out})
        mark = "." if not out["problem"] else "!"
        print(f"{mark} {i:>2}/{len(questions)}  {q['id']}  {out['status']}")

    seconds = sorted(r["model_seconds"] for r in results)
    n = len(seconds)
    input_tokens = sum(r["input_tokens"] for r in results)
    output_tokens = sum(r["output_tokens"] for r in results)

    served = results[0]["model"]
    rates = price_for(served)
    if rates:
        cost = input_tokens / 1e6 * rates[0] + output_tokens / 1e6 * rates[1]
        cost_note = "list price estimate, your gateway may differ"
    else:
        cost, cost_note = None, f"no price on file for {served}"

    record = {
        "meta": {
            "run_id": run_id,
            "started": started.isoformat(),
            "k": k,
            "prompt_file": PROMPT.name,
            "prompt_sha": sha(PROMPT),
            "corpus_sha": sha(ARTICLES),
            "questions_sha": sha(QUESTIONS),
            "chat_model_requested": MODEL,
            "chat_model_served": served,
            "embed_model": EMBED_MODEL,
            "retriever": RETRIEVER,
            "git": git_state(),
            "cases": n,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": cost,
            "cost_note": cost_note,
            "cached_responses": sum(1 for r in results if r["cached"]),
            "p50_seconds": seconds[n // 2],
            "p95_seconds": seconds[min(int(n * 0.95), n - 1)],
            "latency_note": "replayed from cache for cached calls, see shared/llm.py",
        },
        "results": results,
    }

    RUNS.mkdir(parents=True, exist_ok=True)
    path = RUNS / f"{run_id}.json"
    path.write_text(json.dumps(record, indent=2))
    flush()

    m = record["meta"]
    print(f"\nrun {run_id}, {n} cases, k={k}")
    print(f"  served      {served}")
    print(f"  tokens      {input_tokens} in, {output_tokens} out")
    print(f"  cost        {('$%.4f' % cost) if cost else cost_note}")
    print(f"  latency     p50 {m['p50_seconds']}s, p95 {m['p95_seconds']}s")
    print(f"  cached      {m['cached_responses']}/{n}")
    print(f"  problems    {sum(1 for r in results if r['problem'])}")
    print(f"\nsaved {path}")


if __name__ == "__main__":
    main()