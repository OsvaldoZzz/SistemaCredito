import calendar
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from sqlalchemy import delete, func, inspect, select, text, update
from sqlalchemy.orm import Session

from app.config.conexion import obtener_sesion
from app.datos.modelos import Cliente, PagoPrestamo, Prestamo
from app.logica.calculos_prestamo import calcular_estado_cuota, generar_cuotas
from app.logica.validaciones import (
    validar_condiciones_prestamo,
    validar_fecha,
    validar_id,
    validar_monto,
)


def asegurar_esquema_prestamos(session: Session) -> None:
    """Actualiza las columnas heredadas y crea la tabla de abonos si hace falta."""
    columnas = {
        columna["name"]
        for columna in inspect(session.connection()).get_columns("prestamo")
    }
    if "frecuencia_pago" not in columnas:
        session.execute(
            text(
                "ALTER TABLE prestamo "
                "ADD COLUMN frecuencia_pago VARCHAR(10) NOT NULL DEFAULT 'Mensual'"
            )
        )
    if "fecha_primer_pago" not in columnas:
        session.execute(
            text("ALTER TABLE prestamo ADD COLUMN fecha_primer_pago DATE NULL")
        )
    if session.bind.dialect.name == "sqlite":
        fecha_siguiente = _fecha_mes_siguiente(date.today())
        session.execute(
            update(Prestamo)
            .where(Prestamo.fecha_primer_pago.is_(None))
            .values(fecha_primer_pago=fecha_siguiente)
        )
    else:
        session.execute(
            text(
                "UPDATE prestamo "
                "SET fecha_primer_pago = DATE_ADD(CURDATE(), INTERVAL 1 MONTH) "
                "WHERE fecha_primer_pago IS NULL"
            )
        )
    PagoPrestamo.__table__.create(session.connection(), checkfirst=True)


