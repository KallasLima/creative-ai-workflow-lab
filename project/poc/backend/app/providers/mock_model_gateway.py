from __future__ import annotations


_SUPPORTED_LOCALES = ["fr-FR", "de-DE", "es-ES", "pt-BR", "it-IT", "nl-NL", "ja-JP", "ko-KR"]

_PHRASEBOOK = {
    "shop the drop": {
        "fr-FR": "Acheter la nouveaute",
        "de-DE": "Drop shoppen",
        "es-ES": "Compra el lanzamiento",
        "pt-BR": "Comprar o lancamento",
        "it-IT": "Acquista il drop",
        "nl-NL": "Shop de drop",
        "ja-JP": "新作を見る",
        "ko-KR": "신상품 쇼핑하기",
    },
    "shop the new drop": {
        "fr-FR": "Acheter la nouvelle collection",
        "de-DE": "Neue Kollektion shoppen",
        "es-ES": "Compra la nueva coleccion",
        "pt-BR": "Comprar a nova colecao",
        "it-IT": "Scopri la nuova collezione",
        "nl-NL": "Shop de nieuwe drop",
        "ja-JP": "新作コレクションを見る",
        "ko-KR": "새 컬렉션 쇼핑하기",
    },
    "spring performance gear for every morning run": {
        "fr-FR": "Tenue performance pour chaque sortie matinale",
        "de-DE": "Performance-Gear fuer jeden Morgenlauf",
        "es-ES": "Equipo de rendimiento para cada carrera matinal",
        "pt-BR": "Equipamento de performance para toda corrida de manha",
        "it-IT": "Gear performance per ogni corsa del mattino",
        "nl-NL": "Performance gear voor elke ochtendrun",
        "ja-JP": "朝のランを支える高機能ギア",
        "ko-KR": "아침 러닝을 위한 퍼포먼스 기어",
    },
    "run further with gear built for spring.": {
        "fr-FR": "Allez plus loin avec un equipement pense pour le printemps.",
        "de-DE": "Lauf weiter mit Gear fuer den Fruehling.",
        "es-ES": "Llega mas lejos con equipo pensado para primavera.",
        "pt-BR": "Corra mais longe com equipamento feito para a primavera.",
        "it-IT": "Corri piu lontano con gear pensato per la primavera.",
        "nl-NL": "Loop verder met gear gemaakt voor de lente.",
        "ja-JP": "春に向けたギアで、もっと遠くへ。",
        "ko-KR": "봄을 위해 만든 기어로 더 멀리 달리세요.",
    },
}

_FALLBACK_PREFIXES = {
    "fr-FR": "FR brand adaptation",
    "de-DE": "DE brand adaptation",
    "es-ES": "ES brand adaptation",
    "pt-BR": "PT-BR brand adaptation",
    "it-IT": "IT brand adaptation",
    "nl-NL": "NL brand adaptation",
    "ja-JP": "JA brand adaptation",
    "ko-KR": "KO brand adaptation",
}


def _normalize(value: str) -> str:
    return " ".join(value.strip().lower().split())


def _fallback_localization(source_text: str, locale: str) -> str:
    source = source_text.strip() or "Selected layer copy"
    if len(source) > 58:
        source = source[:55].rstrip() + "..."
    return f"{_FALLBACK_PREFIXES[locale]}: {source}"


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


def localized_text_by_locale(source_text: str = "Shop the drop") -> dict[str, str]:
    exact_match = _PHRASEBOOK.get(_normalize(source_text), {})
    return {
        locale: exact_match.get(locale, _fallback_localization(source_text, locale))
        for locale in _SUPPORTED_LOCALES
    }
