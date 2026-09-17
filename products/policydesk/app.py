"""PolicyDesk as an HTTP service.

The CLI was for us. This is what a support tool or a chat widget calls.
Everything the product does already lives in ask.py, so this file is only
the boundary: validate the request, call the product, shape the response.
"""

import sys
from pathlib import Path
from typing import Literal
import hashlib
import json
import logging
import time
import uuid

from fastapi import Depends, FastAPI, Request, Response, status
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from shared.db import connect  # noqa: E402
from shared.redact import redact

from ask import MODEL, PROMPT, answer  # noqa: E402
from contract import Citation  # noqa: E402
from retrieve import RETRIEVER  # noqa: E402
from auth import caller_audience  # noqa: E402

app = FastAPI(
    title="PolicyDesk",
    summary="Answers Nimbus refund questions from the help centre.",
    version=PROMPT.stem,
)

def caller_identity(request: Request) -> str:
    """Rate limit per API key, falling back to IP for unauthenticated calls.

    Per key, not per IP, because a limit is a property of the customer. One
    tenant behind a shared office IP should not throttle another.
    """
    return request.headers.get("x-api-key") or get_remote_address(request)


limiter = Limiter(key_func=caller_identity)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

class AskRequest(BaseModel):
    """Anything that fails this never reaches the model, so it costs nothing."""

    question: str = Field(min_length=3, max_length=500)
    

class AskResponse(BaseModel):
    status: Literal["answered", "no_answer"]
    answer: str | None = None
    citations: list[Citation] = []
    confidence: Literal["low", "medium", "high"]
    handoff_reason: str | None = None
    audience: Literal["customer", "agent"]
    trace_url: str | None = None


@app.post("/ask", response_model=AskResponse)
@limiter.limit("20/minute")
def ask(request: Request, body: AskRequest, audience: str = Depends(caller_audience)) -> dict:
    """Answer one refund question.

    Deliberately `def` and not `async def`. The work inside is blocking, so
    FastAPI runs it in a threadpool. An `async def` would block the event
    loop and every other request with it.
    """
    return answer(body.question, audience)


@app.get("/health")
def health() -> dict:
    """Is this instance able to serve. Checked by the load balancer."""
    try:
        with connect() as conn:
            chunks = conn.execute("SELECT count(*) FROM chunks").fetchone()[0]
        database = "ok"
    except Exception as e:
        chunks, database = 0, f"unavailable: {type(e).__name__}"

    return {
        "status": "ok" if database == "ok" and chunks else "degraded",
        "database": database,
        "chunks": chunks,
        "prompt": PROMPT.name,
        "retriever": RETRIEVER,
        "model": MODEL,
    }
logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("policydesk")

for noisy in ("httpx", "httpcore", "openai"):
    logging.getLogger(noisy).setLevel(logging.WARNING)

@app.middleware("http")
async def access_log(request: Request, call_next):
    """One JSON line per request, with nothing personal in it.

    The API key is logged as a short hash. You can tell two requests came
    from the same caller and which key to revoke, without the log file
    holding a working credential.
    """
    request_id = str(uuid.uuid4())
    started = time.monotonic()

    response = await call_next(request)

    key = request.headers.get("x-api-key", "")
    log.info(json.dumps({
        "request_id": request_id,
        "method": request.method,
        "path": request.url.path,
        "status": response.status_code,
        "ms": round((time.monotonic() - started) * 1000),
        "key": hashlib.sha256(key.encode()).hexdigest()[:8] if key else None,
    }))

    response.headers["x-request-id"] = request_id
    return response

@app.get("/health")
def health(response: Response) -> dict:
    """Is this instance able to serve. Checked by the load balancer.

    Returns 503 when degraded, because orchestrators route on the status
    code and never read the body.
    """
    try:
        with connect() as conn:
            chunks = conn.execute("SELECT count(*) FROM chunks").fetchone()[0]
        database = "ok"
    except Exception as e:
        chunks, database = 0, f"unavailable: {type(e).__name__}"

    healthy = database == "ok" and chunks > 0
    if not healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "ok" if healthy else "degraded",
        "database": database,
        "chunks": chunks,
        "prompt": PROMPT.name,
        "retriever": RETRIEVER,
        "model": MODEL,
    }