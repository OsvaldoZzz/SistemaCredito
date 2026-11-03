from typing import Any

from app.config.conexion import obtener_conexion
from app.logica.validaciones import validar_datos_rol, validar_id


def _asegurar_tabla_asignaciones(cursor) -> None:
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS cobrador_clientes (
            cobrador_id INT NOT NULL,
            cliente_id INT NOT NULL,
            PRIMARY KEY (cobrador_id, cliente_id),
            CONSTRAINT fk_cobrador_clientes_usuario
                FOREIGN KEY (cobrador_id) REFERENCES usuarios(id) ON DELETE CASCADE,
            CONSTRAINT fk_cobrador_clientes_cliente
                FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE CASCADE
        ) ENGINE=InnoDB
        """
    )


def listar_usuarios() -> list[dict[str, Any]]:
    """Lee los usuarios con rol (administrador, recepcionista, cobrador) de MySQL.

    La tabla guarda el nombre en la columna ``nombre``; el programa lo usa como
    ``usuario``. El ID se devuelve como texto, igual que en la lista interna.
    """
    conexion = obtener_conexion()
    cursor = None
    try:
        cursor = conexion.cursor(dictionary=True)
        _asegurar_tabla_asignaciones(cursor)
        cursor.execute("SELECT id, rol, nombre, password FROM usuarios ORDER BY id")
        usuarios = [
            {
                "id": str(fila["id"]),
                "rol": fila["rol"],
                "usuario": fila["nombre"],
                "password": fila["password"],
            }
            for fila in cursor.fetchall()
        ]
        cursor.execute(
            "SELECT cobrador_id, cliente_id FROM cobrador_clientes ORDER BY cliente_id"
        )
        asignaciones: dict[str, list[str]] = {}
        for fila in cursor.fetchall():
            asignaciones.setdefault(str(fila["cobrador_id"]), []).append(
                f"id:{fila['cliente_id']}"
            )
        for usuario in usuarios:
            if usuario["rol"] == "cobrador":
                usuario["clientes_asignados"] = asignaciones.get(usuario["id"], [])
        return usuarios
    finally:
        if cursor is not None:
            cursor.close()
        conexion.close()


def guardar_asignaciones_cobrador(
    cobrador_id: int,
    cliente_ids: list[int],
) -> bool:
    """Reemplaza las asignaciones de clientes de un cobrador."""
    validar_id(cobrador_id)
    cliente_ids_unicos = list(dict.fromkeys(cliente_ids))
    for cliente_id in cliente_ids_unicos:
        validar_id(cliente_id)

    conexion = obtener_conexion()
    cursor = None
    try:
        cursor = conexion.cursor()
        _asegurar_tabla_asignaciones(cursor)
        cursor.execute(
            "SELECT rol FROM usuarios WHERE id = %s",
            (cobrador_id,),
        )
        usuario = cursor.fetchone()
        if usuario is None:
            raise ValueError("El cobrador ya no existe en la base de datos.")
        if usuario[0] != "cobrador":
            raise ValueError("Solo se pueden asignar clientes a un cobrador.")

        if cliente_ids_unicos:
            marcadores = ", ".join(["%s"] * len(cliente_ids_unicos))
            cursor.execute(
                f"SELECT id FROM clientes WHERE id IN ({marcadores})",
                tuple(cliente_ids_unicos),
            )
            encontrados = {fila[0] for fila in cursor.fetchall()}
            if encontrados != set(cliente_ids_unicos):
                raise ValueError(
                    "Uno o más clientes seleccionados ya no existen en la base de datos."
                )

        cursor.execute(
            "DELETE FROM cobrador_clientes WHERE cobrador_id = %s",
            (cobrador_id,),
        )
        if cliente_ids_unicos:
            cursor.executemany(
                """
                INSERT INTO cobrador_clientes (cobrador_id, cliente_id)
                VALUES (%s, %s)
                """,
                [(cobrador_id, cliente_id) for cliente_id in cliente_ids_unicos],
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


def actualizar_usuario(
    usuario_id: int,
    nombre: str,
    rol: str,
    password: str | None = None,
) -> bool:
    """Actualiza el nombre, rol y, si se indicó, contraseña de un usuario."""
    validar_id(usuario_id)
    nombre = nombre.strip() if isinstance(nombre, str) else nombre
    conexion = obtener_conexion()
    cursor = None
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, password FROM usuarios WHERE id = %s",
            (usuario_id,),
        )
        usuario_actual = cursor.fetchone()
        if usuario_actual is None:
            return False

        password_validacion = (
            password if password is not None else usuario_actual["password"]
        )
        error = validar_datos_rol(nombre, password_validacion, rol, [])
        if error:
            raise ValueError(error)

        cursor.execute(
            """
            SELECT id FROM usuarios
            WHERE LOWER(TRIM(nombre)) = %s AND id <> %s
            LIMIT 1
            """,
            (nombre.casefold(), usuario_id),
        )
        if cursor.fetchone() is not None:
            raise ValueError("Ya existe un usuario con ese nombre.")

        sql = "UPDATE usuarios SET nombre = %s, rol = %s"
        parametros = [nombre, rol]
        if password is not None:
            sql += ", password = %s"
            parametros.append(password)
        sql += " WHERE id = %s"
        parametros.append(usuario_id)
        cursor.execute(sql, tuple(parametros))
        conexion.commit()
        return True
    except Exception:
        conexion.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()
        conexion.close()
