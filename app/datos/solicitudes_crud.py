from datetime import date
from typing import Any

from sqlalchemy import inspect, select, text

from app.config.conexion import obtener_sesion
from app.datos.modelos import Cliente, Prestamo, SolicitudPrestamo
from app.datos.prestamos_crud import (
    asegurar_esquema_prestamos,
    validar_cliente_sin_prestamos_pendientes,
)
from app.logica.calculos_prestamo import FRECUENCIAS_PAGO
from app.logica.validaciones import (
    validar_condiciones_prestamo,
    validar_fecha,
    validar_id,
    validar_monto,
)


def _crear_tabla_solicitudes(session) -> None:
    SolicitudPrestamo.__table__.create(session.connection(), checkfirst=True)
    inspector = inspect(session.connection())
    columnas = {
        columna["name"]
        for columna in inspector.get_columns("solicitudes_prestamo")
    }
    if "frecuencia_pago" not in columnas:
        session.execute(
            text(
                "ALTER TABLE solicitudes_prestamo "
                "ADD COLUMN frecuencia_pago VARCHAR(10) "
                "NOT NULL DEFAULT 'Mensual'"
            )
        )
    if "ingreso_mensual" not in columnas:
        session.execute(
            text(
                "ALTER TABLE solicitudes_prestamo "
                "ADD COLUMN ingreso_mensual DECIMAL(12, 2) NULL"
            )
        )


def crear_solicitud_prestamo(
    cliente_id: int,
    monto: float,
    plazo: int,
    ingreso_mensual: float | None = None,
    frecuencia_pago: str = "Mensual",
) -> int:
    if frecuencia_pago not in FRECUENCIAS_PAGO:
        raise ValueError("La frecuencia debe ser semanal, quincenal o mensual.")
    validar_id(cliente_id)
    monto = validar_condiciones_prestamo(monto, plazo)
    if ingreso_mensual is None:
        raise ValueError("Ingresa el ingreso mensual del cliente.")
    ingreso_mensual = validar_monto(ingreso_mensual)

    with obtener_sesion() as session, session.begin():
        _crear_tabla_solicitudes(session)
        asegurar_esquema_prestamos(session)
        validar_cliente_sin_prestamos_pendientes(session, cliente_id)
        solicitud = SolicitudPrestamo(
            cliente_id=cliente_id,
            monto=monto,
            plazo=plazo,
            ingreso_mensual=ingreso_mensual,
            frecuencia_pago=frecuencia_pago,
            estado="Pendiente",
        )
        session.add(solicitud)
        session.flush()
        return solicitud.id


def listar_solicitudes_pendientes() -> list[dict[str, Any]]:
    with obtener_sesion() as session, session.begin():
        _crear_tabla_solicitudes(session)
        filas = session.execute(
            select(
                SolicitudPrestamo.id,
                SolicitudPrestamo.cliente_id,
                SolicitudPrestamo.monto,
                SolicitudPrestamo.plazo,
                SolicitudPrestamo.estado,
                SolicitudPrestamo.frecuencia_pago,
                SolicitudPrestamo.fecha_solicitud,
                SolicitudPrestamo.ingreso_mensual,
                Cliente.nombre,
                Cliente.cedula,
            )
            .join(Cliente, Cliente.id == SolicitudPrestamo.cliente_id)
            .where(SolicitudPrestamo.estado == "Pendiente")
            .order_by(SolicitudPrestamo.fecha_solicitud, SolicitudPrestamo.id)
        ).mappings()
        return [dict(fila) for fila in filas]


def resolver_solicitud_prestamo(
    solicitud_id: int,
    aprobada: bool,
    fecha_primer_pago: date | None = None,
) -> int | None:
    validar_id(solicitud_id)
    if type(aprobada) is not bool:
        raise ValueError("La decisión de la solicitud no es válida.")
    if aprobada and fecha_primer_pago is not None:
        validar_fecha(fecha_primer_pago)
    with obtener_sesion() as session, session.begin():
        _crear_tabla_solicitudes(session)
        asegurar_esquema_prestamos(session)
        solicitud = session.scalar(
            select(SolicitudPrestamo)
            .where(
                SolicitudPrestamo.id == solicitud_id,
                SolicitudPrestamo.estado == "Pendiente",
            )
            .with_for_update()
        )
        if solicitud is None:
            raise ValueError("La solicitud ya fue resuelta o no existe.")

        prestamo_id = None
        if aprobada:
            validar_id(solicitud.cliente_id)
            validar_condiciones_prestamo(solicitud.monto, solicitud.plazo)
            if solicitud.frecuencia_pago not in FRECUENCIAS_PAGO:
                raise ValueError("La frecuencia de la solicitud no es válida.")
            validar_cliente_sin_prestamos_pendientes(
                session,
                solicitud.cliente_id,
            )
            prestamo = Prestamo(
                cliente_id=solicitud.cliente_id,
                monto=solicitud.monto,
                plazo=solicitud.plazo,
                estado="Activo",
                fecha_primer_pago=fecha_primer_pago or date.today(),
                frecuencia_pago=solicitud.frecuencia_pago,
            )
            session.add(prestamo)
            session.flush()
            prestamo_id = prestamo.id

        solicitud.estado = "Aprobada" if aprobada else "Rechazada"
        return prestamo_id
