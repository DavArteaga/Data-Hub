"""Router: /bitacora"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.db import BitacoraIngesta
from app.models.schemas import BitacoraItem, BitacoraResponse

router = APIRouter(prefix="/bitacora", tags=["bitacora"])


@router.get("", response_model=BitacoraResponse)
async def get_bitacora(
    limit: int = Query(20, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> BitacoraResponse:
    stmt = (
        select(BitacoraIngesta)
        .options(selectinload(BitacoraIngesta.fuente))
        .order_by(BitacoraIngesta.fecha.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    entries = result.scalars().all()

    items = [
        BitacoraItem(
            id=e.id,
            fuente=e.fuente.nombre,
            fecha=e.fecha,
            registros_ingestados=e.registros_ingestados,
            registros_rechazados=e.registros_rechazados,
            estado=e.estado,
            mensaje=e.mensaje,
        )
        for e in entries
    ]
    return BitacoraResponse(items=items)
