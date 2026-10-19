import math
from typing import Any

from conexion import obtener_conexion


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
        cursor = conexion.cursor()
        cursor.execute("SELECT id FROM prestamo WHERE id = %s", (prestamo_id,))
        if cursor.fetchone() is None:
            conexion.rollback()
            return False
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


def listar_todos_los_prestamos() -> list[dict[str, Any]]:
    conexion = obtener_conexion()
    cursor = None
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, cliente_id, monto, plazo, estado
            FROM prestamo
            ORDER BY cliente_id, id
            """
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
    if not math.isfinite(monto) or monto <= 0 or plazo <= 0:
        raise ValueError("El monto y el plazo deben ser mayores que cero.")
    if estado not in {"Activo", "Pagado", "Vencido"}:
        raise ValueError("El estado del préstamo no es válido.")

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
