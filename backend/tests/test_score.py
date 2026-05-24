"""Unit tests for the score engine."""
from __future__ import annotations

import pytest

from app.services.score import (
    calculate_score,
    compute_actualidad,
    consensus_message,
    explain_score,
)


# ---------------------------------------------------------------------------
# calculate_score
# ---------------------------------------------------------------------------

def test_calculate_score_perfect() -> None:
    score = calculate_score(1.0, 1.0, 1.0)
    assert score == 1.0


def test_calculate_score_zero() -> None:
    score = calculate_score(0.0, 0.0, 0.0)
    assert score == 0.0


def test_calculate_score_formula() -> None:
    # 0.3*0.8 + 0.3*0.9 + 0.4*0.95 = 0.24 + 0.27 + 0.38 = 0.89
    score = calculate_score(0.8, 0.9, 0.95)
    assert abs(score - 0.89) < 1e-4


def test_calculate_score_clamped_below() -> None:
    assert calculate_score(-1.0, -1.0, -1.0) == 0.0


def test_calculate_score_clamped_above() -> None:
    assert calculate_score(2.0, 2.0, 2.0) == 1.0


def test_calculate_score_empresa_a() -> None:
    """Empresa A target ≈ 0.92."""
    # completitud=1.0, actualidad≈0.8 (2024, ref 2026 → 2 years), tier=0.95
    score = calculate_score(1.0, 0.8, 0.95)
    # 0.3 + 0.24 + 0.38 = 0.92
    assert abs(score - 0.92) < 0.01


# ---------------------------------------------------------------------------
# explain_score
# ---------------------------------------------------------------------------

def test_explain_score_keys() -> None:
    breakdown = explain_score(1.0, 0.8, 0.95)
    expected_keys = {
        "completitud", "actualidad", "tier_fuente",
        "contribucion_completitud", "contribucion_actualidad", "contribucion_tier",
        "score_final", "calculo", "formula",
    }
    assert expected_keys.issubset(breakdown.keys())


def test_explain_score_values() -> None:
    breakdown = explain_score(0.5, 0.5, 0.5)
    assert breakdown["score_final"] == calculate_score(0.5, 0.5, 0.5)
    assert breakdown["contribucion_completitud"] == pytest.approx(0.15)
    assert breakdown["contribucion_actualidad"] == pytest.approx(0.15)
    assert breakdown["contribucion_tier"] == pytest.approx(0.20)


# ---------------------------------------------------------------------------
# compute_actualidad
# ---------------------------------------------------------------------------

def test_actualidad_current_year() -> None:
    assert compute_actualidad(2024, 2024) == 1.0


def test_actualidad_5_years_ago() -> None:
    val = compute_actualidad(2019, 2024)
    assert val == pytest.approx(0.5)


def test_actualidad_10_years_ago() -> None:
    assert compute_actualidad(2014, 2024) == 0.0


def test_actualidad_older_than_10() -> None:
    assert compute_actualidad(2000, 2024) == 0.0


def test_actualidad_2_years_ago() -> None:
    val = compute_actualidad(2022, 2024)
    assert val == pytest.approx(0.8)


# ---------------------------------------------------------------------------
# consensus_message
# ---------------------------------------------------------------------------

def test_consensus_single_source() -> None:
    msg = consensus_message([100.0])
    assert "única" in msg.lower()


def test_consensus_high_agreement() -> None:
    msg = consensus_message([100.0, 101.0, 99.5])
    assert "concordancia" in msg.lower()


def test_consensus_medium_divergence() -> None:
    msg = consensus_message([100.0, 115.0])
    assert "divergencia" in msg.lower()


def test_consensus_high_divergence() -> None:
    msg = consensus_message([100.0, 180.0])
    assert "alta divergencia" in msg.lower()


def test_consensus_all_zero() -> None:
    msg = consensus_message([0.0, 0.0])
    assert "cero" in msg.lower()
