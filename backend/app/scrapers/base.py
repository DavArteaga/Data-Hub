"""Abstract base class for all DataCore Hub scrapers."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class ScrapeResult:
    fuente_nombre: str
    records: list[dict[str, Any]] = field(default_factory=list)
    registros_ingestados: int = 0
    registros_rechazados: int = 0
    estado: str = "ok"          # ok | warn | error
    mensaje: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


class BaseScraper(ABC):
    """All scrapers inherit from this class."""

    def __init__(self, fuente_nombre: str, timeout: int = 30) -> None:
        self.fuente_nombre = fuente_nombre
        self.timeout = timeout

    @abstractmethod
    async def fetch(self, **kwargs: Any) -> ScrapeResult:
        """Execute the scraping / import logic and return a ScrapeResult."""

    def _make_result(self, **kwargs: Any) -> ScrapeResult:
        return ScrapeResult(fuente_nombre=self.fuente_nombre, **kwargs)
