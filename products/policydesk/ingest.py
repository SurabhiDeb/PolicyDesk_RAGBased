"""Read the help articles, cut them into chunks, embed them, store them.

CRUDE ON PURPOSE. Indexes everything, including archived, draft, superseded
and internal articles, with no filtering. Beat 3 finds out what that costs.
"""

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from shared.db import DSN, connect  # noqa: E402
from shared.embed import EMBED_MODEL, embed  # noqa: E402

HERE = Path(__file__).parent
ARTICLES = HERE / "data" / "articles.jsonl"
SCHEMA = HERE / "schema.sql"

INSERT = """
INSERT INTO chunks
    (article_id, title, section, text, visibility, status, last_updated,
     supersedes, embedding)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
"""


def split_sections(article: dict) -> list[dict]:
    """One chunk per '## ' heading. Help articles are already structured."""
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


def main():
    articles = [
        json.loads(line) for line in ARTICLES.read_text().splitlines() if line.strip()
    ]
    print(f"{len(articles)} articles")

    rows = []
    for article in articles:
        for chunk in split_sections(article):
            rows.append(
                {
                    **article,
                    **chunk,
                    # Title and heading go into the embedded text. A chunk
                    # that just says "Delays" means nothing without them.
                    "embed_text": (
                        f"{article['title']}. {chunk['section']}.\n{chunk['text']}"
                    ),
                }
            )

    print(f"{len(rows)} chunks")
    vectors = embed([r["embed_text"] for r in rows])

    with connect() as conn:
        conn.execute(SCHEMA.read_text())
        with conn.cursor() as cur:
            cur.executemany(
                INSERT,
                [
                    (
                        r["article_id"],
                        r["title"],
                        r["section"],
                        r["text"],
                        r["visibility"],
                        r["status"],
                        r["last_updated"],
                        r["supersedes"],
                        np.array(v),
                    )
                    for r, v in zip(rows, vectors)
                ],
            )
        conn.commit()

        counts = conn.execute(
            "SELECT status, visibility, count(*) FROM chunks"
            " GROUP BY 1, 2 ORDER BY 1, 2"
        ).fetchall()

    print(f"\nstored {len(rows)} chunks of {len(vectors[0])} numbers")
    print(f"model {EMBED_MODEL}")
    print(f"database {DSN}\n")
    for status, visibility, n in counts:
        print(f"  {status:<10} {visibility:<9} {n}")


if __name__ == "__main__":
    main()