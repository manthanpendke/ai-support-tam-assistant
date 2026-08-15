from datetime import datetime, timezone

import pytest

from app.services.account_health import (
    AccountHealthService,
)


def test_unknown_account_is_rejected():
    service = AccountHealthService()

    with pytest.raises(
        ValueError,
        match="Account not found",
    ):
        service.analyze(
            "ACCOUNT_DOES_NOT_EXIST",
            reference_time=datetime.now(
                timezone.utc
            ),
        )


def test_account_health_structure():
    service = AccountHealthService()

    # Use one of the real account IDs from the dataset.
    from app.services.data_loader import load_accounts

    account = load_accounts()[0]

    result = service.analyze(
        account["account_id"],
        reference_time=datetime.now(
            timezone.utc
        ),
    )

    assert result.account_id == account["account_id"]

    assert 0 <= result.health_score <= 100

    assert result.health_status in {
        "Healthy",
        "Watch",
        "At Risk",
        "Critical",
    }

    assert result.ticket_count_90d >= 0

    assert result.open_ticket_count >= 0


def test_health_score_is_deterministic():
    service = AccountHealthService()

    from app.services.data_loader import load_accounts

    account = load_accounts()[0]

    reference_time = datetime(
        2026,
        8,
        14,
        tzinfo=timezone.utc,
    )

    first = service.analyze(
        account["account_id"],
        reference_time=reference_time,
    )

    second = service.analyze(
        account["account_id"],
        reference_time=reference_time,
    )

    assert first == second