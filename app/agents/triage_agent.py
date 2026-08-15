import re

from app.models.triage import TriageResult
from app.prompts.triage_v1 import (
    SYSTEM_PROMPT,
    build_user_prompt,
)
from app.rag.context import format_retrieval_context
from app.rag.retriever import (
    RetrievalResult,
    TfidfRetriever,
)
from app.services.llm_client import GroqLLMClient


class TriageAgent:

    def __init__(
        self,
        retriever: TfidfRetriever,
        llm_client: GroqLLMClient | None = None,
        top_k: int = 5,
    ):
        self.retriever = retriever

        self.llm_client = (
            llm_client
            if llm_client is not None
            else GroqLLMClient()
        )

        self.top_k = top_k

    def triage(
        self,
        subject: str,
        body: str,
    ) -> TriageResult:

        if not subject.strip():
            raise ValueError(
                "Ticket subject cannot be empty."
            )

        if not body.strip():
            raise ValueError(
                "Ticket body cannot be empty."
            )

        retrieval_query = (
            f"{subject}\n{body}"
        )

        results = self.retriever.search(
            retrieval_query,
            top_k=self.top_k,
        )

        kb_context = format_retrieval_context(
            results
        )

        user_prompt = build_user_prompt(
            subject=subject,
            body=body,
            kb_context=kb_context,
        )

        raw_result = self.llm_client.generate_json(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        # -------------------------------------------------
        # Normalize LLM output before Pydantic validation.
        # -------------------------------------------------

        raw_result = self._normalize_result(
            raw_result
        )

        result = TriageResult.model_validate(
            raw_result
        )

        # -------------------------------------------------
        # Ground the result against the retrieved KB.
        # -------------------------------------------------

        result = self._ground_result(
            result=result,
            retrieval_results=results,
            ticket_text=retrieval_query,
        )

        # -------------------------------------------------
        # Ground product against ticket and KB.
        # -------------------------------------------------

        grounded_product = self._extract_product(
            ticket_text=retrieval_query,
            current_product=result.product,
            retrieval_results=results,
        )

        if grounded_product:
            result = result.model_copy(
                update={
                    "product": grounded_product,
                }
            )

        return result

    @staticmethod
    def _normalize_result(
        result: dict,
    ) -> dict:
        """
        Normalize simple LLM variations before
        Pydantic validation.
        """

        if not isinstance(result, dict):
            return result

        normalized = dict(result)

        # -------------------------------------------------
        # Normalize category capitalization.
        # -------------------------------------------------

        category_map = {
            "bug": "Bug",
            "feature request": "Feature Request",
            "how-to": "How-To",
            "how to": "How-To",
            "performance": "Performance",
            "billing": "Billing",
            "integration": "Integration",
            "onboarding": "Onboarding",
            "data loss": "Data Loss",
        }

        category = normalized.get("category")

        if isinstance(category, str):

            cleaned_category = category.strip()

            normalized["category"] = (
                category_map.get(
                    cleaned_category.lower(),
                    cleaned_category,
                )
            )

        # -------------------------------------------------
        # Normalize urgency.
        # -------------------------------------------------

        urgency = normalized.get("urgency")

        if isinstance(urgency, str):

            normalized["urgency"] = (
                urgency.strip().upper()
            )

        # -------------------------------------------------
        # Normalize product names.
        # -------------------------------------------------

        product = normalized.get("product")

        if isinstance(product, str):

            product_map = {
                "databridge": "DataBridge Pro",
                "databridge pro": "DataBridge Pro",
                "cloudsync": "CloudSync",
                "analyticshub": "AnalyticsHub",
                "workflowengine": "WorkflowEngine",
            }

            normalized["product"] = product_map.get(
                product.strip().lower(),
                product.strip(),
            )

        return normalized

    @staticmethod
    def _extract_special_terms(
        text: str,
    ) -> set[str]:

        return set(
            re.findall(
                r"[a-zA-Z]+_[a-zA-Z0-9_]+",
                text,
            )
        )

    @classmethod
    def _extract_product(
        cls,
        ticket_text: str,
        current_product: str | None,
        retrieval_results: list[RetrievalResult],
    ) -> str | None:
        """
        Determine product using deterministic evidence.

        Priority:

        1. Explicit product in ticket.
        2. Known product-specific error identifier.
        3. Product-specific KB source containing
           the structured error.
        4. Preserve normalized LLM result.
        """

        known_products = (
            "DataBridge Pro",
            "CloudSync",
            "AnalyticsHub",
            "WorkflowEngine",
        )

        ticket_lower = ticket_text.lower()

        # -------------------------------------------------
        # 1. Explicit product in ticket.
        # -------------------------------------------------

        for product in sorted(
            known_products,
            key=len,
            reverse=True,
        ):

            if product.lower() in ticket_lower:
                return product

        # -------------------------------------------------
        # 2. Deterministic product/error mapping.
        # -------------------------------------------------

        special_terms = {
            term.lower()
            for term in cls._extract_special_terms(
                ticket_text
            )
        }

        error_product_map = {
            "pipeline_stalled": "DataBridge Pro",
        }

        for term, product in error_product_map.items():

            if term in special_terms:
                return product

        # -------------------------------------------------
        # 3. Inspect product-specific retrieved chunks.
        # -------------------------------------------------

        if special_terms:

            product_matches = []

            for retrieval_result in retrieval_results:

                source = (
                    retrieval_result.chunk.source
                    or ""
                ).lower()

                content = (
                    retrieval_result.chunk.content
                    or ""
                ).lower()

                heading = (
                    retrieval_result.chunk.heading
                    or ""
                ).lower()

                has_special_term = any(
                    term in content
                    for term in special_terms
                )

                if not has_special_term:
                    continue

                matched_product = None

                for product in sorted(
                    known_products,
                    key=len,
                    reverse=True,
                ):

                    product_lower = product.lower()

                    product_slug = (
                        product_lower.replace(
                            " ",
                            "-",
                        )
                    )

                    if product_slug in source:
                        matched_product = product
                        break

                    if product_lower in content:
                        matched_product = product
                        break

                    if product_lower in heading:
                        matched_product = product
                        break

                if matched_product:

                    product_matches.append(
                        (
                            retrieval_result.score,
                            matched_product,
                        )
                    )

            if product_matches:

                product_matches.sort(
                    key=lambda item: -item[0]
                )

                return product_matches[0][1]

        # -------------------------------------------------
        # 4. Preserve LLM result.
        # -------------------------------------------------

        return current_product

    @classmethod
    def _find_grounded_source(
        cls,
        ticket_text: str,
        retrieval_results: list[RetrievalResult],
    ) -> str | None:

        if not retrieval_results:
            return None

        special_terms = {
            term.lower()
            for term in cls._extract_special_terms(
                ticket_text
            )
        }

        if special_terms:

            matching_results = []

            for result in retrieval_results:

                content = (
                    result.chunk.content.lower()
                )

                heading = (
                    result.chunk.heading.lower()
                )

                matched = any(
                    term in content
                    for term in special_terms
                )

                if not matched:
                    continue

                section_bonus = 0.0

                if any(
                    word in heading
                    for word in (
                        "error",
                        "troubleshoot",
                        "common issue",
                        "common errors",
                    )
                ):
                    section_bonus = 0.5

                matching_results.append(
                    (
                        result.score + section_bonus,
                        result,
                    )
                )

            if matching_results:

                matching_results.sort(
                    key=lambda item: (
                        -item[0],
                        item[1].chunk.chunk_id,
                    )
                )

                return (
                    matching_results[0][1]
                    .chunk
                    .source
                )

        return retrieval_results[0].chunk.source

    @classmethod
    def _ground_result(
        cls,
        result: TriageResult,
        retrieval_results: list[RetrievalResult],
        ticket_text: str,
    ) -> TriageResult:

        if not retrieval_results:

            return result.model_copy(
                update={
                    "known_issue": False,
                    "kb_document": None,
                }
            )

        grounded_source = cls._find_grounded_source(
            ticket_text=ticket_text,
            retrieval_results=retrieval_results,
        )

        if result.known_issue and grounded_source:

            return result.model_copy(
                update={
                    "kb_document": grounded_source,
                }
            )

        return result