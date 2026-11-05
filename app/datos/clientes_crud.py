from typing import Any

from sqlalchemy import func, inspect, select, text, update, delete

from app.config.conexion import obtener_sesion
from app.datos.modelos import Cliente
from app.logica.ubicacion import validar_coordenadas
from app.logica.validaciones import (
    validar_datos_cliente,
    validar_direccion,
    validar_id,
    validar_monto,
)


_ubicacion_lista = False


def asegurar_columnas_ubicacion() -> None:
    """Agrega clientes.latitud y clientes.longitud si todavía no existen."""
    global _ubicacion_lista
    if _ubicacion_lista:
        return
    with obtener_sesion() as session:
        columnas = {
            columna["name"]
            for columna in inspect(session.connection()).get_columns("clientes")
        }
        for columna in ("latitud", "longitud"):
            if columna not in columnas:
                session.execute(
                    text(
                        f"ALTER TABLE clientes ADD COLUMN {columna} "
                        "DECIMAL(10, 7) NULL"
                    )
                )
        session.commit()
        _ubicacion_lista = True


def _validar_cliente(nombre, cedula, correo, password, direccion):
    error = validar_datos_cliente(nombre, cedula, correo, password, direccion)
    if error:
        raise ValueError(error)


def _comprobar_duplicado(session, cedula, correo, cliente_id=None):
    consulta = select(Cliente.id).where(
        (func.lower(func.trim(Cliente.cedula)) == cedula.casefold())
        | (func.lower(func.trim(Cliente.correo)) == correo.casefold())
    )
    if cliente_id is not None:
        consulta = consulta.where(Cliente.id != cliente_id)
    if session.scalar(consulta.limit(1)) is not None:
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
    nombre, cedula, correo, direccion = (
        valor.strip() for valor in (nombre, cedula, correo, direccion)
    )
    latitud, longitud = validar_coordenadas(latitud, longitud)
    asegurar_columnas_ubicacion()
    with obtener_sesion() as session, session.begin():
        _comprobar_duplicado(session, cedula, correo)
        cliente = Cliente(
            nombre=nombre,
            cedula=cedula,
            correo=correo,
            password=password,
            direccion=direccion,
            monto=monto,
            latitud=latitud,
            longitud=longitud,
        )
        session.add(cliente)
        session.flush()
        return cliente.id


def listar_clientes() -> list[dict[str, Any]]:
    """Devuelve todos los clientes."""
    asegurar_columnas_ubicacion()
    with obtener_sesion() as session:
        clientes = session.scalars(select(Cliente).order_by(Cliente.id)).all()
        return [
            {
                "id": cliente.id,
                "nombre": cliente.nombre,
                "cedula": cliente.cedula,
                "correo": cliente.correo,
                "password": cliente.password,
                "direccion": cliente.direccion,
                "monto": cliente.monto,
                "latitud": cliente.latitud,
                "longitud": cliente.longitud,
            }
            for cliente in clientes
        ]


def obtener_cliente(cliente_id: int) -> dict[str, Any] | None:
    """Busca un cliente por su ID."""
    validar_id(cliente_id)
    asegurar_columnas_ubicacion()
    with obtener_sesion() as session:
        cliente = session.get(Cliente, cliente_id)
        if cliente is None:
            return None
        return {
            "id": cliente.id,
            "nombre": cliente.nombre,
            "cedula": cliente.cedula,
            "correo": cliente.correo,
            "direccion": cliente.direccion,
            "monto": cliente.monto,
            "latitud": cliente.latitud,
            "longitud": cliente.longitud,
        }


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
    _validar_cliente(
        nombre,
        cedula,
        correo,
        password if password is not None else "********",
        direccion,
    )
    monto = validar_monto(monto, permitir_cero=True)
    nombre, cedula, correo, direccion = (
        valor.strip() for valor in (nombre, cedula, correo, direccion)
    )
    if ubicacion is not None:
        ubicacion = validar_coordenadas(*ubicacion)
        asegurar_columnas_ubicacion()
    with obtener_sesion() as session, session.begin():
        _comprobar_duplicado(session, cedula, correo, cliente_id)
        valores = {
            "nombre": nombre,
            "cedula": cedula,
            "correo": correo,
            "direccion": direccion,
            "monto": monto,
        }
        if password is not None:
            valores["password"] = password
        if ubicacion is not None:
            valores.update(latitud=ubicacion[0], longitud=ubicacion[1])
        resultado = session.execute(
            update(Cliente)
            .where(Cliente.id == cliente_id)
            .values(**valores)
            .execution_options(synchronize_session=False)
        )
        return resultado.rowcount > 0


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
    asegurar_columnas_ubicacion()
    with obtener_sesion() as session, session.begin():
        resultado = session.execute(
            update(Cliente)
            .where(Cliente.id == cliente_id)
            .values(
                direccion=direccion.strip(),
                latitud=latitud,
                longitud=longitud,
            )
            .execution_options(synchronize_session=False)
        )
        return resultado.rowcount > 0


def eliminar_cliente(cliente_id: int) -> bool:
    """Elimina un cliente. Devuelve si encontró el registro."""
    validar_id(cliente_id)
    with obtener_sesion() as session, session.begin():
        resultado = session.execute(delete(Cliente).where(Cliente.id == cliente_id))
        return resultado.rowcount > 0
