"""Scraper for datos.gov.co — Supersociedades financial datasets via Socrata SODA API.

Datasets used:
  prwj-nzxa : Estado de Resultado Integral  → ingresos_anuales
  pfdp-zks5 : Estado de Situación Financiera → activos_totales
"""
from __future__ import annotations

from typing import Any

import httpx

from app.scrapers.base import BaseScraper, ScrapeResult

SODA_BASE = "https://www.datos.gov.co/resource"
INGRESOS_DATASET = "prwj-nzxa"
ACTIVOS_DATASET = "pfdp-zks5"

_INGRESOS_KEYWORDS = [
    "ingresos de actividades ordinarias",
    "ingresos operacionales",
    "total ingresos operacionales",
    "ingresos netos",
    "otros ingresos",
]
_ACTIVOS_KEYWORDS = [
    "total de activos",
    "activo total",
    "total activos",
    "total del activo",
    "activos totales",
]


def _bare(nit: str) -> str:
    """Strip check digit and whitespace: '900111111-1' → '900111111'."""
    return nit.split("-")[0].strip()


def _matches(text: str, keywords: list[str]) -> bool:
    t = text.lower().strip()
    return any(k in t for k in keywords)


def _to_float(raw: Any) -> float | None:
    try:
        return float(str(raw).replace(",", "").replace(" ", ""))
    except (ValueError, TypeError):
        return None


def _to_year(raw: Any) -> int | None:
    try:
        return int(str(raw).strip()[:4])
    except (ValueError, TypeError):
        return None


class DatosGovScraper(BaseScraper):
    """Queries datos.gov.co SODA API for Supersociedades financial data by NIT."""

    FUENTE_NOMBRE = "datos.gov.co"

    def __init__(self, nits: list[str] | None = None, timeout: int = 30) -> None:
        super().__init__(fuente_nombre=self.FUENTE_NOMBRE, timeout=timeout)
        self.nits: list[str] = nits or []

    async def fetch(self, **kwargs: Any) -> ScrapeResult:
        nits = list(kwargs.get("nits", self.nits))
        if not nits:
            return self._make_result(
                records=[],
                registros_rechazados=0,
                estado="warn",
                mensaje="No NITs provided to DatosGovScraper.",
            )

        records: list[dict[str, Any]] = []
        rechazados = 0

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for nit in nits:
                bare = _bare(nit)
                for fetch_fn, indicator in [
                    (self._fetch_ingresos, "ingresos_anuales"),
                    (self._fetch_activos, "activos_totales"),
                ]:
                    try:
                        recs = await fetch_fn(client, nit, bare)
                        records.extend(recs)
                    except httpx.HTTPError:
                        rechazados += 1
                    except Exception:
                        rechazados += 1

        if not records and rechazados == 0:
            return self._make_result(
                records=[],
                registros_rechazados=0,
                estado="warn",
                mensaje="No matching financial records found for the given NITs.",
            )

        estado = "ok" if rechazados == 0 else "warn"
        mensaje = f"{rechazados} requests failed." if rechazados else None
        return self._make_result(
            records=records,
            registros_ingestados=len(records),
            registros_rechazados=rechazados,
            estado=estado,
            mensaje=mensaje,
        )

    async def _query_soda(
        self, client: httpx.AsyncClient, dataset_id: str, bare_nit: str
    ) -> list[dict[str, Any]]:
        url = f"{SODA_BASE}/{dataset_id}.json"
        resp = await client.get(
            url,
            params={
                "$where": f"nit='{bare_nit}'",
                "$limit": "500",
                "$order": "periodo DESC",
            },
        )
        resp.raise_for_status()
        return resp.json()

    async def _fetch_ingresos(
        self, client: httpx.AsyncClient, nit_full: str, bare_nit: str
    ) -> list[dict[str, Any]]:
        rows = await self._query_soda(client, INGRESOS_DATASET, bare_nit)
        out = []
        for row in rows:
            concepto = row.get("concepto", "")
            if not _matches(concepto, _INGRESOS_KEYWORDS):
                continue
            valor = _to_float(row.get("valor"))
            if valor is None:
                continue
            anio = _to_year(row.get("periodo") or row.get("fecha_corte"))
            if anio is None:
                continue
            out.append({
                "nit": nit_full,
                "indicador": "ingresos_anuales",
                "anio": anio,
                "valor_numerico": valor,
                "fuente": self.fuente_nombre,
            })
        return out

    async def _fetch_activos(
        self, client: httpx.AsyncClient, nit_full: str, bare_nit: str
    ) -> list[dict[str, Any]]:
        rows = await self._query_soda(client, ACTIVOS_DATASET, bare_nit)
        out = []
        for row in rows:
            concepto = row.get("concepto", "")
            if not _matches(concepto, _ACTIVOS_KEYWORDS):
                continue
            valor = _to_float(row.get("valor"))
            if valor is None:
                continue
            anio = _to_year(row.get("periodo") or row.get("fecha_corte"))
            if anio is None:
                continue
            out.append({
                "nit": nit_full,
                "indicador": "activos_totales",
                "anio": anio,
                "valor_numerico": valor,
                "fuente": self.fuente_nombre,
            })
        return out
