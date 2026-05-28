from app.db.connection import db_session
from app.services.seed_data import seed_database


SCHEMA = """
CREATE TABLE IF NOT EXISTS accounts (
    account_id TEXT PRIMARY KEY,
    holder_name TEXT NOT NULL,
    vpa TEXT NOT NULL UNIQUE,
    bank_name TEXT NOT NULL,
    city TEXT NOT NULL,
    account_type TEXT NOT NULL,
    created_at TEXT NOT NULL,
    kyc_level TEXT NOT NULL,
    device_id TEXT NOT NULL,
    phone_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS transactions (
    txn_id TEXT PRIMARY KEY,
    sender_id TEXT NOT NULL,
    receiver_id TEXT NOT NULL,
    amount REAL NOT NULL,
    txn_time TEXT NOT NULL,
    txn_type TEXT NOT NULL,
    channel TEXT NOT NULL,
    city TEXT NOT NULL,
    device_id TEXT NOT NULL,
    status TEXT NOT NULL,
    note TEXT NOT NULL,
    label TEXT NOT NULL DEFAULT 'legit',
    FOREIGN KEY(sender_id) REFERENCES accounts(account_id),
    FOREIGN KEY(receiver_id) REFERENCES accounts(account_id)
);

CREATE TABLE IF NOT EXISTS risk_cases (
    case_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    opened_at TEXT NOT NULL,
    priority TEXT NOT NULL,
    status TEXT NOT NULL,
    assigned_to TEXT NOT NULL,
    summary TEXT NOT NULL,
    FOREIGN KEY(account_id) REFERENCES accounts(account_id)
);

CREATE INDEX IF NOT EXISTS idx_transactions_sender ON transactions(sender_id);
CREATE INDEX IF NOT EXISTS idx_transactions_receiver ON transactions(receiver_id);
CREATE INDEX IF NOT EXISTS idx_transactions_time ON transactions(txn_time);
CREATE INDEX IF NOT EXISTS idx_transactions_label ON transactions(label);
"""


def create_schema() -> None:
    with db_session() as connection:
        connection.executescript(SCHEMA)


def initialize_database(seed: bool = True) -> None:
    create_schema()
    if seed:
        seed_database()
