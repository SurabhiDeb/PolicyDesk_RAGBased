"""Evals, not tests. These read the committed run record and check it against
the targets in SPEC.md. No model calls, so CI runs them for free.

Targets we do not meet yet are marked xfail(strict=True). The build stays
green, but the moment one starts passing pytest fails, which forces the
marker to be removed. A known gap cannot quietly become a forgotten one.
"""

import json
from pathlib import Path

import pytest

from metrics import abstention, exposure, first_gold_rank, quotes

HERE = Path(__file__).resolve().parent.parent
RUNS = HERE / "runs"
ARTICLES = HERE / "data" / "articles.jsonl"


# The gate measures what we ship, D24, not whatever experiment ran last.
# Comparison runs against other models and retrievers stay in runs/ as the
# evidence for those decisions and must never become what CI enforces.
SHIPPED_MODEL = "haiku-4-5"
SHIPPED_RETRIEVER = "filtered-v1"


@pytest.fixture(scope="session")
def run():
    files = sorted(p for p in RUNS.glob("*-v*.json")
                   if "groundedness" not in p.name)
    assert files, f"no run record in {RUNS}"

    for path in reversed(files):
        record = json.loads(path.read_text())
        meta = record["meta"]
        if (SHIPPED_MODEL in meta.get("chat_model_served", "")
                and meta.get("retriever") == SHIPPED_RETRIEVER):
            return record

    raise AssertionError(
        f"no run in {RUNS} used {SHIPPED_MODEL} with {SHIPPED_RETRIEVER}")


@pytest.fixture(scope="session")
def results(run):
    return run["results"]


@pytest.fixture(scope="session")
def articles():
    return {
        json.loads(l)["article_id"]: json.loads(l)["body"]
        for l in ARTICLES.read_text().splitlines() if l.strip()
    }


# --- Non-negotiable. These block the build today. ---

def test_no_internal_article_reaches_a_customer(results):
    """C1. The worst failure in the spec."""
    leaks = exposure(results)["c1_internal_leaks"]
    assert leaks == [], f"internal content shown to a customer in {leaks}"


def test_every_response_parsed(results):
    """C5. A malformed response cannot be served at all."""
    broken = [r["id"] for r in results if r["problem"]]
    assert broken == [], f"unparseable output in {broken}"


def test_every_quote_is_verbatim(results, articles):
    """C2. A fabricated citation survives review, which is why it is critical."""
    invalid = quotes(results, articles)["invalid"]
    assert invalid == [], f"quotes not found in their article: {invalid}"


def test_answered_cases_carry_citations(results):
    """Contract. An answer with no source cannot be checked by anyone."""
    bare = [r["id"] for r in results
            if r["status"] == "answered" and not r.get("citations")]
    assert bare == [], f"answered with no citations: {bare}"


def test_latency_within_budget(run):
    seconds = sorted(r["model_seconds"] for r in run["results"])
    p95 = seconds[int(len(seconds) * 0.95) - 1]
    assert p95 < 6.0, f"p95 latency {p95}s over the 6s budget"

def test_no_banned_article_is_ever_cited(results):
    """C3. Archived, draft or superseded content must never be quoted."""
    cited = exposure(results)["cited_cases"]
    assert cited == [], f"archived, draft or superseded cited in {cited}"

def test_recall_at_1(results):
    """The right article should usually be the top hit, not merely present."""
    gold = [r for r in results if r["expected_articles"]]
    at_one = sum(1 for r in gold if first_gold_rank(r) == 1)
    assert at_one / len(gold) >= 0.80, f"recall@1 {at_one / len(gold):.0%}"

def test_every_answerable_case_retrieves_its_article(results):
    gold = [r for r in results if r["expected_articles"]]
    missed = [r["id"] for r in gold if first_gold_rank(r) is None]
    assert missed == [], f"gold article never retrieved for {missed}"

# --- Known gaps. Expected to fail until the beat that fixes them. ---

@pytest.mark.xfail(strict=True, reason="q34, q35 contradiction and q37 scope, see runs/v4-notes.md")
def test_abstention_recall(results):
    a = abstention(results)
    assert a["recall"] >= 0.95, f"abstention recall {a['recall']:.0%}"



