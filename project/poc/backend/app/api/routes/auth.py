from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ...core.config import CONTRACT_VERSION, MODEL, NOW, SESSION_TOKEN
from ...core.security import pkce_challenge, require_versions, sign_id_token
from ...db import connect, insert_audit
from ...schemas import AuthExchangeRequest, AuthStartRequest

router = APIRouter()


@router.post("/auth/plugin/start")
def auth_start(request: AuthStartRequest) -> dict:
    require_versions(request.contractVersion, request.pluginVersion)
    auth_code = "oauth_code_demo"
    with connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO plugin_auth_requests
            (request_id, local_nonce, state, code_challenge, code_challenge_method, auth_code, completed, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("auth_req_demo", request.localNonce, request.state, request.codeChallenge, request.codeChallengeMethod, auth_code, 0, NOW),
        )
        insert_audit(conn, "audit_auth_start_001", "plugin_oauth_started", payload={"state": request.state, "codeChallengeMethod": request.codeChallengeMethod})
        conn.commit()
    return {
        "requestId": "auth_req_demo",
        "browserUrl": "http://localhost:5173/mock-auth/auth_req_demo",
        "state": request.state,
        "codeChallengeMethod": request.codeChallengeMethod,
        "authorizationCodeIssued": True,
        "expiresAt": "2026-05-23T23:59:00Z",
        "pollAfterMs": 500,
    }


@router.post("/auth/plugin/exchange")
def auth_exchange(request: AuthExchangeRequest) -> dict:
    require_versions(request.contractVersion, request.pluginVersion)
    with connect() as conn:
        auth_request = conn.execute("SELECT * FROM plugin_auth_requests WHERE request_id = ?", (request.requestId,)).fetchone()
        if not auth_request:
            raise HTTPException(status_code=400, detail={"code": "auth_request_invalid", "message": "Demo auth request was not completed."})
        if auth_request["completed"]:
            raise HTTPException(status_code=400, detail={"code": "auth_request_invalid", "message": "Auth code was already exchanged."})
        if auth_request["local_nonce"] != request.localNonce or auth_request["state"] != request.state:
            raise HTTPException(status_code=400, detail={"code": "auth_request_invalid", "message": "OAuth state or nonce did not match."})
        if pkce_challenge(request.codeVerifier) != auth_request["code_challenge"]:
            raise HTTPException(status_code=400, detail={"code": "auth_request_invalid", "message": "PKCE verifier did not match the auth request."})
        id_token = sign_id_token(
            {
                "iss": "https://auth.local.creative-ai-workflow",
                "aud": "creative-ai-workflow-figma-plugin",
                "sub": "usr_maya",
                "tenant_id": "tenant_designtechco",
                "session_id": SESSION_TOKEN,
                "nonce": request.localNonce,
                "iat": 1779556800,
                "exp": 1779609540,
            }
        )
        conn.execute("UPDATE plugin_auth_requests SET completed = 1 WHERE request_id = ?", (request.requestId,))
        conn.execute(
            """
            INSERT OR REPLACE INTO plugin_sessions
            (session_token, user_id, tenant_id, state, id_token, expires_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (SESSION_TOKEN, "usr_maya", "tenant_designtechco", request.state, id_token, "2026-05-24T00:59:00Z", NOW),
        )
        insert_audit(conn, "audit_auth_exchange_001", "plugin_session_issued", payload={"state": request.state, "userId": "usr_maya", "model": MODEL})
        conn.commit()

    if request.requestId != "auth_req_demo" or request.localNonce != "demo_nonce":
        raise HTTPException(status_code=400, detail={"code": "auth_request_invalid", "message": "Demo auth request was not completed."})
    return {
        "requestId": "auth_req_demo",
        "session": {"accessToken": SESSION_TOKEN, "expiresAt": "2026-05-24T00:59:00Z", "tokenType": "Bearer"},
        "oauth": {"state": request.state, "pkceVerified": True, "idTokenIssued": True},
        "idToken": id_token,
        "user": {"userId": "usr_maya", "displayName": "Maya Chen"},
    }

