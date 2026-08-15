from app.services.account_health import (
    AccountHealthService,
)
from app.services.data_loader import (
    load_accounts,
)


def main():

    accounts = load_accounts()

    service = AccountHealthService()

    results = []

    for account in accounts:
        result = service.analyze(
            account["account_id"]
        )

        results.append(result)

    results.sort(
        key=lambda result: (
            result.health_score,
            result.account_id,
        )
    )

    print(
        "\nTASK 2 — ACCOUNT HEALTH OVERVIEW\n"
    )

    for result in results:

        print(
            f"{result.account_id:10} | "
            f"{result.account_name or 'Unknown':30} | "
            f"{result.health_status:10} | "
            f"Score: {result.health_score:6.2f} | "
            f"90d Tickets: {result.ticket_count_90d:3} | "
            f"Open: {result.open_ticket_count:3} | "
            f"Renewal: "
            f"{result.days_to_renewal}"
        )


if __name__ == "__main__":
    main()