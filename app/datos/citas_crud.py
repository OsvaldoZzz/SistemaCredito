from datetime import date

from sqlalchemy import select

from app.config.conexion import obtener_sesion
from app.datos.modelos import Cita, Cliente
from app.logica.validaciones import validar_fecha_cita, validar_id


def crear_cita(cliente_id: int, fecha: date) -> int:
    validar_id(cliente_id)
    validar_fecha_cita(fecha)

    with obtener_sesion() as session, session.begin():
        existente = session.scalar(
            select(Cita.id)
            .where(Cita.cliente_id == cliente_id, Cita.fecha == fecha)
            .limit(1)
        )
        if existente is not None:
            raise ValueError("Ya tienes una cita registrada para esa fecha.")
        cita = Cita(cliente_id=cliente_id, fecha=fecha, estado="Pendiente")
        session.add(cita)
        session.flush()
        return cita.id


def listar_citas(cliente_id: int) -> list[dict]:
    validar_id(cliente_id)
    with obtener_sesion() as session:
        citas = session.scalars(
            select(Cita)
            .where(Cita.cliente_id == cliente_id)
            .order_by(Cita.fecha, Cita.id)
        ).all()
        return [
            {"id": cita.id, "fecha": cita.fecha, "estado": cita.estado}
            for cita in citas
        ]


def listar_todas_las_citas() -> list[dict]:
    with obtener_sesion() as session:
        filas = session.execute(
            select(
                Cita.id,
                Cita.cliente_id,
                Cita.fecha,
                Cita.estado,
                Cliente.nombre,
                Cliente.cedula,
            )
            .join(Cliente, Cliente.id == Cita.cliente_id)
            .order_by(Cita.fecha, Cita.id)
        ).mappings()
        return [dict(fila) for fila in filas]
