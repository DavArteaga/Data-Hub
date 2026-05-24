"""RUES scraper — Registro Único Empresarial y Social.

Uses Playwright to search companies by NIT on rues.org.co.
Extracts: razon_social, estado, CIIU, and registration data.

Requires:
    pip install playwright
    playwright install chromium
"""
from __future__ import annotations

import re
from typing import Any

from app.scrapers.base import BaseScraper, ScrapeResult

SEARCH_URL = "https://www.rues.org.co/busqueda-avanzada"


def _clean(text: str) -> str:
    return " ".join(text.strip().split())


class RuesScraper(BaseScraper):
    """Scrapes company registration data from RUES for a list of NITs."""

    FUENTE_NOMBRE = "RUES"

    def __init__(self, nits: list[str] | None = None, timeout: int = 60) -> None:
        super().__init__(fuente_nombre=self.FUENTE_NOMBRE, timeout=timeout)
        self.nits: list[str] = nits or []

    async def fetch(self, **kwargs: Any) -> ScrapeResult:
        try:
            from playwright.async_api import async_playwright, TimeoutError as PWTimeout
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
                mensaje="No NITs proporcionados a RuesScraper.",
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
                    rec = await self._scrape_one(page, nit)
                    if rec:
                        records.append(rec)
                    else:
                        rechazados += 1
                except Exception:
                    rechazados += 1

            await browser.close()

        estado = "ok" if rechazados == 0 else ("warn" if records else "error")
        mensaje = f"{rechazados} NITs sin resultado en RUES." if rechazados else None
        return self._make_result(
            records=records,
            registros_ingestados=len(records),
            registros_rechazados=rechazados,
            estado=estado,
            mensaje=mensaje,
        )

    async def _scrape_one(self, page: Any, nit: str) -> dict[str, Any] | None:
        from playwright.async_api import TimeoutError as PWTimeout

        bare_nit = nit.split("-")[0].strip()
        await page.goto(SEARCH_URL, wait_until="networkidle", timeout=self.timeout * 1000)

        # Try multiple selector strategies for the NIT search input
        input_selectors = [
            "input[placeholder*='NIT']",
            "input[placeholder*='nit']",
            "input[name='nit']",
            "input[id*='nit']",
            "input[type='text']",
        ]
        nit_input = None
        for sel in input_selectors:
            try:
                el = page.locator(sel).first
                await el.wait_for(state="visible", timeout=3000)
                nit_input = el
                break
            except PWTimeout:
                continue

        if nit_input is None:
            return None

        await nit_input.triple_click()
        await nit_input.fill(bare_nit)
        await page.keyboard.press("Enter")

        # Wait for results
        try:
            await page.wait_for_selector(
                "table tbody tr, .result-item, .empresa-item, [class*='result']",
                timeout=10_000,
            )
        except PWTimeout:
            return None

        # Extract data from first result row
        razon_social = ""
        estado_text = "Activa"
        ciiu_text = "0000"

        # Try table structure
        rows = await page.locator("table tbody tr").all()
        if rows:
            first = rows[0]
            cells = await first.locator("td").all()
            texts = [_clean(await c.inner_text()) for c in cells]
            for i, t in enumerate(texts):
                if len(t) > 5 and not re.match(r"^\d", t):
                    razon_social = razon_social or t
                if re.match(r"^\d{4}$", t):
                    ciiu_text = t
                if t.lower() in ("activa", "inactiva", "cancelada", "disuelta", "liquidada"):
                    estado_text = t.capitalize()

        # Try card/list structure if table didn't work
        if not razon_social:
            card_sel = "[class*='result'] [class*='name'], [class*='razon'], h3, h4"
            try:
                el = page.locator(card_sel).first
                razon_social = _clean(await el.inner_text())
            except Exception:
                pass

        if not razon_social:
            return None

        return {
            "nit": nit,
            "razon_social": razon_social,
            "ciiu_principal": ciiu_text,
            "estado": estado_text,
            # RUES does not expose financial indicators — record valor=None
            "indicador": "num_empleados",
            "anio": 2024,
            "valor_numerico": None,
            "fuente": self.fuente_nombre,
        }
