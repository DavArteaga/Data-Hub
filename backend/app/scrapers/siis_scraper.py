"""Supersociedades SIIS scraper — Sistema Integrado de Información Societaria.

Uses Playwright to navigate the Angular SPA at siis.ia.supersociedades.gov.co
and extract financial statement data (ingresos, activos) by NIT.

Requires:
    pip install playwright
    playwright install chromium
"""
from __future__ import annotations

import re
from typing import Any

from app.scrapers.base import BaseScraper, ScrapeResult

SIIS_URL = "https://siis.ia.supersociedades.gov.co/#/"
SIIS_SEARCH_FRAGMENT = "https://siis.ia.supersociedades.gov.co/#/empresas"


def _clean(text: str) -> str:
    return " ".join(text.strip().split())


def _to_float(text: str) -> float | None:
    cleaned = re.sub(r"[^0-9.\-]", "", text.replace(",", ""))
    try:
        return float(cleaned)
    except ValueError:
        return None


def _extract_year(text: str) -> int | None:
    m = re.search(r"(20\d{2})", text)
    return int(m.group(1)) if m else None


class SiisScraper(BaseScraper):
    """Scrapes financial statements from Supersociedades SIIS by NIT."""

    FUENTE_NOMBRE = "Superintendencia de Sociedades"

    def __init__(self, nits: list[str] | None = None, timeout: int = 60) -> None:
        super().__init__(fuente_nombre=self.FUENTE_NOMBRE, timeout=timeout)
        self.nits: list[str] = nits or []

    async def fetch(self, **kwargs: Any) -> ScrapeResult:
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            return self._make_result(
                records=[],
                registros_rechazados=0,
                estado="error",
                mensaje=(
                    "playwright no está instalado. "
                    "Ejecuta: pip install playwright && playwright install chromium"
                ),
            )

        nits = list(kwargs.get("nits", self.nits))
        if not nits:
            return self._make_result(
                records=[],
                registros_rechazados=0,
                estado="warn",
                mensaje="No NITs proporcionados a SiisScraper.",
            )

        records: list[dict[str, Any]] = []
        rechazados = 0

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            ctx = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                locale="es-CO",
            )
            page = await ctx.new_page()
            page.set_default_timeout(self.timeout * 1000)

            for nit in nits:
                try:
                    recs = await self._scrape_one(page, nit)
                    records.extend(recs)
                    if not recs:
                        rechazados += 1
                except Exception:
                    rechazados += 1

            await browser.close()

        estado = "ok" if rechazados == 0 else ("warn" if records else "error")
        mensaje = f"{rechazados} NITs sin resultado en SIIS." if rechazados else None
        return self._make_result(
            records=records,
            registros_ingestados=len(records),
            registros_rechazados=rechazados,
            estado=estado,
            mensaje=mensaje,
        )

    async def _scrape_one(self, page: Any, nit: str) -> list[dict[str, Any]]:
        from playwright.async_api import TimeoutError as PWTimeout

        bare_nit = nit.split("-")[0].strip()

        # Navigate to SIIS and search by NIT
        await page.goto(SIIS_URL, wait_until="networkidle", timeout=self.timeout * 1000)

        # Look for search input (Angular SPA — try multiple selectors)
        input_selectors = [
            "input[placeholder*='NIT']",
            "input[placeholder*='nit']",
            "input[placeholder*='empresa']",
            "input[matinput]",
            "input[type='text']",
            "mat-form-field input",
        ]
        search_input = None
        for sel in input_selectors:
            try:
                el = page.locator(sel).first
                await el.wait_for(state="visible", timeout=3000)
                search_input = el
                break
            except PWTimeout:
                continue

        if search_input is None:
            return []

        await search_input.triple_click()
        await search_input.fill(bare_nit)
        await page.keyboard.press("Enter")

        # Wait for Angular to load results
        try:
            await page.wait_for_load_state("networkidle", timeout=15_000)
        except PWTimeout:
            pass

        records: list[dict[str, Any]] = []

        # Try to find financial data rows — look for income/asset values
        # SIIS typically shows a financial statements table
        row_selectors = [
            "table tbody tr",
            "mat-table mat-row",
            "[class*='row'][class*='financial']",
            ".mat-row",
        ]
        rows = []
        for sel in row_selectors:
            found = await page.locator(sel).all()
            if found:
                rows = found
                break

        for row in rows:
            text = _clean(await row.inner_text())
            valor = None
            anio = _extract_year(text)
            indicador = None

            low = text.lower()
            if any(k in low for k in ["ingresos de actividades", "ingresos operacionales", "ingresos netos"]):
                indicador = "ingresos_anuales"
                nums = re.findall(r"[\d,\.]+", text)
                for n in reversed(nums):
                    v = _to_float(n)
                    if v and v > 1_000:
                        valor = v
                        break
            elif any(k in low for k in ["activo total", "total activos", "total del activo"]):
                indicador = "activos_totales"
                nums = re.findall(r"[\d,\.]+", text)
                for n in reversed(nums):
                    v = _to_float(n)
                    if v and v > 1_000:
                        valor = v
                        break

            if indicador and valor and anio:
                records.append({
                    "nit": nit,
                    "indicador": indicador,
                    "anio": anio,
                    "valor_numerico": valor,
                    "fuente": self.fuente_nombre,
                })

        return records
