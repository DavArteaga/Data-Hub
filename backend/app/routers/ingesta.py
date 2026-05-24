"""Router: /ingesta"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.etl.pipeline import run_ingestion
from app.models.schemas import IngestaResponse

router = APIRouter(prefix="/ingesta", tags=["ingesta"])


@router.post("/{fuente_nombre}", response_model=IngestaResponse)
async def trigger_ingesta(
    fuente_nombre: str,
    db: AsyncSession = Depends(get_db),
) -> IngestaResponse:
    """Trigger a mock ingestion for the specified data source.

    fuente_nombre must match one of the registered source names exactly,
    e.g. "RUES", "DIAN", "Superintendencia de Sociedades", etc.
    """
    summary = await run_ingestion(db, fuente_nombre)
    return IngestaResponse(
        fuente=summary["fuente"],
        estado=summary["estado"],
        registros_ingestados=summary["registros_ingestados"],
        registros_rechazados=summary["registros_rechazados"],
        mensaje=summary.get("mensaje"),
    )
