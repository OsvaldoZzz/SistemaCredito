import calendar
import math
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from calculos_prestamo import calcular_estado_cuota, generar_cuotas
from conexion import obtener_conexion


def asegurar_esquema_prestamos(cursor) -> None:
    cursor.execute(
        "SHOW COLUMNS FROM prestamo LIKE 'fecha_primer_pago'"
    )
    if not cursor.fetchall():
        cursor.execute(
            "ALTER TABLE prestamo "
            "ADD COLUMN fecha_primer_pago DATE NULL"
        )
    cursor.execute(
        """
        UPDATE prestamo
        SET fecha_primer_pago = DATE_ADD(CURDATE(), INTERVAL 1 MONTH)
        WHERE fecha_primer_pago IS NULL
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS pagos_prestamo (
            id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            prestamo_id INT NOT NULL,
            numero_cuota INT NOT NULL,
            monto DECIMAL(12, 2) NOT NULL,
            fecha_pago DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_pagos_prestamo_cuota
                (prestamo_id, numero_cuota, fecha_pago),
            CONSTRAINT fk_pagos_prestamo
                FOREIGN KEY (prestamo_id) REFERENCES prestamo(id)
                ON DELETE CASCADE
        ) ENGINE=InnoDB
        """
    )


def _fecha_mes_siguiente(fecha: date) -> date:
    mes = fecha.month % 12 + 1
    anio = fecha.year + (fecha.month // 12)
    dia = min(fecha.day, calendar.monthrange(anio, mes)[1])
    return date(anio, mes, dia)


def _cargar_cuotas_prestamo(cursor, prestamo_id: int) -> list[dict[str, Any]]:
    cursor.execute(
        """
        SELECT monto, plazo, fecha_primer_pago
        FROM prestamo
        WHERE id = %s
        """,
        (prestamo_id,),
    )
    prestamo = cursor.fetchone()
    if prestamo is None:
        raise ValueError("El préstamo no existe.")

    cursor.execute(
        """
        SELECT numero_cuota, monto, fecha_pago
        FROM pagos_prestamo
        WHERE prestamo_id = %s
        ORDER BY fecha_pago, id
        """,
        (prestamo_id,),
    )
    pagos_por_cuota: dict[int, list[dict[str, Any]]] = {}
    for pago in cursor.fetchall():
        pagos_por_cuota.setdefault(pago["numero_cuota"], []).append(pago)

    cursor.execute("SELECT CURRENT_DATE AS fecha_corte")
    fecha_corte = cursor.fetchone()["fecha_corte"]
    cuotas = generar_cuotas(
        prestamo["monto"],
        prestamo["plazo"],
        prestamo["fecha_primer_pago"],
    )
    resultado = []
    for cuota in cuotas:
        pagos = pagos_por_cuota.get(cuota["numero"], [])
        estado = calcular_estado_cuota(
            cuota["monto"],
            cuota["fecha_vencimiento"],
            pagos,
            fecha_corte,
        )
        resultado.append({
            **cuota,
            **estado,
            "fecha_corte": fecha_corte,
            "pagado": sum(
                (Decimal(str(pago["monto"])) for pago in pagos),
                Decimal("0.00"),
            ),
            "ultimo_pago": pagos[-1]["fecha_pago"] if pagos else None,
            "pagos": pagos,
        })
    return resultado


def _agregar_cuotas_pendientes(
    cursor,
    prestamos: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    for prestamo in prestamos:
        cuotas = _cargar_cuotas_prestamo(cursor, prestamo["id"])
        prestamo["cuotas_pendientes"] = sum(
            cuota["total_pendiente"] > 0
            for cuota in cuotas
        )
    return prestamos


def listar_cuotas_prestamo(prestamo_id: int) -> list[dict[str, Any]]:
    conexion = obtener_conexion()
    cursor = None
    try:
        cursor = conexion.cursor(dictionary=True)
        asegurar_esquema_prestamos(cursor)
        cuotas = _cargar_cuotas_prestamo(cursor, prestamo_id)
        conexion.commit()
        return cuotas
    except Exception:
        conexion.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()
        conexion.close()


def registrar_abono_cuota(
    prestamo_id: int,
    numero_cuota: int,
    monto: Decimal | int | float | str,
) -> dict[str, Any]:
    monto_pago = Decimal(str(monto))
    if not monto_pago.is_finite() or monto_pago <= 0:
        raise ValueError("El monto del abono debe ser mayor que cero.")
    monto_pago = monto_pago.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )
    if monto_pago <= 0:
        raise ValueError("El abono debe ser de al menos C$ 0.01.")

    conexion = obtener_conexion()
    cursor = None
    try:
        cursor = conexion.cursor(dictionary=True)
        asegurar_esquema_prestamos(cursor)
        cursor.execute(
            "SELECT id FROM prestamo WHERE id = %s FOR UPDATE",
            (prestamo_id,),
        )
        if cursor.fetchone() is None:
            raise ValueError("El préstamo no existe.")

        cuotas = _cargar_cuotas_prestamo(cursor, prestamo_id)
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

        cursor.execute(
            """
            INSERT INTO pagos_prestamo (prestamo_id, numero_cuota, monto)
            VALUES (%s, %s, %s)
            """,
            (prestamo_id, numero_cuota, monto_pago),
        )
        pago_id = cursor.lastrowid
        cursor.execute(
            "SELECT fecha_pago FROM pagos_prestamo WHERE id = %s",
            (pago_id,),
        )
        pago = cursor.fetchone()

        cuotas_actualizadas = _cargar_cuotas_prestamo(cursor, prestamo_id)
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
        cursor.execute(
            "UPDATE prestamo SET estado = %s WHERE id = %s",
            (estado, prestamo_id),
        )
        conexion.commit()
        return {
            "id": pago_id,
            "fecha_pago": pago["fecha_pago"],
            "estado_prestamo": estado,
        }
    except Exception:
        conexion.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()
        conexion.close()


def actualizar_prestamo(
    prestamo_id: int,
    monto: float,
    plazo: int,
    estado: str,
) -> bool:
    if not math.isfinite(monto) or monto <= 0 or plazo <= 0:
        raise ValueError("El monto y el plazo deben ser mayores que cero.")
    if estado not in {"Activo", "Pagado", "Vencido"}:
        raise ValueError("El estado del préstamo no es válido.")

    conexion = obtener_conexion()
    cursor = None
    try:
        cursor = conexion.cursor(dictionary=True)
        asegurar_esquema_prestamos(cursor)
        cursor.execute(
            "SELECT id, monto, plazo FROM prestamo WHERE id = %s FOR UPDATE",
            (prestamo_id,),
        )
        prestamo = cursor.fetchone()
        if prestamo is None:
            conexion.rollback()
            return False
        cursor.execute(
            "SELECT COUNT(*) AS cantidad FROM pagos_prestamo "
            "WHERE prestamo_id = %s",
            (prestamo_id,),
        )
        if cursor.fetchone()["cantidad"] and (
            Decimal(str(prestamo["monto"])) != Decimal(str(monto))
            or prestamo["plazo"] != plazo
        ):
            raise ValueError(
                "No se puede cambiar el monto o plazo de un préstamo "
                "que ya tiene abonos registrados."
            )
        if estado == "Pagado" and any(
            cuota["total_pendiente"] > 0
            for cuota in _cargar_cuotas_prestamo(cursor, prestamo_id)
        ):
            raise ValueError(
                "No se puede marcar como pagado un préstamo que aún tiene "
                "saldo pendiente."
            )
        cursor.execute(
            """
            UPDATE prestamo
            SET monto = %s, plazo = %s, estado = %s
            WHERE id = %s
            """,
            (monto, plazo, estado, prestamo_id),
        )
        conexion.commit()
        return True
    except Exception:
        conexion.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()
        conexion.close()


def eliminar_prestamo(prestamo_id: int) -> bool:
    conexion = obtener_conexion()
    cursor = None
    try:
        cursor = conexion.cursor()
        cursor.execute("DELETE FROM prestamo WHERE id = %s", (prestamo_id,))
        conexion.commit()
        return cursor.rowcount > 0
    except Exception:
        conexion.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()
        conexion.close()


def listar_prestamos(cliente_id: int) -> list[dict[str, Any]]:
    conexion = obtener_conexion()
    cursor = None
    try:
        cursor = conexion.cursor(dictionary=True)
        asegurar_esquema_prestamos(cursor)
        cursor.execute(
            """
            SELECT id, monto, plazo, estado, fecha_primer_pago
            FROM prestamo
            WHERE cliente_id = %s
            ORDER BY id
            """,
            (cliente_id,),
        )
        prestamos = _agregar_cuotas_pendientes(cursor, cursor.fetchall())
        conexion.commit()
        return prestamos
    finally:
        if cursor is not None:
            cursor.close()
        conexion.close()


def listar_todos_los_prestamos() -> list[dict[str, Any]]:
    conexion = obtener_conexion()
    cursor = None
    try:
        cursor = conexion.cursor(dictionary=True)
        asegurar_esquema_prestamos(cursor)
        cursor.execute(
            """
            SELECT id, cliente_id, monto, plazo, estado, fecha_primer_pago
            FROM prestamo
            ORDER BY cliente_id, id
            """
        )
        prestamos = _agregar_cuotas_pendientes(cursor, cursor.fetchall())
        conexion.commit()
        return prestamos
    finally:
        if cursor is not None:
            cursor.close()
        conexion.close()


def crear_prestamo(
    cliente_id: int,
    monto: float,
    plazo: int,
    estado: str = "Activo",
    fecha_primer_pago: date | None = None,
) -> int:
    if not math.isfinite(monto) or monto <= 0 or plazo <= 0:
        raise ValueError("El monto y el plazo deben ser mayores que cero.")
    if estado not in {"Activo", "Pagado", "Vencido"}:
        raise ValueError("El estado del préstamo no es válido.")

    conexion = obtener_conexion()
    cursor = None
    try:
        cursor = conexion.cursor()
        asegurar_esquema_prestamos(cursor)
        cursor.execute(
            """
            INSERT INTO prestamo
                (cliente_id, monto, plazo, estado, fecha_primer_pago)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                cliente_id,
                monto,
                plazo,
                estado,
                fecha_primer_pago or _fecha_mes_siguiente(date.today()),
            ),
        )
        conexion.commit()
        return cursor.lastrowid
    except Exception:
        conexion.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()
        conexion.close()
