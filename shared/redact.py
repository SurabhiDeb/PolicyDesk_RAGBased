"""Strip personal data before anything is written down.

Applied to logs and to traces. A support question is exactly where a
customer pastes a card number, and once it is in a log file it is in your
backups, your log vendor, and your incident screenshots.

Deliberately blunt. Over-redacting a question costs you a little debugging
context. Under-redacting puts a live card number in a log.
"""

import re

# Order matters. Card numbers must be caught before the generic digit run,
# or the generic rule would eat them in pieces and the pattern would never
# match.
PATTERNS = [
    ("[EMAIL]", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")),
    ("[CARD]", re.compile(r"\b\d(?:[ -]?\d){12,18}\b")),
    ("[SORTCODE]", re.compile(r"\b\d{2}-\d{2}-\d{2}\b")),
    ("[PHONE]", re.compile(r"\b(?:\+44|0)\s?\d{3,4}\s?\d{3}\s?\d{3,4}\b")),
    ("[ACCOUNT]", re.compile(r"\b\d{8,}\b")),
]


def redact(text: str | None) -> str | None:
    """Replace anything that looks personal with a label."""
    if not text:
        return text
    for label, pattern in PATTERNS:
        text = pattern.sub(label, text)
    return text
