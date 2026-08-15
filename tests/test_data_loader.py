from app.services.data_loader import (
    dataset_summary,
    get_account,
    get_account_tickets,
    get_ticket,
    load_accounts,
    load_tickets,
)


def test_dataset_sizes():
    assert len(load_accounts()) == 50
    assert len(load_tickets()) == 500


def test_ids_are_unique():
    accounts = load_accounts()
    tickets = load_tickets()

    assert len({a["account_id"] for a in accounts}) == len(accounts)
    assert len({t["ticket_id"] for t in tickets}) == len(tickets)


def test_lookup_functions():
    accounts = load_accounts()
    tickets = load_tickets()

    assert get_account(accounts[0]["account_id"]) is not None
    assert get_ticket(tickets[0]["ticket_id"]) is not None


def test_missing_account_is_handled():
    # The supplied schema explicitly allows ticket/account mismatches.
    tickets = load_tickets()
    accounts = load_accounts()
    account_ids = {a["account_id"] for a in accounts}

    missing = next(
        t["account_id"] for t in tickets if t["account_id"] not in account_ids
    )

    assert get_account(missing) is None


def test_account_ticket_filter():
    tickets = load_tickets()
    account_id = tickets[0]["account_id"]

    result = get_account_tickets(account_id, days=90)

    assert all(t["account_id"] == account_id for t in result)


def test_summary():
    summary = dataset_summary()

    assert summary["accounts"] == 50
    assert summary["tickets"] == 500
    assert summary["duplicate_account_ids"] == 0
    assert summary["duplicate_ticket_ids"] == 0
