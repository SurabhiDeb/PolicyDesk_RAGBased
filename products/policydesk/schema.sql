-- The search index. Created once, then maintained by sync.py.
--
-- The old version dropped and rebuilt the table on every ingest. That is
-- fine for 16 articles and wrong for 40,000, because the index is empty
-- while it runs and every embedding is paid for again.

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS chunks (
    id            bigserial PRIMARY KEY,
    article_id    text NOT NULL,
    title         text NOT NULL,
    section       text NOT NULL,
    text          text NOT NULL,
    visibility    text NOT NULL CHECK (visibility IN ('public', 'internal')),
    status        text NOT NULL CHECK (status IN ('published', 'draft', 'archived')),
    last_updated  date NOT NULL,
    supersedes    text,

    -- From the source system. The only identifiers guaranteed stable across
    -- a rename, and what the incremental sync compares against.
    zendesk_id    bigint NOT NULL,
    updated_at    timestamptz NOT NULL,

    embedding     vector(768) NOT NULL,

    tsv           tsvector GENERATED ALWAYS AS (
                      to_tsvector('english',
                          title || ' ' || section || ' ' || text)
                  ) STORED,

    -- What makes an upsert possible. Without it every sync would insert
    -- duplicates instead of updating.
    UNIQUE (article_id, section)
);

-- Where the sync remembers how far it got. One row.
CREATE TABLE IF NOT EXISTS sync_state (
    source           text PRIMARY KEY,
    last_updated_at  timestamptz,
    last_run_at      timestamptz NOT NULL,
    articles_seen    integer NOT NULL,
    chunks_written   integer NOT NULL,
    chunks_deleted   integer NOT NULL
);