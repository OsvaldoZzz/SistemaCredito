from datetime import date

from conexion import obtener_conexion


def crear_cita(cliente_id: int, fecha: date) -> int:
    conexion = obtener_conexion()
    cursor = None
    try:
        cursor = conexion.cursor()
        cursor.execute(
            """
            INSERT INTO citas (cliente_id, fecha)
            VALUES (%s, %s)
            """,
            (cliente_id, fecha),
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
