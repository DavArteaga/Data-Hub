"""ETL pipeline for DataCore Hub.

Orchestrates: scrape → normalise → score → persist.
"""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db import (
    BitacoraIngesta,
    Empresa,
    Fuente,
    Indicador,
    Periodo,
    Valor,
)
from app.scrapers.base import ScrapeResult
from app.scrapers.mock_scraper import MockScraper
from app.services.normalizer import normalize_estado, normalize_nit
from app.services.score import calculate_score, compute_actualidad


# ---------------------------------------------------------------------------
# Helpers to fetch / create lookup records
# ---------------------------------------------------------------------------

async def _get_or_create_periodo(
    session: AsyncSession, anio: int, trimestre: int | None = None
) -> Periodo:
    stmt = select(Periodo).where(
        Periodo.anio == anio, Periodo.trimestre == trimestre
    )
    result = await session.execute(stmt)
    periodo = result.scalar_one_or_none()
    if periodo is None:
        periodo = Periodo(anio=anio, trimestre=trimestre)
        session.add(periodo)
        await session.flush()
    return periodo


async def _get_indicador(session: AsyncSession, codigo: str) -> Indicador | None:
    result = await session.execute(
        select(Indicador).where(Indicador.codigo == codigo)
    )
    return result.scalar_one_or_none()


async def _get_fuente_by_name(session: AsyncSession, nombre: str) -> Fuente | None:
    result = await session.execute(
        select(Fuente).where(Fuente.nombre == nombre)
    )
    return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# Main pipeline function
# ---------------------------------------------------------------------------

async def run_ingestion(
    session: AsyncSession,
    fuente_nombre: str,
) -> dict[str, Any]:
    """Run a full ingestion cycle for the named fuente.

    Returns a summary dict compatible with IngestaResponse.
    """
    # Resolve fuente record
    fuente = await _get_fuente_by_name(session, fuente_nombre)
    if fuente is None:
        return {
            "fuente": fuente_nombre,
            "estado": "error",
            "registros_ingestados": 0,
            "registros_rechazados": 0,
            "mensaje": f"Fuente '{fuente_nombre}' not found in database.",
        }

    # Resolve all company NITs to pass to scrapers that query by NIT
    nits_result = await session.execute(select(Empresa.nit))
    all_nits: list[str] = list(nits_result.scalars().all())

    # Scraper dispatch map — maps fuente nombre → scraper instance
    from app.scrapers.datos_gov_scraper import DatosGovScraper
    from app.scrapers.rues_scraper import RuesScraper
    from app.scrapers.siis_scraper import SiisScraper
    from app.scrapers.dane_scraper import DaneScraper

    _SCRAPERS: dict[str, Any] = {
        "datos.gov.co": DatosGovScraper(nits=all_nits),
        "RUES": RuesScraper(nits=all_nits),
        "Superintendencia de Sociedades": SiisScraper(nits=all_nits),
        "DANE": DaneScraper(nits=all_nits),
    }

    scraper_obj = _SCRAPERS.get(fuente_nombre)
    if scraper_obj is None:
        scraper_obj = MockScraper(fuente_nombre=fuente_nombre)

    result: ScrapeResult = await scraper_obj.fetch(nits=all_nits)

    if result.estado == "error":
        await _write_bitacora(session, fuente, result)
        await session.commit()
        return {
            "fuente": fuente_nombre,
            "estado": "error",
            "registros_ingestados": 0,
            "registros_rechazados": result.registros_rechazados,
            "mensaje": result.mensaje,
        }

    ingestados = 0
    rechazados = result.registros_rechazados
    reference_year = datetime.now(UTC).year

    for rec in result.records:
        try:
            nit = normalize_nit(rec["nit"])
            indicador_codigo = rec["indicador"]
            anio = int(rec["anio"])
            valor_numerico: float | None = rec.get("valor_numerico")

            # Ensure empresa exists
            empresa_result = await session.execute(
                select(Empresa).where(Empresa.nit == nit)
            )
            empresa = empresa_result.scalar_one_or_none()
            if empresa is None:
                empresa = Empresa(
                    nit=nit,
                    razon_social=rec.get("razon_social", "Desconocida"),
                    ciiu_principal=rec.get("ciiu_principal", "0000"),
                    estado=normalize_estado(rec.get("estado", "Activa")),
                )
                session.add(empresa)
                await session.flush()

            indicador = await _get_indicador(session, indicador_codigo)
            if indicador is None:
                rechazados += 1
                continue

            periodo = await _get_or_create_periodo(session, anio)

            # Compute score
            completitud = 1.0 if valor_numerico is not None else 0.0
            actualidad = compute_actualidad(anio, reference_year)
            score_val = calculate_score(completitud, actualidad, fuente.tier)

            # Upsert valor (one record per nit+indicador+periodo+fuente)
            existing = await session.execute(
                select(Valor).where(
                    Valor.nit == nit,
                    Valor.indicador_id == indicador.id,
                    Valor.periodo_id == periodo.id,
                    Valor.fuente_id == fuente.id,
                )
            )
            valor_obj = existing.scalar_one_or_none()
            valor_str = str(int(valor_numerico)) if valor_numerico is not None else ""
            if valor_obj is None:
                valor_obj = Valor(
                    nit=nit,
                    indicador_id=indicador.id,
                    periodo_id=periodo.id,
                    fuente_id=fuente.id,
                    valor=valor_str,
                    valor_numerico=valor_numerico,
                    score=score_val,
                    fecha_captura=datetime.now(UTC),
                )
                session.add(valor_obj)
            else:
                valor_obj.valor = valor_str
                valor_obj.valor_numerico = valor_numerico
                valor_obj.score = score_val
                valor_obj.fecha_captura = datetime.now(UTC)

            ingestados += 1

        except Exception as exc:
            rechazados += 1
            continue

    # Update fuente.ultima_ingesta
    fuente.ultima_ingesta = datetime.now(UTC)

    # Write bitacora
    result.registros_ingestados = ingestados
    result.registros_rechazados = rechazados
    await _write_bitacora(session, fuente, result)

    await session.commit()

    return {
        "fuente": fuente_nombre,
        "estado": result.estado,
        "registros_ingestados": ingestados,
        "registros_rechazados": rechazados,
        "mensaje": result.mensaje,
    }


async def _write_bitacora(
    session: AsyncSession, fuente: Fuente, result: ScrapeResult
) -> None:
    entry = BitacoraIngesta(
        fuente_id=fuente.id,
        fecha=datetime.now(UTC),
        registros_ingestados=result.registros_ingestados,
        registros_rechazados=result.registros_rechazados,
        estado=result.estado,
        mensaje=result.mensaje,
    )
    session.add(entry)
    await session.flush()
