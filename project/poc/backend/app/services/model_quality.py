from __future__ import annotations

import json
from typing import Any

from fastapi import HTTPException

from ..core.config import NOW
from ..db import FIXTURES, connect, insert_audit
from ..providers.mock_model_gateway import copy_variants_for_layer, localized_text_by_locale


def _score_checks(checks: list[dict[str, Any]]) -> tuple[float, bool]:
    if not checks:
        return 0.0, False
    passed = sum(1 for check in checks if check["passed"])
    score = round(passed / len(checks), 3)
    return score, passed == len(checks)


def _evaluate_copy_sample(sample: dict[str, Any]) -> dict[str, Any]:
    variants = copy_variants_for_layer(sample["layerId"])
    best_text = variants[0]["text"]
    lower_text = best_text.lower()
    banned = [phrase for phrase in sample.get("bannedPhrases", []) if phrase.lower() in lower_text]
    missing_terms = [term for term in sample.get("requiredTerms", []) if term.lower() not in lower_text]
    checks = [
        {"name": "schema_valid", "passed": all("variantId" in variant and "text" in variant and "score" in variant for variant in variants)},
        {"name": "required_terms_present", "passed": not missing_terms, "missingTerms": missing_terms},
        {"name": "banned_phrases_absent", "passed": not banned, "bannedPhrasesFound": banned},
        {"name": "max_length_respected", "passed": len(best_text) <= int(sample["maxCharacters"]), "characters": len(best_text)},
    ]
    score, passed = _score_checks(checks)
    return {"sampleId": sample["sampleId"], "operationType": "copy", "score": score, "passed": passed, "checks": checks, "outputPreview": best_text}


def _evaluate_localization_sample(sample: dict[str, Any]) -> dict[str, Any]:
    locale_text = localized_text_by_locale()
    required = sample.get("requiredLocales", [])
    outputs = [{"locale": locale, "text": locale_text[locale]} for locale in required if locale in locale_text]
    joined = " ".join(output["text"].lower() for output in outputs)
    banned = [phrase for phrase in sample.get("bannedPhrases", []) if phrase.lower() in joined]
    over_limit = [output["locale"] for output in outputs if len(output["text"]) > int(sample["maxCharacters"])]
    checks = [
        {"name": "schema_valid", "passed": all("locale" in output and "text" in output for output in outputs)},
        {"name": "locale_coverage", "passed": len(outputs) == len(required), "expected": len(required), "actual": len(outputs)},
        {"name": "banned_phrases_absent", "passed": not banned, "bannedPhrasesFound": banned},
        {"name": "max_length_respected", "passed": not over_limit, "overLimitLocales": over_limit},
    ]
    score, passed = _score_checks(checks)
    return {
        "sampleId": sample["sampleId"],
        "operationType": "localization",
        "score": score,
        "passed": passed,
        "checks": checks,
        "outputPreview": json.dumps(outputs, ensure_ascii=False),
    }


def run_quality_gate() -> dict[str, Any]:
    fixture = json.loads((FIXTURES / "golden-samples.json").read_text())
    results = []
    for sample in fixture["samples"]:
        if sample["operationType"] == "copy":
            results.append(_evaluate_copy_sample(sample))
        elif sample["operationType"] == "localization":
            results.append(_evaluate_localization_sample(sample))
        else:
            raise HTTPException(status_code=400, detail={"code": "quality_gate_failed", "message": "Unsupported golden sample operation."})
    aggregate = round(sum(result["score"] for result in results) / len(results), 3)
    passed = aggregate >= float(fixture["threshold"]) and all(result["passed"] for result in results)
    return {
        "requestId": "req_quality_001",
        "qualityRunId": "quality_run_001",
        "provider": fixture["provider"],
        "model": fixture["model"],
        "threshold": fixture["threshold"],
        "score": aggregate,
        "passed": passed,
        "sampleCount": len(results),
        "results": results,
    }


def evaluate_and_persist_quality_gate() -> dict[str, Any]:
    result = run_quality_gate()
    with connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO model_quality_runs
            (run_id, provider, model, threshold, score, passed, sample_count, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result["qualityRunId"],
                result["provider"],
                result["model"],
                result["threshold"],
                result["score"],
                1 if result["passed"] else 0,
                result["sampleCount"],
                NOW,
            ),
        )
        for index, sample_result in enumerate(result["results"], start=1):
            conn.execute(
                """
                INSERT OR REPLACE INTO model_quality_results
                (result_id, run_id, sample_id, operation_type, score, passed, checks_json, output_preview, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"quality_result_{index:03d}",
                    result["qualityRunId"],
                    sample_result["sampleId"],
                    sample_result["operationType"],
                    sample_result["score"],
                    1 if sample_result["passed"] else 0,
                    json.dumps(sample_result["checks"], ensure_ascii=False),
                    sample_result["outputPreview"],
                    NOW,
                ),
            )
        insert_audit(
            conn,
            "audit_quality_gate_001",
            "model_quality_gate_completed",
            operation_id=result["qualityRunId"],
            payload={"provider": result["provider"], "model": result["model"], "score": result["score"], "passed": result["passed"]},
        )
        conn.commit()
    return {
        **result,
        "qualityGate": {
            "goldenSampleSet": "project/poc/fixtures/golden-samples.json",
            "proves": "Executable provider-quality gate mechanics against local golden samples.",
            "doesNotProve": "Live paid or approved model-provider quality in a production environment.",
        },
    }

