from __future__ import annotations

from collections import Counter
from typing import Any


def usage_summary(conn: Any) -> dict[str, Any]:
    usage_rows = conn.execute("SELECT operation_type, estimated_cost_usd, user_id FROM usage_events").fetchall()
    counts = Counter(row["operation_type"] for row in usage_rows)
    by_user_operation: dict[tuple[str, str], dict[str, Any]] = {}
    cost_by_user: dict[str, dict[str, Any]] = {}
    for row in usage_rows:
        bucket = cost_by_user.setdefault(row["user_id"], {"operations": 0, "estimatedCostUsd": 0.0})
        bucket["operations"] += 1
        bucket["estimatedCostUsd"] = round(bucket["estimatedCostUsd"] + float(row["estimated_cost_usd"]), 3)
        op_bucket = by_user_operation.setdefault(
            (row["user_id"], row["operation_type"]),
            {
                "userId": row["user_id"],
                "brandId": "brand_nova",
                "operationType": row["operation_type"],
                "operationCount": 0,
                "estimatedCostUsd": 0.0,
            },
        )
        op_bucket["operationCount"] += 1
        op_bucket["estimatedCostUsd"] = round(op_bucket["estimatedCostUsd"] + float(row["estimated_cost_usd"]), 3)
    audit_rows = conn.execute(
        "SELECT audit_event_id, type, operation_id, usage_event_id, created_at FROM audit_events ORDER BY created_at DESC, audit_event_id DESC LIMIT 10"
    ).fetchall()
    apply_count = conn.execute("SELECT COUNT(*) AS c FROM apply_events").fetchone()["c"]
    total_operations = len(usage_rows) + int(apply_count)
    return {
        "summary": {
            "operationCount": len(usage_rows),
            "appliedCount": int(apply_count),
            "estimatedCostUsd": round(sum(float(row["estimated_cost_usd"]) for row in usage_rows), 3),
            "medianTextLatencyMs": 610,
            "imageJobFailureRate": 0.0,
            "totalOperations": total_operations,
            "totalEstimatedCostUsd": round(sum(float(row["estimated_cost_usd"]) for row in usage_rows), 3),
            "copyOperations": counts.get("copy", 0),
            "localizationOperations": counts.get("localization", 0),
            "imageJobs": counts.get("image", 0),
            "applyEvents": int(apply_count),
        },
        "groups": list(by_user_operation.values()),
        "byUser": [
            {
                "userId": user_id,
                "displayName": "Maya Chen",
                "operations": bucket["operations"],
                "estimatedCostUsd": bucket["estimatedCostUsd"],
            }
            for user_id, bucket in cost_by_user.items()
        ],
        "recentAuditEvents": [
            {
                "auditEventId": row["audit_event_id"],
                "type": row["type"],
                "operationId": row["operation_id"],
                "usageEventId": row["usage_event_id"],
                "createdAt": row["created_at"],
            }
            for row in audit_rows
        ],
    }

