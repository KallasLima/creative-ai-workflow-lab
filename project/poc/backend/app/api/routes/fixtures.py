from __future__ import annotations

import json

from fastapi import APIRouter

from ...db import FIXTURES

router = APIRouter()


@router.get("/fixtures/figma-selection")
def figma_selection() -> dict:
    return json.loads((FIXTURES / "figma-selection.json").read_text())

