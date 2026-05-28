from __future__ import annotations

import random
from datetime import datetime, timedelta

from app.db.connection import db_session


BANKS = ["SBI", "HDFC", "ICICI", "Axis", "Kotak", "PNB", "BOB", "Canara"]
CITIES = ["Delhi", "Noida", "Gurugram", "Mumbai", "Bengaluru", "Pune", "Jaipur", "Lucknow"]
CHANNELS = ["UPI_APP", "QR_SCAN", "COLLECT_REQUEST", "PAYMENT_LINK", "WEB_CHECKOUT"]
TYPES = ["P2P", "P2M", "REFUND", "COLLECT"]


def _account(account_id: str, index: int, profile: str = "consumer") -> tuple:
    bank = BANKS[index % len(BANKS)]
    city = CITIES[(index * 3) % len(CITIES)]
    device_suffix = index if profile != "mule" else index % 7
    phone_suffix = (index * 17) % 997
    created = datetime(2025, 1, 1) + timedelta(days=index % 280)
    return (
        account_id,
        f"{profile.title()} User {index:03d}",
        f"{account_id.lower()}@{bank.lower()}",
        bank,
        city,
        profile,
        created.isoformat(),
        "MINIMUM" if profile in {"mule", "new"} else "FULL",
        f"DEV-{device_suffix:04d}",
        f"PH-{phone_suffix:04d}",
    )


def _txn(
    txn_id: str,
    sender: str,
    receiver: str,
    amount: float,
    txn_time: datetime,
    txn_type: str = "P2P",
    channel: str = "UPI_APP",
    city: str = "Delhi",
    device_id: str = "DEV-0001",
    status: str = "SUCCESS",
    note: str = "regular transfer",
    label: str = "legit",
) -> tuple:
    return (
        txn_id,
        sender,
        receiver,
        round(amount, 2),
        txn_time.isoformat(),
        txn_type,
        channel,
        city,
        device_id,
        status,
        note,
        label,
    )


