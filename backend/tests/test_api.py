"""Integration tests for DataCore Hub API.

Uses an in-memory SQLite database so tests are fully isolated.
"""
from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.database import Base, get_db
from app.main import app
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
# Test database setup
# ---------------------------------------------------------------------------

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DB_URL, echo=False, future=True)
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@pytest_asyncio.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_db():
    """Create tables and seed minimal data once per session."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        # Fuentes
        fuente_sup = Fuente(
            nombre="Superintendencia de Sociedades",
            url_base="https://www.supersociedades.gov.co",
            tipo="scraping",
            tier=0.95,
        )
        fuente_cc = Fuente(
            nombre="Cámara de Comercio",
            url_base="https://www.ccmedellin.com.co",
            tipo="scraping",
            tier=0.85,
        )
        fuente_dane = Fuente(
            nombre="DANE",
            url_base="https://www.dane.gov.co",
            tipo="file",
            tier=0.70,
        )
        fuente_rues = Fuente(
            nombre="RUES",
            url_base="https://www.rues.org.co",
            tipo="scraping",
            tier=0.90,
        )
        fuente_dian = Fuente(
            nombre="DIAN",
            url_base="https://www.dian.gov.co",
            tipo="scraping",
            tier=0.95,
        )
        session.add_all([fuente_sup, fuente_cc, fuente_dane, fuente_rues, fuente_dian])

        # Indicadores
        ind_emp = Indicador(
            codigo="num_empleados",
            descripcion="Número de empleados",
            unidad="personas",
        )
        ind_ing = Indicador(
            codigo="ingresos_anuales",
            descripcion="Ingresos operacionales anuales",
            unidad="COP",
        )
        ind_act = Indicador(
            codigo="activos_totales",
            descripcion="Activos totales",
            unidad="COP",
        )
        session.add_all([ind_emp, ind_ing, ind_act])

        # Períodos
        periodos = [Periodo(anio=y) for y in range(2015, 2025)]
        session.add_all(periodos)

        # Empresas
        emp_a = Empresa(
            nit="900111111-1",
            razon_social="Empresa A S.A.S.",
            ciiu_principal="6201",
            ciiu_secundarios=["6202", "6209"],
            estado="Activa",
        )
        emp_b = Empresa(
            nit="900222222-2",
            razon_social="Empresa B S.A.S.",
            ciiu_principal="6201",
            ciiu_secundarios=[],
            estado="Activa",
        )
        emp_f = Empresa(
            nit="900666666-6",
            razon_social="Empresa F S.A.S.",
            ciiu_principal="6201",
            ciiu_secundarios=[],
            estado="Inactiva",
        )
        session.add_all([emp_a, emp_b, emp_f])
        await session.flush()

        # Valores for 2024 (Empresa A)
        periodo_2024 = next(p for p in periodos if p.anio == 2024)
        ref_year = 2026
        for ind, val_num in [
            (ind_emp, 47.0),
            (ind_ing, 1_280_000_000.0),
            (ind_act, 850_000_000.0),
        ]:
            score = calculate_score(1.0, compute_actualidad(2024, ref_year), fuente_sup.tier)
            session.add(
                Valor(
                    nit="900111111-1",
                    indicador_id=ind.id,
                    periodo_id=periodo_2024.id,
                    fuente_id=fuente_sup.id,
                    valor=str(int(val_num)),
                    valor_numerico=val_num,
                    score=round(score, 4),
                    fecha_captura=datetime.now(UTC),
                )
            )

        # Historical valores for Empresa A – num_empleados 2015-2023
        for p in periodos:
            if p.anio == 2024:
                continue
            val_num = round(47.0 * (0.92 ** (2024 - p.anio)), 2)
            score = calculate_score(1.0, compute_actualidad(p.anio, ref_year), fuente_sup.tier)
            session.add(
                Valor(
                    nit="900111111-1",
                    indicador_id=ind_emp.id,
                    periodo_id=p.id,
                    fuente_id=fuente_sup.id,
                    valor=str(int(val_num)),
                    valor_numerico=val_num,
                    score=round(score, 4),
                    fecha_captura=datetime.now(UTC),
                )
            )

        # Bitácora
        session.add(
            BitacoraIngesta(
                fuente_id=fuente_rues.id,
                fecha=datetime(2026, 5, 18, 22, 0, 0),
                registros_ingestados=1240,
                registros_rechazados=12,
                estado="ok",
                mensaje=None,
            )
        )
        session.add(
            BitacoraIngesta(
                fuente_id=fuente_dian.id,
                fecha=datetime(2026, 5, 15, 14, 0, 0),
                registros_ingestados=540,
                registros_rechazados=87,
                estado="warn",
                mensaje="Alta tasa de rechazo.",
            )
        )

        await session.commit()

    app.dependency_overrides[get_db] = override_get_db
    yield
    await test_engine.dispose()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_health(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "uptime_seconds" in data
    assert data["service"] == "DataCore Hub API"


# ---------------------------------------------------------------------------
# GET /empresas
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_empresas(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/empresas")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data
    assert data["page"] == 1
    assert isinstance(data["items"], list)


@pytest.mark.asyncio
async def test_list_empresas_filter_ciiu(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/empresas?ciiu=6201")
    assert resp.status_code == 200
    data = resp.json()
    assert data["filtros_aplicados"].get("ciiu") == "6201"
    for item in data["items"]:
        assert item["ciiu_principal"] == "6201"


@pytest.mark.asyncio
async def test_list_empresas_pagination(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/empresas?page=1&size=2")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) <= 2
    assert data["size"] == 2


# ---------------------------------------------------------------------------
# GET /empresas/{nit}
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_empresa_detail(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/empresas/900111111-1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["nit"] == "900111111-1"
    assert data["razon_social"] == "Empresa A S.A.S."
    assert "indicadores" in data
    assert "score_global" in data
    assert "fuentes_consultadas" in data


@pytest.mark.asyncio
async def test_get_empresa_not_found(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/empresas/999999999-9")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /empresas/{nit}/score
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_empresa_score(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/empresas/900111111-1/score")
    assert resp.status_code == 200
    data = resp.json()
    assert data["nit"] == "900111111-1"
    assert "formula" in data
    assert "indicadores" in data
    if data["indicadores"]:
        ind = data["indicadores"][0]
        assert "desglose" in ind
        assert "fuentes" in ind
        assert "consenso" in ind


@pytest.mark.asyncio
async def test_get_empresa_score_with_filter(client: AsyncClient) -> None:
    resp = await client.get(
        "/api/v1/empresas/900111111-1/score?indicador=num_empleados"
    )
    assert resp.status_code == 200
    data = resp.json()
    for ind in data["indicadores"]:
        assert ind["codigo"] == "num_empleados"


# ---------------------------------------------------------------------------
# GET /empresas/{nit}/historico
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_historico(client: AsyncClient) -> None:
    resp = await client.get(
        "/api/v1/empresas/900111111-1/historico?indicador=num_empleados"
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["nit"] == "900111111-1"
    assert data["indicador"] == "num_empleados"
    assert "serie" in data
    assert len(data["serie"]) > 0
    for item in data["serie"]:
        assert "periodo" in item
        assert "valor" in item
        assert "fuente" in item
        assert "score" in item


@pytest.mark.asyncio
async def test_get_historico_missing_indicador(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/empresas/900111111-1/historico")
    # indicador is required query param
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_get_historico_bad_indicador(client: AsyncClient) -> None:
    resp = await client.get(
        "/api/v1/empresas/900111111-1/historico?indicador=no_existe"
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /indicadores
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_indicadores(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/indicadores")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    codigos = [i["codigo"] for i in data]
    assert "num_empleados" in codigos
    assert "ingresos_anuales" in codigos
    assert "activos_totales" in codigos


# ---------------------------------------------------------------------------
# GET /fuentes
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_fuentes(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/fuentes")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    for f in data:
        assert "tier" in f
        assert "nombre" in f
        assert "tipo" in f


# ---------------------------------------------------------------------------
# GET /bitacora
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_bitacora(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/bitacora")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    for item in data["items"]:
        assert "fuente" in item
        assert "estado" in item
        assert "registros_ingestados" in item


@pytest.mark.asyncio
async def test_get_bitacora_limit(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/bitacora?limit=1")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) <= 1


# ---------------------------------------------------------------------------
# POST /ingesta
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_trigger_ingesta(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/ingesta/RUES")
    assert resp.status_code == 200
    data = resp.json()
    assert data["fuente"] == "RUES"
    assert data["estado"] in ("ok", "warn", "error")
    assert isinstance(data["registros_ingestados"], int)


@pytest.mark.asyncio
async def test_trigger_ingesta_unknown_fuente(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/ingesta/FuenteQueNoExiste")
    assert resp.status_code == 200
    data = resp.json()
    assert data["estado"] == "error"
