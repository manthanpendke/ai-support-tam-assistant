from app.rag.retriever import RetrievalResult


def format_retrieval_context(
    results: list[RetrievalResult],
) -> str:

    if not results:
        return "No relevant knowledge-base evidence was found."

    sections = []

    for index, result in enumerate(
        results,
        start=1,
    ):
        chunk = result.chunk

        sections.append(
            f"""
EVIDENCE {index}

Source: {chunk.source}
Category: {chunk.category}
Heading: {chunk.heading}
Retrieval Score: {result.score:.4f}

Content:
{chunk.content}
""".strip()
        )

    return "\n\n".join(sections)