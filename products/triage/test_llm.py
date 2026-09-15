"""Confirm the wrapper works and that the cache actually saves a call."""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from shared.llm import ask

QUESTION = "Reply with exactly: wrapper working"


def timed(**kwargs):
    started = time.perf_counter()
    answer = ask(QUESTION, model="anthropic/claude-haiku-4.5", max_tokens=20, **kwargs)
    return answer, time.perf_counter() - started


first, first_wall = timed()
second, second_wall = timed()

for label, answer, wall in (
    ("first call ", first, first_wall),
    ("second call", second, second_wall),
):
    print(
        f"{label}  cached={str(answer.cached):5}  "
        f"wall={wall:6.3f}s  model={answer.model_seconds:5.2f}s  "
        f"| {answer.text}"
    )

print()
print("Identical answers:", first.text == second.text)