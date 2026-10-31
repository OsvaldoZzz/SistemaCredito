from datetime import date
from typing import Any

from app.config.conexion import obtener_conexion
from app.logica.calculos_prestamo import FRECUENCIAS_PAGO
from app.datos.prestamos_crud import (
    asegurar_esquema_prestamos,
    validar_cliente_sin_prestamos_pendientes,
)
from app.logica.validaciones import validar_condiciones_prestamo, validar_fecha, validar_id, validar_monto


def _crear_tabla_solicitudes(cursor) -> None:
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS solicitudes_prestamo (
            id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            cliente_id INT NOT NULL,
            monto DECIMAL(12, 2) NOT NULL,
            plazo INT NOT NULL,
            frecuencia_pago VARCHAR(10) NOT NULL DEFAULT 'Mensual',
            ingreso_mensual DECIMAL(12, 2) NULL,
            estado VARCHAR(20) NOT NULL DEFAULT 'Pendiente',
            fecha_solicitud TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_solicitudes_estado (estado),
            CONSTRAINT fk_solicitudes_cliente
                FOREIGN KEY (cliente_id) REFERENCES clientes(id)
                ON DELETE CASCADE
        ) ENGINE=InnoDB
        """
    )
    # Conserva las solicitudes anteriores cuando la tabla ya existe.
    cursor.execute("SHOW COLUMNS FROM solicitudes_prestamo LIKE 'frecuencia_pago'")
    if not cursor.fetchall():
        cursor.execute(
            "ALTER TABLE solicitudes_prestamo "
            "ADD COLUMN frecuencia_pago VARCHAR(10) NOT NULL DEFAULT 'Mensual'"
        )
    cursor.execute("SHOW COLUMNS FROM solicitudes_prestamo LIKE 'ingreso_mensual'")
    if not cursor.fetchall():
        cursor.execute(
            "ALTER TABLE solicitudes_prestamo "
            "ADD COLUMN ingreso_mensual DECIMAL(12, 2) NULL"
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

    conexion = obtener_conexion()
    cursor = None
    try:
        cursor = conexion.cursor(dictionary=True)
        _crear_tabla_solicitudes(cursor)
        asegurar_esquema_prestamos(cursor)
        validar_cliente_sin_prestamos_pendientes(cursor, cliente_id)
        cursor.execute(
            """
            INSERT INTO solicitudes_prestamo
                (cliente_id, monto, plazo, ingreso_mensual, frecuencia_pago)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (cliente_id, monto, plazo, ingreso_mensual, frecuencia_pago),
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


def listar_solicitudes_pendientes() -> list[dict[str, Any]]:
    conexion = obtener_conexion()
    cursor = None
    try:
        cursor = conexion.cursor()
        _crear_tabla_solicitudes(cursor)
        cursor.close()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT s.id, s.cliente_id, s.monto, s.plazo, s.estado, s.frecuencia_pago,
                   s.fecha_solicitud, s.ingreso_mensual, c.nombre, c.cedula
            FROM solicitudes_prestamo AS s
            JOIN clientes AS c ON c.id = s.cliente_id
            WHERE s.estado = 'Pendiente'
            ORDER BY s.fecha_solicitud, s.id
            """
        )
        return cursor.fetchall()
    finally:
        if cursor is not None:
            cursor.close()
        conexion.close()


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
    conexion = obtener_conexion()
    cursor = None
    try:
        cursor = conexion.cursor(dictionary=True)
        _crear_tabla_solicitudes(cursor)
        asegurar_esquema_prestamos(cursor)
        cursor.execute(
            """
            SELECT cliente_id, monto, plazo, frecuencia_pago
            FROM solicitudes_prestamo
            WHERE id = %s AND estado = 'Pendiente'
            FOR UPDATE
            """,
            (solicitud_id,),
        )
        solicitud = cursor.fetchone()
        if solicitud is None:
            raise ValueError("La solicitud ya fue resuelta o no existe.")

        estado = "Aprobada" if aprobada else "Rechazada"
        prestamo_id = None
        if aprobada:
            validar_id(solicitud["cliente_id"])
            validar_condiciones_prestamo(solicitud["monto"], solicitud["plazo"])
            if solicitud["frecuencia_pago"] not in FRECUENCIAS_PAGO:
                raise ValueError("La frecuencia de la solicitud no es válida.")
            validar_cliente_sin_prestamos_pendientes(
                cursor,
                solicitud["cliente_id"],
            )
            cursor.execute(
                """
                INSERT INTO prestamo
                    (cliente_id, monto, plazo, estado, fecha_primer_pago, frecuencia_pago)
                VALUES (%s, %s, %s, 'Activo', %s, %s)
                """,
                (
                    solicitud["cliente_id"],
                    solicitud["monto"],
                    solicitud["plazo"],
                    fecha_primer_pago or date.today(),
                    solicitud["frecuencia_pago"],
                ),
            )
            prestamo_id = cursor.lastrowid

        cursor.execute(
            """
            UPDATE solicitudes_prestamo
            SET estado = %s
            WHERE id = %s
            """,
            (estado, solicitud_id),
        )
        conexion.commit()
        return prestamo_id
    except Exception:
        conexion.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()
        conexion.close()
