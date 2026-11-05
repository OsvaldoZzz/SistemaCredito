from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Index,
    Numeric,
    String,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Cliente(Base):
    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(255))
    cedula: Mapped[str] = mapped_column(String(255))
    correo: Mapped[str] = mapped_column(String(255))
    password: Mapped[str] = mapped_column(String(255))
    direccion: Mapped[str] = mapped_column(String(255))
    monto: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    latitud: Mapped[Decimal | None] = mapped_column(Numeric(10, 7), nullable=True)
    longitud: Mapped[Decimal | None] = mapped_column(Numeric(10, 7), nullable=True)


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rol: Mapped[str] = mapped_column(String(100))
    nombre: Mapped[str] = mapped_column(String(255))
    password: Mapped[str] = mapped_column(String(255))


class Prestamo(Base):
    __tablename__ = "prestamo"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"))
    monto: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    plazo: Mapped[int] = mapped_column(Integer)
    estado: Mapped[str] = mapped_column(String(20))
    fecha_primer_pago: Mapped[date | None] = mapped_column(Date, nullable=True)
    frecuencia_pago: Mapped[str] = mapped_column(String(10), default="Mensual")


class Cita(Base):
    __tablename__ = "citas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"))
    fecha: Mapped[date] = mapped_column(Date)
    estado: Mapped[str] = mapped_column(String(30))


class CobradorCliente(Base):
    __tablename__ = "cobrador_clientes"

    cobrador_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), primary_key=True
    )
    cliente_id: Mapped[int] = mapped_column(
        ForeignKey("clientes.id", ondelete="CASCADE"), primary_key=True
    )


class PagoPrestamo(Base):
    __tablename__ = "pagos_prestamo"
    __table_args__ = (
        Index("idx_pagos_prestamo_cuota", "prestamo_id", "numero_cuota", "fecha_pago"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    prestamo_id: Mapped[int] = mapped_column(
        ForeignKey("prestamo.id", ondelete="CASCADE")
    )
    numero_cuota: Mapped[int] = mapped_column(Integer)
    monto: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    fecha_pago: Mapped[datetime] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP")
    )


class SolicitudPrestamo(Base):
    __tablename__ = "solicitudes_prestamo"
    __table_args__ = (Index("idx_solicitudes_estado", "estado"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cliente_id: Mapped[int] = mapped_column(
        ForeignKey("clientes.id", ondelete="CASCADE")
    )
    monto: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    plazo: Mapped[int] = mapped_column(Integer)
    frecuencia_pago: Mapped[str] = mapped_column(
        String(10), default="Mensual", server_default=text("'Mensual'")
    )
    ingreso_mensual: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    estado: Mapped[str] = mapped_column(
        String(20), default="Pendiente", server_default=text("'Pendiente'")
    )
    fecha_solicitud: Mapped[datetime] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP")
    )
