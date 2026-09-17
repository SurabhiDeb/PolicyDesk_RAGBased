"""Who is calling, and therefore what they may see.

The audience comes from the API key, never from the request body. A caller
that can name its own audience can name itself an agent, and every visibility
rule in retrieve.py stops meaning anything.
"""

import os
import secrets

from dotenv import load_dotenv
from fastapi import Header, HTTPException

load_dotenv()


def _load_keys() -> dict[str, str]:
    """POLICYDESK_API_KEYS=key1:customer,key2:agent"""
    keys = {}
    for pair in os.environ.get("POLICYDESK_API_KEYS", "").split(","):
        if not pair.strip():
            continue
        key, _, audience = pair.partition(":")
        if audience.strip() not in ("customer", "agent"):
            raise RuntimeError(f"Bad audience in POLICYDESK_API_KEYS: {pair!r}")
        keys[key.strip()] = audience.strip()
    return keys


KEYS = _load_keys()


def caller_audience(x_api_key: str = Header(default="")) -> str:
    """The audience this key is allowed to act as, or 401."""
    for key, audience in KEYS.items():
        # compare_digest takes the same time whether the first character
        # matches or the last, so the comparison leaks nothing about the key.
        if secrets.compare_digest(x_api_key, key):
            return audience

    raise HTTPException(status_code=401, detail="Invalid or missing API key")