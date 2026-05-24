from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any

BACKEND_ROOT = Path(__file__).resolve().parents[1]
POC_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = POC_ROOT / "fixtures"
DEFAULT_DB = BACKEND_ROOT / ".data" / "poc.sqlite"


def db_path() -> Path:
    configured = os.environ.get("POC_DB_PATH")
    return Path(configured) if configured else DEFAULT_DB


def connect() -> sqlite3.Connection:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    init_db(conn)
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS tenants (
          tenant_id TEXT PRIMARY KEY,
          name TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS users (
          user_id TEXT PRIMARY KEY,
          tenant_id TEXT NOT NULL,
          display_name TEXT NOT NULL,
          role TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS brands (
          brand_id TEXT PRIMARY KEY,
          tenant_id TEXT NOT NULL,
          name TEXT NOT NULL,
          active_profile_id TEXT NOT NULL DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS brand_guidelines (
          guideline_id TEXT PRIMARY KEY,
          tenant_id TEXT NOT NULL,
          brand_id TEXT NOT NULL,
          source_name TEXT NOT NULL,
          size_bytes INTEGER NOT NULL,
          extracted_characters INTEGER NOT NULL,
          content TEXT NOT NULL,
          created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS brand_profiles (
          profile_id TEXT PRIMARY KEY,
          brand_id TEXT NOT NULL,
          status TEXT NOT NULL,
          confidence TEXT NOT NULL DEFAULT 'medium',
          version INTEGER NOT NULL,
          source_guideline_id TEXT NOT NULL,
          tone_json TEXT NOT NULL,
          banned_phrases_json TEXT NOT NULL,
          locale_notes_json TEXT NOT NULL,
          visual_notes_json TEXT NOT NULL DEFAULT '[]',
          review_notes_json TEXT NOT NULL DEFAULT '[]',
          updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS operation_requests (
          operation_id TEXT PRIMARY KEY,
          request_id TEXT NOT NULL,
          client_request_id TEXT NOT NULL,
          idempotency_key TEXT,
          tenant_id TEXT NOT NULL,
          brand_id TEXT NOT NULL,
          profile_id TEXT NOT NULL,
          user_id TEXT NOT NULL,
          operation_type TEXT NOT NULL,
          payload_json TEXT NOT NULL,
          created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS model_invocations (
          invocation_id TEXT PRIMARY KEY,
          operation_id TEXT NOT NULL,
          provider TEXT NOT NULL,
          model TEXT NOT NULL,
          latency_ms INTEGER NOT NULL,
          input_units INTEGER NOT NULL,
          output_units INTEGER NOT NULL,
          estimated_cost_usd REAL NOT NULL,
          created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS usage_events (
          usage_event_id TEXT PRIMARY KEY,
          operation_id TEXT,
          user_id TEXT NOT NULL,
          tenant_id TEXT NOT NULL,
          brand_id TEXT NOT NULL,
          operation_type TEXT NOT NULL,
          estimated_cost_usd REAL NOT NULL,
          created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS image_jobs (
          job_id TEXT PRIMARY KEY,
          client_request_id TEXT NOT NULL,
          idempotency_key TEXT,
          tenant_id TEXT NOT NULL,
          brand_id TEXT NOT NULL,
          profile_id TEXT NOT NULL,
          user_id TEXT NOT NULL,
          prompt TEXT NOT NULL,
          status TEXT NOT NULL,
          get_count INTEGER NOT NULL DEFAULT 0,
          usage_event_id TEXT,
          asset_id TEXT,
          created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS assets (
          asset_id TEXT PRIMARY KEY,
          job_id TEXT NOT NULL,
          width INTEGER NOT NULL,
          height INTEGER NOT NULL,
          placeholder_only INTEGER NOT NULL,
          rights_status TEXT NOT NULL DEFAULT 'ideation_only',
          safety_status TEXT NOT NULL DEFAULT 'passed',
          policy_checks_json TEXT NOT NULL DEFAULT '[]',
          content_type TEXT NOT NULL,
          bytes BLOB NOT NULL,
          created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS apply_events (
          apply_event_id TEXT PRIMARY KEY,
          operation_id TEXT NOT NULL,
          applied_by TEXT NOT NULL,
          applied_items_json TEXT NOT NULL,
          created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS audit_events (
          audit_event_id TEXT PRIMARY KEY,
          type TEXT NOT NULL,
          operation_id TEXT,
          usage_event_id TEXT,
          payload_json TEXT NOT NULL,
          created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS plugin_auth_requests (
          request_id TEXT PRIMARY KEY,
          local_nonce TEXT NOT NULL,
          state TEXT NOT NULL,
          code_challenge TEXT NOT NULL,
          code_challenge_method TEXT NOT NULL,
          auth_code TEXT NOT NULL,
          completed INTEGER NOT NULL DEFAULT 0,
          created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS plugin_sessions (
          session_token TEXT PRIMARY KEY,
          user_id TEXT NOT NULL,
          tenant_id TEXT NOT NULL,
          state TEXT NOT NULL,
          id_token TEXT NOT NULL,
          expires_at TEXT NOT NULL,
          created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS model_quality_runs (
          run_id TEXT PRIMARY KEY,
          provider TEXT NOT NULL,
          model TEXT NOT NULL,
          threshold REAL NOT NULL,
          score REAL NOT NULL,
          passed INTEGER NOT NULL,
          sample_count INTEGER NOT NULL,
          created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS model_quality_results (
          result_id TEXT PRIMARY KEY,
          run_id TEXT NOT NULL,
          sample_id TEXT NOT NULL,
          operation_type TEXT NOT NULL,
          score REAL NOT NULL,
          passed INTEGER NOT NULL,
          checks_json TEXT NOT NULL,
          output_preview TEXT NOT NULL,
          created_at TEXT NOT NULL
        );
        """
    )
    ensure_column(conn, "assets", "rights_status", "TEXT NOT NULL DEFAULT 'ideation_only'")
    ensure_column(conn, "assets", "safety_status", "TEXT NOT NULL DEFAULT 'passed'")
    ensure_column(conn, "assets", "policy_checks_json", "TEXT NOT NULL DEFAULT '[]'")
    seed(conn)
    conn.commit()


def ensure_column(conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in existing:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def seed(conn: sqlite3.Connection) -> None:
    now = "2026-05-23T12:00:00Z"
    conn.execute(
        "INSERT OR IGNORE INTO tenants (tenant_id, name) VALUES (?, ?)",
        ("tenant_designtechco", "DesignTechCo"),
    )
    conn.execute(
        "INSERT OR IGNORE INTO tenants (tenant_id, name) VALUES (?, ?)",
        ("tenant_studioarc", "Studio Arc"),
    )
    conn.execute(
        "INSERT OR IGNORE INTO users (user_id, tenant_id, display_name, role) VALUES (?, ?, ?, ?)",
        ("usr_maya", "tenant_designtechco", "Maya Chen", "designer"),
    )
    conn.execute(
        "INSERT OR IGNORE INTO users (user_id, tenant_id, display_name, role) VALUES (?, ?, ?, ?)",
        ("usr_ravi", "tenant_studioarc", "Ravi Patel", "admin"),
    )
    conn.execute(
        "INSERT OR IGNORE INTO brands (brand_id, tenant_id, name, active_profile_id) VALUES (?, ?, ?, ?)",
        ("brand_nova", "tenant_designtechco", "Nova Athletics", "profile_nova_v3"),
    )
    conn.execute(
        "INSERT OR IGNORE INTO brands (brand_id, tenant_id, name, active_profile_id) VALUES (?, ?, ?, ?)",
        ("brand_luma", "tenant_studioarc", "Luma Home", ""),
    )
    sample = (FIXTURES / "brand-guideline-sample.md").read_text()
    conn.execute(
        """
        INSERT OR IGNORE INTO brand_guidelines
        (guideline_id, tenant_id, brand_id, source_name, size_bytes, extracted_characters, content, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "guide_nova_001",
            "tenant_designtechco",
            "brand_nova",
            "brand-guideline-sample.md",
            len(sample.encode("utf-8")),
            len(sample),
            sample,
            now,
        ),
    )
    conn.execute(
        """
        INSERT OR IGNORE INTO brand_profiles
        (profile_id, brand_id, status, confidence, version, source_guideline_id, tone_json, banned_phrases_json, locale_notes_json, visual_notes_json, review_notes_json, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "profile_nova_v3",
            "brand_nova",
            "active",
            "high",
            3,
            "guide_nova_001",
            json.dumps(["energetic", "clear", "performance-led"]),
            json.dumps(["cheap", "miracle"]),
            json.dumps(["Preserve concise CTA style across locales"]),
            json.dumps(["Use bright ecommerce lifestyle placeholder imagery."]),
            json.dumps([]),
            now,
        ),
    )


def insert_audit(
    conn: sqlite3.Connection,
    audit_event_id: str,
    event_type: str,
    operation_id: str | None = None,
    usage_event_id: str | None = None,
    payload: dict[str, Any] | None = None,
) -> None:
    conn.execute(
        """
        INSERT OR IGNORE INTO audit_events
        (audit_event_id, type, operation_id, usage_event_id, payload_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            audit_event_id,
            event_type,
            operation_id,
            usage_event_id,
            json.dumps(payload or {}),
            "2026-05-23T12:00:00Z",
        ),
    )
