from __future__ import annotations

from fastapi import APIRouter, Depends

from ...core.security import require_auth
from ...db import connect
from ...services.usage_reports import usage_summary

router = APIRouter(dependencies=[Depends(require_auth)])


@router.get("/reports/usage")
def usage_report() -> dict:
    with connect() as conn:
        return {"requestId": "req_usage_001", **usage_summary(conn)}

