from app.config import KB_DIR
from app.rag.chunker import chunk_documents
from app.rag.document_loader import load_markdown_documents
from app.rag.retriever import TfidfRetriever


def main():
    documents = load_markdown_documents(KB_DIR)
    chunks = chunk_documents(documents)

    print(f"Loaded documents: {len(documents)}")
    print(f"Created chunks: {len(chunks)}")

    retriever = TfidfRetriever(chunks)

    query = "DataBridge Pro ERR_CONNECTION_TIMEOUT"

    print(f"\nQuery: {query}\n")

    results = retriever.search(query, top_k=5)

    for index, result in enumerate(results, start=1):
        print(f"{index}. Score: {result.score:.4f}")
        print(f"   Source: {result.chunk.source}")
        print(f"   Heading: {result.chunk.heading}")
        print(f"   Chunk: {result.chunk.content[:300]}")
        print()


if __name__ == "__main__":
    main()