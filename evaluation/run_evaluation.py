import json
from pathlib import Path

from app.agents.factory import build_retriever
from app.agents.triage_agent import TriageAgent
from app.services.account_health import AccountHealthService


PROJECT_ROOT = Path(__file__).resolve().parents[1]

CASES_PATH = (
    PROJECT_ROOT
    / "evaluation"
    / "cases.json"
)


def load_cases():
    with CASES_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def build_triage_agent():
    """
    Build the triage agent using the exact
    retriever configuration used by the
    application's triage demo.
    """

    retriever = build_retriever()

    return TriageAgent(
        retriever=retriever,
        top_k=8,
    )


def run_triage_evaluation(
    cases,
):
    print("\n" + "=" * 70)
    print("TRIAGE EVALUATION")
    print("=" * 70)

    agent = build_triage_agent()

    passed = 0
    total = len(cases)

    for case in cases:

        case_id = case["case_id"]

        try:

            ticket = case["ticket"]

            result = agent.triage(
                subject=ticket["subject"],
                body=ticket["body"],
            )

            expected = case["expected"]

            case_passed = True

            for field, expected_value in expected.items():

                actual_value = getattr(
                    result,
                    field,
                    None,
                )

                if actual_value != expected_value:

                    case_passed = False

                    print(
                        f"\nFAIL: {case_id}"
                    )

                    print(
                        f"  Field: {field}"
                    )

                    print(
                        f"  Expected: {expected_value}"
                    )

                    print(
                        f"  Actual: {actual_value}"
                    )

            if case_passed:

                passed += 1

                print(
                    f"PASS: {case_id}"
                )

        except Exception as exc:

            print(
                f"\nFAIL: {case_id}"
            )

            print(
                f"  Error: "
                f"{type(exc).__name__}: {exc}"
            )

    print(
        f"\nTriage result: "
        f"{passed}/{total} passed"
    )

    return passed, total


def run_account_health_evaluation(
    account_ids,
):
    print("\n" + "=" * 70)
    print("ACCOUNT HEALTH EVALUATION")
    print("=" * 70)

    service = AccountHealthService()

    passed = 0
    total = len(account_ids)

    for account_id in account_ids:

        try:

            # AccountHealthService exposes analyze()
            # as the public account-health operation.
            result = service.analyze(
                account_id=account_id,
            )

            case_passed = True

            # -------------------------------------------------
            # Account ID
            # -------------------------------------------------

            if result.account_id != account_id:

                case_passed = False

                print(
                    f"  Invalid account_id: "
                    f"{result.account_id}"
                )

            # -------------------------------------------------
            # Health score
            # -------------------------------------------------

            if not (
                0 <= result.health_score <= 100
            ):

                case_passed = False

                print(
                    f"  Invalid health score: "
                    f"{result.health_score}"
                )

            # -------------------------------------------------
            # Health status
            # -------------------------------------------------

            if result.health_status not in {
                "Healthy",
                "Watch",
                "At Risk",
                "Critical",
            }:

                case_passed = False

                print(
                    f"  Invalid health status: "
                    f"{result.health_status}"
                )

            # -------------------------------------------------
            # Ticket counts
            # -------------------------------------------------

            count_fields = [
                "ticket_count_90d",
                "open_ticket_count",
                "p1_count",
                "p2_count",
                "p3_count",
                "p4_count",
                "recent_ticket_count_30d",
            ]

            for field in count_fields:

                value = getattr(
                    result,
                    field,
                )

                if value < 0:

                    case_passed = False

                    print(
                        f"  Invalid {field}: "
                        f"{value}"
                    )

            # -------------------------------------------------
            # Seat utilization
            # -------------------------------------------------

            if not (
                0
                <= result.seats_utilization_percent
                <= 100
            ):

                case_passed = False

                print(
                    "  Invalid seat utilization: "
                    f"{result.seats_utilization_percent}"
                )

            # -------------------------------------------------
            # Data quality warnings
            # -------------------------------------------------

            if not isinstance(
                result.data_quality_warnings,
                list,
            ):

                case_passed = False

                print(
                    "  data_quality_warnings "
                    "must be a list"
                )

            # -------------------------------------------------
            # Result
            # -------------------------------------------------

            if case_passed:

                passed += 1

                print(
                    f"PASS: {account_id}"
                )

            else:

                print(
                    f"FAIL: {account_id}"
                )

        except Exception as exc:

            print(
                f"FAIL: {account_id}"
            )

            print(
                f"  Error: "
                f"{type(exc).__name__}: {exc}"
            )

    print(
        f"\nAccount Health result: "
        f"{passed}/{total} passed"
    )

    return passed, total


def main():

    cases = load_cases()

    triage_passed, triage_total = (
        run_triage_evaluation(
            cases["triage_cases"]
        )
    )

    health_passed, health_total = (
        run_account_health_evaluation(
            cases["account_health_cases"]
        )
    )

    total_passed = (
        triage_passed
        + health_passed
    )

    total_cases = (
        triage_total
        + health_total
    )

    print("\n" + "=" * 70)
    print("OVERALL EVALUATION")
    print("=" * 70)

    print(
        f"Passed: "
        f"{total_passed}/{total_cases}"
    )

    percentage = (
        total_passed / total_cases * 100
        if total_cases
        else 0
    )

    print(
        f"Score: {percentage:.1f}%"
    )

    if total_passed == total_cases:

        print(
            "\nSTATUS: PASS"
        )

    else:

        print(
            "\nSTATUS: REVIEW FAILURES"
        )


if __name__ == "__main__":
    main()