"""Router: /fuentes"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.db import Fuente
from app.models.schemas import FuenteSchema

router = APIRouter(prefix="/fuentes", tags=["fuentes"])


@router.get("", response_model=list[FuenteSchema])
async def list_fuentes(
    db: AsyncSession = Depends(get_db),
) -> list[FuenteSchema]:
    result = await db.execute(
        select(Fuente).order_by(Fuente.tier.desc(), Fuente.nombre)
    )
    fuentes = result.scalars().all()
    return [FuenteSchema.model_validate(f) for f in fuentes]
