import unittest
from datetime import date

from sqlalchemy import inspect, select

from app.config.conexion import obtener_engine, obtener_sesion
from app.datos import clientes_crud, prestamos_crud, solicitudes_crud
from app.datos.modelos import Cliente, Prestamo, SolicitudPrestamo
from orm_test_utils import OrmTestCase


class OrmMigrationsTest(OrmTestCase):
    def test_ubicacion_agrega_columnas_faltantes_a_clientes_existentes(self):
        with obtener_sesion() as session, session.begin():
            session.add(Cliente(
                nombre="Ana",
                cedula="12345678",
                correo="ana@example.com",
                password="clave1234",
                direccion="Centro",
                monto=0,
            ))
        with obtener_engine().begin() as connection:
            connection.exec_driver_sql("ALTER TABLE clientes DROP COLUMN latitud")
            connection.exec_driver_sql("ALTER TABLE clientes DROP COLUMN longitud")

        clientes_crud._ubicacion_lista = False
        clientes_crud.asegurar_columnas_ubicacion()
        columnas = {
            columna["name"]
            for columna in inspect(obtener_engine()).get_columns("clientes")
        }
        self.assertIn("latitud", columnas)
        self.assertIn("longitud", columnas)
        self.assertIsNone(clientes_crud.obtener_cliente(1)["latitud"])

    def test_prestamos_agrega_esquema_y_pagos_a_tablas_heredadas(self):
        with obtener_sesion() as session, session.begin():
            session.add(Cliente(
                nombre="Ana",
                cedula="12345678",
                correo="ana@example.com",
                password="clave1234",
                direccion="Centro",
                monto=0,
            ))
            session.flush()
            session.add(Prestamo(
                cliente_id=1,
                monto=100,
                plazo=1,
                estado="Activo",
                fecha_primer_pago=date.today(),
                frecuencia_pago="Semanal",
            ))
        with obtener_engine().begin() as connection:
            connection.exec_driver_sql("DROP TABLE pagos_prestamo")
            connection.exec_driver_sql(
                "ALTER TABLE prestamo DROP COLUMN frecuencia_pago"
            )
            connection.exec_driver_sql(
                "ALTER TABLE prestamo DROP COLUMN fecha_primer_pago"
            )

        with obtener_sesion() as session, session.begin():
            prestamos_crud.asegurar_esquema_prestamos(session)

        columnas = {
            columna["name"]
            for columna in inspect(obtener_engine()).get_columns("prestamo")
        }
        self.assertIn("fecha_primer_pago", columnas)
        self.assertIn("frecuencia_pago", columnas)
        self.assertTrue(inspect(obtener_engine()).has_table("pagos_prestamo"))
        with obtener_sesion() as session:
            prestamo = session.get(Prestamo, 1)
            self.assertEqual(prestamo.frecuencia_pago, "Mensual")
            self.assertIsNotNone(prestamo.fecha_primer_pago)

    def test_solicitudes_actualiza_columnas_sin_perder_registros(self):
        with obtener_sesion() as session, session.begin():
            session.add(Cliente(
                nombre="Ana",
                cedula="12345678",
                correo="ana@example.com",
                password="clave1234",
                direccion="Centro",
                monto=0,
            ))
        with obtener_engine().begin() as connection:
            connection.exec_driver_sql("DROP TABLE solicitudes_prestamo")
            connection.exec_driver_sql(
                """
                CREATE TABLE solicitudes_prestamo (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente_id INTEGER NOT NULL,
                    monto NUMERIC(12, 2) NOT NULL,
                    plazo INTEGER NOT NULL,
                    estado VARCHAR(20) NOT NULL DEFAULT 'Pendiente',
                    fecha_solicitud DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.exec_driver_sql(
                """
                INSERT INTO solicitudes_prestamo (cliente_id, monto, plazo)
                VALUES (1, 100, 4)
                """
            )

        with obtener_sesion() as session, session.begin():
            solicitudes_crud._crear_tabla_solicitudes(session)
            solicitud = session.scalar(
                select(SolicitudPrestamo).where(SolicitudPrestamo.id == 1)
            )
            self.assertEqual(solicitud.frecuencia_pago, "Mensual")
            self.assertIsNone(solicitud.ingreso_mensual)


if __name__ == "__main__":
    unittest.main()
