from datetime import date

from conexion import obtener_conexion


def crear_cita(cliente_id: int, fecha: date) -> int:
    if cliente_id <= 0:
        raise ValueError("El cliente seleccionado no es válido.")
    if fecha < date.today():
        raise ValueError("No se puede agendar una cita en una fecha pasada.")

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


def listar_citas(cliente_id: int) -> list[dict]:
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
