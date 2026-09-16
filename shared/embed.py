"""Turns text into vectors. Cached to disk, same deal as llm.py.

A vector is a list of numbers representing meaning. Two texts about the same
thing land close together, which is how retrieval finds the right article.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

EMBED_MODEL = "baai/bge-base-en-v1.5"
CACHE_DIR = Path(__file__).resolve().parent.parent / "cache" / "embeddings"

_client = OpenAI(
    base_url=os.environ["AICREDITS_BASE_URL"],
    api_key=os.environ["AICREDITS_API_KEY"],
)


def _key(text: str) -> str:
    return hashlib.sha256(f"{EMBED_MODEL}\x00{text}".encode()).hexdigest()


def embed(texts: list[str]) -> list[list[float]]:
    """Vectors for these texts, in order. Only uncached ones cost money."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    out: list[list[float] | None] = [None] * len(texts)
    todo: list[int] = []

    for i, text in enumerate(texts):
        path = CACHE_DIR / f"{_key(text)}.json"
        if path.exists():
            out[i] = json.loads(path.read_text())
        else:
            todo.append(i)

    if todo:
        print(f"  embedding {len(todo)} new, {len(texts) - len(todo)} cached")
        response = _client.embeddings.create(
            model=EMBED_MODEL,
            input=[texts[i] for i in todo],
        )
        for slot, item in zip(todo, response.data):
            out[slot] = item.embedding
            (CACHE_DIR / f"{_key(texts[slot])}.json").write_text(json.dumps(item.embedding))

    return out  # type: ignore[return-value]