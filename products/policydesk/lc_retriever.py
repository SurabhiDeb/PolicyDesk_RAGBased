"""PolicyDesk retrieval as a LangChain retriever.

Almost nobody's production store matches the shape LangChain's built-in
vector stores expect, and rewriting a working index to fit a library is the
wrong trade. What people actually do is wrap their own search behind
BaseRetriever, which is all this is.

The payoff is that PolicyDesk retrieval now plugs into anything that takes a
LangChain retriever, without the visibility filter, the RRF, or the Postgres
schema changing at all.
"""

import sys
from pathlib import Path

from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

sys.path.insert(0, str(Path(__file__).resolve().parent))

from retrieve import RETRIEVER, search  # noqa: E402


class PolicyDeskRetriever(BaseRetriever):
    """Wraps retrieve.search so LangChain can use it.

    BaseRetriever is a pydantic model, so these are declared as fields with
    types rather than set in an __init__.
    """

    audience: str = "customer"
    k: int = 5

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> list[Document]:
        hits = search(query, self.k, self.audience)
        return [
            Document(
                page_content=hit["text"],
                metadata={
                    "article_id": hit["article_id"],
                    "title": hit["title"],
                    "section": hit["section"],
                    "visibility": hit["visibility"],
                    "status": hit["status"],
                    "retriever": RETRIEVER,
                },
            )
            for hit in hits
        ]


def main():
    if len(sys.argv) < 2:
        sys.exit('Usage: python3 lc_retriever.py "question" [customer|agent]')

    audience = sys.argv[-1] if sys.argv[-1] in ("customer", "agent") else "customer"
    words = sys.argv[1:-1] if audience == sys.argv[-1] else sys.argv[1:]
    question = " ".join(words)

    retriever = PolicyDeskRetriever(audience=audience, k=5)

    # invoke is the standard LangChain interface. Every chain, agent and
    # pipeline that accepts a retriever calls exactly this.
    for doc in retriever.invoke(question):
        m = doc.metadata
        print(f"{m['article_id']}  {m['title']} / {m['section']}")
        print(f"   {doc.page_content[:90]}")


if __name__ == "__main__":
    main()
