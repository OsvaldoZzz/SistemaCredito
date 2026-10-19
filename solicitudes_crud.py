import math
from typing import Any

from conexion import obtener_conexion


def _crear_tabla_solicitudes(cursor) -> None:
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS solicitudes_prestamo (
            id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            cliente_id INT NOT NULL,
            monto DECIMAL(12, 2) NOT NULL,
            plazo INT NOT NULL,
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
) -> int:
    if (
        cliente_id <= 0
        or not math.isfinite(monto)
        or monto <= 0
        or plazo <= 0
    ):
        raise ValueError("El cliente, monto y plazo deben ser válidos.")
    if ingreso_mensual is not None and (
        not math.isfinite(ingreso_mensual)
        or ingreso_mensual <= 0
        or ingreso_mensual > 9_999_999_999.99
    ):
        raise ValueError("El ingreso mensual debe ser mayor que cero y válido.")

    conexion = obtener_conexion()
    cursor = None
    try:
        cursor = conexion.cursor()
        _crear_tabla_solicitudes(cursor)
        cursor.execute(
            """
            INSERT INTO solicitudes_prestamo
                (cliente_id, monto, plazo, ingreso_mensual)
            VALUES (%s, %s, %s, %s)
            """,
            (cliente_id, monto, plazo, ingreso_mensual),
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
            SELECT s.id, s.cliente_id, s.monto, s.plazo, s.estado,
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


def resolver_solicitud_prestamo(solicitud_id: int, aprobada: bool) -> int | None:
    conexion = obtener_conexion()
    cursor = None
    try:
        cursor = conexion.cursor(dictionary=True)
        _crear_tabla_solicitudes(cursor)
        cursor.execute(
            """
            SELECT cliente_id, monto, plazo
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
            cursor.execute(
                """
                INSERT INTO prestamo (cliente_id, monto, plazo, estado)
                VALUES (%s, %s, %s, 'Activo')
                """,
                (
                    solicitud["cliente_id"],
                    solicitud["monto"],
                    solicitud["plazo"],
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
