"""DataCore Hub API – main application entry-point."""
from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.config import settings
from app.database import AsyncSessionLocal, init_db
from app.models.db import Fuente
from app.models.schemas import HealthResponse
from app.routers import bitacora, empresas, fuentes, indicadores, ingesta

logger = logging.getLogger("datacore.startup")
logging.basicConfig(level=logging.INFO)

_START_TIME: float = 0.0


async def _seed_if_empty() -> None:
    """Run scripts/init_db.seed() if the fuentes table is empty.

    Render's free tier has ephemeral filesystem, so the SQLite file is wiped
    on every cold start. This ensures the demo always has data without needing
    a manual seed step.
    """
    async with AsyncSessionLocal() as session:
        existing = await session.execute(select(Fuente).limit(1))
        if existing.scalar_one_or_none() is None:
            logger.info("Empty DB detected – running seed...")
            # Import here to avoid circular dependency at module load
            from scripts.init_db import seed
            await seed()
            logger.info("Seed completed.")
        else:
            logger.info("DB already seeded – skipping.")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    global _START_TIME
    _START_TIME = time.time()
    await init_db()
    try:
        await _seed_if_empty()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Seed step failed (non-fatal): %s", exc)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "DataCore Hub – motor de ingesta, normalización y scoring de datos "
        "empresariales colombianos."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
# Browser spec forbids `allow_credentials=True` together with `allow_origins=["*"]`.
# Disable credentials when wildcard is in use (we don't use cookies anyway).
origins = settings.cors_origins_list
_allow_credentials = origins != ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https://.*\.vercel\.app" if origins == ["*"] else None,
    allow_credentials=_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
API_PREFIX = "/api/v1"

app.include_router(empresas.router, prefix=API_PREFIX)
app.include_router(indicadores.router, prefix=API_PREFIX)
app.include_router(fuentes.router, prefix=API_PREFIX)
app.include_router(ingesta.router, prefix=API_PREFIX)
app.include_router(bitacora.router, prefix=API_PREFIX)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/api/v1/health", response_model=HealthResponse, tags=["health"])
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=settings.APP_NAME,
        version=settings.APP_VERSION,
        uptime_seconds=round(time.time() - _START_TIME, 2),
    )
