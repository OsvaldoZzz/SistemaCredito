from typing import Any

from app.config.conexion import obtener_conexion
from app.logica.validaciones import validar_datos_cliente, validar_id, validar_monto


def _validar_cliente(nombre, cedula, correo, password, direccion):
    error = validar_datos_cliente(nombre, cedula, correo, password, direccion)
    if error:
        raise ValueError(error)


def _comprobar_duplicado(cursor, cedula, correo, cliente_id=None):
    sql = "SELECT id FROM clientes WHERE (LOWER(TRIM(cedula)) = %s OR LOWER(TRIM(correo)) = %s)"
    parametros = [cedula.casefold(), correo.casefold()]
    if cliente_id is not None:
        sql += " AND id <> %s"
        parametros.append(cliente_id)
    cursor.execute(sql + " LIMIT 1", tuple(parametros))
    if cursor.fetchone() is not None:
        raise ValueError("Ya existe un cliente con esa cédula o correo.")


def crear_cliente(
    nombre: str,
    cedula: str,
    correo: str,
    password: str,
    direccion: str,
    monto: float = 0,
) -> int:
    """Crea un cliente y devuelve el ID generado."""
    _validar_cliente(nombre, cedula, correo, password, direccion)
    monto = validar_monto(monto, permitir_cero=True)
    nombre, cedula, correo, direccion = (v.strip() for v in (nombre, cedula, correo, direccion))
    sql = """
        INSERT INTO clientes
            (nombre, cedula, correo, password, direccion, monto)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    conexion = obtener_conexion()
    cursor = None
    try:
        cursor = conexion.cursor()
        _comprobar_duplicado(cursor, cedula, correo)
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
            SELECT id, nombre, cedula, correo, password, direccion, monto
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
    validar_id(cliente_id)
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
    password: str | None = None,
) -> bool:
    """Actualiza los datos de un cliente. Devuelve si encontró el registro."""
    validar_id(cliente_id)
    _validar_cliente(nombre, cedula, correo, password if password is not None else "********", direccion)
    monto = validar_monto(monto, permitir_cero=True)
    nombre, cedula, correo, direccion = (v.strip() for v in (nombre, cedula, correo, direccion))
    conexion = obtener_conexion()
    cursor = None
    try:
        cursor = conexion.cursor()
        _comprobar_duplicado(cursor, cedula, correo, cliente_id)
        sql = """
            UPDATE clientes
            SET nombre = %s, cedula = %s, correo = %s,
                direccion = %s, monto = %s
        """
        parametros = [nombre, cedula, correo, direccion, monto]
        if password is not None:
            sql += ", password = %s"
            parametros.append(password)
        sql += " WHERE id = %s"
        parametros.append(cliente_id)
        cursor.execute(sql, tuple(parametros))
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
    validar_id(cliente_id)
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
