"""Prove Langfuse is reachable, and see which update methods the span
objects expose. Throwaway once we know."""

import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
load_dotenv()

from langfuse import (  # noqa: E402
    LangfuseGeneration,
    LangfuseRetriever,
    LangfuseSpan,
    get_client,
    propagate_attributes,
)

lf = get_client()
print("auth_check:", lf.auth_check())

for cls in (LangfuseSpan, LangfuseRetriever, LangfuseGeneration):
    print(f"\n{cls.__name__}:", [n for n in dir(cls) if not n.startswith("_")])

with propagate_attributes(
    trace_name="smoke-test",
    tags=["smoke"],
    metadata={"purpose": "wiring check"},
    environment="dev",
):
    with lf.start_as_current_observation(
        name="answer", as_type="chain", input={"question": "hello"}
    ):
        with lf.start_as_current_observation(
            name="retrieve", as_type="retriever", input="hello"
        ):
            lf.update_current_span(
                output=[{"article_id": "NIM-101", "distance": 0.12}]
            )

        with lf.start_as_current_observation(
            name="generate", as_type="generation",
            model="anthropic/claude-haiku-4.5", input="hello",
        ):
            lf.update_current_generation(
                output="hi there",
                usage_details={"input": 10, "output": 5},
            )

        # Both children have closed, so the current observation is the outer
        # chain again. Its output becomes the trace output.
        lf.update_current_span(output="hi there")
        print("\ntrace url:", lf.get_trace_url())

lf.flush()
print("flushed")