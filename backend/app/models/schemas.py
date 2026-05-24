from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, field_validator


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

class OrmBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Empresa
# ---------------------------------------------------------------------------

class EmpresaListItem(OrmBase):
    nit: str
    razon_social: str
    ciiu_principal: str
    estado: str
    score_global: float = 0.0


class EmpresaIndicador(OrmBase):
    codigo: str
    descripcion: str
    valor: Any
    unidad: str
    periodo: str
    score: float
    fuente_principal: str


class EmpresaDetail(OrmBase):
    nit: str
    razon_social: str
    ciiu_principal: str
    ciiu_secundarios: list[str] = []
    estado: str
    fecha_constitucion: Optional[date] = None
    fuentes_consultadas: list[str] = []
    score_global: float = 0.0
    indicadores: list[EmpresaIndicador] = []


class EmpresaListResponse(BaseModel):
    page: int
    size: int
    total: int
    filtros_aplicados: dict[str, Any] = {}
    items: list[EmpresaListItem]


# ---------------------------------------------------------------------------
# Score
# ---------------------------------------------------------------------------

class ScoreDesglose(BaseModel):
    completitud: float
    actualidad: float
    tier_fuente: float
    calculo: str


class ScoreFuente(BaseModel):
    nombre: str
    valor: Any
    tier: float


class ScoreIndicador(BaseModel):
    codigo: str
    score_final: float
    desglose: ScoreDesglose
    fuentes: list[ScoreFuente]
    consenso: str


class ScoreResponse(BaseModel):
    nit: str
    razon_social: str
    score_global: float
    formula: str = "score = 0.3*completitud + 0.3*actualidad + 0.4*tier_fuente"
    indicadores: list[ScoreIndicador]


# ---------------------------------------------------------------------------
# Histórico
# ---------------------------------------------------------------------------

class HistoricoItem(BaseModel):
    periodo: str
    valor: Any
    fuente: str
    score: float


class HistoricoResponse(BaseModel):
    nit: str
    indicador: str
    descripcion: str
    unidad: str
    serie: list[HistoricoItem]


# ---------------------------------------------------------------------------
# Indicador
# ---------------------------------------------------------------------------

class IndicadorSchema(OrmBase):
    id: int
    codigo: str
    descripcion: str
    unidad: str


# ---------------------------------------------------------------------------
# Fuente
# ---------------------------------------------------------------------------

class FuenteSchema(OrmBase):
    id: int
    nombre: str
    url_base: Optional[str] = None
    tipo: str
    tier: float
    ultima_ingesta: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Ingesta
# ---------------------------------------------------------------------------

class IngestaResponse(BaseModel):
    fuente: str
    estado: str
    registros_ingestados: int
    registros_rechazados: int
    mensaje: Optional[str] = None


# ---------------------------------------------------------------------------
# Bitácora
# ---------------------------------------------------------------------------

class BitacoraItem(BaseModel):
    id: int
    fuente: str
    fecha: datetime
    registros_ingestados: int
    registros_rechazados: int
    estado: str
    mensaje: Optional[str] = None


class BitacoraResponse(BaseModel):
    items: list[BitacoraItem]


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    uptime_seconds: float
