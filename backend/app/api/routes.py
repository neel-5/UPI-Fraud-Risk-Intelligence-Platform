from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.schemas.risk import SeedResetResponse, SimulationRequest
from app.services.repository import load_accounts, load_cases, load_transactions, reset_seed_data
from app.services.risk_engine import GraphRiskEngine

router = APIRouter(prefix="/api", tags=["risk-intelligence"])


def _engine() -> GraphRiskEngine:
    return GraphRiskEngine(load_accounts(), load_transactions())


@router.get("/overview")
def overview() -> dict:
    return _engine().overview()


@router.get("/accounts")
def accounts(
    risk_tier: str | None = Query(default=None, description="Low, Medium, High, or Critical"),
    limit: int = Query(default=30, ge=1, le=150),
) -> list[dict]:
    scored = _engine().score_all_accounts()
    if risk_tier:
        scored = [row for row in scored if row["risk_tier"].lower() == risk_tier.lower()]
    return scored[:limit]


@router.get("/accounts/{account_id}")
def account_detail(account_id: str) -> dict:
    engine = _engine()
    try:
        account = engine.score_account(account_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {
        **account,
        "recent_transactions": load_transactions(limit=25, account_id=account_id),
    }


@router.get("/transactions")
def transactions(
    account_id: str | None = Query(default=None),
    flagged_only: bool = Query(default=False),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[dict]:
    rows = load_transactions(limit=limit, account_id=account_id)
    if flagged_only:
        rows = [row for row in rows if row["label"] == "fraud"]
    return rows


@router.get("/graph")
def graph(
    limit: int = Query(default=80, ge=10, le=150),
    minimum_score: float = Query(default=0, ge=0, le=100),
) -> dict:
    return _engine().graph_payload(limit=limit, minimum_score=minimum_score)


@router.get("/heatmap")
def heatmap() -> list[dict]:
    return _engine().transaction_heatmap()


@router.get("/cases")
def cases() -> list[dict]:
    return load_cases()


@router.post("/simulate")
def simulate(payload: SimulationRequest) -> dict:
    engine = _engine()
    try:
        return engine.simulate_transaction(payload.model_dump())
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/admin/reset-seed", response_model=SeedResetResponse)
def reset_seed() -> SeedResetResponse:
    reset_seed_data()
    return SeedResetResponse(message="Seed data reset successfully.")
