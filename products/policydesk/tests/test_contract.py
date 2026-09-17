"""The output contract, from SPEC.md section 3."""

import pytest
from pydantic import ValidationError

from contract import Answer

CITE = {"article_id": "NIM-113", "section": "Delays", "quote": "ten days"}


def test_valid_answered():
    a = Answer(status="answered", answer="ten days", citations=[CITE],
               confidence="high")
    assert a.citations[0].article_id == "NIM-113"


def test_valid_no_answer():
    a = Answer(status="no_answer", confidence="low",
               handoff_reason="not covered")
    assert a.answer is None


def test_answered_without_citations_is_rejected():
    with pytest.raises(ValidationError):
        Answer(status="answered", answer="ten days", citations=[],
               confidence="high")


def test_no_answer_carrying_citations_is_rejected():
    with pytest.raises(ValidationError):
        Answer(status="no_answer", citations=[CITE], confidence="low",
               handoff_reason="x")


def test_no_answer_without_a_reason_is_rejected():
    with pytest.raises(ValidationError):
        Answer(status="no_answer", confidence="low")


def test_unknown_status_is_rejected():
    with pytest.raises(ValidationError):
        Answer(status="maybe", answer="x", citations=[CITE], confidence="high")


def test_confidence_is_not_free_text():
    with pytest.raises(ValidationError):
        Answer(status="answered", answer="x", citations=[CITE],
               confidence="quite sure")