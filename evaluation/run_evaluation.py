import json
from datetime import datetime, timezone
from pathlib import Path

from app.agents.factory import build_retriever
from app.agents.triage_agent import TriageAgent
from app.services.account_health import AccountHealthService
from app.services.data_loader import get_account


PROJECT_ROOT = Path(__file__).resolve().parents[1]

CASES_PATH = PROJECT_ROOT / "evaluation" / "cases.json"
REPORT_PATH = PROJECT_ROOT / "evaluation" / "eval_report.json"


def load_cases():
    with CASES_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def build_triage_agent():
    retriever = build_retriever()

    return TriageAgent(
        retriever=retriever,
        top_k=8,
    )


def evaluate_triage_case(
    agent,
    case,
):
    case_id = case["case_id"]
    ticket = case["ticket"]
    expected = case["expected"]

    failures = []
    checked_fields = len(expected)

    try:
        result = agent.triage(
            subject=ticket["subject"],
            body=ticket["body"],
        )

        for field, expected_value in expected.items():

            actual_value = getattr(
                result,
                field,
                None,
            )

            if actual_value != expected_value:

                failures.append(
                    {
                        "field": field,
                        "expected": expected_value,
                        "actual": actual_value,
                    }
                )

        if checked_fields == 0:
            quality_score = 1.0
        else:
            quality_score = (
                checked_fields - len(failures)
            ) / checked_fields

        return {
            "case_id": case_id,
            "task": "triage",
            "passed": len(failures) == 0,
            "quality_score": round(
                quality_score,
                2,
            ),
            "checked_fields": checked_fields,
            "failures": failures,
        }

    except Exception as exc:

        return {
            "case_id": case_id,
            "task": "triage",
            "passed": False,
            "quality_score": 0.0,
            "checked_fields": checked_fields,
            "failures": [
                {
                    "error": (
                        f"{type(exc).__name__}: "
                        f"{exc}"
                    )
                }
            ],
        }


def run_triage_evaluation(cases):
    print("\n" + "=" * 70)
    print("TRIAGE EVALUATION")
    print("=" * 70)

    agent = build_triage_agent()

    results = []

    for case in cases:

        result = evaluate_triage_case(
            agent,
            case,
        )

        results.append(result)

        if result["passed"]:

            print(
                f"PASS: {result['case_id']} "
                f"(score={result['quality_score']:.2f})"
            )

        else:

            print(
                f"\nFAIL: {result['case_id']} "
                f"(score={result['quality_score']:.2f})"
            )

            for failure in result["failures"]:
                print(
                    f"  {failure}"
                )

    passed = sum(
        1
        for result in results
        if result["passed"]
    )

    total = len(results)

    average_score = (
        sum(
            result["quality_score"]
            for result in results
        )
        / total
        if total
        else 0.0
    )

    print(
        f"\nTriage result: "
        f"{passed}/{total} passed"
    )

    print(
        f"Triage quality score: "
        f"{average_score:.2f}"
    )

    return {
        "passed": passed,
        "total": total,
        "average_quality_score": round(
            average_score,
            2,
        ),
        "cases": results,
    }


def evaluate_account_health_case(
    service,
    account_id,
):
    failures = []

    try:

        account = get_account(
            account_id
        )

        if account is None:

            return {
                "case_id": account_id,
                "task": "account_health",
                "passed": False,
                "quality_score": 0.0,
                "checks": 0,
                "failures": [
                    {
                        "error": "Account not found"
                    }
                ],
            }

        result = service.analyze(
             account_id=account_id,
            )

        checks = []

        # Account ID
        checks.append(
            (
                "account_id",
                result.account_id == account_id,
            )
        )

        # Health score
        checks.append(
            (
                "health_score",
                0
                <= result.health_score
                <= 100,
            )
        )

        # Health status
        checks.append(
            (
                "health_status",
                result.health_status
                in {
                    "Healthy",
                    "Watch",
                    "At Risk",
                    "Critical",
                },
            )
        )

        # Ticket counts
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

            checks.append(
                (
                    field,
                    value >= 0,
                )
            )

        # Seat utilization
        checks.append(
            (
                "seats_utilization_percent",
                0
                <= result.seats_utilization_percent
                <= 100,
            )
        )

        # Data quality warnings
        checks.append(
            (
                "data_quality_warnings",
                isinstance(
                    result.data_quality_warnings,
                    list,
                ),
            )
        )

        for field, passed in checks:

            if not passed:

                failures.append(
                    {
                        "field": field,
                        "error": "Acceptance check failed",
                    }
                )

        total_checks = len(checks)

        quality_score = (
            (
                total_checks
                - len(failures)
            )
            / total_checks
            if total_checks
            else 0.0
        )

        return {
            "case_id": account_id,
            "task": "account_health",
            "passed": len(failures) == 0,
            "quality_score": round(
                quality_score,
                2,
            ),
            "checks": total_checks,
            "failures": failures,
        }

    except Exception as exc:

        return {
            "case_id": account_id,
            "task": "account_health",
            "passed": False,
            "quality_score": 0.0,
            "checks": 0,
            "failures": [
                {
                    "error": (
                        f"{type(exc).__name__}: "
                        f"{exc}"
                    )
                }
            ],
        }


