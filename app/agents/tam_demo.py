import json

from app.services.account_health import (
    AccountHealthService,
)
from app.services.data_loader import (
    get_account,
)
from app.agents.tam_agent import TAMAgent


def main():

    account_id = "ACC-3336"

    account = get_account(
        account_id
    )

    if account is None:
        raise ValueError(
            f"Account not found: {account_id}"
        )

    health_service = (
        AccountHealthService()
    )

    health = health_service.analyze(
        account_id
    )

    agent = TAMAgent()

    result = agent.analyze(
        account_health=health,
        account=account,
    )

    print(
        "\nTASK 3 — TAM EXECUTIVE SUMMARY\n"
    )

    print(
        json.dumps(
            result.model_dump(),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()