from datetime import date

from app.config.conexion import obtener_conexion
from app.logica.validaciones import validar_fecha, validar_id


def crear_cita(cliente_id: int, fecha: date) -> int:
    validar_id(cliente_id)
    validar_fecha(fecha)

    conexion = obtener_conexion()
    cursor = None
    try:
        cursor = conexion.cursor()
        cursor.execute(
            "SELECT id FROM citas WHERE cliente_id = %s AND fecha = %s LIMIT 1",
            (cliente_id, fecha),
        )
        if cursor.fetchone() is not None:
            raise ValueError("Ya tienes una cita registrada para esa fecha.")
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


def listar_citas(cliente_id: int) -> list[dict]:
    validar_id(cliente_id)
    conexion = obtener_conexion()
    cursor = None
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, fecha, estado
            FROM citas
            WHERE cliente_id = %s
            ORDER BY fecha, id
            """,
            (cliente_id,),
        )
        return cursor.fetchall()
    finally:
        if cursor is not None:
            cursor.close()
        conexion.close()


def listar_todas_las_citas() -> list[dict]:
    conexion = obtener_conexion()
    cursor = None
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT citas.id, citas.cliente_id, citas.fecha, citas.estado,
                   clientes.nombre, clientes.cedula
            FROM citas
            JOIN clientes ON clientes.id = citas.cliente_id
            ORDER BY citas.fecha, citas.id
            """
        )
        return cursor.fetchall()
    finally:
        if cursor is not None:
            cursor.close()
        conexion.close()
