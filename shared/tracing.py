"""The only file that knows which tracer we use.

Same idea as llm.py and db.py. Swapping Langfuse for Phoenix or Braintrust
is an edit here and nowhere else.

Tracing is optional on purpose. Without keys the whole thing turns into
no-ops, so CI and anyone without a Langfuse instance can still run the code.
Observability that can take the product down is worse than none.
"""

import contextlib
import os

from dotenv import load_dotenv

load_dotenv()

ENABLED = bool(os.environ.get("LANGFUSE_PUBLIC_KEY"))
ENVIRONMENT = os.environ.get("LANGFUSE_ENVIRONMENT", "dev")

if ENABLED:
    from langfuse import get_client
    from langfuse import propagate_attributes as _propagate

    tracer = get_client()
else:
    tracer = None


class _NullSpan:
    """Stands in for a span when tracing is off."""

    def update(self, **kwargs):
        pass

    def score(self, **kwargs):
        pass


def trace_attributes(**kwargs):
    """Trace-level name, tags, session and metadata. Wraps one whole request."""
    if not ENABLED:
        return contextlib.nullcontext()
    return _propagate(environment=ENVIRONMENT, **kwargs)


@contextlib.contextmanager
def observation(name: str, as_type: str = "span", **kwargs):
    """One step inside a trace. as_type is 'retriever', 'generation', 'chain'."""
    if not ENABLED:
        yield _NullSpan()
        return
    with tracer.start_as_current_observation(name=name, as_type=as_type, **kwargs) as obs:
        yield obs


def trace_url():
    return tracer.get_trace_url() if ENABLED else None


def flush():
    """Short scripts must call this or the batched events never leave."""
    if ENABLED:
        tracer.flush()