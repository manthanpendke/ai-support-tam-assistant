import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from app.config import ACCOUNTS_PATH, TICKETS_PATH


def _load_json(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON array in {path}")

    return data


def load_tickets() -> list[dict[str, Any]]:
    return _load_json(TICKETS_PATH)


def load_accounts() -> list[dict[str, Any]]:
    return _load_json(ACCOUNTS_PATH)


def get_account_map() -> dict[str, dict[str, Any]]:
    return {account["account_id"]: account for account in load_accounts()}


def get_ticket_map() -> dict[str, dict[str, Any]]:
    return {ticket["ticket_id"]: ticket for ticket in load_tickets()}


def get_account(account_id: str) -> dict[str, Any] | None:
    return get_account_map().get(account_id)


def get_ticket(ticket_id: str) -> dict[str, Any] | None:
    return get_ticket_map().get(ticket_id)


def get_account_tickets(
    account_id: str,
    days: int = 90,
    reference_time: datetime | None = None,
) -> list[dict[str, Any]]:
    """Return tickets for an account from the previous `days`.

    If reference_time is omitted, current UTC time is used, matching the
    assignment's data-schema example.
    """
    reference_time = reference_time or datetime.now(timezone.utc)
    cutoff = reference_time - timedelta(days=days)

    result = []
    for ticket in load_tickets():
        if ticket.get("account_id") != account_id:
            continue

        created_at = datetime.fromisoformat(
            ticket["created_at"].replace("Z", "+00:00")
        )
        if created_at > cutoff:
            result.append(ticket)

    return sorted(result, key=lambda t: (t["created_at"], t["ticket_id"]))


def dataset_summary() -> dict[str, Any]:
    tickets = load_tickets()
    accounts = load_accounts()

    ticket_account_ids = {t["account_id"] for t in tickets}
    account_ids = {a["account_id"] for a in accounts}

    return {
        "accounts": len(accounts),
        "tickets": len(tickets),
        "unique_ticket_account_ids": len(ticket_account_ids),
        "ticket_account_ids_without_account_record": len(
            ticket_account_ids - account_ids
        ),
        "duplicate_account_ids": len(accounts) - len(account_ids),
        "duplicate_ticket_ids": len(tickets) - len({t["ticket_id"] for t in tickets}),
    }
