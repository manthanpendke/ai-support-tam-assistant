import json
import re

from app.models.account_health import AccountHealth
from app.models.tam_summary import TAMSummary
from app.services.data_loader import get_account_tickets
from app.services.llm_client import GroqLLMClient


class TAMAgent:

    def __init__(
        self,
        llm_client: GroqLLMClient | None = None,
    ):
        self.llm_client = (
            llm_client
            or GroqLLMClient()
        )

    @staticmethod
    def _parse_json_response(
        raw_response: str,
    ) -> dict:

        if not raw_response:
            raise ValueError(
                "Groq returned an empty response."
            )

        cleaned = raw_response.strip()

        cleaned = re.sub(
            r"^```json\s*",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )

        cleaned = re.sub(
            r"^```\s*",
            "",
            cleaned,
        )

        cleaned = re.sub(
            r"\s*```$",
            "",
            cleaned,
        )

        cleaned = cleaned.strip()

        try:
            parsed = json.loads(cleaned)

        except json.JSONDecodeError as exc:
            raise ValueError(
                "Groq returned invalid JSON.\n"
                f"Raw response:\n{raw_response}"
            ) from exc

        if not isinstance(parsed, dict):
            raise ValueError(
                "Groq response must be a JSON object."
            )

        return parsed

    def analyze(
        self,
        account_health: AccountHealth,
        account: dict,
    ) -> TAMSummary:

        # -------------------------------------------------
        # Load account ticket history.
        # -------------------------------------------------

        tickets = get_account_tickets(
            account_health.account_id,
            days=90,
        )

        # -------------------------------------------------
        # Keep only required ticket fields.
        # -------------------------------------------------

        ticket_context = []

        for ticket in tickets:
            ticket_context.append(
                {
                    "ticket_id": ticket.get(
                        "ticket_id"
                    ),
                    "subject": ticket.get(
                        "subject"
                    ),
                    "body": ticket.get(
                        "body"
                    ),
                    "product": ticket.get(
                        "product"
                    ),
                    "product_area": ticket.get(
                        "product_area"
                    ),
                    "category": ticket.get(
                        "category"
                    ),
                    "urgency": ticket.get(
                        "urgency"
                    ),
                    "status": ticket.get(
                        "status"
                    ),
                    "created_at": ticket.get(
                        "created_at"
                    ),
                    "tags": ticket.get(
                        "tags",
                        [],
                    ),
                    "satisfaction_score": ticket.get(
                        "satisfaction_score"
                    ),
                }
            )

        # -------------------------------------------------
        # Deterministic account context.
        # -------------------------------------------------

        account_context = {
            "account_id": account_health.account_id,

            "account_name": (
                account_health.account_name
            ),

            "tam": account_health.tam,

            "plan_tier": (
                account_health.plan_tier
            ),

            "arr_usd": account_health.arr_usd,

            "health_status": (
                account_health.health_status
            ),

            "health_score": (
                account_health.health_score
            ),

            "ticket_count_90d": (
                account_health.ticket_count_90d
            ),

            "open_ticket_count": (
                account_health.open_ticket_count
            ),

            "p1_count": (
                account_health.p1_count
            ),

            "p2_count": (
                account_health.p2_count
            ),

            "p3_count": (
                account_health.p3_count
            ),

            "p4_count": (
                account_health.p4_count
            ),

            "recent_ticket_count_30d": (
                account_health.recent_ticket_count_30d
            ),

            "seats_utilization_percent": (
                account_health.seats_utilization_percent
            ),

            "usage_trend": (
                account_health.usage_trend
            ),

            "days_to_renewal": (
                account_health.days_to_renewal
            ),

            "nps_score": (
                account_health.nps_score
            ),

            "escalation_notes": (
                account_health.escalation_notes
            ),

            "recurring_themes": (
                account_health.recurring_themes
            ),

            "recommended_actions": (
                account_health.recommended_actions
            ),

            "data_quality_warnings": (
                account_health.data_quality_warnings
            ),

            "products": account.get(
                "products",
                [],
            ),

            "integrations_active": account.get(
                "integrations_active",
                [],
            ),

            "region": account.get(
                "region"
            ),

            "industry": account.get(
                "industry"
            ),

            "customer_since": account.get(
                "customer_since"
            ),

            "primary_contact": account.get(
                "primary_contact"
            ),

            "tickets_last_90_days": ticket_context,
        }

        # -------------------------------------------------
        # LLM instructions.
        # -------------------------------------------------

        system_prompt = """
You are an experienced Technical Account Manager.

Your task is to create an executive-facing TAM account
brief using ONLY the supplied account data and ticket
history.

The output contains:

1. Executive Summary
2. Open Risks & Flagged Issues
3. Recommended Talking Points

IMPORTANT FACTUAL RULES:

1. health_score is authoritative.

2. health_status is authoritative.

3. DO NOT recalculate health_score.

4. DO NOT invent customer facts.

5. Use ONLY information present in the supplied data.

6. The structured ticket counts are authoritative.

7. Do not infer current ticket counts from escalation notes.

8. If p1_count is 0, there is NO current P1 ticket.

9. If p2_count is 0, there is NO current P2 ticket.

10. If p3_count is 0, there is NO current P3 ticket.

11. If p4_count is 0, there is NO current P4 ticket.

12. Historical escalation notes may be discussed as
    historical information.

13. Never convert historical escalation notes into
    current ticket counts.

14. open_ticket_count is authoritative.

15. ticket_count_90d is authoritative.

16. DO NOT mention P1, P2, P3, or P4 in any narrative
    field unless the corresponding deterministic count
    is greater than zero.

17. DO NOT invent an exact ticket priority count.

18. DO NOT state that there is a current priority ticket
    unless the supplied structured count confirms it.

19. Prefer general wording such as:
    "support backlog",
    "support workload",
    "support escalation history",
    "open support issues".

20. Do not state exact ticket counts in generated
    narrative fields. Python owns deterministic
    ticket-count facts.

21. For ticket-derived risks, provide a direct quote
    copied exactly from the ticket subject or body.

22. NEVER invent or paraphrase evidence_quote.

23. If no ticket supports a risk, ticket_id and
    evidence_quote must be null.

24. Account-level risks such as renewal risk,
    competitive vendor evaluation, adoption risk,
    and usage risk may be identified directly from
    account-level data.

25. Recommended talking points must be actionable
    discussion topics for the TAM.

26. Data-quality warnings must be preserved exactly.

27. Do not resolve contradictions by guessing.

28. Keep executive_summary between 3 and 5 sentences.

29. Return ONLY valid JSON.

30. Do not wrap the JSON in Markdown.

The JSON MUST contain exactly:

{
  "account_id": "string",

  "executive_summary": "string",

  "open_risks": [
    {
      "flag": "string",
      "reason": "string",
      "ticket_id": "string or null",
      "evidence_quote": "string or null"
    }
  ],

  "talking_points": [
    "string"
  ],

  "top_risks": [
    "string"
  ],

  "recommended_actions": [
    "string"
  ],

  "renewal_risk": "Low|Medium|High|Unknown",

  "customer_sentiment":
    "Positive|Neutral|At Risk|Unknown",

  "data_quality_warnings": [
    "string"
  ]
}

RENEWAL RISK:

High:
- renewal overdue or within 30 days AND meaningful
  risk signals exist.

Medium:
- renewal within 60 days OR moderate risk.

Low:
- renewal sufficiently distant and no significant
  renewal concern.

Unknown:
- renewal information unavailable.

CUSTOMER SENTIMENT:

At Risk:
- significant escalation, adoption, support,
  renewal, or competitive risk.

Positive:
- healthy account with positive signals.

Neutral:
- no strong positive or negative signal.

Unknown:
- insufficient information.

TICKET EVIDENCE:

When identifying a churn or escalation risk from a
ticket:

- Use the ticket_id from the supplied ticket.
- Copy a short direct quote from the ticket subject
  or body.
- Do not alter the quote.
- Do not invent a quote.

IMPORTANT:

The LLM is responsible for interpretation.

Python is responsible for deterministic facts.

Do not generate deterministic ticket counts or
unsupported priority claims in narrative text.
"""

        user_prompt = f"""
Analyze this customer account.

ACCOUNT DATA:

{json.dumps(
    account_context,
    indent=2,
)}

AUTHORITATIVE DETERMINISTIC VALUES:

health_score:
{account_health.health_score}

health_status:
{account_health.health_status}

ticket_count_90d:
{account_health.ticket_count_90d}

open_ticket_count:
{account_health.open_ticket_count}

p1_count:
{account_health.p1_count}

p2_count:
{account_health.p2_count}

p3_count:
{account_health.p3_count}

p4_count:
{account_health.p4_count}

recent_ticket_count_30d:
{account_health.recent_ticket_count_30d}

days_to_renewal:
{account_health.days_to_renewal}

data_quality_warnings:
{json.dumps(
    account_health.data_quality_warnings,
    indent=2,
)}

IMPORTANT:

The deterministic values above are authoritative.

Do not contradict them.

Do not infer current P1/P2/P3/P4 tickets from
historical escalation notes.

Do not mention a ticket priority in narrative text
unless the corresponding structured count is greater
than zero.

Do not generate exact ticket counts in narrative
text.

For ticket-derived risks, evidence_quote MUST be
copied exactly from the supplied ticket subject or
body.

Do not invent ticket evidence.

Return ONLY valid JSON.
"""

        # -------------------------------------------------
        # Generate LLM response.
        # -------------------------------------------------

        raw_response = self.llm_client.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        parsed = self._parse_json_response(
            raw_response
        )

        # -------------------------------------------------
        # Protect deterministic fields.
        # -------------------------------------------------

        parsed["account_id"] = (
            account_health.account_id
        )

        parsed["data_quality_warnings"] = (
            account_health.data_quality_warnings
        )

        # -------------------------------------------------
        # Normalize string fields.
        # -------------------------------------------------

        if "renewal_risk" in parsed:
            parsed["renewal_risk"] = (
                str(
                    parsed["renewal_risk"]
                ).strip()
            )

        if "customer_sentiment" in parsed:
            parsed["customer_sentiment"] = (
                str(
                    parsed["customer_sentiment"]
                ).strip()
            )

        # -------------------------------------------------
        # Build lookup of actual tickets.
        # -------------------------------------------------

        ticket_lookup = {
            ticket.get("ticket_id"): ticket
            for ticket in tickets
        }

        # -------------------------------------------------
        # Validate open risk evidence.
        # -------------------------------------------------

        validated_risks = []

        for risk in parsed.get(
            "open_risks",
            [],
        ):

            if not isinstance(
                risk,
                dict,
            ):
                continue

            ticket_id = risk.get(
                "ticket_id"
            )

            evidence_quote = risk.get(
                "evidence_quote"
            )

            if ticket_id:

                ticket = ticket_lookup.get(
                    ticket_id
                )

                # Unknown ticket ID.
                if ticket is None:

                    risk["ticket_id"] = None
                    risk["evidence_quote"] = None

                else:

                    ticket_text = " ".join(
                        [
                            str(
                                ticket.get(
                                    "subject",
                                    "",
                                )
                            ),
                            str(
                                ticket.get(
                                    "body",
                                    "",
                                )
                            ),
                        ]
                    )

                    # Evidence must literally occur
                    # in the real ticket.
                    if (
                        not evidence_quote
                        or evidence_quote
                        not in ticket_text
                    ):
                        risk["evidence_quote"] = None

            validated_risks.append(
                risk
            )

        parsed["open_risks"] = (
            validated_risks
        )

        # -------------------------------------------------
        # Final deterministic priority protection.
        #
        # This is a safety layer in case the LLM ignores
        # the prompt.
        # -------------------------------------------------

        def protect_ticket_priority_claims(
            text: str,
        ) -> str:

            if not isinstance(
                text,
                str,
            ):
                return text

            counts = {
                "P1": account_health.p1_count,
                "P2": account_health.p2_count,
                "P3": account_health.p3_count,
                "P4": account_health.p4_count,
            }

            for priority, count in counts.items():

                if count > 0:
                    continue

                # "including 1 P2 ticket"
                text = re.sub(
                    rf"\bincluding\s+\d+\s+"
                    rf"{priority}\s+tickets?\b",
                    "including support tickets",
                    text,
                    flags=re.IGNORECASE,
                )

                # "with 1 P2 ticket"
                text = re.sub(
                    rf"\bwith\s+\d+\s+"
                    rf"{priority}\s+tickets?\b",
                    "with support tickets",
                    text,
                    flags=re.IGNORECASE,
                )

                # "with 1 being a P2 ticket"
                text = re.sub(
                    rf"\bwith\s+\d+\s+being\s+"
                    rf"(?:a|an)\s+{priority}\s+ticket\b",
                    "with a support ticket",
                    text,
                    flags=re.IGNORECASE,
                )

                # "has 1 P2 ticket"
                text = re.sub(
                    rf"\bhas\s+\d+\s+"
                    rf"{priority}\s+tickets?\b",
                    "has support tickets",
                    text,
                    flags=re.IGNORECASE,
                )

                # "has a P2 ticket"
                text = re.sub(
                    rf"\bhas\s+(?:a|an)\s+"
                    rf"{priority}\s+ticket\b",
                    "has a support ticket",
                    text,
                    flags=re.IGNORECASE,
                )

                # "current P2 ticket"
                text = re.sub(
                    rf"\bcurrent\s+"
                    rf"{priority}\s+tickets?\b",
                    "current support tickets",
                    text,
                    flags=re.IGNORECASE,
                )

                # "active P2 ticket"
                text = re.sub(
                    rf"\bactive\s+"
                    rf"{priority}\s+tickets?\b",
                    "active support tickets",
                    text,
                    flags=re.IGNORECASE,
                )

                # "recurring P2 issues"
                text = re.sub(
                    rf"\brecurring\s+"
                    rf"{priority}\s+(?:issues?|tickets?)\b",
                    "recurring support issues",
                    text,
                    flags=re.IGNORECASE,
                )

                # "P2 issues" / "P2 tickets"
                text = re.sub(
                    rf"\b{priority}\s+"
                    rf"(?:tickets?|issues?)\b",
                    "support issues",
                    text,
                    flags=re.IGNORECASE,
                )

            text = re.sub(
                r"\s+",
                " ",
                text,
            ).strip()

            return text

        # -------------------------------------------------
        # Apply safety layer to all narrative fields.
        # -------------------------------------------------

        parsed["executive_summary"] = (
            protect_ticket_priority_claims(
                parsed.get(
                    "executive_summary",
                    "",
                )
            )
        )

        parsed["top_risks"] = [
            protect_ticket_priority_claims(
                risk
            )
            for risk in parsed.get(
                "top_risks",
                [],
            )
        ]

        parsed["recommended_actions"] = [
            protect_ticket_priority_claims(
                action
            )
            for action in parsed.get(
                "recommended_actions",
                [],
            )
        ]

        parsed["talking_points"] = [
            protect_ticket_priority_claims(
                point
            )
            for point in parsed.get(
                "talking_points",
                [],
            )
        ]

        # -------------------------------------------------
        # Validate final structured response.
        # -------------------------------------------------

        return TAMSummary.model_validate(
            parsed
        )