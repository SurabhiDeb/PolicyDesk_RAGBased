-- The shape of the search index. Rebuilt from articles.jsonl every ingest.

CREATE EXTENSION IF NOT EXISTS vector;

DROP TABLE IF EXISTS chunks;

CREATE TABLE chunks (
    id            bigserial PRIMARY KEY,
    article_id    text NOT NULL,
    title         text NOT NULL,
    section       text NOT NULL,
    text          text NOT NULL,
    visibility    text NOT NULL CHECK (visibility IN ('public', 'internal')),
    status        text NOT NULL CHECK (status IN ('published', 'draft', 'archived')),
    last_updated  date NOT NULL,
    supersedes    text,
    embedding     vector(768) NOT NULL
);

-- No vector index on purpose. At 43 rows a sequential scan is faster than
-- any index, and HNSW only pays off in the thousands.