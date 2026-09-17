"""Answer one refund question from the retrieved articles. Prompt v1.

CRUDE ON PURPOSE. No visibility filtering, no status filtering, no rule about
superseded articles, no check that a quote is real. Beat 3 reads the damage.

Every call produces a Langfuse trace with retrieval and generation as
separate steps, so a bad answer can be traced to which chunks caused it.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from shared.llm import ask as ask_model  # noqa: E402
from shared.tracing import flush, observation, trace_attributes, trace_url  # noqa: E402

from retrieve import search  # noqa: E402
from text import strip_fences  # noqa: E402

HERE = Path(__file__).parent
PROMPT = HERE / "prompts" / "v1.md"
MODEL = "anthropic/claude-haiku-4.5"
MAX_TOKENS = 600

TRACED_HIT_FIELDS = ("article_id", "section", "visibility", "status", "distance")


def build_context(hits: list[dict]) -> str:
    return "\n\n".join(
        f"[{h['article_id']}] {h['title']} / {h['section']}\n{h['text']}"
        for h in hits
    )



def answer(
    question: str,
    audience: str = "customer",
    k: int = 5,
    question_id: str | None = None,
    run_id: str | None = None,
) -> dict:
    with trace_attributes(
        trace_name="policydesk.answer",
        session_id=run_id,
        tags=[f"audience:{audience}", f"prompt:{PROMPT.stem}"],
        metadata={"k": k, "question_id": question_id},
    ):
        with observation(
            "answer", "chain", input={"question": question, "audience": audience}
        ) as root:

            with observation("retrieve", "retriever", input=question) as span:
                hits = search(question, k)
                span.update(
                    output=[
                        {f: h[f] for f in TRACED_HIT_FIELDS} for h in hits
                    ]
                )

            user = f"Help articles:\n\n{build_context(hits)}\n\nQuestion: {question}"

            with observation(
                "generate",
                "generation",
                input=user,
                model=MODEL,
                model_parameters={"max_tokens": MAX_TOKENS, "temperature": 0},
            ) as gen:
                reply = ask_model(
                    user,
                    system=PROMPT.read_text(),
                    model=MODEL,
                    max_tokens=MAX_TOKENS,
                )
                # Tokens are only reported for calls that really happened.
                # Counting a cache hit would make Langfuse overstate spend.
                usage = (
                    {}
                    if reply.cached
                    else {
                        "usage_details": {
                            "input": reply.input_tokens,
                            "output": reply.output_tokens,
                        }
                    }
                )
                gen.update(
                    output=reply.text,
                    metadata={
                        "cached": reply.cached,
                        "finish_reason": reply.finish_reason,
                        "served_model": reply.model,
                    },
                    **usage,
                )

            problem = None
            try:
                parsed = json.loads(strip_fences(reply.text))
            except json.JSONDecodeError as e:
                parsed, problem = {}, f"unparseable: {e}"

            if reply.finish_reason != "stop":
                problem = f"finish_reason was {reply.finish_reason}"

            if problem:
                # Section 6 rule 6. Anything unreadable hands off to a human.
                parsed = {
                    "status": "no_answer",
                    "answer": None,
                    "citations": [],
                    "confidence": "low",
                    "handoff_reason": "The system could not produce a usable answer.",
                }

            result = {
                **parsed,
                "audience": audience,
                "question": question,
                "retrieved": [h["article_id"] for h in hits],
                "problem": problem,
                "model": reply.model,
                "input_tokens": reply.input_tokens,
                "output_tokens": reply.output_tokens,
                "model_seconds": reply.model_seconds,
                "cached": reply.cached,
            }

            root.update(output=result)
            result["trace_url"] = trace_url()
            return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("question")
    parser.add_argument("--audience", default="customer",
                        choices=["customer", "agent"])
    parser.add_argument("-k", type=int, default=5)
    args = parser.parse_args()

    result = answer(args.question, args.audience, args.k)
    print(json.dumps(result, indent=2))
    flush()


if __name__ == "__main__":
    main()