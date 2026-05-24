from __future__ import annotations

from fastapi import APIRouter

from ...core.config import CONTRACT_VERSION
from ...db import connect

router = APIRouter()


@router.get("/health")
def health() -> dict:
    with connect() as conn:
        conn.execute("SELECT 1").fetchone()
    return {"requestId": "req_health_001", "status": "ok", "contractVersion": CONTRACT_VERSION, "database": "sqlite"}

