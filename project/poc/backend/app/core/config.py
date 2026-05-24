from __future__ import annotations

import base64
import hashlib

CONTRACT_VERSION = "2026-05-poc"
PLUGIN_VERSION = "0.1.0"
SESSION_TOKEN = "demo_plugin_session"
ADMIN_TOKEN = "demo_admin_session"
DEMO_CODE_VERIFIER = "demo_code_verifier"
DEMO_CODE_CHALLENGE = base64.urlsafe_b64encode(hashlib.sha256(DEMO_CODE_VERIFIER.encode()).digest()).rstrip(b"=").decode()
ID_TOKEN_SECRET = b"local-poc-sso-secret"
NOW = "2026-05-23T12:00:00Z"
MODEL = "mock-gpt-4o-equivalent"
LOCALES = ["fr-FR", "de-DE", "es-ES", "pt-BR", "it-IT", "nl-NL", "ja-JP", "ko-KR"]

