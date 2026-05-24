from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    JSON,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Empresa(Base):
    __tablename__ = "empresas"

    nit: Mapped[str] = mapped_column(String(20), primary_key=True, index=True)
    razon_social: Mapped[str] = mapped_column(String(255), nullable=False)
    ciiu_principal: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    ciiu_secundarios: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    fecha_constitucion: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    estado: Mapped[str] = mapped_column(String(50), nullable=False, default="Activa")

    valores: Mapped[list["Valor"]] = relationship(
        "Valor", back_populates="empresa", cascade="all, delete-orphan"
    )


class Fuente(Base):
    __tablename__ = "fuentes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    url_base: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)  # api/scraping/file
    tier: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    ultima_ingesta: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    valores: Mapped[list["Valor"]] = relationship("Valor", back_populates="fuente")
    bitacora_entries: Mapped[list["BitacoraIngesta"]] = relationship(
        "BitacoraIngesta", back_populates="fuente"
    )


class Indicador(Base):
    __tablename__ = "indicadores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    descripcion: Mapped[str] = mapped_column(String(255), nullable=False)
    unidad: Mapped[str] = mapped_column(String(50), nullable=False)

    valores: Mapped[list["Valor"]] = relationship("Valor", back_populates="indicador")


class Periodo(Base):
    __tablename__ = "periodos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    anio: Mapped[int] = mapped_column(Integer, nullable=False)
    trimestre: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    valores: Mapped[list["Valor"]] = relationship("Valor", back_populates="periodo")


class Valor(Base):
    __tablename__ = "valores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nit: Mapped[str] = mapped_column(
        String(20), ForeignKey("empresas.nit"), nullable=False, index=True
    )
    indicador_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("indicadores.id"), nullable=False
    )
    periodo_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("periodos.id"), nullable=False
    )
    fuente_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("fuentes.id"), nullable=False
    )
    valor: Mapped[str] = mapped_column(String(255), nullable=False)
    valor_numerico: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    fecha_captura: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now()
    )

    empresa: Mapped["Empresa"] = relationship("Empresa", back_populates="valores")
    indicador: Mapped["Indicador"] = relationship("Indicador", back_populates="valores")
    periodo: Mapped["Periodo"] = relationship("Periodo", back_populates="valores")
    fuente: Mapped["Fuente"] = relationship("Fuente", back_populates="valores")


class BitacoraIngesta(Base):
    __tablename__ = "bitacora_ingesta"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fuente_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("fuentes.id"), nullable=False
    )
    fecha: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now()
    )
    registros_ingestados: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    registros_rechazados: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    estado: Mapped[str] = mapped_column(String(10), nullable=False, default="ok")
    mensaje: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    fuente: Mapped["Fuente"] = relationship("Fuente", back_populates="bitacora_entries")
