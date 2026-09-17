"""The output contract from SPEC.md section 3, as code.

Hand-written checks are how Triage shipped TRUE instead of true. A schema
makes the malformed case impossible to miss.
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator


class Citation(BaseModel):
    article_id: str
    section: str
    quote: str


class Answer(BaseModel):
    """What the model must return. `audience` is set by us, not by it."""

    status: Literal["answered", "no_answer"]
    answer: Optional[str] = None
    citations: list[Citation] = Field(default_factory=list)
    confidence: Literal["low", "medium", "high"]
    handoff_reason: Optional[str] = None

    @model_validator(mode="after")
    def consistent(self):
        if self.status == "answered":
            if not self.answer:
                raise ValueError("answered requires an answer")
            if not self.citations:
                raise ValueError("answered requires at least one citation")
        else:
            if self.answer:
                raise ValueError("no_answer must not carry an answer")
            if self.citations:
                raise ValueError("no_answer must not carry citations")
            if not self.handoff_reason:
                raise ValueError("no_answer requires a handoff_reason")
        return self