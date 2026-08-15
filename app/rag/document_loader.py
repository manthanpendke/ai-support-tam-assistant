from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Document:
    source: str
    category: str
    content: str


def load_markdown_documents(kb_dir: Path) -> list[Document]:
    documents = []

    for path in sorted(kb_dir.rglob("*.md")):
        category = path.parent.name

        content = path.read_text(
            encoding="utf-8"
        ).strip()

        if not content:
            continue

        documents.append(
            Document(
                source=str(path.relative_to(kb_dir)),
                category=category,
                content=content,
            )
        )

    return documents