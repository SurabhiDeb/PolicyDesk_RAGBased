"""Ordinary software tests. One right answer, no model, no network."""

import pytest

from text import split_sections, strip_fences

ARTICLE = {
    "body": "## First\nalpha\n\n## Second\nbeta\ngamma\n",
}


def test_one_chunk_per_heading():
    assert [c["section"] for c in split_sections(ARTICLE)] == ["First", "Second"]


def test_chunk_keeps_all_its_lines():
    assert split_sections(ARTICLE)[1]["text"] == "beta\ngamma"


def test_text_before_the_first_heading_is_dropped():
    article = {"body": "orphan line\n\n## Real\nbody"}
    assert [c["section"] for c in split_sections(article)] == ["Real"]


def test_no_headings_gives_no_chunks():
    assert split_sections({"body": "just prose"}) == []


def test_empty_section_is_skipped():
    article = {"body": "## Empty\n\n## Full\nbody"}
    assert [c["section"] for c in split_sections(article)] == ["Full"]


@pytest.mark.parametrize(
    "raw",
    ['{"a": 1}', '```json\n{"a": 1}\n```', '```\n{"a": 1}\n```', '  {"a": 1}  '],
)
def test_strip_fences_leaves_bare_json(raw):
    assert strip_fences(raw) == '{"a": 1}'