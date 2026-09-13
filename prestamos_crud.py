from typing import Any

from conexion import obtener_conexion


def listar_prestamos(cliente_id: int) -> list[dict[str, Any]]:
    conexion = obtener_conexion()
    cursor = None
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, monto, plazo, estado
            FROM prestamo
            WHERE cliente_id = %s
            ORDER BY id
            """,
            (cliente_id,),
        )
        return cursor.fetchall()
    finally:
        if cursor is not None:
            cursor.close()
        conexion.close()


def crear_prestamo(
    cliente_id: int,
    monto: float,
    plazo: int,
    estado: str = "Activo",
) -> int:
    conexion = obtener_conexion()
    cursor = None
    try:
        cursor = conexion.cursor()
        cursor.execute(
            """
            INSERT INTO prestamo (cliente_id, monto, plazo, estado)
            VALUES (%s, %s, %s, %s)
            """,
            (cliente_id, monto, plazo, estado),
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
