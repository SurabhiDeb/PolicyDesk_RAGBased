"""Answer one refund question from the retrieved articles. Prompt v1.

CRUDE ON PURPOSE. No visibility filtering, no status filtering, no rule about
superseded articles, no check that a quote is real. Beat 3 reads the damage.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from shared.llm import ask as ask_model  # noqa: E402

from retrieve import search  # noqa: E402

HERE = Path(__file__).parent
PROMPT = HERE / "prompts" / "v1.md"
MODEL = "anthropic/claude-haiku-4.5"


def build_context(hits: list[dict]) -> str:
    """The retrieved chunks, formatted for the prompt."""
    return "\n\n".join(
        f"[{h['article_id']}] {h['title']} / {h['section']}\n{h['text']}"
        for h in hits
    )


def strip_fences(text: str) -> str:
    """Models like wrapping JSON in ``` even when told not to."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text
        text = text.rsplit("```", 1)[0]
    return text.strip()


def answer(question: str, audience: str = "customer", k: int = 5) -> dict:
    hits = search(question, k)
    user = f"Help articles:\n\n{build_context(hits)}\n\nQuestion: {question}"

    reply = ask_model(
        user,
        system=PROMPT.read_text(),
        model=MODEL,
        max_tokens=600,
    )

    problem = None
    try:
        parsed = json.loads(strip_fences(reply.text))
    except json.JSONDecodeError as e:
        parsed, problem = {}, f"unparseable: {e}"

    if reply.finish_reason != "stop":
        problem = f"finish_reason was {reply.finish_reason}"

    if problem:
        # Section 6 rule 6. Anything we cannot read hands off to a human.
        parsed = {
            "status": "no_answer",
            "answer": None,
            "citations": [],
            "confidence": "low",
            "handoff_reason": "The system could not produce a usable answer.",
        }

    return {
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("question")
    parser.add_argument("--audience", default="customer",
                        choices=["customer", "agent"])
    parser.add_argument("-k", type=int, default=5)
    args = parser.parse_args()

    result = answer(args.question, args.audience, args.k)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()