# Data notes

The supplied datasets contain 50 account records and 500 ticket records.

Tickets may reference an account ID that does not exist in `accounts.json`. This is intentional according to the supplied data schema, so the application must handle missing account metadata gracefully.

Task 2 uses the last 90 days of ticket history. The reference time should be made explicit for deterministic evaluation.
