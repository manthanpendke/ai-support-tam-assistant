from typing import Literal

from pydantic import BaseModel, Field


Urgency = Literal["P1", "P2", "P3", "P4"]

Category = Literal[
    "Bug",
    "Feature Request",
    "How-To",
    "Performance",
    "Billing",
    "Integration",
    "Onboarding",
    "Data Loss",
]


class TriageResult(BaseModel):
    product: str = Field(
        description="Product involved in the ticket."
    )

    product_area: str = Field(
        description="Specific product area or feature involved."
    )

    category: Category = Field(
        description="Primary support ticket category."
    )

    urgency: Urgency = Field(
        description="Ticket urgency from P1 to P4."
    )

    reasoning: str = Field(
        description="Concise explanation for the classification."
    )

    known_issue: bool = Field(
        description="Whether the issue matches known KB information."
    )

    kb_document: str | None = Field(
        default=None,
        description="Relevant knowledge-base document path."
    )

    recommended_responder_team: str = Field(
        description="Team that should handle the ticket."
    )

    first_response: str = Field(
        description="Customer-facing first response."
    )