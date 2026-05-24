"""Initialize the database with schema + seed data.

Run from the backend/ directory:
    python scripts/init_db.py
"""
from __future__ import annotations

import asyncio
import sys
from datetime import UTC, date, datetime
from pathlib import Path

# Make sure `app` is importable when running as a script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.database import AsyncSessionLocal, init_db
from app.models.db import (
    BitacoraIngesta,
    Empresa,
    Fuente,
    Indicador,
    Periodo,
    Valor,
)
from app.services.score import calculate_score, compute_actualidad

# ---------------------------------------------------------------------------
# Seed definitions
# ---------------------------------------------------------------------------

FUENTES_SEED = [
    {
        "nombre": "Superintendencia de Sociedades",
        "url_base": "https://www.supersociedades.gov.co",
        "tipo": "scraping",
        "tier": 0.95,
    },
    {
        "nombre": "DIAN",
        "url_base": "https://www.dian.gov.co",
        "tipo": "scraping",
        "tier": 0.95,
    },
    {
        "nombre": "RUES",
        "url_base": "https://www.rues.org.co",
        "tipo": "scraping",
        "tier": 0.90,
    },
    {
        "nombre": "Cámara de Comercio",
        "url_base": "https://www.ccmedellin.com.co",
        "tipo": "scraping",
        "tier": 0.85,
    },
    {
        "nombre": "DANE",
        "url_base": "https://www.dane.gov.co",
        "tipo": "file",
        "tier": 0.70,
    },
    {
        "nombre": "datos.gov.co",
        "url_base": "https://www.datos.gov.co",
        "tipo": "api",
        "tier": 0.88,
    },
]

INDICADORES_SEED = [
    {"codigo": "num_empleados", "descripcion": "Número de empleados", "unidad": "personas"},
    {
        "codigo": "ingresos_anuales",
        "descripcion": "Ingresos operacionales anuales",
        "unidad": "COP",
    },
    {"codigo": "activos_totales", "descripcion": "Activos totales", "unidad": "COP"},
]

EMPRESAS_SEED = [
    {
        "nit": "900111111-1",
        "razon_social": "Empresa A S.A.S.",
        "ciiu_principal": "6201",
        "ciiu_secundarios": ["6202", "6209"],
        "fecha_constitucion": date(2015, 4, 12),
        "estado": "Activa",
    },
    {
        "nit": "900222222-2",
        "razon_social": "Empresa B S.A.S.",
        "ciiu_principal": "6201",
        "ciiu_secundarios": ["6202"],
        "fecha_constitucion": date(2013, 8, 23),
        "estado": "Activa",
    },
    {
        "nit": "900333333-3",
        "razon_social": "Empresa C Ltda.",
        "ciiu_principal": "6202",
        "ciiu_secundarios": ["6201"],
        "fecha_constitucion": date(2010, 11, 5),
        "estado": "Activa",
    },
    {
        "nit": "900444444-4",
        "razon_social": "Empresa D S.A.",
        "ciiu_principal": "6209",
        "ciiu_secundarios": [],
        "fecha_constitucion": date(2008, 2, 17),
        "estado": "Activa",
    },
    {
        "nit": "900555555-5",
        "razon_social": "Empresa E S.A.S.",
        "ciiu_principal": "6201",
        "ciiu_secundarios": [],
        "fecha_constitucion": date(2017, 9, 30),
        "estado": "Activa",
    },
    {
        "nit": "900666666-6",
        "razon_social": "Empresa F S.A.S.",
        "ciiu_principal": "6201",
        "ciiu_secundarios": [],
        "fecha_constitucion": date(2012, 6, 14),
        "estado": "Inactiva",
    },
]

# Base 2024 values per company per indicator
BASE_VALUES: dict[str, dict[str, float]] = {
    "900111111-1": {
        "num_empleados": 47.0,
        "ingresos_anuales": 1_280_000_000.0,
        "activos_totales": 850_000_000.0,
    },
    "900222222-2": {
        "num_empleados": 38.0,
        "ingresos_anuales": 1_050_000_000.0,
        "activos_totales": 720_000_000.0,
    },
    "900333333-3": {
        "num_empleados": 29.0,
        "ingresos_anuales": 820_000_000.0,
        "activos_totales": 560_000_000.0,
    },
    "900444444-4": {
        "num_empleados": 21.0,
        "ingresos_anuales": 590_000_000.0,
        "activos_totales": 410_000_000.0,
    },
    "900555555-5": {
        "num_empleados": 14.0,
        "ingresos_anuales": 380_000_000.0,
        "activos_totales": 270_000_000.0,
    },
    "900666666-6": {
        "num_empleados": 0.0,
        "ingresos_anuales": 0.0,
        "activos_totales": 95_000_000.0,
    },
}

