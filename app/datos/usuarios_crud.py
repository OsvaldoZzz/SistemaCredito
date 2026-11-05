from typing import Any

from sqlalchemy import delete, func, select

from app.config.conexion import obtener_sesion
from app.datos.modelos import CobradorCliente, Cliente, Usuario
from app.logica.validaciones import validar_datos_rol, validar_id


def _asegurar_tabla_asignaciones(session) -> None:
    CobradorCliente.__table__.create(session.connection(), checkfirst=True)


def listar_usuarios() -> list[dict[str, Any]]:
    """Devuelve usuarios con los clientes asignados a cada cobrador."""
    with obtener_sesion() as session, session.begin():
        _asegurar_tabla_asignaciones(session)
        usuarios = [
            {
                "id": str(usuario.id),
                "rol": usuario.rol,
                "usuario": usuario.nombre,
                "password": usuario.password,
            }
            for usuario in session.scalars(
                select(Usuario).order_by(Usuario.id)
            ).all()
        ]
        asignaciones: dict[str, list[str]] = {}
        filas = session.execute(
            select(CobradorCliente.cobrador_id, CobradorCliente.cliente_id)
            .order_by(CobradorCliente.cliente_id)
        )
        for cobrador_id, cliente_id in filas:
            asignaciones.setdefault(str(cobrador_id), []).append(
                f"id:{cliente_id}"
            )
        for usuario in usuarios:
            if usuario["rol"] == "cobrador":
                usuario["clientes_asignados"] = asignaciones.get(usuario["id"], [])
        return usuarios


def guardar_asignaciones_cobrador(
    cobrador_id: int,
    cliente_ids: list[int],
) -> bool:
    """Reemplaza las asignaciones de clientes de un cobrador."""
    validar_id(cobrador_id)
    cliente_ids_unicos = list(dict.fromkeys(cliente_ids))
    for cliente_id in cliente_ids_unicos:
        validar_id(cliente_id)

    with obtener_sesion() as session, session.begin():
        _asegurar_tabla_asignaciones(session)
        usuario = session.scalar(
            select(Usuario)
            .where(Usuario.id == cobrador_id)
            .with_for_update()
        )
        if usuario is None:
            raise ValueError("El cobrador ya no existe en la base de datos.")
        if usuario.rol != "cobrador":
            raise ValueError("Solo se pueden asignar clientes a un cobrador.")

        if cliente_ids_unicos:
            encontrados = set(
                session.scalars(
                    select(Cliente.id).where(Cliente.id.in_(cliente_ids_unicos))
                ).all()
            )
            if encontrados != set(cliente_ids_unicos):
                raise ValueError(
                    "Uno o más clientes seleccionados ya no existen en la base de datos."
                )

        session.execute(
            delete(CobradorCliente).where(
                CobradorCliente.cobrador_id == cobrador_id
            )
        )
        session.add_all(
            CobradorCliente(cobrador_id=cobrador_id, cliente_id=cliente_id)
            for cliente_id in cliente_ids_unicos
        )
        return True


def actualizar_usuario(
    usuario_id: int,
    nombre: str,
    rol: str,
    password: str | None = None,
) -> bool:
    """Actualiza el nombre, rol y, si se indicó, contraseña de un usuario."""
    validar_id(usuario_id)
    nombre = nombre.strip() if isinstance(nombre, str) else nombre
    with obtener_sesion() as session, session.begin():
        usuario = session.get(Usuario, usuario_id)
        if usuario is None:
            return False

        password_validacion = (
            password if password is not None else usuario.password
        )
        error = validar_datos_rol(nombre, password_validacion, rol, [])
        if error:
            raise ValueError(error)

        duplicado = session.scalar(
            select(Usuario.id)
            .where(
                func.lower(func.trim(Usuario.nombre)) == nombre.casefold(),
                Usuario.id != usuario_id,
            )
            .limit(1)
        )
        if duplicado is not None:
            raise ValueError("Ya existe un usuario con ese nombre.")

        usuario.nombre = nombre
        usuario.rol = rol
        if password is not None:
            usuario.password = password
        return True
