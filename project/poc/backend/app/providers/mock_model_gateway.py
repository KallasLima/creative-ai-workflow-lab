from __future__ import annotations


def copy_variants_for_layer(layer_id: str) -> list[dict]:
    if layer_id == "txt_cta":
        return [
            {"variantId": "v1", "text": "Shop spring gear", "score": 0.9},
            {"variantId": "v2", "text": "Find your run kit", "score": 0.87},
            {"variantId": "v3", "text": "Start your spring run", "score": 0.85},
        ]
    return [
        {"variantId": "v1", "text": "Spring miles start with gear that keeps up.", "score": 0.91},
        {"variantId": "v2", "text": "Built for longer runs and brighter days.", "score": 0.88},
        {"variantId": "v3", "text": "Your spring run kit, ready for every mile.", "score": 0.86},
    ]


def localized_text_by_locale() -> dict[str, str]:
    return {
        "fr-FR": "Découvrir la collection",
        "de-DE": "Kollektion shoppen",
        "es-ES": "Compra la colección",
        "pt-BR": "Compre a coleção",
        "it-IT": "Scopri la collezione",
        "nl-NL": "Shop de collectie",
        "ja-JP": "コレクションを見る",
        "ko-KR": "컬렉션 쇼핑하기",
    }