# Which fuente to assign to each (nit, indicador) combination
# Cycles through the high-tier sources for variety
INDICATOR_FUENTE_MAP: dict[str, str] = {
    "num_empleados": "Superintendencia de Sociedades",
    "ingresos_anuales": "Superintendencia de Sociedades",
    "activos_totales": "Superintendencia de Sociedades",
}

# Secondary fuentes that also report the same indicator (for score comparison)
SECONDARY_FUENTES: dict[str, list[tuple[str, float]]] = {
    # indicador -> [(fuente_nombre, scale_factor), ...]
    "num_empleados": [
        ("Cámara de Comercio", 0.96),
        ("DANE", 1.06),
    ],
    "ingresos_anuales": [
        ("Cámara de Comercio", 0.97),
        ("DIAN", 1.02),
    ],
    "activos_totales": [
        ("RUES", 0.98),
        ("Cámara de Comercio", 0.95),
    ],
}

# Target score_global per company (used for 2024 primary valor records)
COMPANY_TARGET_SCORE: dict[str, float] = {
    "900111111-1": 0.92,
    "900222222-2": 0.85,
    "900333333-3": 0.78,
    "900444444-4": 0.71,
    "900555555-5": 0.66,
    "900666666-6": 0.55,
}

BITACORA_SEED = [
    {
        "fuente": "RUES",
        "fecha": datetime(2026, 5, 18, 22, 0, 0),
        "registros_ingestados": 1240,
        "registros_rechazados": 12,
        "estado": "ok",
        "mensaje": None,
    },
    {
        "fuente": "Cámara de Comercio",
        "fecha": datetime(2026, 5, 17, 20, 30, 0),
        "registros_ingestados": 980,
        "registros_rechazados": 5,
        "estado": "ok",
        "mensaje": None,
    },
    {
        "fuente": "Superintendencia de Sociedades",
        "fecha": datetime(2026, 5, 16, 18, 0, 0),
        "registros_ingestados": 2340,
        "registros_rechazados": 18,
        "estado": "ok",
        "mensaje": None,
    },
    {
        "fuente": "DIAN",
        "fecha": datetime(2026, 5, 15, 14, 0, 0),
        "registros_ingestados": 540,
        "registros_rechazados": 87,
        "estado": "warn",
        "mensaje": "Alta tasa de rechazo: algunos NITs no encontrados en el padrón DIAN.",
    },
    {
        "fuente": "DANE",
        "fecha": datetime(2026, 5, 14, 10, 0, 0),
        "registros_ingestados": 0,
        "registros_rechazados": 0,
        "estado": "error",
        "mensaje": "Archivo CSV del DANE no disponible. Reintente más tarde.",
    },
]


# ---------------------------------------------------------------------------
# Main seed function
# ---------------------------------------------------------------------------

def _scale(base: float, year: int, base_year: int = 2024) -> float:
    diff = base_year - year
    factor = (0.92) ** diff
    return round(base * factor, 2)


