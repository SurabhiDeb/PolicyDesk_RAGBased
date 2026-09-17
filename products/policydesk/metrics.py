"""Numbers from a run record. No model calls, no database, no judgement.

Retrieval and answering are measured separately and never averaged. A good
answer over bad retrieval is luck, and one number would hide which half
is broken.
"""

BANNED = {"NIM-099": "archived", "NIM-103": "superseded", "NIM-210": "draft"}
INTERNAL = {"NIM-201", "NIM-202", "NIM-203"}


def banned_for(audience: str) -> dict:
    """Articles this audience must never be shown."""
    out = dict(BANNED)
    if audience == "customer":
        out.update({a: "internal" for a in INTERNAL})
    return out


def _gold_cases(results):
    """Only cases with a known right article can measure retrieval."""
    return [r for r in results if r["expected_articles"]]


def first_gold_rank(r) -> int | None:
    """1-based rank of the first chunk from a gold article, or None.

    Rank is chunk rank, not article rank. Several chunks can come from the
    same article, so rank 3 does not mean the third best article.
    """
    for i, article in enumerate(r["retrieved"], start=1):
        if article in r["expected_articles"]:
            return i
    return None


def retrieval(results) -> dict:
    cases = _gold_cases(results)
    ranks = [first_gold_rank(r) for r in cases]
    found = [x for x in ranks if x is not None]

    return {
        "cases": len(cases),
        "recall_at_5": sum(1 for x in found if x <= 5) / len(cases),
        "recall_at_1": sum(1 for x in found if x == 1) / len(cases),
        "mrr": sum(1 / x for x in found) / len(cases),
        "missed": [r["id"] for r, x in zip(cases, ranks) if x is None],
    }


def exposure(results) -> dict:
    """How often banned material reaches the model, and how often it is used."""
    retrieved_hits, cited_hits, critical = [], [], []

    for r in results:
        banned = banned_for(r["audience"])
        cited = [c.get("article_id") for c in r.get("citations") or []]

        if any(a in banned for a in r["retrieved"]):
            retrieved_hits.append(r["id"])
        bad_cited = sorted({a for a in cited if a in banned})
        if bad_cited:
            cited_hits.append(r["id"])
            if any(banned[a] == "internal" for a in bad_cited):
                critical.append(r["id"])

    n = len(results)
    return {
        "retrieved_banned": len(retrieved_hits) / n,
        "cited_banned": len(cited_hits) / n,
        "cited_cases": cited_hits,
        "c1_internal_leaks": critical,
    }


def abstention(results) -> dict:
    """Treating no_answer as the positive class."""
    tp = sum(1 for r in results
             if r["expected_status"] == "no_answer" and r["status"] == "no_answer")
    fn = sum(1 for r in results
             if r["expected_status"] == "no_answer" and r["status"] == "answered")
    fp = sum(1 for r in results
             if r["expected_status"] == "answered" and r["status"] == "no_answer")

    return {
        "recall": tp / (tp + fn) if tp + fn else 0.0,
        "precision": tp / (tp + fp) if tp + fp else 0.0,
        "should_have_abstained": [r["id"] for r in results
                                  if r["expected_status"] == "no_answer"
                                  and r["status"] == "answered"],
        "wrongly_abstained": [r["id"] for r in results
                              if r["expected_status"] == "answered"
                              and r["status"] == "no_answer"],
    }


def quotes(results, articles: dict) -> dict:
    """Every quote must appear verbatim in the article it names.

    Mechanical, no judge. articles maps article_id to its full body text.
    """
    bad = []
    for r in results:
        for c in r.get("citations") or []:
            body = articles.get(c.get("article_id"))
            if body is None or c.get("quote", "") not in body:
                bad.append((r["id"], c.get("article_id")))
    return {"invalid": bad}
