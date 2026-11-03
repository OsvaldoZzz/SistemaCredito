import unittest
from unittest.mock import MagicMock, patch

from app.datos import usuarios_crud


class UsuariosCrudTest(unittest.TestCase):
    def test_guardar_asignaciones_reemplaza_en_una_transaccion(self):
        conexion = MagicMock()
        cursor = conexion.cursor.return_value
        cursor.fetchone.return_value = ("cobrador",)
        cursor.fetchall.return_value = [(11,), (12,)]

        with patch.object(usuarios_crud, "obtener_conexion", return_value=conexion):
            guardado = usuarios_crud.guardar_asignaciones_cobrador(
                7, [11, 12, 11]
            )

        self.assertTrue(guardado)
        cursor.executemany.assert_called_once_with(
            """
                INSERT INTO cobrador_clientes (cobrador_id, cliente_id)
                VALUES (%s, %s)
                """,
            [(7, 11), (7, 12)],
        )
        conexion.commit.assert_called_once()
        conexion.rollback.assert_not_called()
        cursor.close.assert_called_once()
        conexion.close.assert_called_once()

    def test_guardar_asignaciones_rechaza_ids_invalidos_y_revierte(self):
        conexion = MagicMock()
        cursor = conexion.cursor.return_value
        cursor.fetchone.return_value = ("cobrador",)
        cursor.fetchall.return_value = [(11,)]

        with patch.object(usuarios_crud, "obtener_conexion", return_value=conexion):
            with self.assertRaisesRegex(ValueError, "ya no existen"):
                usuarios_crud.guardar_asignaciones_cobrador(7, [11, 12])

        conexion.commit.assert_not_called()
        conexion.rollback.assert_called_once()

    def test_guardar_asignaciones_rechaza_usuario_que_no_es_cobrador(self):
        conexion = MagicMock()
        cursor = conexion.cursor.return_value
        cursor.fetchone.return_value = ("recepcionista",)

        with patch.object(usuarios_crud, "obtener_conexion", return_value=conexion):
            with self.assertRaisesRegex(ValueError, "Solo se pueden asignar"):
                usuarios_crud.guardar_asignaciones_cobrador(7, [])

        conexion.commit.assert_not_called()
        conexion.rollback.assert_called_once()

    def test_listar_usuarios_incluye_asignaciones_persistidas(self):
        conexion = MagicMock()
        cursor = conexion.cursor.return_value
        cursor.fetchall.side_effect = [
            [
                {"id": 7, "rol": "cobrador", "nombre": "Cobrador", "password": "clave1234"},
                {"id": 8, "rol": "recepcionista", "nombre": "Recepción", "password": "clave5678"},
            ],
            [{"cobrador_id": 7, "cliente_id": 11}],
        ]

        with patch.object(usuarios_crud, "obtener_conexion", return_value=conexion):
            usuarios = usuarios_crud.listar_usuarios()

        self.assertEqual(usuarios[0]["clientes_asignados"], ["id:11"])
        self.assertNotIn("clientes_asignados", usuarios[1])

    def test_actualizar_usuario_guarda_cambios_y_conserva_password_vacio(self):
        conexion = MagicMock()
        cursor = conexion.cursor.return_value
        cursor.fetchone.side_effect = [{"id": 7, "password": "clave1234"}, None]

        with patch.object(usuarios_crud, "obtener_conexion", return_value=conexion):
            actualizado = usuarios_crud.actualizar_usuario(
                7, "Nombre Actualizado", "recepcionista"
            )

        self.assertTrue(actualizado)
        self.assertEqual(
            cursor.execute.call_args_list[-1].args,
            (
                "UPDATE usuarios SET nombre = %s, rol = %s WHERE id = %s",
                ("Nombre Actualizado", "recepcionista", 7),
            ),
        )
        conexion.commit.assert_called_once()
        conexion.rollback.assert_not_called()
        cursor.close.assert_called_once()
        conexion.close.assert_called_once()

    def test_actualizar_usuario_rechaza_nombre_duplicado_y_revierte(self):
        conexion = MagicMock()
        cursor = conexion.cursor.return_value
        cursor.fetchone.side_effect = [{"id": 7, "password": "clave1234"}, {"id": 8}]

        with patch.object(usuarios_crud, "obtener_conexion", return_value=conexion):
            with self.assertRaisesRegex(ValueError, "Ya existe un usuario"):
                usuarios_crud.actualizar_usuario(
                    7, "Nombre Existente", "recepcionista"
                )

        conexion.commit.assert_not_called()
        conexion.rollback.assert_called_once()
        cursor.close.assert_called_once()
        conexion.close.assert_called_once()

    def test_actualizar_usuario_indica_si_no_existe(self):
        conexion = MagicMock()
        cursor = conexion.cursor.return_value
        cursor.fetchone.return_value = None

        with patch.object(usuarios_crud, "obtener_conexion", return_value=conexion):
            actualizado = usuarios_crud.actualizar_usuario(
                99, "Nombre Nuevo", "cobrador"
            )

        self.assertFalse(actualizado)
        conexion.commit.assert_not_called()
        conexion.rollback.assert_not_called()


if __name__ == "__main__":
    unittest.main()
