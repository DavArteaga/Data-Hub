"""RUES scraper stub.

In production this would send HTTP requests to https://www.rues.org.co.
For the MVP it delegates to the mock scraper so the pipeline always works
without network access.
"""
from __future__ import annotations

from app.scrapers.base import BaseScraper, ScrapeResult
from app.scrapers.mock_scraper import MockScraper


class RuesScraper(BaseScraper):
    """Registro Único Empresarial y Social (RUES) scraper."""

    def __init__(self, timeout: int = 30) -> None:
        super().__init__(fuente_nombre="RUES", timeout=timeout)
        self._mock = MockScraper(fuente_nombre="RUES", timeout=timeout)

    async def fetch(self, **kwargs) -> ScrapeResult:  # type: ignore[override]
        """Delegate to mock for MVP; replace with real HTTP logic for production."""
        result = await self._mock.fetch(**kwargs)
        result.fuente_nombre = self.fuente_nombre
        return result
