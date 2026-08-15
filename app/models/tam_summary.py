from pydantic import BaseModel, Field
from typing import Literal


RenewalRisk = Literal[
    "Low",
    "Medium",
    "High",
    "Unknown",
]

CustomerSentiment = Literal[
    "Positive",
    "Neutral",
    "At Risk",
    "Unknown",
]


class RiskFlag(BaseModel):
    flag: str

    reason: str

    ticket_id: str | None = None

    evidence_quote: str | None = None


class TAMSummary(BaseModel):
    account_id: str

    # -------------------------------------------------
    # Required 3-section TAM brief
    # -------------------------------------------------

    executive_summary: str

    open_risks: list[RiskFlag] = Field(
        default_factory=list,
    )

    talking_points: list[str] = Field(
        default_factory=list,
    )

    # -------------------------------------------------
    # Existing fields kept for backward compatibility
    # -------------------------------------------------

    top_risks: list[str] = Field(
        default_factory=list,
    )

    recommended_actions: list[str] = Field(
        default_factory=list,
    )

    renewal_risk: RenewalRisk = "Unknown"

    customer_sentiment: CustomerSentiment = "Unknown"

    data_quality_warnings: list[str] = Field(
        default_factory=list,
    )