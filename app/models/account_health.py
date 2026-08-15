from typing import Literal

from pydantic import BaseModel, Field


HealthStatus = Literal[
    "Healthy",
    "Watch",
    "At Risk",
    "Critical",
]


class AccountHealth(BaseModel):
    account_id: str

    account_name: str | None = None

    tam: str | None = None

    plan_tier: str | None = None

    arr_usd: float | None = None

    health_status: HealthStatus

    health_score: float = Field(
        ge=0,
        le=100,
    )

    ticket_count_90d: int = Field(
        ge=0,
    )

    open_ticket_count: int = Field(
        ge=0,
    )

    p1_count: int = Field(
        ge=0,
    )

    p2_count: int = Field(
        ge=0,
    )

    p3_count: int = Field(
        ge=0,
    )

    p4_count: int = Field(
        ge=0,
    )

    recent_ticket_count_30d: int = Field(
        ge=0,
    )

    seats_utilization_percent: float = Field(
        ge=0,
        le=100,
    )
    
    data_quality_warnings: list[str] = Field(
    default_factory=list,
    )

    usage_trend: str | None = None

    days_to_renewal: int | None = None

    nps_score: float | None = None

    escalation_notes: list[str] = Field(
        default_factory=list,
    )

    recurring_themes: list[str] = Field(
        default_factory=list,
    )

    recommended_actions: list[str] = Field(
        default_factory=list,
    )