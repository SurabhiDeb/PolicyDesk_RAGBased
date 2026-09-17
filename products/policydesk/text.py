"""Pure text helpers. No database, no model, no credentials.

Everything here is a function of its arguments and nothing else, which is
exactly what makes it testable in milliseconds.
"""


def split_sections(article: dict) -> list[dict]:
    """One chunk per '## ' heading. Text before the first heading is dropped."""
    chunks, heading, buf = [], None, []

    def flush():
        text = "\n".join(buf).strip()
        if text and heading:
            chunks.append({"section": heading, "text": text})

    for line in article["body"].splitlines():
        if line.startswith("## "):
            flush()
            heading, buf = line[3:].strip(), []
        else:
            buf.append(line)
    flush()
    return chunks


def strip_fences(text: str) -> str:
    """Models wrap JSON in ``` even when told not to."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text
        text = text.rsplit("```", 1)[0]
    return text.strip()