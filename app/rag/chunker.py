from dataclasses import dataclass

from app.rag.document_loader import Document


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    source: str
    category: str
    heading: str
    content: str


def _extract_heading(lines: list[str]) -> str:
    headings = [
        line.strip()
        for line in lines
        if line.strip().startswith("#")
    ]

    return headings[-1] if headings else "Document"


def _split_table_rows(content: str) -> list[str]:
    lines = content.splitlines()

    table_rows = []

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("|") and stripped.endswith("|"):
            # Ignore Markdown separator rows such as:
            # |---|---|
            if "---" in stripped.replace("|", "").replace(":", ""):
                continue

            table_rows.append(stripped)

    return table_rows


def chunk_documents(documents: list[Document]) -> list[Chunk]:
    chunks = []

    for document in documents:
        sections = document.content.split("\n---\n")

        for section_index, section in enumerate(sections):
            section = section.strip()

            if not section:
                continue

            lines = section.splitlines()
            heading = _extract_heading(lines)

            chunk_id = (
                f"{document.source}"
                f"::section-{section_index}"
            )

            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    source=document.source,
                    category=document.category,
                    heading=heading,
                    content=section,
                )
            )

            # Table rows are additionally represented as small
            # atomic chunks for precise error/limit retrieval.
            for row_index, row in enumerate(
                _split_table_rows(section)
            ):
                chunks.append(
                    Chunk(
                        chunk_id=(
                            f"{document.source}"
                            f"::section-{section_index}"
                            f"::table-{row_index}"
                        ),
                        source=document.source,
                        category=document.category,
                        heading=heading,
                        content=row,
                    )
                )

    return chunks