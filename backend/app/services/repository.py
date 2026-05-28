from __future__ import annotations

from typing import Any

from app.db.connection import db_session
from app.services.seed_data import seed_database


def _rows_to_dicts(rows: list[Any]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


def load_accounts() -> list[dict[str, Any]]:
    with db_session() as connection:
        rows = connection.execute(
            """
            SELECT account_id, holder_name, vpa, bank_name, city, account_type,
                   created_at, kyc_level, device_id, phone_hash
            FROM accounts
            ORDER BY account_id
            """
        ).fetchall()
        return _rows_to_dicts(rows)


def load_transactions(limit: int | None = None, account_id: str | None = None) -> list[dict[str, Any]]:
    where = ""
    params: list[Any] = []
    if account_id:
        where = "WHERE sender_id = ? OR receiver_id = ?"
        params.extend([account_id, account_id])
    limit_sql = "LIMIT ?" if limit else ""
    if limit:
        params.append(limit)
    with db_session() as connection:
        rows = connection.execute(
            f"""
            SELECT txn_id, sender_id, receiver_id, amount, txn_time, txn_type,
                   channel, city, device_id, status, note, label
            FROM transactions
            {where}
            ORDER BY txn_time DESC
            {limit_sql}
            """,
            params,
        ).fetchall()
        return _rows_to_dicts(rows)


def load_cases() -> list[dict[str, Any]]:
    with db_session() as connection:
        rows = connection.execute(
            """
            SELECT c.case_id, c.account_id, c.opened_at, c.priority, c.status,
                   c.assigned_to, c.summary, a.vpa, a.holder_name
            FROM risk_cases c
            JOIN accounts a ON a.account_id = c.account_id
            ORDER BY c.opened_at DESC
            """
        ).fetchall()
        return _rows_to_dicts(rows)


def reset_seed_data() -> None:
    seed_database(force=True)