def _fecha_mes_siguiente(fecha: date) -> date:
    mes = fecha.month % 12 + 1
    anio = fecha.year + (fecha.month // 12)
    dia = min(fecha.day, calendar.monthrange(anio, mes)[1])
    return date(anio, mes, dia)


def _cargar_cuotas_prestamo(
    session: Session,
    prestamo_id: int,
) -> list[dict[str, Any]]:
    prestamo = session.get(Prestamo, prestamo_id)
    if prestamo is None:
        raise ValueError("El préstamo no existe.")

    pagos = session.scalars(
        select(PagoPrestamo)
        .where(PagoPrestamo.prestamo_id == prestamo_id)
        .order_by(PagoPrestamo.fecha_pago, PagoPrestamo.id)
    ).all()
    pagos_por_cuota: dict[int, list[dict[str, Any]]] = {}
    for pago in pagos:
        pagos_por_cuota.setdefault(pago.numero_cuota, []).append({
            "id": pago.id,
            "numero_cuota": pago.numero_cuota,
            "monto": pago.monto,
            "fecha_pago": pago.fecha_pago,
        })

    fecha_corte = session.scalar(select(func.current_date()))
    cuotas = generar_cuotas(
        prestamo.monto,
        prestamo.plazo,
        prestamo.fecha_primer_pago,
        prestamo.frecuencia_pago,
    )
    resultado = []
    for cuota in cuotas:
        pagos_cuota = pagos_por_cuota.get(cuota["numero"], [])
        estado = calcular_estado_cuota(
            cuota["monto"],
            cuota["fecha_vencimiento"],
            pagos_cuota,
            fecha_corte,
        )
        resultado.append({
            **cuota,
            **estado,
            "fecha_corte": fecha_corte,
            "pagado": sum(
                (Decimal(str(pago["monto"])) for pago in pagos_cuota),
                Decimal("0.00"),
            ),
            "ultimo_pago": pagos_cuota[-1]["fecha_pago"] if pagos_cuota else None,
            "pagos": pagos_cuota,
            "pagos_calculados": estado["pagos_calculados"],
        })
    return resultado


def _agregar_cuotas_pendientes(
    session: Session,
    prestamos: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    for prestamo in prestamos:
        cuotas = _cargar_cuotas_prestamo(session, prestamo["id"])
        pendientes = [cuota for cuota in cuotas if cuota["total_pendiente"] > 0]
        prestamo["cuotas_pendientes"] = len(pendientes)
        prestamo["saldo_pendiente"] = sum(
            (cuota["total_pendiente"] for cuota in pendientes), Decimal("0.00")
        )
        prestamo["proximo_vencimiento"] = min(
            (cuota["fecha_vencimiento"] for cuota in pendientes), default=None
        )
        prestamo["estado_actual"] = (
            "Pagado" if not pendientes
            else "Vencido" if any(cuota["dias_mora"] > 0 for cuota in pendientes)
            else "Activo"
        )
    return prestamos


def validar_cliente_sin_prestamos_pendientes(
    session: Session,
    cliente_id: int,
) -> None:
    cliente = session.scalar(
        select(Cliente.id).where(Cliente.id == cliente_id).with_for_update()
    )
    if cliente is None:
        raise ValueError("El cliente no existe.")

    prestamos = session.scalars(
        select(Prestamo.id)
        .where(Prestamo.cliente_id == cliente_id)
        .with_for_update()
    ).all()
    for prestamo_id in prestamos:
        if any(
            cuota["total_pendiente"] > 0
            for cuota in _cargar_cuotas_prestamo(session, prestamo_id)
        ):
            raise ValueError(
                "El cliente ya tiene un préstamo con saldo pendiente. "
                "Debe liquidarlo antes de solicitar otro."
            )


def listar_cuotas_prestamo(prestamo_id: int) -> list[dict[str, Any]]:
    validar_id(prestamo_id)
    with obtener_sesion() as session, session.begin():
        asegurar_esquema_prestamos(session)
        return _cargar_cuotas_prestamo(session, prestamo_id)


def registrar_abono_cuota(
    prestamo_id: int,
    numero_cuota: int,
    monto: Decimal | int | float | str,
) -> dict[str, Any]:
    validar_id(prestamo_id)
    validar_id(numero_cuota)
    monto_pago = validar_monto(monto).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )

    with obtener_sesion() as session, session.begin():
        asegurar_esquema_prestamos(session)
        prestamo = session.scalar(
            select(Prestamo)
            .where(Prestamo.id == prestamo_id)
            .with_for_update()
        )
        if prestamo is None:
            raise ValueError("El préstamo no existe.")

        cuotas = _cargar_cuotas_prestamo(session, prestamo_id)
        cuota = next(
            (item for item in cuotas if item["numero"] == numero_cuota),
            None,
        )
        if cuota is None:
            raise ValueError("La cuota seleccionada no existe.")
        if monto_pago > cuota["total_pendiente"]:
            raise ValueError(
                "El abono no puede superar el total pendiente de la cuota."
            )

        pago = PagoPrestamo(
            prestamo_id=prestamo_id,
            numero_cuota=numero_cuota,
            monto=monto_pago,
        )
        session.add(pago)
        session.flush()
        session.refresh(pago)

        cuotas_actualizadas = _cargar_cuotas_prestamo(session, prestamo_id)
        if all(item["total_pendiente"] == 0 for item in cuotas_actualizadas):
            estado = "Pagado"
        elif any(
            item["fecha_vencimiento"] < item["fecha_corte"]
            and item["total_pendiente"] > 0
            for item in cuotas_actualizadas
        ):
            estado = "Vencido"
        else:
            estado = "Activo"
        prestamo.estado = estado
        session.flush()
        return {
            "id": pago.id,
            "fecha_pago": pago.fecha_pago,
            "estado_prestamo": estado,
        }


def actualizar_prestamo(
    prestamo_id: int,
    monto: float,
    plazo: int,
    estado: str,
) -> bool:
    validar_id(prestamo_id)
    monto = validar_condiciones_prestamo(monto, plazo)
    if estado not in {"Activo", "Pagado", "Vencido"}:
        raise ValueError("El estado del préstamo no es válido.")

    with obtener_sesion() as session, session.begin():
        asegurar_esquema_prestamos(session)
        prestamo = session.scalar(
            select(Prestamo)
            .where(Prestamo.id == prestamo_id)
            .with_for_update()
        )
        if prestamo is None:
            return False
        cantidad_pagos = session.scalar(
            select(func.count(PagoPrestamo.id)).where(
                PagoPrestamo.prestamo_id == prestamo_id
            )
        )
        if cantidad_pagos and (
            Decimal(str(prestamo.monto)) != Decimal(str(monto))
            or prestamo.plazo != plazo
        ):
            raise ValueError(
                "No se puede cambiar el monto o plazo de un préstamo "
                "que ya tiene abonos registrados."
            )
        if estado == "Pagado" and any(
            cuota["total_pendiente"] > 0
            for cuota in _cargar_cuotas_prestamo(session, prestamo_id)
        ):
            raise ValueError(
                "No se puede marcar como pagado un préstamo que aún tiene "
                "saldo pendiente."
            )
        prestamo.monto = monto
        prestamo.plazo = plazo
        prestamo.estado = estado
        return True


def eliminar_prestamo(prestamo_id: int) -> bool:
    validar_id(prestamo_id)
    with obtener_sesion() as session, session.begin():
        resultado = session.execute(
            delete(Prestamo).where(Prestamo.id == prestamo_id)
        )
        return resultado.rowcount > 0


def _listar_prestamos(session: Session, consulta) -> list[dict[str, Any]]:
    filas = session.execute(consulta).mappings().all()
    return _agregar_cuotas_pendientes(
        session,
        [dict(fila) for fila in filas],
    )


def listar_prestamos(cliente_id: int) -> list[dict[str, Any]]:
    validar_id(cliente_id)
    with obtener_sesion() as session, session.begin():
        asegurar_esquema_prestamos(session)
        return _listar_prestamos(
            session,
            select(
                Prestamo.id,
                Prestamo.monto,
                Prestamo.plazo,
                Prestamo.estado,
                Prestamo.fecha_primer_pago,
                Prestamo.frecuencia_pago,
            )
            .where(Prestamo.cliente_id == cliente_id)
            .order_by(Prestamo.id),
        )


def listar_todos_los_prestamos() -> list[dict[str, Any]]:
    with obtener_sesion() as session, session.begin():
        asegurar_esquema_prestamos(session)
        return _listar_prestamos(
            session,
            select(
                Prestamo.id,
                Prestamo.cliente_id,
                Prestamo.monto,
                Prestamo.plazo,
                Prestamo.estado,
                Prestamo.fecha_primer_pago,
                Prestamo.frecuencia_pago,
            ).order_by(Prestamo.cliente_id, Prestamo.id),
        )


def crear_prestamo(
    cliente_id: int,
    monto: float,
    plazo: int,
    estado: str = "Activo",
    fecha_primer_pago: date | None = None,
) -> int:
    validar_id(cliente_id)
    monto = validar_condiciones_prestamo(monto, plazo)
    if fecha_primer_pago is not None:
        validar_fecha(fecha_primer_pago)
    if estado not in {"Activo", "Pagado", "Vencido"}:
        raise ValueError("El estado del préstamo no es válido.")
    if estado == "Pagado":
        raise ValueError(
            "Un préstamo nuevo no puede estar pagado sin registrar sus abonos."
        )

    with obtener_sesion() as session, session.begin():
        asegurar_esquema_prestamos(session)
        validar_cliente_sin_prestamos_pendientes(session, cliente_id)
        prestamo = Prestamo(
            cliente_id=cliente_id,
            monto=monto,
            plazo=plazo,
            estado=estado,
            fecha_primer_pago=(
                fecha_primer_pago or _fecha_mes_siguiente(date.today())
            ),
            frecuencia_pago="Mensual",
        )
        session.add(prestamo)
        session.flush()
        return prestamo.id
