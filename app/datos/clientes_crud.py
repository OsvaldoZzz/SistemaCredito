from typing import Any

from app.logica.ubicacion import validar_coordenadas

from app.config.conexion import obtener_conexion
from app.logica.validaciones import validar_datos_cliente, validar_direccion, validar_id, validar_monto


_ubicacion_lista = False


def asegurar_columnas_ubicacion() -> None:
    """Agrega clientes.latitud y clientes.longitud si todavía no existen."""
    global _ubicacion_lista
    if _ubicacion_lista:
        return
    conexion = obtener_conexion()
    cursor = None
    try:
        cursor = conexion.cursor()
        for columna in ("latitud", "longitud"):
            cursor.execute("SHOW COLUMNS FROM clientes LIKE %s", (columna,))
            if not cursor.fetchall():
                cursor.execute(
                    f"ALTER TABLE clientes ADD COLUMN {columna} DECIMAL(10, 7) NULL"
                )
        conexion.commit()
        _ubicacion_lista = True
    finally:
        if cursor is not None:
            cursor.close()
        conexion.close()


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
    latitud: float | None = None,
    longitud: float | None = None,
) -> int:
    """Crea un cliente y devuelve el ID generado."""
    _validar_cliente(nombre, cedula, correo, password, direccion)
    monto = validar_monto(monto, permitir_cero=True)
    nombre, cedula, correo, direccion = (v.strip() for v in (nombre, cedula, correo, direccion))
    latitud, longitud = validar_coordenadas(latitud, longitud)
    asegurar_columnas_ubicacion()
    sql = """
        INSERT INTO clientes
            (nombre, cedula, correo, password, direccion, monto, latitud, longitud)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    conexion = obtener_conexion()
    cursor = None
    try:
        cursor = conexion.cursor()
        _comprobar_duplicado(cursor, cedula, correo)
        cursor.execute(sql, (nombre, cedula, correo, password, direccion, monto, latitud, longitud))
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
    asegurar_columnas_ubicacion()
    conexion = obtener_conexion()
    cursor = None
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, nombre, cedula, correo, password, direccion, monto, latitud, longitud
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
    asegurar_columnas_ubicacion()
    conexion = obtener_conexion()
    cursor = None
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, nombre, cedula, correo, direccion, monto, latitud, longitud
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
    *,
    ubicacion: tuple[float, float] | None = None,
) -> bool:
    """Actualiza los datos de un cliente. Devuelve si encontró el registro."""
    validar_id(cliente_id)
    _validar_cliente(nombre, cedula, correo, password if password is not None else "********", direccion)
    monto = validar_monto(monto, permitir_cero=True)
    nombre, cedula, correo, direccion = (v.strip() for v in (nombre, cedula, correo, direccion))
    if ubicacion is not None:
        ubicacion = validar_coordenadas(*ubicacion)
        asegurar_columnas_ubicacion()
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
        if ubicacion is not None:
            sql += ", latitud = %s, longitud = %s"
            parametros.extend(ubicacion)
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


def actualizar_direccion_cliente(
    cliente_id: int,
    direccion: str,
    latitud: float | None,
    longitud: float | None,
) -> bool:
    """Guarda la dirección en texto y el punto del mapa de un cliente."""
    validar_id(cliente_id)
    error = validar_direccion(direccion)
    if error:
        raise ValueError(error)
    latitud, longitud = validar_coordenadas(latitud, longitud)
    direccion = direccion.strip()
    asegurar_columnas_ubicacion()
    conexion = obtener_conexion()
    cursor = None
    try:
        cursor = conexion.cursor()
        cursor.execute(
            """
            UPDATE clientes
            SET direccion = %s, latitud = %s, longitud = %s
            WHERE id = %s
            """,
            (direccion, latitud, longitud, cliente_id),
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
