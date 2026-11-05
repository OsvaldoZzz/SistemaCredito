import unittest

from app.config.conexion import obtener_sesion
from app.datos.modelos import Cliente, Usuario
from app.datos.usuarios_crud import (
    actualizar_usuario,
    guardar_asignaciones_cobrador,
    listar_usuarios,
)
from orm_test_utils import OrmTestCase


class UsuariosCrudTest(OrmTestCase):
    def setUp(self):
        super().setUp()
        with obtener_sesion() as session, session.begin():
            session.add_all([
                Usuario(id=7, rol="cobrador", nombre="Cobrador", password="clave1234"),
                Usuario(id=8, rol="recepcionista", nombre="Recepción", password="clave5678"),
                Cliente(
                    id=11, nombre="Ana", cedula="12345678", correo="ana@example.com",
                    password="clave1234", direccion="Centro", monto=0,
                ),
                Cliente(
                    id=12, nombre="Luis", cedula="87654321", correo="luis@example.com",
                    password="clave5678", direccion="Centro", monto=0,
                ),
            ])

    def test_guardar_asignaciones_reemplaza_y_quita_duplicados(self):
        self.assertTrue(guardar_asignaciones_cobrador(7, [11, 12, 11]))
        usuarios = listar_usuarios()
        self.assertEqual(usuarios[0]["clientes_asignados"], ["id:11", "id:12"])
        self.assertNotIn("clientes_asignados", usuarios[1])

        guardar_asignaciones_cobrador(7, [12])
        self.assertEqual(
            listar_usuarios()[0]["clientes_asignados"],
            ["id:12"],
        )

    def test_asignar_rechaza_ids_inexistentes_sin_perder_asignaciones(self):
        guardar_asignaciones_cobrador(7, [11])
        with self.assertRaisesRegex(ValueError, "ya no existen"):
            guardar_asignaciones_cobrador(7, [11, 99])
        self.assertEqual(
            listar_usuarios()[0]["clientes_asignados"],
            ["id:11"],
        )

    def test_asignar_solo_a_cobradores_existentes(self):
        with self.assertRaisesRegex(ValueError, "Solo se pueden asignar"):
            guardar_asignaciones_cobrador(8, [])
        with self.assertRaisesRegex(ValueError, "ya no existe"):
            guardar_asignaciones_cobrador(99, [])

    def test_actualizar_usuario_conserva_password_si_no_se_indica(self):
        self.assertTrue(actualizar_usuario(7, "Nombre Actualizado", "recepcionista"))
        with obtener_sesion() as session:
            usuario = session.get(Usuario, 7)
            self.assertEqual(usuario.nombre, "Nombre Actualizado")
            self.assertEqual(usuario.rol, "recepcionista")
            self.assertEqual(usuario.password, "clave1234")

    def test_actualizar_usuario_rechaza_nombre_duplicado(self):
        with self.assertRaisesRegex(ValueError, "Ya existe un usuario"):
            actualizar_usuario(7, "Recepción", "cobrador")

    def test_actualizar_usuario_indica_si_no_existe(self):
        self.assertFalse(actualizar_usuario(99, "Usuario Nuevo", "cobrador"))


if __name__ == "__main__":
    unittest.main()
