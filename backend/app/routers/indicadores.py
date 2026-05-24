"""Router: /indicadores"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.db import Indicador
from app.models.schemas import IndicadorSchema

router = APIRouter(prefix="/indicadores", tags=["indicadores"])


@router.get("", response_model=list[IndicadorSchema])
async def list_indicadores(
    db: AsyncSession = Depends(get_db),
) -> list[IndicadorSchema]:
    result = await db.execute(select(Indicador).order_by(Indicador.id))
    indicadores = result.scalars().all()
    return [IndicadorSchema.model_validate(i) for i in indicadores]
