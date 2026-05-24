from __future__ import annotations

import base64
import hashlib
import hmac
import json
from typing import Annotated

from fastapi import Header, HTTPException

from .config import ADMIN_TOKEN, CONTRACT_VERSION, ID_TOKEN_SECRET, PLUGIN_VERSION, SESSION_TOKEN


def require_auth(authorization: Annotated[str | None, Header()] = None) -> None:
    if authorization != f"Bearer {SESSION_TOKEN}":
        raise HTTPException(status_code=401, detail={"code": "unauthorized", "message": "Valid plugin session required."})


def require_admin(x_admin_token: Annotated[str | None, Header(alias="X-Admin-Token")] = None) -> None:
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail={"code": "admin_required", "message": "Admin session required."})


def pkce_challenge(verifier: str) -> str:
    return base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()


def b64url_json(payload: dict) -> str:
    return base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).rstrip(b"=").decode()


def sign_id_token(payload: dict) -> str:
    header = b64url_json({"alg": "HS256", "typ": "JWT"})
    body = b64url_json(payload)
    signature = hmac.new(ID_TOKEN_SECRET, f"{header}.{body}".encode(), hashlib.sha256).digest()
    return f"{header}.{body}.{base64.urlsafe_b64encode(signature).rstrip(b'=').decode()}"


def require_versions(contract_version: str, plugin_version: str) -> None:
    if contract_version != CONTRACT_VERSION or plugin_version != PLUGIN_VERSION:
        raise HTTPException(status_code=400, detail={"code": "contract_mismatch", "message": "Unsupported contract or plugin version."})

