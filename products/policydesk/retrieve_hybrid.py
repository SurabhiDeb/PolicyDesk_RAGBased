"""Hybrid retrieval. Vector search and keyword search, fused.

v3, hybrid-v1. The filter from v2 is unchanged and still decides what this
audience may see. The change is how candidates are ranked.

Vector search understands that "shop" and "merchant" mean the same thing.
Keyword search knows the difference between "180 days" and "120 days".
Neither does the other's job, so both run and the results are fused.
"""

import re
import sys
import textwrap
from pathlib import Path

import numpy as np
from psycopg.rows import dict_row

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from shared.db import connect  # noqa: E402
from shared.embed import embed  # noqa: E402

RETRIEVER = "hybrid-v1"

# How many candidates each half contributes before fusing. Wider than the
# final k, so a result ranked poorly by one half can still be rescued by the
# other.
POOL = 20

# Reciprocal Rank Fusion constant. 60 is the value from the original paper
# and everyone uses it. Larger means rank differences matter less.
RRF_K = 60

SEARCH = """
WITH allowed AS (
    SELECT * FROM chunks
    WHERE status = 'published'
      AND (%(audience)s = 'agent' OR visibility = 'public')
      AND article_id NOT IN (
            SELECT supersedes FROM chunks
            WHERE supersedes <> '' AND status = 'published'
      )
),
query AS (
    SELECT websearch_to_tsquery('english', %(fts)s) AS q
),
vector_hits AS (
    SELECT id, ROW_NUMBER() OVER (ORDER BY embedding <=> %(vector)s) AS rank
    FROM allowed
    ORDER BY embedding <=> %(vector)s
    LIMIT %(pool)s
),
keyword_hits AS (
    SELECT a.id,
           ROW_NUMBER() OVER (ORDER BY ts_rank(a.tsv, query.q) DESC) AS rank
    FROM allowed a, query
    WHERE a.tsv @@ query.q
    ORDER BY ts_rank(a.tsv, query.q) DESC
    LIMIT %(pool)s
)
SELECT a.article_id, a.title, a.section, a.text,
       a.visibility, a.status, a.supersedes,
       COALESCE(1.0 / (%(rrf)s + v.rank), 0)
     + COALESCE(1.0 / (%(rrf)s + k.rank), 0) AS score,
       v.rank AS vector_rank,
       k.rank AS keyword_rank
FROM allowed a
LEFT JOIN vector_hits v ON v.id = a.id
LEFT JOIN keyword_hits k ON k.id = a.id
WHERE v.id IS NOT NULL OR k.id IS NOT NULL
ORDER BY score DESC
LIMIT %(top_n)s
"""


def or_terms(question: str) -> str:
    """Turn a question into an OR of its words.

    websearch_to_tsquery ANDs bare terms, so "how long does a refund take"
    would demand a chunk containing every one of those words and find
    nothing. The keyword half wants any match, and the ranking sorts out
    which matches are worth having.
    """
    words = re.findall(r"[a-zA-Z0-9]+", question.lower())
    return " or ".join(words)


def search(question: str, k: int = 5, audience: str = "customer") -> list[dict]:
    """The k allowed chunks that rank best across both halves."""
    vector = embed([question])[0]
    with connect() as conn:
        conn.row_factory = dict_row
        return conn.execute(
            SEARCH,
            {
                "vector": np.array(vector),
                "fts": or_terms(question),
                "audience": audience,
                "pool": POOL,
                "rrf": RRF_K,
                "top_n": k,
            },
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
        where = f"vec {hit['vector_rank'] or '-'}, kw {hit['keyword_rank'] or '-'}"
        print(f"{rank}. {hit['score']:.4f}  ({where})  {hit['article_id']}  "
              f"{hit['title']} / {hit['section']}{flag}")
        print(textwrap.indent(textwrap.fill(hit["text"], 76), "     "))
        print()


if __name__ == "__main__":
    main()
