from __future__ import annotations

from fastapi import APIRouter, Depends

from ...core.security import require_auth
from ...services.model_quality import evaluate_and_persist_quality_gate

router = APIRouter(dependencies=[Depends(require_auth)])


@router.post("/quality/model-gateway/evaluate")
def model_quality_evaluate() -> dict:
    return evaluate_and_persist_quality_gate()

