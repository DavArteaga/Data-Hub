"""Router: /empresas"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.db import Empresa, Fuente, Indicador, Periodo, Valor
from app.models.schemas import (
    EmpresaDetail,
    EmpresaIndicador,
    EmpresaListItem,
    EmpresaListResponse,
    HistoricoItem,
    HistoricoResponse,
    ScoreDesglose,
    ScoreFuente,
    ScoreIndicador,
    ScoreResponse,
)
from app.services.score import (
    calculate_score,
    compute_actualidad,
    consensus_message,
    explain_score,
)

router = APIRouter(prefix="/empresas", tags=["empresas"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _compute_empresa_score(session: AsyncSession, nit: str) -> float:
    """Global score = average of best score per indicator for the most recent year."""
    best_vals = await _best_valor_per_indicador(session, nit, latest_year=2024)
    if not best_vals:
        return 0.0
    return round(sum(v.score for v in best_vals) / len(best_vals), 4)


async def _best_valor_per_indicador(
    session: AsyncSession, nit: str, latest_year: int = 2024
) -> list[Valor]:
    """Return the highest-score Valor per indicador for the latest year."""
    # Subquery: max score per indicador in 2024
    subq = (
        select(
            Valor.indicador_id,
            func.max(Valor.score).label("max_score"),
        )
        .join(Periodo, Valor.periodo_id == Periodo.id)
        .where(Valor.nit == nit, Periodo.anio == latest_year)
        .group_by(Valor.indicador_id)
        .subquery()
    )

    stmt = (
        select(Valor)
        .join(
            subq,
            (Valor.indicador_id == subq.c.indicador_id)
            & (Valor.score == subq.c.max_score),
        )
        .join(Periodo, Valor.periodo_id == Periodo.id)
        .where(Valor.nit == nit, Periodo.anio == latest_year)
        .options(
            selectinload(Valor.indicador),
            selectinload(Valor.fuente),
            selectinload(Valor.periodo),
        )
    )
    result = await session.execute(stmt)
    all_rows = list(result.scalars().unique().all())
    # Keep only the best row per indicador (highest tier as tiebreaker)
    seen: dict[int, Valor] = {}
    for v in sorted(all_rows, key=lambda x: (x.score, x.fuente.tier), reverse=True):
        if v.indicador_id not in seen:
            seen[v.indicador_id] = v
    return list(seen.values())


# ---------------------------------------------------------------------------
# GET /empresas
# ---------------------------------------------------------------------------

@router.get("", response_model=EmpresaListResponse)
async def list_empresas(
    ciiu: Optional[str] = Query(None, description="Filter by CIIU code"),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> EmpresaListResponse:
    stmt = select(Empresa)
    if ciiu:
        stmt = stmt.where(Empresa.ciiu_principal == ciiu)

    # Total count
    count_result = await db.execute(
        select(func.count()).select_from(stmt.subquery())
    )
    total = count_result.scalar_one()

    # Paginated records
    stmt = stmt.offset((page - 1) * size).limit(size)
    result = await db.execute(stmt)
    empresas = result.scalars().all()

    items: list[EmpresaListItem] = []
    for emp in empresas:
        score_global = await _compute_empresa_score(db, emp.nit)
        items.append(
            EmpresaListItem(
                nit=emp.nit,
                razon_social=emp.razon_social,
                ciiu_principal=emp.ciiu_principal,
                estado=emp.estado,
                score_global=score_global,
            )
        )

    filtros: dict = {}
    if ciiu:
        filtros["ciiu"] = ciiu

    return EmpresaListResponse(
        page=page,
        size=size,
        total=total,
        filtros_aplicados=filtros,
        items=items,
    )


# ---------------------------------------------------------------------------
# GET /empresas/{nit}
# ---------------------------------------------------------------------------

@router.get("/{nit}", response_model=EmpresaDetail)
async def get_empresa(
    nit: str,
    db: AsyncSession = Depends(get_db),
) -> EmpresaDetail:
    result = await db.execute(select(Empresa).where(Empresa.nit == nit))
    empresa = result.scalar_one_or_none()
    if empresa is None:
        raise HTTPException(status_code=404, detail=f"Empresa '{nit}' not found")

    best_valores = await _best_valor_per_indicador(db, nit)

    # Collect ALL fuentes that have data for this company in 2024
    all_2024_stmt = (
        select(Valor)
        .join(Periodo, Valor.periodo_id == Periodo.id)
        .where(Valor.nit == nit, Periodo.anio == 2024)
        .options(selectinload(Valor.fuente))
    )
    all_2024_result = await db.execute(all_2024_stmt)
    fuentes_set: set[str] = {v.fuente.nombre for v in all_2024_result.scalars().unique().all()}

    indicadores_out: list[EmpresaIndicador] = []
    for v in best_valores:
        indicadores_out.append(
            EmpresaIndicador(
                codigo=v.indicador.codigo,
                descripcion=v.indicador.descripcion,
                valor=v.valor_numerico if v.valor_numerico is not None else v.valor,
                unidad=v.indicador.unidad,
                periodo=str(v.periodo.anio),
                score=round(v.score, 4),
                fuente_principal=v.fuente.nombre,
            )
        )

    score_global = await _compute_empresa_score(db, nit)

    return EmpresaDetail(
        nit=empresa.nit,
        razon_social=empresa.razon_social,
        ciiu_principal=empresa.ciiu_principal,
        ciiu_secundarios=empresa.ciiu_secundarios or [],
        estado=empresa.estado,
        fecha_constitucion=empresa.fecha_constitucion,
        fuentes_consultadas=sorted(fuentes_set),
        score_global=score_global,
        indicadores=indicadores_out,
    )


# ---------------------------------------------------------------------------
# GET /empresas/{nit}/score
# ---------------------------------------------------------------------------

@router.get("/{nit}/score", response_model=ScoreResponse)
async def get_empresa_score(
    nit: str,
    indicador: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> ScoreResponse:
    result = await db.execute(select(Empresa).where(Empresa.nit == nit))
    empresa = result.scalar_one_or_none()
    if empresa is None:
        raise HTTPException(status_code=404, detail=f"Empresa '{nit}' not found")

    # Load 2024 valores with all joins
    stmt = (
        select(Valor)
        .join(Periodo, Valor.periodo_id == Periodo.id)
        .where(Valor.nit == nit, Periodo.anio == 2024)
        .options(
            selectinload(Valor.indicador),
            selectinload(Valor.fuente),
            selectinload(Valor.periodo),
        )
    )
    if indicador:
        stmt = stmt.join(Indicador, Valor.indicador_id == Indicador.id).where(
            Indicador.codigo == indicador
        )

    valores_result = await db.execute(stmt)
    all_valores = list(valores_result.scalars().unique().all())

    # Group by indicador
    by_indicador: dict[str, list[Valor]] = {}
    for v in all_valores:
        by_indicador.setdefault(v.indicador.codigo, []).append(v)

    score_indicadores: list[ScoreIndicador] = []
    reference_year = 2026

    for codigo, vals in by_indicador.items():
        # Best (highest score) valor is the primary
        best = max(vals, key=lambda v: v.score)
        completitud = 1.0 if best.valor_numerico is not None else 0.0
        actualidad = compute_actualidad(best.periodo.anio, reference_year)
        breakdown = explain_score(completitud, actualidad, best.fuente.tier)

        fuentes_out = [
            ScoreFuente(
                nombre=v.fuente.nombre,
                valor=v.valor_numerico if v.valor_numerico is not None else v.valor,
                tier=v.fuente.tier,
            )
            for v in sorted(vals, key=lambda x: x.fuente.tier, reverse=True)
        ]

        numeric_vals = [
            v.valor_numerico for v in vals if v.valor_numerico is not None
        ]
        consenso = consensus_message(numeric_vals)
        if best.fuente.tier >= 0.9:
            consenso += f" Se prioriza {best.fuente.nombre} por mayor tier de confiabilidad."

        calculo_str = (
            f"0.3*{breakdown['completitud']} + "
            f"0.3*{breakdown['actualidad']} + "
            f"0.4*{breakdown['tier_fuente']} = "
            f"{breakdown['score_final']}"
        )

        score_indicadores.append(
            ScoreIndicador(
                codigo=codigo,
                score_final=round(best.score, 4),
                desglose=ScoreDesglose(
                    completitud=breakdown["completitud"],
                    actualidad=breakdown["actualidad"],
                    tier_fuente=breakdown["tier_fuente"],
                    calculo=calculo_str,
                ),
                fuentes=fuentes_out,
                consenso=consenso,
            )
        )

    score_global = await _compute_empresa_score(db, nit)

    return ScoreResponse(
        nit=empresa.nit,
        razon_social=empresa.razon_social,
        score_global=score_global,
        indicadores=score_indicadores,
    )


# ---------------------------------------------------------------------------
# GET /empresas/{nit}/historico
# ---------------------------------------------------------------------------

@router.get("/{nit}/historico", response_model=HistoricoResponse)
async def get_empresa_historico(
    nit: str,
    indicador: str = Query(..., description="Indicator code, e.g. num_empleados"),
    db: AsyncSession = Depends(get_db),
) -> HistoricoResponse:
    result = await db.execute(select(Empresa).where(Empresa.nit == nit))
    empresa = result.scalar_one_or_none()
    if empresa is None:
        raise HTTPException(status_code=404, detail=f"Empresa '{nit}' not found")

    ind_result = await db.execute(
        select(Indicador).where(Indicador.codigo == indicador)
    )
    ind_obj = ind_result.scalar_one_or_none()
    if ind_obj is None:
        raise HTTPException(status_code=404, detail=f"Indicador '{indicador}' not found")

    # One best-score record per year
    subq = (
        select(
            Periodo.anio,
            func.max(Valor.score).label("max_score"),
        )
        .join(Valor, Valor.periodo_id == Periodo.id)
        .where(Valor.nit == nit, Valor.indicador_id == ind_obj.id)
        .group_by(Periodo.anio)
        .subquery()
    )

    stmt = (
        select(Valor)
        .join(Periodo, Valor.periodo_id == Periodo.id)
        .join(
            subq,
            (Periodo.anio == subq.c.anio) & (Valor.score == subq.c.max_score),
        )
        .where(Valor.nit == nit, Valor.indicador_id == ind_obj.id)
        .options(
            selectinload(Valor.fuente),
            selectinload(Valor.periodo),
        )
        .order_by(Periodo.anio)
    )
    vals_result = await db.execute(stmt)
    valores = list(vals_result.scalars().unique().all())

    serie = [
        HistoricoItem(
            periodo=str(v.periodo.anio),
            valor=v.valor_numerico if v.valor_numerico is not None else v.valor,
            fuente=v.fuente.nombre,
            score=round(v.score, 4),
        )
        for v in valores
    ]

    return HistoricoResponse(
        nit=empresa.nit,
        indicador=ind_obj.codigo,
        descripcion=ind_obj.descripcion,
        unidad=ind_obj.unidad,
        serie=serie,
    )