def seed_database(force: bool = False) -> None:
    random.seed(42)
    with db_session() as connection:
        existing = connection.execute("SELECT COUNT(*) FROM accounts").fetchone()[0]
        if existing and not force:
            return

        connection.execute("DELETE FROM risk_cases")
        connection.execute("DELETE FROM transactions")
        connection.execute("DELETE FROM accounts")

        accounts = []
        for idx in range(1, 91):
            accounts.append(_account(f"ACC{idx:04d}", idx, "consumer"))
        for idx in range(91, 111):
            accounts.append(_account(f"ACC{idx:04d}", idx, "merchant"))
        for idx in range(111, 126):
            accounts.append(_account(f"ACC{idx:04d}", idx, "mule"))
        for idx in range(126, 136):
            accounts.append(_account(f"ACC{idx:04d}", idx, "new"))

        connection.executemany(
            """
            INSERT INTO accounts (
                account_id, holder_name, vpa, bank_name, city, account_type,
                created_at, kyc_level, device_id, phone_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            accounts,
        )

        base = datetime(2026, 5, 1, 9, 0, 0)
        transactions = []
        txn_counter = 1

        def next_id() -> str:
            nonlocal txn_counter
            value = f"TXN{txn_counter:06d}"
            txn_counter += 1
            return value

        consumers = [f"ACC{i:04d}" for i in range(1, 91)]
        merchants = [f"ACC{i:04d}" for i in range(91, 111)]
        mules = [f"ACC{i:04d}" for i in range(111, 126)]
        new_accounts = [f"ACC{i:04d}" for i in range(126, 136)]

        for day in range(24):
            for _ in range(24):
                sender = random.choice(consumers)
                receiver = random.choice(merchants if random.random() < 0.65 else consumers)
                if sender == receiver:
                    continue
                time = base + timedelta(days=day, minutes=random.randint(0, 1380))
                amount = random.choice([99, 149, 249, 499, 799, 1200, 2499, 4999]) * random.uniform(0.85, 1.15)
                transactions.append(
                    _txn(
                        next_id(),
                        sender,
                        receiver,
                        amount,
                        time,
                        random.choice(TYPES),
                        random.choice(CHANNELS),
                        random.choice(CITIES),
                        f"DEV-{random.randint(1, 90):04d}",
                        "SUCCESS",
                        "normal payment",
                    )
                )

        # Smurfing pattern: many small transfers from victims into mule accounts.
        victims = ["ACC0003", "ACC0011", "ACC0027", "ACC0034", "ACC0046", "ACC0062", "ACC0075"]
        smurf_start = base + timedelta(days=19, hours=18)
        for hour in range(6):
            for victim in victims:
                receiver = random.choice(mules[:7])
                transactions.append(
                    _txn(
                        next_id(),
                        victim,
                        receiver,
                        random.uniform(4800, 9900),
                        smurf_start + timedelta(hours=hour, minutes=random.randint(0, 50)),
                        "P2P",
                        "COLLECT_REQUEST",
                        random.choice(["Delhi", "Noida", "Gurugram"]),
                        f"DEV-{random.randint(111, 117):04d}",
                        "SUCCESS",
                        "urgent collect request",
                        "fraud",
                    )
                )

        # Layering pattern: mules rapidly move funds through a circular chain.
        ring = ["ACC0111", "ACC0112", "ACC0113", "ACC0114", "ACC0115", "ACC0116"]
        ring_start = base + timedelta(days=20, hours=22)
        for cycle in range(7):
            for i, sender in enumerate(ring):
                receiver = ring[(i + 1) % len(ring)]
                transactions.append(
                    _txn(
                        next_id(),
                        sender,
                        receiver,
                        random.uniform(4200, 8800),
                        ring_start + timedelta(minutes=cycle * 13 + i),
                        "P2P",
                        "PAYMENT_LINK",
                        random.choice(CITIES),
                        f"DEV-{111 + (i % 3):04d}",
                        "SUCCESS",
                        "wallet settlement",
                        "fraud",
                    )
                )

        # Account takeover pattern: unusual large outgoing transfers from new devices.
        takeover_accounts = ["ACC0019", "ACC0058", "ACC0084"]
        for idx, sender in enumerate(takeover_accounts):
            for hop in range(5):
                receiver = random.choice(mules[6:] + new_accounts)
                transactions.append(
                    _txn(
                        next_id(),
                        sender,
                        receiver,
                        random.uniform(15500, 46000),
                        base + timedelta(days=22, hours=idx * 2, minutes=hop * 8),
                        "P2P",
                        "UPI_APP",
                        random.choice(["Mumbai", "Bengaluru", "Pune"]),
                        f"DEV-NEW-{idx}",
                        "SUCCESS" if hop < 4 else "FAILED",
                        "device changed",
                        "fraud",
                    )
                )

        # Benign high-volume merchants, included so the model must distinguish risk from activity.
        for merchant in merchants[:6]:
            for i in range(36):
                transactions.append(
                    _txn(
                        next_id(),
                        random.choice(consumers),
                        merchant,
                        random.uniform(180, 2600),
                        base + timedelta(days=random.randint(0, 23), minutes=random.randint(0, 1380)),
                        "P2M",
                        "QR_SCAN",
                        random.choice(CITIES),
                        f"DEV-{random.randint(1, 90):04d}",
                        "SUCCESS",
                        "merchant purchase",
                    )
                )

        connection.executemany(
            """
            INSERT INTO transactions (
                txn_id, sender_id, receiver_id, amount, txn_time, txn_type,
                channel, city, device_id, status, note, label
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            transactions,
        )

        cases = [
            (
                "CASE-0001",
                "ACC0111",
                datetime(2026, 5, 24, 10, 15).isoformat(),
                "Critical",
                "Open",
                "Risk Ops",
                "Circular mule-ring activity with shared devices and rapid fund movement.",
            ),
            (
                "CASE-0002",
                "ACC0019",
                datetime(2026, 5, 24, 11, 40).isoformat(),
                "High",
                "Reviewing",
                "Fraud Analyst",
                "Large unusual transfers after device change and failed transfer attempts.",
            ),
            (
                "CASE-0003",
                "ACC0117",
                datetime(2026, 5, 25, 9, 5).isoformat(),
                "High",
                "Open",
                "Risk Ops",
                "Receiver in multiple collect-request complaints from unrelated victims.",
            ),
        ]
        connection.executemany(
            """
            INSERT INTO risk_cases (
                case_id, account_id, opened_at, priority, status, assigned_to, summary
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            cases,
        )
