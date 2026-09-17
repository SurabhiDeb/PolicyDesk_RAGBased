"""Find the chunks most similar to a question, filtered to what this
audience is allowed to see.

v2. The filter is the change. The prompt is untouched.

Three rules, all from SPEC.md section 4.
  published only          draft and archived never surface
  public only for a customer   internal is agent-only
  nothing superseded      an article replaced by a live one is dead
"""

import sys
import textwrap
from pathlib import Path

import numpy as np
from psycopg.rows import dict_row

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from shared.db import connect  # noqa: E402
from shared.embed import embed  # noqa: E402

RETRIEVER = "filtered-v1"

SEARCH = """
SELECT article_id, title, section, text, visibility, status, supersedes,
       embedding <=> %(vector)s AS distance
FROM chunks
WHERE status = 'published'
  AND (%(audience)s = 'agent' OR visibility = 'public')
  AND article_id NOT IN (
        SELECT supersedes FROM chunks
        WHERE supersedes <> '' AND status = 'published'
  )
ORDER BY distance
LIMIT %(k)s
"""


def search(question: str, k: int = 5, audience: str = "customer") -> list[dict]:
    """The k allowed chunks closest in meaning to the question."""
    vector = embed([question])[0]
    with connect() as conn:
        conn.row_factory = dict_row
        return conn.execute(
            SEARCH,
            {"vector": np.array(vector), "audience": audience, "k": k},
        ).fetchall()


def main():
    if len(sys.argv) < 2:
        sys.exit('Usage: python3 retrieve.py "question" [customer|agent]')

    audience = "customer"
    args = sys.argv[1:]
    if args[-1] in ("customer", "agent"):
        audience = args.pop()

    question = " ".join(args)
    print(f"\nQ: {question}   [{audience}]\n")

    for rank, hit in enumerate(search(question, 5, audience), start=1):
        flag = "  INTERNAL" if hit["visibility"] == "internal" else ""
        print(f"{rank}. {hit['distance']:.3f}  {hit['article_id']}  "
              f"{hit['title']} / {hit['section']}{flag}")
        print(textwrap.indent(textwrap.fill(hit["text"], 76), "     "))
        print()


if __name__ == "__main__":
    main()