"""Keep the search index in step with the help centre.

Replaces ingest.py. The difference is that this one does not throw the index
away first.

  incremental  only articles changed since the last run, upserted
  --full       every article, and anything no longer in the source is deleted

Deletion is the part naive syncs miss. An upsert can add and update, and it
can never remove. An article that gets unpublished, or a section that gets
edited out, stays in the index forever answering questions it should not.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from shared.db import DSN, connect  # noqa: E402
from shared.embed import EMBED_MODEL, embed  # noqa: E402

from html_sections import split_html_sections  # noqa: E402
from source_zendesk import SOURCE, fetch  # noqa: E402

HERE = Path(__file__).parent
SCHEMA = HERE / "schema.sql"

UPSERT = """
INSERT INTO chunks (article_id, title, section, text, visibility, status,
                    last_updated, supersedes, zendesk_id, updated_at, embedding)
VALUES (%(article_id)s, %(title)s, %(section)s, %(text)s, %(visibility)s,
        %(status)s, %(last_updated)s, %(supersedes)s, %(zendesk_id)s,
        %(updated_at)s, %(embedding)s)
ON CONFLICT (article_id, section) DO UPDATE SET
    title        = EXCLUDED.title,
    text         = EXCLUDED.text,
    visibility   = EXCLUDED.visibility,
    status       = EXCLUDED.status,
    last_updated = EXCLUDED.last_updated,
    supersedes   = EXCLUDED.supersedes,
    zendesk_id   = EXCLUDED.zendesk_id,
    updated_at   = EXCLUDED.updated_at,
    embedding    = EXCLUDED.embedding
"""

# A section edited out of an article leaves a chunk behind. This removes any
# chunk of a synced article whose heading is no longer in that article.
PRUNE_SECTIONS = """
DELETE FROM chunks
WHERE article_id = %(article_id)s AND section <> ALL(%(sections)s)
"""

# Only safe on a full sync, when the article list is known to be complete.
PRUNE_ARTICLES = """
DELETE FROM chunks WHERE article_id <> ALL(%(article_ids)s)
"""

READ_STATE = "SELECT last_updated_at FROM sync_state WHERE source = %s"

WRITE_STATE = """
INSERT INTO sync_state (source, last_updated_at, last_run_at, articles_seen,
                        chunks_written, chunks_deleted)
VALUES (%(source)s, %(last_updated_at)s, %(last_run_at)s, %(articles_seen)s,
        %(chunks_written)s, %(chunks_deleted)s)
ON CONFLICT (source) DO UPDATE SET
    last_updated_at = EXCLUDED.last_updated_at,
    last_run_at     = EXCLUDED.last_run_at,
    articles_seen   = EXCLUDED.articles_seen,
    chunks_written  = EXCLUDED.chunks_written,
    chunks_deleted  = EXCLUDED.chunks_deleted
"""

SOURCE_NAME = "zendesk"


def chunk_rows(article: dict) -> list[dict]:
    """One article as the rows it becomes."""
    return [
        {
            "article_id": article["article_id"],
            "title": article["title"],
            "section": chunk["section"],
            "text": chunk["text"],
            "visibility": article["visibility"],
            "status": article["status"],
            "last_updated": article["last_updated"],
            "supersedes": article["supersedes"] or "",
            "zendesk_id": article["zendesk_id"],
            "updated_at": article["updated_at"],
            # The title and heading go into the embedded text. A chunk that
            # just says "Delays" means nothing without them.
            "embed_text": (
                f"{article['title']}. {chunk['section']}.\n{chunk['text']}"
            ),
        }
        for chunk in split_html_sections(article["body_html"])
    ]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action="store_true",
                        help="sync every article and delete anything missing")
    args = parser.parse_args()

    started = datetime.now(timezone.utc)

    with connect() as conn:
        conn.execute(SCHEMA.read_text())
        conn.commit()

        row = conn.execute(READ_STATE, (SOURCE_NAME,)).fetchone()
        since = None if args.full else (row[0] if row else None)

        if since:
            print(f"incremental since {since}")
        else:
            print("full sync" if args.full else "first run, syncing everything")

        everything = fetch(SOURCE)
        changed = fetch(SOURCE, since=since)
        print(f"{len(everything)} articles in source, {len(changed)} changed")

        rows = [r for article in changed for r in chunk_rows(article)]
        written = deleted = 0

        if rows:
            vectors = embed([r["embed_text"] for r in rows])
            for row_, vector in zip(rows, vectors):
                row_["embedding"] = np.array(vector)
                del row_["embed_text"]

            with conn.cursor() as cur:
                cur.executemany(UPSERT, rows)
                written = len(rows)

                for article in changed:
                    cur.execute(PRUNE_SECTIONS, {
                        "article_id": article["article_id"],
                        "sections": [
                            c["section"]
                            for c in split_html_sections(article["body_html"])
                        ],
                    })
                    deleted += cur.rowcount

        if args.full:
            with conn.cursor() as cur:
                cur.execute(PRUNE_ARTICLES, {
                    "article_ids": [a["article_id"] for a in everything],
                })
                deleted += cur.rowcount

        high_water = max((a["updated_at"] for a in everything), default=None)
        conn.execute(WRITE_STATE, {
            "source": SOURCE_NAME,
            "last_updated_at": high_water,
            "last_run_at": started,
            "articles_seen": len(changed),
            "chunks_written": written,
            "chunks_deleted": deleted,
        })
        conn.commit()

        total = conn.execute("SELECT count(*) FROM chunks").fetchone()[0]
        counts = conn.execute(
            "SELECT status, visibility, count(*) FROM chunks"
            " GROUP BY 1, 2 ORDER BY 1, 2"
        ).fetchall()

    print(f"\nwritten {written}, deleted {deleted}, index now {total} chunks")
    print(f"high water mark {high_water}")
    print(f"model {EMBED_MODEL}")
    print(f"database {DSN}\n")
    for status, visibility, n in counts:
        print(f"  {status:<10} {visibility:<9} {n}")


if __name__ == "__main__":
    main()
