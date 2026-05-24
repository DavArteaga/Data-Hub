"""Mock scraper for DataCore Hub.

Reads data/raw/sample_empresas.csv and generates plausible indicator values
for each company so the ingestion pipeline works end-to-end without any
external network dependency.
"""
from __future__ import annotations

import csv
import random
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.config import BASE_DIR
from app.scrapers.base import BaseScraper, ScrapeResult

_CSV_PATH = BASE_DIR / "data" / "raw" / "sample_empresas.csv"

# Base values for Empresa A (nit 900111111-1) — others are scaled down
_BASE_VALUES: dict[str, dict[str, float]] = {
    "900111111-1": {
        "num_empleados": 47.0,
        "ingresos_anuales": 1_280_000_000.0,
        "activos_totales": 850_000_000.0,
    },
    "900222222-2": {
        "num_empleados": 38.0,
        "ingresos_anuales": 1_050_000_000.0,
        "activos_totales": 720_000_000.0,
    },
    "900333333-3": {
        "num_empleados": 29.0,
        "ingresos_anuales": 820_000_000.0,
        "activos_totales": 560_000_000.0,
    },
    "900444444-4": {
        "num_empleados": 21.0,
        "ingresos_anuales": 590_000_000.0,
        "activos_totales": 410_000_000.0,
    },
    "900555555-5": {
        "num_empleados": 14.0,
        "ingresos_anuales": 380_000_000.0,
        "activos_totales": 270_000_000.0,
    },
    "900666666-6": {
        "num_empleados": 0.0,
        "ingresos_anuales": 0.0,
        "activos_totales": 95_000_000.0,
    },
}


def _scale(base: float, year: int, base_year: int = 2024) -> float:
    """Apply a small year-over-year growth factor so historical values differ."""
    diff = base_year - year  # positive = older
    factor = (0.92) ** diff  # ~8 % annual growth going forward
    # Add a small random jitter (±3 %)
    jitter = 1.0 + random.uniform(-0.03, 0.03)
    return round(base * factor * jitter, 2)


class MockScraper(BaseScraper):
    """Reads the CSV seed file and builds synthetic Valor records."""

    def __init__(self, fuente_nombre: str = "RUES", timeout: int = 30) -> None:
        super().__init__(fuente_nombre=fuente_nombre, timeout=timeout)

    async def fetch(self, **kwargs: Any) -> ScrapeResult:  # type: ignore[override]
        records: list[dict[str, Any]] = []
        rechazados = 0

        if not _CSV_PATH.exists():
            return self._make_result(
                records=[],
                registros_ingestados=0,
                registros_rechazados=0,
                estado="error",
                mensaje=f"CSV not found: {_CSV_PATH}",
            )

        with _CSV_PATH.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                nit = row.get("nit", "").strip()
                if not nit:
                    rechazados += 1
                    continue

                base = _BASE_VALUES.get(nit, {
                    "num_empleados": 5.0,
                    "ingresos_anuales": 50_000_000.0,
                    "activos_totales": 30_000_000.0,
                })

                for anio in range(2015, 2025):
                    for indicador, base_val in base.items():
                        records.append({
                            "nit": nit,
                            "razon_social": row.get("razon_social", ""),
                            "ciiu_principal": row.get("ciiu_principal", ""),
                            "estado": row.get("estado", "Activa"),
                            "fecha_constitucion": row.get("fecha_constitucion", ""),
                            "indicador": indicador,
                            "anio": anio,
                            "valor_numerico": _scale(base_val, anio),
                            "fuente": self.fuente_nombre,
                        })

        return self._make_result(
            records=records,
            registros_ingestados=len(records),
            registros_rechazados=rechazados,
            estado="ok",
            mensaje=None,
        )
