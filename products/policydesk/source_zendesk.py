"""Translate Zendesk's article shape into ours.

The only file that knows what the source system looks like. Pointing this at
a live Zendesk is a change here and nowhere else, the same way shared/llm.py
is the only file that knows the model provider.

Three of our seven fields have no Zendesk equivalent, so they live in
label_names, which is where content teams actually put workflow state.
  NIM-113             our stable article id
  archived            Zendesk has draft and published, nothing else
  supersedes:NIM-103  no such concept exists in Zendesk
"""

import json
from pathlib import Path
from datetime import datetime

HERE = Path(__file__).parent
SOURCE = HERE / "data" / "zendesk_articles.json"


def status_of(raw: dict) -> str:
    """draft is a real Zendesk field. archived is a label we agreed on."""
    if raw["draft"]:
        return "draft"
    if "archived" in raw["label_names"]:
        return "archived"
    return "published"


def label_value(labels: list[str], prefix: str) -> str:
    for label in labels:
        if label.startswith(prefix):
            return label[len(prefix):]
    return ""


def to_article(raw: dict) -> dict:
    """One Zendesk article as the record the rest of the product expects."""
    labels = raw["label_names"]
    article_id = next((l for l in labels if l.startswith("NIM-")), None)
    if not article_id:
        raise ValueError(
            f"Zendesk article {raw['id']} has no NIM- label. "
            "Without it there is no stable key to upsert on."
        )

    return {
        "article_id": article_id,
        "title": raw["title"],
        "body_html": raw["body"],
        # null user_segment_id means everyone. Any segment means restricted.
        "visibility": "internal" if raw["user_segment_id"] else "public",
        "status": status_of(raw),
        "last_updated": raw["updated_at"][:10],
        "supersedes": label_value(labels, "supersedes:"),
        # Kept for the sync in step 3. The source's own id and timestamp are
        # the only things guaranteed stable across a rename.
        "zendesk_id": raw["id"],
        "updated_at": raw["updated_at"],
    }

def parse_time(value) -> datetime:
    """Zendesk sends Z, Postgres returns an offset. Compare as instants."""
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value.replace("Z", "+00:00"))

def fetch(path: Path = SOURCE, since: str | datetime | None = None) -> list[dict]:
    """Every article, or only those changed since an ISO timestamp.

    A real client would page through next_page and pass start_time to the
    incremental endpoint. The filtering is done here so the rest of the
    product never learns which it was.
    """
    payload = json.loads(path.read_text())
    articles = [to_article(raw) for raw in payload["articles"]]
    if since:
        cutoff = parse_time(since)
        articles = [a for a in articles
                    if parse_time(a["updated_at"]) > cutoff]
    return articles

