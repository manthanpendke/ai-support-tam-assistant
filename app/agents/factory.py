from app.config import KB_DIR
from app.rag.chunker import chunk_documents
from app.rag.document_loader import load_markdown_documents
from app.rag.retriever import TfidfRetriever


def build_retriever() -> TfidfRetriever:
    documents = load_markdown_documents(
        KB_DIR
    )

    chunks = chunk_documents(
        documents
    )

    return TfidfRetriever(
        chunks
    )