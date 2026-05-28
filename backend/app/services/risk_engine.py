from __future__ import annotations

import math
from collections import Counter, defaultdict, deque
from dataclasses import dataclass
from datetime import datetime
from statistics import mean
from typing import Any


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value)


@dataclass
class RiskSignal:
    name: str
    value: float
    weight: float
    explanation: str

    @property
    def contribution(self) -> float:
        return self.value * self.weight


class GraphRiskEngine:
    """Scores UPI accounts using graph behavior, velocity, device reuse, and anomaly signals."""

    def __init__(self, accounts: list[dict[str, Any]], transactions: list[dict[str, Any]]) -> None:
        self.accounts = {account["account_id"]: account for account in accounts}
        self.transactions = transactions
        self.outgoing: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self.incoming: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self.neighbors: dict[str, set[str]] = defaultdict(set)
        self.device_accounts: dict[str, set[str]] = defaultdict(set)
        self.edge_counts: Counter[tuple[str, str]] = Counter()
        self._build_indexes()
        self.components = self._connected_components()
        self.component_by_account = {
            account_id: component for component in self.components for account_id in component
        }
        self.max_sent = max((sum(txn["amount"] for txn in txns) for txns in self.outgoing.values()), default=1)
        self.max_degree = max((len(nodes) for nodes in self.neighbors.values()), default=1)
        self.max_component = max((len(component) for component in self.components), default=1)

    def _build_indexes(self) -> None:
        for account in self.accounts.values():
            self.device_accounts[account["device_id"]].add(account["account_id"])

        for txn in self.transactions:
            sender = txn["sender_id"]
            receiver = txn["receiver_id"]
            self.outgoing[sender].append(txn)
            self.incoming[receiver].append(txn)
            self.neighbors[sender].add(receiver)
            self.neighbors[receiver].add(sender)
            self.edge_counts[(sender, receiver)] += 1

    def _connected_components(self) -> list[set[str]]:
        unseen = set(self.accounts)
        components: list[set[str]] = []
        while unseen:
            start = unseen.pop()
            component = {start}
            queue: deque[str] = deque([start])
            while queue:
                node = queue.popleft()
                for neighbor in self.neighbors[node]:
                    if neighbor in unseen:
                        unseen.remove(neighbor)
                        component.add(neighbor)
                        queue.append(neighbor)
            components.append(component)
        return components

    def _has_cycle_signal(self, account_id: str) -> bool:
        for neighbor in self.neighbors[account_id]:
            if (account_id, neighbor) in self.edge_counts and (neighbor, account_id) in self.edge_counts:
                return True
            for second_hop in self.neighbors[neighbor]:
                if second_hop != account_id and (second_hop, account_id) in self.edge_counts:
                    return True
        return False

    def _hourly_burst(self, txns: list[dict[str, Any]]) -> int:
        by_hour = Counter(_parse_time(txn["txn_time"]).strftime("%Y-%m-%d %H") for txn in txns)
        return max(by_hour.values(), default=0)

    def _risk_signals(self, account_id: str) -> list[RiskSignal]:
        account = self.accounts[account_id]
        outgoing = self.outgoing[account_id]
        incoming = self.incoming[account_id]
        all_txns = outgoing + incoming
        sent = sum(txn["amount"] for txn in outgoing)
        received = sum(txn["amount"] for txn in incoming)
        degree = len(self.neighbors[account_id])
        unique_receivers = len({txn["receiver_id"] for txn in outgoing})
        distinct_cities = len({txn["city"] for txn in all_txns})
        failed_count = sum(1 for txn in all_txns if txn["status"] == "FAILED")
        collect_requests = sum(1 for txn in all_txns if txn["channel"] == "COLLECT_REQUEST")
        payment_links = sum(1 for txn in all_txns if txn["channel"] == "PAYMENT_LINK")
        avg_outgoing = mean([txn["amount"] for txn in outgoing] or [0])
        known_fraud_exposure = sum(1 for txn in all_txns if txn["label"] == "fraud")
        component_size = len(self.component_by_account.get(account_id, {account_id}))
        shared_device_count = len(self.device_accounts[account["device_id"]])
        burst = self._hourly_burst(all_txns)
        cycle_signal = self._has_cycle_signal(account_id)

        fanout_intensity = 0
        if unique_receivers >= 5:
            fanout_intensity = min(1.0, unique_receivers / 12)
            if avg_outgoing and avg_outgoing < 10000:
                fanout_intensity += 0.15

        signals = [
            RiskSignal(
                "Transaction Velocity",
                _clamp(math.log1p(sent + received) / math.log1p(self.max_sent + 1), 0, 1),
                18,
                "High total transfer volume compared with the network baseline.",
            ),
            RiskSignal(
                "Graph Centrality",
                _clamp(degree / self.max_degree, 0, 1),
                13,
                "Account is connected to many unique counterparties in the transaction graph.",
            ),
            RiskSignal(
                "Fan-out Pattern",
                _clamp(fanout_intensity, 0, 1),
                13,
                "Funds are distributed to many receivers, a common mule layering pattern.",
            ),
            RiskSignal(
                "Shared Device Reuse",
                _clamp((shared_device_count - 1) / 6, 0, 1),
                12,
                "Multiple accounts are operating from the same device fingerprint.",
            ),
            RiskSignal(
                "Circular Flow",
                1.0 if cycle_signal else 0.0,
                11,
                "Reciprocal or closed-loop transfers were found near this account.",
            ),
            RiskSignal(
                "Burst Activity",
                _clamp(burst / 9, 0, 1),
                10,
                "Many transactions happened inside the same hourly window.",
            ),
            RiskSignal(
                "Risky Channels",
                _clamp((collect_requests + payment_links) / max(len(all_txns), 1), 0, 1),
                8,
                "Collect requests and payment links are overrepresented in activity.",
            ),
            RiskSignal(
                "Known Fraud Exposure",
                _clamp(known_fraud_exposure / 8, 0, 1),
                8,
                "Account is linked to confirmed or seeded fraud-labelled transactions.",
            ),
            RiskSignal(
                "Geo-Device Mismatch",
                _clamp((distinct_cities - 1 + failed_count) / 8, 0, 1),
                5,
                "Activity spans multiple cities or includes failed attempts.",
            ),
            RiskSignal(
                "Community Risk",
                _clamp(component_size / self.max_component, 0, 1),
                2,
                "The connected component around the account is unusually large.",
            ),
        ]

        if account["kyc_level"] == "MINIMUM":
            signals.append(
                RiskSignal(
                    "Weak KYC",
                    1.0,
                    4,
                    "Minimum-KYC account receives extra scrutiny in high-risk flows.",
                )
            )

        return signals

    def score_account(self, account_id: str) -> dict[str, Any]:
        if account_id not in self.accounts:
            raise KeyError(f"Unknown account_id: {account_id}")

        signals = self._risk_signals(account_id)
        raw_score = sum(signal.contribution for signal in signals)
        score = round(_clamp(raw_score), 2)
        tier = self.risk_tier(score)
        top_signals = sorted(signals, key=lambda signal: signal.contribution, reverse=True)[:5]
        outgoing = self.outgoing[account_id]
        incoming = self.incoming[account_id]

        return {
            "account": self.accounts[account_id],
            "risk_score": score,
            "risk_tier": tier,
            "signals": [
                {
                    "name": signal.name,
                    "value": round(signal.value, 3),
                    "weight": signal.weight,
                    "contribution": round(signal.contribution, 2),
                    "explanation": signal.explanation,
                }
                for signal in top_signals
            ],
            "metrics": {
                "outgoing_count": len(outgoing),
                "incoming_count": len(incoming),
                "sent_amount": round(sum(txn["amount"] for txn in outgoing), 2),
                "received_amount": round(sum(txn["amount"] for txn in incoming), 2),
                "unique_neighbors": len(self.neighbors[account_id]),
                "component_size": len(self.component_by_account.get(account_id, {account_id})),
                "shared_device_accounts": len(self.device_accounts[self.accounts[account_id]["device_id"]]),
                "hourly_burst": self._hourly_burst(outgoing + incoming),
            },
        }

    @staticmethod
    def risk_tier(score: float) -> str:
        if score >= 75:
            return "Critical"
        if score >= 55:
            return "High"
        if score >= 35:
            return "Medium"
        return "Low"

    def score_all_accounts(self) -> list[dict[str, Any]]:
        scored = [self.score_account(account_id) for account_id in self.accounts]
        return sorted(scored, key=lambda row: row["risk_score"], reverse=True)

    def graph_payload(self, limit: int = 90, minimum_score: float = 0) -> dict[str, Any]:
        scored = [row for row in self.score_all_accounts() if row["risk_score"] >= minimum_score]
        selected_ids = {row["account"]["account_id"] for row in scored[:limit]}
        nodes = []
        for row in scored[:limit]:
            account = row["account"]
            nodes.append(
                {
                    "id": account["account_id"],
                    "label": account["vpa"],
                    "name": account["holder_name"],
                    "city": account["city"],
                    "account_type": account["account_type"],
                    "risk_score": row["risk_score"],
                    "risk_tier": row["risk_tier"],
                    "degree": row["metrics"]["unique_neighbors"],
                    "component_size": row["metrics"]["component_size"],
                }
            )

        edge_counter: Counter[tuple[str, str]] = Counter()
        edge_amounts: defaultdict[tuple[str, str], float] = defaultdict(float)
        fraud_edges: Counter[tuple[str, str]] = Counter()
        for txn in self.transactions:
            if txn["sender_id"] in selected_ids and txn["receiver_id"] in selected_ids:
                key = (txn["sender_id"], txn["receiver_id"])
                edge_counter[key] += 1
                edge_amounts[key] += txn["amount"]
                if txn["label"] == "fraud":
                    fraud_edges[key] += 1

        links = [
            {
                "source": sender,
                "target": receiver,
                "count": count,
                "amount": round(edge_amounts[(sender, receiver)], 2),
                "fraud_count": fraud_edges[(sender, receiver)],
            }
            for (sender, receiver), count in edge_counter.most_common(160)
        ]
        return {"nodes": nodes, "links": links}

    def overview(self) -> dict[str, Any]:
        scored = self.score_all_accounts()
        transactions = self.transactions
        total_amount = sum(txn["amount"] for txn in transactions)
        fraud_transactions = [txn for txn in transactions if txn["label"] == "fraud"]
        tiers = Counter(row["risk_tier"] for row in scored)
        high_risk = [row for row in scored if row["risk_score"] >= 55]
        return {
            "total_accounts": len(self.accounts),
            "total_transactions": len(transactions),
            "total_volume": round(total_amount, 2),
            "fraud_transaction_rate": round(len(fraud_transactions) / max(len(transactions), 1), 4),
            "high_risk_accounts": len(high_risk),
            "critical_accounts": tiers["Critical"],
            "largest_component_size": self.max_component,
            "risk_tier_counts": dict(tiers),
            "top_accounts": scored[:8],
            "model_notes": [
                "Uses graph centrality, device reuse, transaction velocity, burst activity, circular flows, and channel-risk signals.",
                "Seed data includes benign merchants, smurfing, mule-ring layering, and account-takeover scenarios.",
                "Score is explainable and deterministic, making it suitable for demos, testing, and viva discussion.",
            ],
        }

    def transaction_heatmap(self) -> list[dict[str, Any]]:
        buckets: dict[str, Counter[str]] = defaultdict(Counter)
        for txn in self.transactions:
            parsed = _parse_time(txn["txn_time"])
            buckets[parsed.strftime("%a")][str(parsed.hour)] += 1
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        return [
            {"day": day, "hour": hour, "count": buckets[day][str(hour)]}
            for day in days
            for hour in range(24)
        ]

    def simulate_transaction(self, payload: dict[str, Any]) -> dict[str, Any]:
        sender_id = payload["sender_id"]
        receiver_id = payload["receiver_id"]
        amount = float(payload["amount"])
        if sender_id not in self.accounts or receiver_id not in self.accounts:
            raise KeyError("sender_id or receiver_id not found")

        sender_score = self.score_account(sender_id)["risk_score"]
        receiver_score = self.score_account(receiver_id)["risk_score"]
        pair_seen = (sender_id, receiver_id) in self.edge_counts
        amount_pressure = _clamp((amount - 10000) / 50000, 0, 1) * 18
        new_pair_pressure = 9 if not pair_seen else 0
        risky_channel_pressure = 8 if payload.get("channel") in {"COLLECT_REQUEST", "PAYMENT_LINK"} else 0
        device_pressure = 0
        if payload.get("device_id") and payload["device_id"] != self.accounts[sender_id]["device_id"]:
            device_pressure = 10
        score = round(_clamp((sender_score * 0.36) + (receiver_score * 0.42) + amount_pressure + new_pair_pressure + risky_channel_pressure + device_pressure), 2)
        decision = "BLOCK" if score >= 78 else "MANUAL_REVIEW" if score >= 55 else "ALLOW"
        return {
            "risk_score": score,
            "risk_tier": self.risk_tier(score),
            "decision": decision,
            "reasons": [
                {"label": "Sender account risk", "value": round(sender_score, 2)},
                {"label": "Receiver account risk", "value": round(receiver_score, 2)},
                {"label": "Amount pressure", "value": round(amount_pressure, 2)},
                {"label": "New counterparty", "value": new_pair_pressure},
                {"label": "Risky channel", "value": risky_channel_pressure},
                {"label": "Device change", "value": device_pressure},
            ],
        }
