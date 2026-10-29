import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QComboBox, QDialog, QLineEdit, QListWidget, QMessageBox, QPushButton
from app.ui.GUI_ADMIN import AdminWindow


class AdminRolesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.login = SimpleNamespace(input_user=QLineEdit("Admin"), usuarios=[
            dict(id="1", usuario="Admin", rol="administrador", password="12345678"),
            dict(id="2", usuario="recepcionista1", rol="recepcionista", password="12345678"),
            dict(id="3", usuario="recepcionista2", rol="recepcionista", password="87654321"),
            dict(id="4", usuario="cobrador1", rol="cobrador", password="12345678"),
        ])
        with patch.object(AdminWindow, "showMaximized"):
            self.window = AdminWindow([], self.login)

    def tearDown(self):
        for widget in self.app.topLevelWidgets():
            widget.close()

    def test_detalle_por_seleccion_y_actualizacion(self):
        self.window.tabs.setCurrentIndex(2)
        self.assertTrue(self.window.panelPrestamos.isHidden())
        self.assertFalse(self.window.panelRol.isHidden())
        self.window.listaRecep.setCurrentRow(1)
        self.assertEqual(self.window.lblNombreRol.text(), "Usuario: recepcionista2")
        self.login.usuarios[2]["usuario"] = "nuevo_nombre"
        self.window.actualizarListasRoles()
        self.assertEqual(self.window.lblNombreRol.text(), "Usuario: nuevo_nombre")
        self.assertEqual(self.window.usuarioRolSeleccionado()["id"], "3")
        self.login.usuarios[:] = self.login.usuarios[:1]
        self.window.actualizarListasRoles()
        self.assertIn("Selecciona un recepcionista", self.window.lblNombreRol.text())
        self.assertEqual(self.window.lblIdRol.text(), "")
        self.window.tabs.setCurrentIndex(0)
        self.assertTrue(self.window.panelRol.isHidden())
        self.assertFalse(self.window.panelPrestamos.isHidden())

    def test_acciones_contextuales_y_destinatario(self):
        for indice, rol, usuario_id in ((1, "cobrador", "4"), (2, "recepcionista", "2")):
            self.window.tabs.setCurrentIndex(indice)
            for texto, metodo, args in (
                (f"Crear {rol}", "crearRol", (rol,)),
                (f"Editar {rol}", "actualizarRol", (rol, usuario_id)),
                (f"Eliminar {rol}", "eliminarRol", (rol, usuario_id)),
            ):
                with self.subTest(rol=rol, accion=texto):
                    def elegir(dialogo):
                        botones = {b.text(): b for b in dialogo.findChildren(QPushButton)}
                        self.assertEqual(set(botones), {f"Crear {rol}", f"Editar {rol}", f"Eliminar {rol}", "Cancelar"})
                        botones[texto].click()
                        return dialogo.result()

                    with patch.object(QDialog, "exec", elegir), patch.object(self.window, metodo) as accion:
                        self.window.accionesAdmin()
                        accion.assert_called_once_with(*args)

    def test_acciones_sin_seleccion_y_cancelacion(self):
        self.window.tabs.setCurrentIndex(2)
        self.window.listaRecep.setCurrentRow(-1)

        def cancelar(dialogo):
            botones = {b.text(): b for b in dialogo.findChildren(QPushButton)}
            self.assertTrue(botones["Crear recepcionista"].isEnabled())
            self.assertFalse(botones["Editar recepcionista"].isEnabled())
            self.assertFalse(botones["Eliminar recepcionista"].isEnabled())
            botones["Cancelar"].click()
            return dialogo.result()

        with patch.object(QDialog, "exec", cancelar), patch.object(self.window, "crearRol") as crear:
            self.window.accionesAdmin()
            crear.assert_not_called()

    def test_creacion_fija_el_rol_y_actualiza_lista(self):
        self.window.crearRol("recepcionista")
        self.assertEqual(self.window.infoRol.currentText(), "recepcionista")
        self.assertFalse(self.window.infoRol.isEnabled())
        self.window.infoName.setText("recepcion_nueva")
        self.window.infoPassword.setText("claveLarga123")
        with patch.object(QMessageBox, "information"):
            self.window.btnEnviar.click()
        self.assertEqual(self.login.usuarios[-1]["rol"], "recepcionista")
        self.assertEqual(self.window.listaRecep.count(), 3)
        self.assertEqual(self.window.listaCobradores.count(), 1)

    def test_edicion_seleccionada_valida_duplicados_y_conserva_password(self):
        self.window.tabs.setCurrentIndex(2)
        self.window.listaRecep.setCurrentRow(1)

        def editar(dialogo):
            nombre = dialogo.findChild(QLineEdit, "usuario")
            password = dialogo.findChild(QLineEdit, "password")
            self.assertEqual(nombre.text(), "recepcionista2")
            self.assertEqual(password.text(), "")
            self.assertFalse(dialogo.findChild(QComboBox, "rol").isEnabled())
            guardar = dialogo.findChild(QPushButton, "guardarCambios")
            nombre.setText("recepcionista1")
            with patch.object(QMessageBox, "warning") as aviso:
                guardar.click()
                aviso.assert_called_once()
            self.assertEqual(self.login.usuarios[2]["usuario"], "recepcionista2")
            nombre.setText("recepcion_editada")
            guardar.click()
            return dialogo.result()

        with patch.object(QDialog, "exec", editar), patch.object(QMessageBox, "information"):
            self.window.actualizarRol("recepcionista", "3")
        self.assertEqual(self.login.usuarios[2]["password"], "87654321")
        self.assertEqual(self.window.lblNombreRol.text(), "Usuario: recepcion_editada")
        self.assertEqual(self.login.usuarios[1]["usuario"], "recepcionista1")

    def test_eliminacion_confirma_y_respeta_usuario_seleccionado(self):
        self.window.tabs.setCurrentIndex(2)
        self.window.listaRecep.setCurrentRow(1)

        def eliminar(dialogo):
            dialogo.findChild(QPushButton, "eliminar_rol").click()
            return dialogo.result()

        with patch.object(QDialog, "exec", eliminar), patch.object(QMessageBox, "question", return_value=QMessageBox.No):
            self.window.eliminarRol("recepcionista", "3")
        self.assertEqual(len(self.login.usuarios), 4)
        with patch.object(QDialog, "exec", eliminar), patch.object(QMessageBox, "question", return_value=QMessageBox.Yes), patch.object(QMessageBox, "information"):
            self.window.eliminarRol("recepcionista", "3")
        self.assertEqual([u["id"] for u in self.login.usuarios], ["1", "2", "4"])
        self.assertEqual(self.window.listaRecep.count(), 1)
        self.assertEqual(self.window.lblNombreRol.text(), "Usuario: recepcionista1")

    def preparar_clientes(self):
        self.window.clientes[:] = [
            dict(id=11, nombre="Ana", cedula="12345678", correo="ana@example.com", direccion="Centro"),
            dict(id=12, nombre="Luis", cedula="87654321", correo="luis@example.com", direccion="Norte"),
            dict(id=13, nombre="Ana", cedula="98765432", correo="otra@example.com", direccion="Sur"),
        ]

    def test_asignar_dos_clientes_muestra_datos_y_separa_usuarios(self):
        self.preparar_clientes()
        self.window.tabs.setCurrentIndex(1)

        def asignar(dialogo):
            lista = dialogo.findChild(QListWidget, "clientesAsignables")
            self.assertEqual(lista.count(), 3)
            lista.item(0).setCheckState(Qt.CheckState.Checked)
            lista.item(1).setCheckState(Qt.CheckState.Checked)
            return QDialog.Accepted

        with patch.object(QDialog, "exec", asignar):
            self.window.asignarClientesRol()
        tabla = self.window.tablaClientesRol
        self.assertEqual(tabla.rowCount(), 2)
        self.assertEqual(self.window.lblTotalAsignados.text(), "Clientes asignados: 2")
        self.assertEqual([tabla.item(0, c).text() for c in range(4)], ["Ana", "12345678", "ana@example.com", "Centro"])
        self.assertEqual(self.login.usuarios[3]["clientes_asignados"], ["id:11", "id:12"])
        self.window.tabs.setCurrentIndex(2)
        self.assertEqual(tabla.rowCount(), 0)
        self.assertNotIn("clientes_asignados", self.login.usuarios[1])
        self.window.tabs.setCurrentIndex(1)
        self.assertEqual(tabla.rowCount(), 2)

    def test_asignacion_cancelar_y_quitar_sin_alterar_clientes(self):
        self.preparar_clientes()
        self.login.usuarios[1]["clientes_asignados"] = ["id:11", "id:12"]
        self.window.tabs.setCurrentIndex(2)

        def cambiar(dialogo, resultado):
            lista = dialogo.findChild(QListWidget, "clientesAsignables")
            self.assertEqual(lista.item(0).checkState(), Qt.CheckState.Checked)
            lista.item(0).setCheckState(Qt.CheckState.Unchecked)
            return resultado

        with patch.object(QDialog, "exec", lambda d: cambiar(d, QDialog.Rejected)):
            self.window.asignarClientesRol()
        self.assertEqual(self.window.tablaClientesRol.rowCount(), 2)
        with patch.object(QDialog, "exec", lambda d: cambiar(d, QDialog.Accepted)):
            self.window.asignarClientesRol()
        self.assertEqual(self.login.usuarios[1]["clientes_asignados"], ["id:12"])
        self.assertEqual(self.window.tablaClientesRol.rowCount(), 1)
        self.assertEqual(len(self.window.clientes), 3)

    def test_asignaciones_reflejan_edicion_y_clientes_eliminados(self):
        self.preparar_clientes()
        self.login.usuarios[3]["clientes_asignados"] = ["id:11", "id:12"]
        self.window.tabs.setCurrentIndex(1)
        self.window.clientes[0].update(nombre="Ana editada", cedula="11112222")
        self.window.clientes.pop(1)
        self.window.mostrarRol()
        self.assertEqual(self.window.tablaClientesRol.rowCount(), 1)
        self.assertEqual(self.window.tablaClientesRol.item(0, 0).text(), "Ana editada")
        self.assertEqual(self.window.tablaClientesRol.item(0, 1).text(), "11112222")
        self.window.listaCobradores.setCurrentRow(-1)
        self.assertEqual(self.window.tablaClientesRol.rowCount(), 0)
        self.assertFalse(self.window.btnAsignarClientes.isEnabled())

    def test_clientes_sin_id_conservan_asignacion_al_editar(self):
        cliente = dict(nombre="Ana", cedula="12345678", correo="ana@example.com", direccion="Centro")
        self.window.clientes[:] = [cliente]
        clave = self.window.claveClienteAsignado(cliente)
        self.login.usuarios[3]["clientes_asignados"] = [clave]
        self.window.tabs.setCurrentIndex(1)
        cliente["cedula"] = "11112222"
        self.window.mostrarRol()
        self.assertEqual(self.window.claveClienteAsignado(cliente), clave)
        self.assertEqual(self.window.tablaClientesRol.rowCount(), 1)
        self.assertEqual(self.window.tablaClientesRol.item(0, 1).text(), "11112222")


if __name__ == "__main__":
    unittest.main()
