from app.config import KB_DIR
from app.rag.chunker import chunk_documents
from app.rag.document_loader import load_markdown_documents
from app.rag.retriever import TfidfRetriever


def build_retriever():
    documents = load_markdown_documents(KB_DIR)
    chunks = chunk_documents(documents)

    return TfidfRetriever(chunks)


def test_kb_documents_are_loaded():
    documents = load_markdown_documents(KB_DIR)

    assert len(documents) > 0


def test_chunks_are_created():
    documents = load_markdown_documents(KB_DIR)
    chunks = chunk_documents(documents)

    assert len(chunks) > len(documents)


def test_retriever_returns_results():
    retriever = build_retriever()

    results = retriever.search(
        "AnalyticsHub dashboard loading slowly",
        top_k=3,
    )

    assert len(results) == 3
    assert results[0].score >= 0


def test_databridge_error_retrieval():
    retriever = build_retriever()

    results = retriever.search(
        "DataBridge Pro ERR_CONNECTION_TIMEOUT",
        top_k=5,
    )

    assert len(results) > 0

    combined = " ".join(
        result.chunk.content
        for result in results
    ).lower()

    assert (
        "connection" in combined
        or "timeout" in combined
    )