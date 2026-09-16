"""The only file in this project that knows who the model provider is.

Everything else calls ask() and never learns where the answer came from.
Changing provider is an edit to this file and nowhere else.

It also caches every response to disk, keyed by the exact request. Asking the
same thing twice costs nothing and returns a byte-identical answer. That makes
eval runs free to repeat and makes scores reproducible, which is what lets a
pass rate be used as a build gate at all.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

DEFAULT_MODEL = "anthropic/claude-haiku-4.5"
CACHE_DIR = Path(__file__).resolve().parent.parent / "cache" / "llm"

for _name in ("AICREDITS_API_KEY", "AICREDITS_BASE_URL"):
    if not os.environ.get(_name):
        raise RuntimeError(f"Missing {_name}. Check your .env file.")

_client = OpenAI(
    base_url=os.environ["AICREDITS_BASE_URL"],
    api_key=os.environ["AICREDITS_API_KEY"],
)


@dataclass(frozen=True)
class Answer:
    """One response, plus everything you need to audit or debug it later."""

    text: str
    model: str
    finish_reason: str
    input_tokens: int
    output_tokens: int
    model_seconds: float
    cached: bool

    """One response, plus everything you need to audit or debug it later.

    model_seconds is how long the provider took when this answer was FIRST
    produced. It is replayed unchanged from cache, because it is the number
    your latency budget cares about. It is not how long this call took.
    """

def _cache_key(model, system, user, max_tokens, temperature):
    """A fingerprint of the exact request. Change any input, get a new key."""
    payload = json.dumps(
        {
            "model": model,
            "system": system,
            "user": user,
            "max_tokens": max_tokens,
            "temperature": temperature,
        },
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode()).hexdigest()[:32]


def ask(
    user,
    *,
    system=None,
    model=DEFAULT_MODEL,
    max_tokens=500,
    temperature=0.0,
    use_cache=True,
):
    """Ask the model one question and get an Answer back.

    Args:
        user: The message to send.
        system: Optional instructions that frame the whole task.
        model: Pinned model id. Never an alias containing "latest".
        max_tokens: Ceiling on the reply. You pay for what comes back.
        temperature: 0.0 means "be as consistent as you can".
        use_cache: Set False to force a fresh call.
    """
    key = _cache_key(model, system, user, max_tokens, temperature)
    path = CACHE_DIR / f"{key}.json"

    if use_cache and path.exists():
        saved = json.loads(path.read_text())
        return Answer(**{**saved, "cached": True})

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": user})

    started = time.time()
    response = _client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        messages=messages,
    )
    elapsed = time.time() - started

    record = {
        "text": response.choices[0].message.content,
        "model": response.model,
        "finish_reason": response.choices[0].finish_reason,
        "input_tokens": response.usage.prompt_tokens,
        "output_tokens": response.usage.completion_tokens,
        "model_seconds": round(elapsed, 2),
    }

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2))

    return Answer(**record, cached=False)