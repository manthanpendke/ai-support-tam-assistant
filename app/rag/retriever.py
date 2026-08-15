import math
import re
from collections import Counter
from dataclasses import dataclass

from app.rag.chunker import Chunk


@dataclass(frozen=True)
class RetrievalResult:
    chunk: Chunk
    score: float


def _tokenize(text: str) -> list[str]:
    return re.findall(
        r"[a-zA-Z0-9_]+",
        text.lower(),
    )


class TfidfRetriever:
    def __init__(self, chunks: list[Chunk]):
        self.chunks = sorted(
            chunks,
            key=lambda chunk: chunk.chunk_id,
        )

        self.documents = [
            _tokenize(chunk.content)
            for chunk in self.chunks
        ]

        self.document_count = len(self.documents)

        self.document_frequency = Counter()

        for tokens in self.documents:
            for token in set(tokens):
                self.document_frequency[token] += 1

        self.vectors = [
            self._tfidf_vector(tokens)
            for tokens in self.documents
        ]

    def _idf(self, token: str) -> float:
        df = self.document_frequency.get(token, 0)

        return math.log(
            (1 + self.document_count)
            / (1 + df)
        ) + 1

    def _tfidf_vector(
        self,
        tokens: list[str],
    ) -> dict[str, float]:
        counts = Counter(tokens)

        if not tokens:
            return {}

        total = len(tokens)

        return {
            token: (count / total) * self._idf(token)
            for token, count in counts.items()
        }

    @staticmethod
    def _cosine_similarity(
        first: dict[str, float],
        second: dict[str, float],
    ) -> float:

        if not first or not second:
            return 0.0

        common_tokens = set(first) & set(second)

        dot_product = sum(
            first[token] * second[token]
            for token in common_tokens
        )

        first_norm = math.sqrt(
            sum(value * value for value in first.values())
        )

        second_norm = math.sqrt(
            sum(value * value for value in second.values())
        )

        if first_norm == 0 or second_norm == 0:
            return 0.0

        return dot_product / (
            first_norm * second_norm
        )

    @staticmethod
    def _normalise(text: str) -> str:
        return re.sub(
            r"\s+",
            " ",
            text.lower().strip(),
        )

    @staticmethod
    def _extract_special_terms(text: str) -> set[str]:
        """
        Extract structured identifiers that are especially useful
        for support-ticket retrieval.

        Examples:
        ERR_CONNECTION_TIMEOUT
        CHECKSUM_MISMATCH
        ERR_AUTH_FAILED
        403
        """

        return set(
            re.findall(
                r"[a-zA-Z]+_[a-zA-Z0-9_]+|"
                r"[a-zA-Z]*\d+[a-zA-Z0-9_-]*",
                text,
            )
        )

    def _metadata_score(
        self,
        query: str,
        chunk: Chunk,
    ) -> float:

        query_normalised = self._normalise(query)
        content_normalised = self._normalise(
            chunk.content
        )

        score = 0.0

        # Strong bonus for an exact query phrase.
        if query_normalised in content_normalised:
            score += 1.0

        # Strong bonus for exact error-code/identifier matches.
        special_terms = self._extract_special_terms(query)

        for term in special_terms:
            if term.lower() in content_normalised:
                score += 1.5

        # Small bonus when query terms occur in the source
        # filename or heading.
        query_tokens = set(
            _tokenize(query)
        )

        source_text = self._normalise(
            f"{chunk.source} {chunk.heading}"
        )

        for token in query_tokens:
            if token in source_text:
                score += 0.05

        return score

    def search(
        self,
        query: str,
        top_k: int = 3,
    ) -> list[RetrievalResult]:

        query_tokens = _tokenize(query)

        query_vector = self._tfidf_vector(
            query_tokens
        )

        results = []

        for chunk, vector in zip(
            self.chunks,
            self.vectors,
        ):
            cosine_score = self._cosine_similarity(
                query_vector,
                vector,
            )

            metadata_score = self._metadata_score(
                query,
                chunk,
            )

            # Combine semantic similarity with
            # exact support/error-term matching.
            final_score = (
                cosine_score
                + metadata_score
            )

            results.append(
                RetrievalResult(
                    chunk=chunk,
                    score=final_score,
                )
            )

        # Highest score first.
        # chunk_id provides deterministic tie-breaking.
        results.sort(
            key=lambda result: (
                -result.score,
                result.chunk.chunk_id,
            )
        )

        return results[:top_k]