def run_account_health_evaluation(
    account_ids,
):
    print("\n" + "=" * 70)
    print("ACCOUNT HEALTH EVALUATION")
    print("=" * 70)

    service = AccountHealthService()

    results = []

    for account_id in account_ids:

        result = evaluate_account_health_case(
            service,
            account_id,
        )

        results.append(result)

        if result["passed"]:

            print(
                f"PASS: {result['case_id']} "
                f"(score={result['quality_score']:.2f})"
            )

        else:

            print(
                f"\nFAIL: {result['case_id']} "
                f"(score={result['quality_score']:.2f})"
            )

            for failure in result["failures"]:
                print(
                    f"  {failure}"
                )

    passed = sum(
        1
        for result in results
        if result["passed"]
    )

    total = len(results)

    average_score = (
        sum(
            result["quality_score"]
            for result in results
        )
        / total
        if total
        else 0.0
    )

    print(
        f"\nAccount Health result: "
        f"{passed}/{total} passed"
    )

    print(
        f"Account Health quality score: "
        f"{average_score:.2f}"
    )

    return {
        "passed": passed,
        "total": total,
        "average_quality_score": round(
            average_score,
            2,
        ),
        "cases": results,
    }


def build_report(
    triage_result,
    account_health_result,
):
    total_passed = (
        triage_result["passed"]
        + account_health_result["passed"]
    )

    total_cases = (
        triage_result["total"]
        + account_health_result["total"]
    )

    overall_quality_score = (
        (
            triage_result[
                "average_quality_score"
            ]
            + account_health_result[
                "average_quality_score"
            ]
        )
        / 2
        if total_cases
        else 0.0
    )

    return {
        "evaluation_timestamp": (
            datetime.now(
                timezone.utc
            ).isoformat()
        ),
        "summary": {
            "passed": total_passed,
            "total": total_cases,
            "pass_rate": round(
                total_passed / total_cases,
                3,
            )
            if total_cases
            else 0.0,
            "overall_quality_score": round(
                overall_quality_score,
                2,
            ),
            "status": (
                "PASS"
                if total_passed == total_cases
                else "REVIEW FAILURES"
            ),
        },
        "triage": triage_result,
        "account_health": account_health_result,
    }


def main():

    cases = load_cases()

    triage_result = run_triage_evaluation(
        cases["triage_cases"]
    )

    account_health_result = (
        run_account_health_evaluation(
            cases["account_health_cases"]
        )
    )

    report = build_report(
        triage_result,
        account_health_result,
    )

    REPORT_PATH.write_text(
        json.dumps(
            report,
            indent=2,
        ),
        encoding="utf-8",
    )

    print("\n" + "=" * 70)
    print("OVERALL EVALUATION")
    print("=" * 70)

    print(
        f"Passed: "
        f"{report['summary']['passed']}/"
        f"{report['summary']['total']}"
    )

    print(
        f"Pass rate: "
        f"{report['summary']['pass_rate'] * 100:.1f}%"
    )

    print(
        f"Overall quality score: "
        f"{report['summary']['overall_quality_score']:.2f}"
    )

    print(
        f"STATUS: "
        f"{report['summary']['status']}"
    )

    print(
        f"\nEvaluation report written to:"
        f"\n{REPORT_PATH}"
    )


if __name__ == "__main__":
    main()