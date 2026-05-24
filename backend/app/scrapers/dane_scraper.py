"""DANE scraper — Directorio Estadístico de Empresas.

Downloads the DANE DEE (Directorio Estadístico de Empresas) Excel file,
parses it, and extracts num_empleados by NIT.

The DEE is published at:
  https://www.dane.gov.co/index.php/estadisticas-por-tema/industria/directorio-estadistico-de-empresas

Requires:
    pip install openpyxl
"""
from __future__ import annotations

import io
import re
from typing import Any

import httpx

from app.scrapers.base import BaseScraper, ScrapeResult

# Latest DEE Excel download URL (2023 edition — update when DANE publishes newer)
# This URL comes from the DANE DEE page linked in the project sources.
DEE_EXCEL_URL = (
    "https://www.dane.gov.co/files/operaciones/DEE/anexos/dee2022_resultados.xlsx"
)

# Fallback: try alternative year if above returns 404
DEE_EXCEL_FALLBACK = (
    "https://www.dane.gov.co/files/operaciones/DEE/anexos/dee2021_resultados.xlsx"
)

# Column name patterns to locate NIT and employee count
NIT_COL_PATTERNS = ["nit", "numero_identificacion", "identificacion"]
EMP_COL_PATTERNS = ["personal_ocupado", "empleados", "num_empleados", "total_personal"]
YEAR_COL_PATTERNS = ["anio", "año", "year", "periodo"]


def _find_col(headers: list[str], patterns: list[str]) -> int | None:
    for pat in patterns:
        for i, h in enumerate(headers):
            if pat in h.lower().replace(" ", "_"):
                return i
    return None


def _bare(nit: str) -> str:
    return nit.split("-")[0].strip()


class DaneScraper(BaseScraper):
    """Downloads and parses DANE DEE Excel to extract num_empleados by NIT."""

    FUENTE_NOMBRE = "DANE"

    def __init__(self, nits: list[str] | None = None, timeout: int = 60) -> None:
        super().__init__(fuente_nombre=self.FUENTE_NOMBRE, timeout=timeout)
        self.nits: list[str] = nits or []

    async def fetch(self, **kwargs: Any) -> ScrapeResult:
        try:
            import openpyxl
        except ImportError:
            return self._make_result(
                records=[],
                registros_rechazados=0,
                estado="error",
                mensaje="openpyxl no está instalado. Ejecuta: pip install openpyxl",
            )

        nits = list(kwargs.get("nits", self.nits))

        # Download the Excel file
        content = await self._download_excel()
        if content is None:
            return self._make_result(
                records=[],
                registros_rechazados=0,
                estado="error",
                mensaje="No se pudo descargar el archivo DEE del DANE. Verifique la URL.",
            )

        # Parse
        records, rechazados = self._parse_excel(content, nits)

        if not records:
            return self._make_result(
                records=[],
                registros_rechazados=rechazados,
                estado="warn",
                mensaje="Archivo DEE descargado pero sin coincidencias para los NITs dados.",
            )

        return self._make_result(
            records=records,
            registros_ingestados=len(records),
            registros_rechazados=rechazados,
            estado="ok",
            mensaje=None,
        )

    async def _download_excel(self) -> bytes | None:
        async with httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 DataCore Hub Scraper"},
        ) as client:
            for url in [DEE_EXCEL_URL, DEE_EXCEL_FALLBACK]:
                try:
                    resp = await client.get(url)
                    if resp.status_code == 200:
                        return resp.content
                except httpx.HTTPError:
                    continue
        return None

    def _parse_excel(
        self, content: bytes, nits: list[str]
    ) -> tuple[list[dict[str, Any]], int]:
        import openpyxl

        nit_set = {_bare(n) for n in nits}
        nit_map = {_bare(n): n for n in nits}

        wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
        records: list[dict[str, Any]] = []
        rechazados = 0

        for ws in wb.worksheets:
            rows = ws.iter_rows(values_only=True)
            header_row = next(rows, None)
            if header_row is None:
                continue
            headers = [str(h or "").strip() for h in header_row]

            nit_col = _find_col(headers, NIT_COL_PATTERNS)
            emp_col = _find_col(headers, EMP_COL_PATTERNS)
            year_col = _find_col(headers, YEAR_COL_PATTERNS)

            if nit_col is None or emp_col is None:
                continue

            for row in rows:
                if not row or nit_col >= len(row):
                    continue
                raw_nit = str(row[nit_col] or "").strip().split("-")[0]
                if raw_nit not in nit_set:
                    continue

                emp_val = row[emp_col] if emp_col < len(row) else None
                try:
                    emp_num = float(str(emp_val or "0").replace(",", ""))
                except (ValueError, TypeError):
                    rechazados += 1
                    continue

                anio = 2022
                if year_col is not None and year_col < len(row):
                    try:
                        anio = int(str(row[year_col] or "2022")[:4])
                    except (ValueError, TypeError):
                        pass

                full_nit = nit_map.get(raw_nit, raw_nit)
                records.append({
                    "nit": full_nit,
                    "indicador": "num_empleados",
                    "anio": anio,
                    "valor_numerico": emp_num,
                    "fuente": self.fuente_nombre,
                })

        return records, rechazados