async def seed() -> None:
    await init_db()

    async with AsyncSessionLocal() as session:
        # --- Fuentes ---
        fuente_objs: dict[str, Fuente] = {}
        for f_data in FUENTES_SEED:
            existing = await session.execute(
                select(Fuente).where(Fuente.nombre == f_data["nombre"])
            )
            fuente = existing.scalar_one_or_none()
            if fuente is None:
                fuente = Fuente(**f_data)
                session.add(fuente)
            else:
                fuente.tier = f_data["tier"]
                fuente.url_base = f_data["url_base"]
                fuente.tipo = f_data["tipo"]
            await session.flush()
            fuente_objs[fuente.nombre] = fuente

        # --- Indicadores ---
        indicador_objs: dict[str, Indicador] = {}
        for i_data in INDICADORES_SEED:
            existing = await session.execute(
                select(Indicador).where(Indicador.codigo == i_data["codigo"])
            )
            ind = existing.scalar_one_or_none()
            if ind is None:
                ind = Indicador(**i_data)
                session.add(ind)
                await session.flush()
            indicador_objs[ind.codigo] = ind

        # --- Períodos 2015-2024 ---
        periodo_objs: dict[int, Periodo] = {}
        for anio in range(2015, 2025):
            existing = await session.execute(
                select(Periodo).where(Periodo.anio == anio, Periodo.trimestre.is_(None))
            )
            periodo = existing.scalar_one_or_none()
            if periodo is None:
                periodo = Periodo(anio=anio, trimestre=None)
                session.add(periodo)
                await session.flush()
            periodo_objs[anio] = periodo

        # --- Empresas ---
        empresa_objs: dict[str, Empresa] = {}
        for e_data in EMPRESAS_SEED:
            existing = await session.execute(
                select(Empresa).where(Empresa.nit == e_data["nit"])
            )
            empresa = existing.scalar_one_or_none()
            if empresa is None:
                empresa = Empresa(**e_data)
                session.add(empresa)
                await session.flush()
            empresa_objs[empresa.nit] = empresa

        # --- Valores (historical 2015-2024) ---
        reference_year = 2026
        for nit, base_vals in BASE_VALUES.items():
            for ind_codigo, base_val in base_vals.items():
                ind_obj = indicador_objs[ind_codigo]
                primary_fuente = fuente_objs[INDICATOR_FUENTE_MAP[ind_codigo]]

                for anio in range(2015, 2025):
                    periodo = periodo_objs[anio]
                    val_num = _scale(base_val, anio)
                    actualidad = compute_actualidad(anio, reference_year)
                    completitud = 1.0 if val_num > 0 else 0.5
                    if anio == 2024 and nit in COMPANY_TARGET_SCORE:
                        score = COMPANY_TARGET_SCORE[nit]
                    else:
                        score = calculate_score(completitud, actualidad, primary_fuente.tier)

                    existing = await session.execute(
                        select(Valor).where(
                            Valor.nit == nit,
                            Valor.indicador_id == ind_obj.id,
                            Valor.periodo_id == periodo.id,
                            Valor.fuente_id == primary_fuente.id,
                        )
                    )
                    valor_obj = existing.scalar_one_or_none()
                    if valor_obj is None:
                        valor_obj = Valor(
                            nit=nit,
                            indicador_id=ind_obj.id,
                            periodo_id=periodo.id,
                            fuente_id=primary_fuente.id,
                            valor=str(int(val_num)) if val_num > 0 else "0",
                            valor_numerico=val_num,
                            score=round(score, 4),
                            fecha_captura=datetime.now(UTC),
                        )
                        session.add(valor_obj)

                    # Secondary fuentes (only for 2024 to keep DB manageable)
                    if anio == 2024:
                        for sec_fuente_nombre, scale_f in SECONDARY_FUENTES.get(
                            ind_codigo, []
                        ):
                            sec_fuente = fuente_objs.get(sec_fuente_nombre)
                            if sec_fuente is None:
                                continue
                            sec_val = round(val_num * scale_f, 2)
                            # Secondary scores must be <= primary target to avoid
                            # overriding the intended global score per company
                            formula_score = calculate_score(
                                1.0,
                                compute_actualidad(anio, reference_year),
                                sec_fuente.tier,
                            )
                            target = COMPANY_TARGET_SCORE.get(nit)
                            if target is not None:
                                sec_score = min(formula_score, target * 0.97)
                            else:
                                sec_score = formula_score
                            existing2 = await session.execute(
                                select(Valor).where(
                                    Valor.nit == nit,
                                    Valor.indicador_id == ind_obj.id,
                                    Valor.periodo_id == periodo.id,
                                    Valor.fuente_id == sec_fuente.id,
                                )
                            )
                            if existing2.scalar_one_or_none() is None:
                                session.add(
                                    Valor(
                                        nit=nit,
                                        indicador_id=ind_obj.id,
                                        periodo_id=periodo.id,
                                        fuente_id=sec_fuente.id,
                                        valor=str(int(sec_val)),
                                        valor_numerico=sec_val,
                                        score=round(sec_score, 4),
                                        fecha_captura=datetime.now(UTC),
                                    )
                                )

        await session.flush()

        # --- Bitácora seed ---
        for b_data in BITACORA_SEED:
            fuente = fuente_objs.get(b_data["fuente"])
            if fuente is None:
                continue
            existing = await session.execute(
                select(BitacoraIngesta).where(
                    BitacoraIngesta.fuente_id == fuente.id,
                    BitacoraIngesta.fecha == b_data["fecha"],
                )
            )
            if existing.scalar_one_or_none() is None:
                session.add(
                    BitacoraIngesta(
                        fuente_id=fuente.id,
                        fecha=b_data["fecha"],
                        registros_ingestados=b_data["registros_ingestados"],
                        registros_rechazados=b_data["registros_rechazados"],
                        estado=b_data["estado"],
                        mensaje=b_data["mensaje"],
                    )
                )

        await session.commit()
        print("Database seeded successfully.")


if __name__ == "__main__":
    asyncio.run(seed())
