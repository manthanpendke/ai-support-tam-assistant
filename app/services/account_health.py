from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any

from app.models.account_health import AccountHealth
from app.services.data_loader import (
    get_account,
    get_account_tickets,
)


class AccountHealthService:

    def analyze(
        self,
        account_id: str,
        reference_time: datetime | None = None,
    ) -> AccountHealth:

        reference_time = (
            reference_time
            or datetime.now(timezone.utc)
        )

        account = get_account(account_id)

        if account is None:
            raise ValueError(
                f"Account not found: {account_id}"
            )

        # Only tickets that actually belong to this account
        # are considered. Orphan tickets are ignored.
        tickets = get_account_tickets(
            account_id=account_id,
            days=90,
            reference_time=reference_time,
        )

        recent_cutoff = (
            reference_time
            - timedelta(days=30)
        )

        recent_tickets = [
            ticket
            for ticket in tickets
            if self._parse_datetime(
                ticket["created_at"]
            ) >= recent_cutoff
        ]

        # IMPORTANT:
        # The dataset uses "urgency", not "severity".
        urgency_counts = Counter(
            ticket.get("urgency")
            for ticket in tickets
        )

        open_ticket_count = sum(
            1
            for ticket in tickets
            if self._is_open(ticket)
        )

        # The account record is authoritative for the
        # current open-ticket snapshot when available.
        account_open_tickets = int(
            account.get(
                "open_tickets",
                0,
            )
        )

        open_ticket_count = max(
            open_ticket_count,
            account_open_tickets,
        )

        recurring_themes = (
            self._extract_recurring_themes(
                tickets
            )
        )

        seats_utilization = (
            self._calculate_seat_utilization(
                account
            )
        )

        days_to_renewal = (
            self._days_to_renewal(
                account,
                reference_time,
            )
        )

        data_quality_warnings = (
            self._detect_data_quality_warnings(
                account
            )
        )

        health_score = (
            self._calculate_health_score(
                account=account,
                ticket_count=len(tickets),
                open_ticket_count=open_ticket_count,
                p1_count=urgency_counts["P1"],
                p2_count=urgency_counts["P2"],
                recent_ticket_count=len(
                    recent_tickets
                ),
                seats_utilization=seats_utilization,
                days_to_renewal=days_to_renewal,
            )
        )

        health_status = (
            self._status_from_score(
                health_score
            )
        )

        recommended_actions = (
            self._recommended_actions(
                account=account,
                health_status=health_status,
                p1_count=urgency_counts["P1"],
                p2_count=urgency_counts["P2"],
                recent_ticket_count=len(
                    recent_tickets
                ),
                days_to_renewal=days_to_renewal,
                recurring_themes=recurring_themes,
                data_quality_warnings=(
                    data_quality_warnings
                ),
            )
        )

        return AccountHealth(
            account_id=account_id,

            account_name=account.get(
                "company"
            ),

            tam=account.get(
                "tam"
            ),

            plan_tier=account.get(
                "plan_tier"
            ),

            arr_usd=account.get(
                "arr_usd"
            ),

            health_status=health_status,

            health_score=round(
                health_score,
                2,
            ),

            ticket_count_90d=len(
                tickets
            ),

            open_ticket_count=open_ticket_count,

            p1_count=urgency_counts[
                "P1"
            ],

            p2_count=urgency_counts[
                "P2"
            ],

            p3_count=urgency_counts[
                "P3"
            ],

            p4_count=urgency_counts[
                "P4"
            ],

            recent_ticket_count_30d=len(
                recent_tickets
            ),

            seats_utilization_percent=round(
                seats_utilization,
                2,
            ),

            data_quality_warnings=(
                data_quality_warnings
            ),

            usage_trend=account.get(
                "usage_trend"
            ),

            days_to_renewal=days_to_renewal,

            nps_score=account.get(
                "nps_score"
            ),

            escalation_notes=account.get(
                "escalation_notes",
                [],
            ),

            recurring_themes=(
                recurring_themes
            ),

            recommended_actions=(
                recommended_actions
            ),
        )

    @staticmethod
    def _parse_datetime(
        value: str,
    ) -> datetime:

        return datetime.fromisoformat(
            value.replace(
                "Z",
                "+00:00",
            )
        )

    @staticmethod
    def _is_open(
        ticket: dict[str, Any],
    ) -> bool:

        status = str(
            ticket.get(
                "status",
                "",
            )
        ).lower()

        return status not in {
            "closed",
            "resolved",
        }

    @staticmethod
    def _calculate_seat_utilization(
        account: dict[str, Any],
    ) -> float:

        licensed = account.get(
            "seats_licensed",
            0,
        )

        active = account.get(
            "seats_active",
            0,
        )

        if not licensed:
            return 0.0

        return (
            active / licensed
        ) * 100

    @staticmethod
    def _days_to_renewal(
        account: dict[str, Any],
        reference_time: datetime,
    ) -> int | None:

        renewal_date = account.get(
            "renewal_date"
        )

        if not renewal_date:
            return None

        renewal = datetime.fromisoformat(
            renewal_date
        ).replace(
            tzinfo=timezone.utc
        )

        return (
            renewal.date()
            - reference_time.date()
        ).days

    @staticmethod
    def _detect_data_quality_warnings(
        account: dict[str, Any],
    ) -> list[str]:

        warnings = []

        p1_last_30d = int(
            account.get(
                "p1_tickets_last_30d",
                0,
            )
        )

        escalation_notes = account.get(
            "escalation_notes",
            [],
        )

        has_p1_escalation = any(
            "p1" in str(note).lower()
            for note in escalation_notes
        )

        if (
            has_p1_escalation
            and p1_last_30d == 0
        ):
            warnings.append(
                "Account escalation notes mention "
                "P1 tickets but p1_tickets_last_30d "
                "is 0."
            )

        return warnings

    @staticmethod
    def _calculate_health_score(
        account: dict[str, Any],
        ticket_count: int,
        open_ticket_count: int,
        p1_count: int,
        p2_count: int,
        recent_ticket_count: int,
        seats_utilization: float,
        days_to_renewal: int | None,
    ) -> float:

        score = 100.0

        # -------------------------------------------------
        # 1. Open ticket pressure
        # -------------------------------------------------
        if open_ticket_count >= 10:
            score -= 30

        elif open_ticket_count >= 7:
            score -= 25

        elif open_ticket_count >= 4:
            score -= 15

        elif open_ticket_count >= 2:
            score -= 8

        elif open_ticket_count == 1:
            score -= 3

        # -------------------------------------------------
        # 2. Ticket volume
        # -------------------------------------------------
        if ticket_count >= 20:
            score -= 15

        elif ticket_count >= 10:
            score -= 10

        elif ticket_count >= 5:
            score -= 5

        elif ticket_count >= 2:
            score -= 2

        # -------------------------------------------------
        # 3. P1/P2 ticket pressure
        # -------------------------------------------------
        score -= min(
            p1_count * 20,
            30,
        )

        score -= min(
            p2_count * 8,
            20,
        )

        # -------------------------------------------------
        # 4. Recent activity
        # -------------------------------------------------
        if recent_ticket_count >= 10:
            score -= 15

        elif recent_ticket_count >= 5:
            score -= 10

        elif recent_ticket_count >= 2:
            score -= 5

        # -------------------------------------------------
        # 5. Account usage trend
        # -------------------------------------------------
        usage_trend = str(
            account.get(
                "usage_trend",
                "",
            )
        ).lower()

        if usage_trend == "inactive":
            score -= 15

        elif usage_trend in {
            "declining",
            "down",
        }:
            score -= 10

        # -------------------------------------------------
        # 6. Renewal risk
        # -------------------------------------------------
        if days_to_renewal is not None:

            # Renewal already passed.
            if days_to_renewal < 0:
                score -= 25

            # Renewal within one week.
            elif days_to_renewal <= 7:
                score -= 20

            # Renewal within one month.
            elif days_to_renewal <= 30:
                score -= 12

            # Renewal within two months.
            elif days_to_renewal <= 60:
                score -= 6

        # -------------------------------------------------
        # 7. Seat utilization
        # -------------------------------------------------
        if seats_utilization < 50:
            score -= 10

        elif seats_utilization < 70:
            score -= 5

        # -------------------------------------------------
        # 8. Escalation / business risk
        # -------------------------------------------------
        escalation_notes = account.get(
            "escalation_notes",
            [],
        )

        for note in escalation_notes:

            note_lower = str(
                note
            ).lower()

            if "p1" in note_lower:
                score -= 15

            elif (
                "competing vendor"
                in note_lower
                or "competitor"
                in note_lower
            ):
                score -= 15

            else:
                score -= 5

        # -------------------------------------------------
        # 9. NPS
        # -------------------------------------------------
        nps_score = account.get(
            "nps_score"
        )

        if nps_score is not None:

            if nps_score <= 3:
                score -= 10

            elif nps_score <= 6:
                score -= 5

        return max(
            0.0,
            min(
                100.0,
                score,
            ),
        )

    @staticmethod
    def _status_from_score(
        score: float,
    ) -> str:

        if score >= 80:
            return "Healthy"

        if score >= 60:
            return "Watch"

        if score >= 40:
            return "At Risk"

        return "Critical"

    @staticmethod
    def _extract_recurring_themes(
        tickets: list[dict[str, Any]],
    ) -> list[str]:

        if not tickets:
            return []

        themes = Counter()

        for ticket in tickets:

            product = ticket.get(
                "product"
            )

            category = ticket.get(
                "category"
            )

            if product:
                themes[str(
                    product
                )] += 1

            if category:
                themes[str(
                    category
                )] += 1

        return [
            theme
            for theme, count
            in themes.most_common()
            if count >= 2
        ][:5]

    @staticmethod
    def _recommended_actions(
        account: dict[str, Any],
        health_status: str,
        p1_count: int,
        p2_count: int,
        recent_ticket_count: int,
        days_to_renewal: int | None,
        recurring_themes: list[str],
        data_quality_warnings: list[str],
    ) -> list[str]:

        actions = []

        if p1_count > 0:
            actions.append(
                "Review and actively track "
                "P1 incidents."
            )

        if p2_count > 0:
            actions.append(
                "Review recurring P2 issues "
                "with the account."
            )

        if recent_ticket_count >= 5:
            actions.append(
                "Schedule a TAM health review "
                "due to elevated recent "
                "support activity."
            )

        if days_to_renewal is not None:

            if days_to_renewal < 0:
                actions.append(
                    "Escalate the overdue renewal "
                    "with the TAM immediately."
                )

            elif days_to_renewal <= 30:
                actions.append(
                    "Prioritize renewal planning "
                    "and proactive customer outreach."
                )

            elif days_to_renewal <= 60:
                actions.append(
                    "Begin renewal preparation."
                )

        usage_trend = str(
            account.get(
                "usage_trend",
                "",
            )
        ).lower()

        if usage_trend in {
            "inactive",
            "declining",
            "down",
        }:
            actions.append(
                "Review product adoption and "
                "usage with the customer."
            )

        if account.get(
            "escalation_notes"
        ):
            actions.append(
                "Review account escalation "
                "notes with the TAM."
            )

        if recurring_themes:
            actions.append(
                "Investigate recurring support "
                "themes: "
                + ", ".join(
                    recurring_themes[:3]
                )
                + "."
            )

        if data_quality_warnings:
            actions.append(
                "Review data-quality warnings "
                "before finalizing account risk."
            )

        if health_status in {
            "At Risk",
            "Critical",
        }:
            actions.append(
                "Prioritize proactive customer "
                "outreach."
            )

        if not actions:
            actions.append(
                "Continue normal account "
                "monitoring."
            )

        return actions