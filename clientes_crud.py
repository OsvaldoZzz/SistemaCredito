from typing import Any

from conexion import obtener_conexion


def crear_cliente(
    nombre: str,
    cedula: str,
    correo: str,
    password: str,
    direccion: str,
    monto: float = 0,
) -> int:
    """Crea un cliente y devuelve el ID generado."""
    sql = """
        INSERT INTO clientes
            (nombre, cedula, correo, password, direccion, monto)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    conexion = obtener_conexion()
    cursor = None
    try:
        cursor = conexion.cursor()
        cursor.execute(sql, (nombre, cedula, correo, password, direccion, monto))
        conexion.commit()
        return cursor.lastrowid
    except Exception:
        conexion.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()
        conexion.close()


def listar_clientes() -> list[dict[str, Any]]:
    """Devuelve todos los clientes."""
    conexion = obtener_conexion()
    cursor = None
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, nombre, cedula, correo, direccion, monto
            FROM clientes
            ORDER BY id
            """
        )
        return cursor.fetchall()
    finally:
        if cursor is not None:
            cursor.close()
        conexion.close()


def obtener_cliente(cliente_id: int) -> dict[str, Any] | None:
    """Busca un cliente por su ID."""
    conexion = obtener_conexion()
    cursor = None
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, nombre, cedula, correo, direccion, monto
            FROM clientes
            WHERE id = %s
            """,
            (cliente_id,),
        )
        return cursor.fetchone()
    finally:
        if cursor is not None:
            cursor.close()
        conexion.close()


def actualizar_cliente(
    cliente_id: int,
    nombre: str,
    cedula: str,
    correo: str,
    direccion: str,
    monto: float,
) -> bool:
    """Actualiza los datos de un cliente. Devuelve si encontró el registro."""
    conexion = obtener_conexion()
    cursor = None
    try:
        cursor = conexion.cursor()
        cursor.execute(
            """
            UPDATE clientes
            SET nombre = %s, cedula = %s, correo = %s,
                direccion = %s, monto = %s
            WHERE id = %s
            """,
            (nombre, cedula, correo, direccion, monto, cliente_id),
        )
        conexion.commit()
        return cursor.rowcount > 0
    except Exception:
        conexion.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()
        conexion.close()


def eliminar_cliente(cliente_id: int) -> bool:
    """Elimina un cliente. Devuelve si encontró el registro."""
    conexion = obtener_conexion()
    cursor = None
    try:
        cursor = conexion.cursor()
        cursor.execute("DELETE FROM clientes WHERE id = %s", (cliente_id,))
        conexion.commit()
        return cursor.rowcount > 0
    except Exception:
        conexion.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()
        conexion.close()


if __name__ == "__main__":
    print(listar_clientes())
