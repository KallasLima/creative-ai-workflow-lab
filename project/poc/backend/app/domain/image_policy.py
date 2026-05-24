from __future__ import annotations

from typing import Any

IMAGE_POLICY_CHECKS = ["placeholder_only", "ideation_only", "no_public_figure", "no_protected_mark", "no_final_asset_claim"]
IMAGE_PROMPT_BLOCKS: list[tuple[str, tuple[str, ...]]] = [
    ("public_figure_or_likeness", ("public figure", "celebrity", "famous person", "likeness")),
    ("protected_mark", ("protected logo", "trademark", "brand logo", "competitor logo")),
    ("publication_or_final_asset", ("final campaign", "publication-ready", "final asset", "ready to publish")),
    ("sensitive_claim", ("medical claim", "political endorsement", "before and after")),
]


def evaluate_image_prompt_policy(prompt: str) -> dict[str, Any]:
    normalized = " ".join(prompt.lower().split())
    categories = [category for category, terms in IMAGE_PROMPT_BLOCKS if any(term in normalized for term in terms)]
    return {
        "allowed": not categories,
        "categories": categories,
        "policyChecks": IMAGE_POLICY_CHECKS,
        "rightsStatus": "ideation_only",
        "safetyStatus": "passed" if not categories else "requires_review",
    }

