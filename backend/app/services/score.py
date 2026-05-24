"""Score engine for DataCore Hub.

Formula:
    score_final = 0.3 * completitud + 0.3 * actualidad + 0.4 * tier_fuente

Where:
    - completitud  ∈ [0,1]: fraction of expected non-null fields present.
    - actualidad   ∈ [0,1]: max(0, 1 - years_since_data / 10)
    - tier_fuente  ∈ [0,1]: reliability tier of the data source.
"""
from __future__ import annotations

from datetime import date
from typing import Any


def calculate_score(
    completitud: float,
    actualidad: float,
    tier_fuente: float,
) -> float:
    """Return the weighted data-quality score clamped to [0, 1]."""
    score = 0.3 * completitud + 0.3 * actualidad + 0.4 * tier_fuente
    return round(min(max(score, 0.0), 1.0), 4)


def explain_score(
    completitud: float,
    actualidad: float,
    tier_fuente: float,
) -> dict[str, Any]:
    """Return a step-by-step breakdown of the score calculation."""
    score = calculate_score(completitud, actualidad, tier_fuente)
    c_contrib = round(0.3 * completitud, 4)
    a_contrib = round(0.3 * actualidad, 4)
    t_contrib = round(0.4 * tier_fuente, 4)
    calculo = (
        f"0.3*{completitud} + 0.3*{actualidad} + 0.4*{tier_fuente} = {score}"
    )
    return {
        "completitud": completitud,
        "actualidad": actualidad,
        "tier_fuente": tier_fuente,
        "contribucion_completitud": c_contrib,
        "contribucion_actualidad": a_contrib,
        "contribucion_tier": t_contrib,
        "score_final": score,
        "calculo": calculo,
        "formula": "score = 0.3*completitud + 0.3*actualidad + 0.4*tier_fuente",
    }


def compute_actualidad(data_year: int, reference_year: int | None = None) -> float:
    """Decay linearly: data older than 10 years scores 0."""
    if reference_year is None:
        reference_year = date.today().year
    years_since = max(0, reference_year - data_year)
    return round(max(0.0, 1.0 - years_since / 10.0), 4)


def consensus_message(values: list[float]) -> str:
    """Generate a human-readable consensus message for a set of numeric values."""
    if len(values) <= 1:
        return "Fuente única. No hay comparación disponible."
    max_v = max(values)
    min_v = min(values)
    if max_v == 0:
        return "Todas las fuentes reportan cero."
    divergence = (max_v - min_v) / max_v
    if divergence < 0.05:
        return "Alta concordancia entre fuentes."
    if divergence < 0.20:
        return "Divergencia media entre fuentes. Se prioriza la fuente de mayor tier de confiabilidad."
    return "Alta divergencia entre fuentes. Se recomienda revisión manual."
