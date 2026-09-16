"""Find the chunks most similar to a question.

CRUDE ON PURPOSE. No filtering whatsoever. It will happily hand back
internal, archived, draft and superseded content.
"""

import sys
import textwrap
from pathlib import Path

import numpy as np
from psycopg.rows import dict_row

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from shared.db import connect  # noqa: E402
from shared.embed import embed  # noqa: E402

SEARCH = """
SELECT article_id, title, section, text, visibility, status, supersedes,
       embedding <=> %s AS distance
FROM chunks
ORDER BY distance
LIMIT %s
"""


def search(question: str, k: int = 5) -> list[dict]:
    """The k chunks closest in meaning to the question."""
    vector = embed([question])[0]
    with connect() as conn:
        conn.row_factory = dict_row
        return conn.execute(SEARCH, (np.array(vector), k)).fetchall()


def main():
    if len(sys.argv) < 2:
        sys.exit('Usage: python3 retrieve.py "your question here"')

    question = " ".join(sys.argv[1:])
    print(f"\nQ: {question}\n")

    for rank, hit in enumerate(search(question), start=1):
        flag = ""
        if hit["visibility"] == "internal":
            flag += "  INTERNAL"
        if hit["status"] != "published":
            flag += f"  {hit['status'].upper()}"
        if hit["supersedes"]:
            flag += f"  replaces {hit['supersedes']}"

        print(f"{rank}. {hit['distance']:.3f}  {hit['article_id']}  "
              f"{hit['title']} / {hit['section']}{flag}")
        print(textwrap.indent(textwrap.fill(hit["text"], 76), "     "))
        print()


if __name__ == "__main__":
    main()