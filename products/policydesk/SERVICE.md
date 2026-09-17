# PolicyDesk as a service

Beat 7. The product logic did not change. This is the boundary around it.

    app.py       the HTTP boundary
    auth.py      who is calling, and what they may see
    Dockerfile   how it ships
    shared/redact.py  what never gets written down

---

## Endpoints

    POST /ask     answer one refund question. Requires X-API-Key.
    GET  /health  can this instance serve. 200 ok, 503 degraded.
    GET  /docs    generated from the pydantic models

---

## The security decision that matters

**The audience comes from the API key, never from the request body.**

The first version of `/ask` took `audience` as a field. That meant anyone
could send `{"audience": "agent"}` and read the internal articles. Every
visibility rule built in v2 to stop C1 was bypassable with one word of JSON.

Now a key maps to an audience. The customer widget holds a customer key, the
agent console holds an agent key, and the caller never chooses.

Proved with the same question and two keys.

    customer key -> no_answer, no internal content
    agent key    -> answered from NIM-201

C1 is now enforced in three places that each have to fail before a breach:
the SQL filter, the key-to-audience mapping, and the eval gate in CI.

---

## What the boundary does before the model is reached

Each of these rejects bad input at zero cost, because nothing reaches Haiku.

**Schema validation.** `question` is 3 to 500 characters. A malformed body
returns 422 with a readable error and no spend.

**Authentication.** No key or a wrong key returns 401. Auth runs before the
rate limiter, so an unauthenticated flood never consumes a real customer's
quota.

**Rate limiting.** 20 requests per minute, keyed by API key rather than IP,
because a limit is a property of the customer. One tenant behind a shared
office IP should not throttle another.

Verified: 20 requests returned 200 and the next 5 returned 429.

### Known limitation

The rate limiter keeps its counters in memory. Two instances means two
independent limits, and a restart forgets everything. Production uses a
shared store, usually Redis. Not done, because there is one instance.

---

## Logging and personal data

A support question is exactly where someone pastes a card number.

**The access log writes one JSON line per request** with request id, method,
path, status, duration and a truncated SHA-256 of the API key. It does not
contain the question at all. The safest personal data is the kind never
written down, and an access log has no use for the question.

**The key is logged as an eight-character hash.** You can group requests by
caller and know which key to revoke. The log never holds a working
credential.

**Every response carries `x-request-id`**, which is what ties a customer's
complaint to a log line and a trace.

### The trap, and it is the usual one

Logs felt like the risky place and the tracer did not. Langfuse was storing
every question in full, searchable, in a database.

`shared/redact.py` is now wired into the Langfuse client through its `mask`
hook, so inputs and outputs are redacted before they leave the process.
Cards, emails, sort codes, phone numbers and account numbers become labels.
"180 days" and "500 pounds" survive, which matters because those are answers.

Verified end to end. A question containing `4921 8830 1177 2245` appears in
Langfuse as `my card [CARD] was charged twice`.

**Traces created before the mask still hold the real numbers.** Redaction
protects what you collect from now on and does nothing about what you
already have.

---

## Docker

    python:3.13-slim
    dependencies in their own cached layer, before the code
    runs as an unprivileged user, never root
    HEALTHCHECK hitting /health
    --host 0.0.0.0, because localhost inside a container is the container

`.dockerignore` excludes `.env`. Secrets never enter an image. An image goes
to a registry, gets pulled by anyone with access, and its layers are
readable. Configuration arrives at runtime as environment variables.

The container reaches Postgres on the host through `host.docker.internal`,
which is why `shared/db.py` reads a DSN from the environment rather than
hard-coding one. That decision was made in Beat 2 for a different reason and
paid off here.

### Known limitation

Postgres and Langfuse run on the host, not in the compose file. A real
deployment describes the whole stack in one place.

---

## Where the health check changed

It first returned 200 whether it said `ok` or `degraded`. Orchestrators route
on the status code and never read the body, so a broken instance would keep
receiving traffic, and the Dockerfile's HEALTHCHECK could never fail.

Now it returns 503 when the database is unreachable or the index is empty.
