"""Turn help centre HTML into citable chunks.

The markdown version split on lines starting with '## '. Real help centre
HTML has no such convenience, so this walks the parsed tree instead.
"""

import re

from bs4 import BeautifulSoup

HEADINGS = ("h1", "h2", "h3")
BLOCKS = ("p", "ul", "ol")


def clean(text: str) -> str:
    """Collapse whitespace and close up space before punctuation.

    BeautifulSoup needs a separator when extracting text or inline tags run
    words together, but that separator then leaves "business days ." wherever
    a sentence ended inside a <strong>. A stray space there breaks the
    verbatim quote check, which is a C2 failure caused by a parser.
    """
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+([.,;:!?])", r"\1", text)
    return text.strip()


def split_html_sections(html: str) -> list[dict]:
    """One chunk per heading. Text before the first heading is dropped.

    List items become one line each, because a list of things that cannot be
    refunded reads as three separate facts rather than one sentence.
    """
    soup = BeautifulSoup(html, "html.parser")
    chunks, heading, buf = [], None, []

    def flush():
        text = "\n".join(line for line in buf if line).strip()
        if text and heading:
            chunks.append({"section": heading, "text": text})

    for element in soup.find_all(HEADINGS + BLOCKS):
        if element.name in HEADINGS:
            flush()
            heading, buf = clean(element.get_text(" ")), []
        elif element.name in ("ul", "ol"):
            buf.extend(clean(li.get_text(" ")) for li in element.find_all("li"))
        else:
            buf.append(clean(element.get_text(" ")))

    flush()
    return chunks
