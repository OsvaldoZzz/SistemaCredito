import os
import unittest
from decimal import Decimal
from unittest.mock import MagicMock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QDialog, QDialogButtonBox, QLineEdit, QMessageBox
from app.datos import clientes_crud
from app.logica.ubicacion import validar_coordenadas
from app.ui import mapa_dialogo, ubicacion_ui


class UbicacionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_coordenadas_nulas_cero_decimales_y_limites(self):
        self.assertEqual(validar_coordenadas(None, None), (None, None))
        self.assertEqual(validar_coordenadas(0, 0), (0, 0))
        self.assertEqual(validar_coordenadas(Decimal("12.4379"), Decimal("-86.878")),
                         (12.4379, -86.878))
        for punto in ((None, 1), (1, None), (91, 0), (0, -181),
                      (float("nan"), 0), (0, float("inf")), (True, 0), ("abc", 0)):
            with self.subTest(punto=punto), self.assertRaises(ValueError):
                validar_coordenadas(*punto)

    def test_migracion_agrega_solo_columna_faltante_y_se_ejecuta_una_vez(self):
        conexion = MagicMock()
        cursor = conexion.cursor.return_value
        cursor.fetchall.side_effect = [[], [("longitud",)]]
        with patch.object(clientes_crud, "_ubicacion_lista", False), \
             patch.object(clientes_crud, "obtener_conexion", return_value=conexion) as conectar:
            clientes_crud.asegurar_columnas_ubicacion()
            clientes_crud.asegurar_columnas_ubicacion()
            conectar.assert_called_once()
        alters = [c.args[0] for c in cursor.execute.call_args_list if "ALTER" in c.args[0]]
        self.assertEqual(alters, ["ALTER TABLE clientes ADD COLUMN latitud DECIMAL(10, 7) NULL"])
        conexion.commit.assert_called_once()
        cursor.close.assert_called_once()
        conexion.close.assert_called_once()

    def test_guardado_coordenadas_y_rollback(self):
        conexion = MagicMock()
        cursor = conexion.cursor.return_value
        cursor.rowcount = 1
        with patch.object(clientes_crud, "asegurar_columnas_ubicacion"), \
             patch.object(clientes_crud, "obtener_conexion", return_value=conexion):
            clientes_crud.actualizar_direccion_cliente(3, " Centro ", 12.4379, -86.878)
            self.assertEqual(cursor.execute.call_args.args[1], ("Centro", 12.4379, -86.878, 3))
            cursor.execute.side_effect = RuntimeError("Fallo de escritura")
            with self.assertRaises(RuntimeError):
                clientes_crud.actualizar_direccion_cliente(3, "Centro", 0, 0)
            conexion.rollback.assert_called_once()

    def test_coordenadas_invalidas_no_conectan(self):
        with patch.object(clientes_crud, "obtener_conexion") as conectar:
            with self.assertRaises(ValueError):
                clientes_crud.crear_cliente("Ana", "123456", "a@example.com", "12345678",
                                            "Centro", latitud=100, longitud=0)
            with self.assertRaises(ValueError):
                clientes_crud.actualizar_direccion_cliente(1, "Centro", 0, None)
            conectar.assert_not_called()

    def test_editar_datos_sin_punto_conserva_ubicacion(self):
        conexion = MagicMock()
        conexion.cursor.return_value.rowcount = 1
        conexion.cursor.return_value.fetchone.return_value = None
        with patch.object(clientes_crud, "obtener_conexion", return_value=conexion):
            clientes_crud.actualizar_cliente(1, "Ana", "123456", "a@example.com", "Centro", 0)
        sql = conexion.cursor.return_value.execute.call_args.args[0]
        self.assertNotIn("latitud", sql)
        self.assertNotIn("longitud", sql)

    def test_cancelar_selector_conserva_punto(self):
        campo = ubicacion_ui.CampoUbicacion(12.4, -86.8)
        try:
            with patch.object(ubicacion_ui, "elegir_ubicacion", return_value=None):
                campo.boton.click()
            self.assertEqual((campo.lat, campo.lng), (12.4, -86.8))
            with patch.object(ubicacion_ui, "elegir_ubicacion", return_value=(0, 0)):
                campo.boton.click()
            self.assertEqual((campo.lat, campo.lng), (0, 0))
        finally:
            campo.close()

    def test_direccion_actual_se_envia_al_mapa_y_descarta_punto_anterior(self):
        direccion = QLineEdit("Centro")
        campo = ubicacion_ui.CampoUbicacion(12.4, -86.8, direccion=direccion)
        try:
            direccion.setText("Barrio nuevo, León")
            self.assertEqual((campo.lat, campo.lng), (None, None))
            self.assertFalse(campo.boton.icon().isNull())
            self.assertEqual(campo.boton.text(), "")
            with patch.object(ubicacion_ui, "elegir_ubicacion", return_value=(12.5, -86.9)) as elegir:
                campo.boton.click()
                elegir.assert_called_once_with(campo.window(), None, None,
                                               direccion="Barrio nuevo, León")
            self.assertEqual((campo.lat, campo.lng), (12.5, -86.9))
        finally:
            campo.close()
            direccion.close()

    def test_direccion_en_ambos_proveedores_se_codifica_sin_inyectar_html(self):
        for clave in ("", "llave-de-prueba"):
            with self.subTest(clave=clave), patch.object(mapa_dialogo, "clave_api", return_value=clave):
                html = mapa_dialogo._html(None, None, True, 'León </script> "centro"')
                self.assertNotIn('León </script>', html)
                self.assertIn(r'\u003c/script>', html)
                self.assertIn("else if (DIRECCION) { buscar(); }", html)
                self.assertNotIn("__DIRECCION__", html)

    def test_error_al_guardar_no_cambia_cliente_ni_cierra_dialogo(self):
        cliente = dict(id=1, direccion="Centro", latitud=None, longitud=None)

        def interactuar(dialogo):
            dialogo.findChild(QLineEdit).setText("Barrio nuevo")
            campo = dialogo.findChild(ubicacion_ui.CampoUbicacion)
            campo.lat, campo.lng = 12.4, -86.8
            with patch.object(ubicacion_ui, "actualizar_direccion_cliente", side_effect=ValueError("Error")), \
                 patch.object(QMessageBox, "critical") as aviso, \
                 patch.object(dialogo, "accept") as aceptar:
                dialogo.findChild(QDialogButtonBox).accepted.emit()
                aviso.assert_called_once()
                aceptar.assert_not_called()
                self.assertEqual(cliente["direccion"], "Centro")
                self.assertIsNone(cliente["latitud"])
            with patch.object(ubicacion_ui, "actualizar_direccion_cliente", return_value=True):
                dialogo.findChild(QDialogButtonBox).accepted.emit()
            self.assertEqual(cliente["direccion"], "Barrio nuevo")
            self.assertEqual(cliente["latitud"], 12.4)
            return QDialog.Accepted

        with patch.object(QDialog, "exec", interactuar):
            self.assertTrue(ubicacion_ui.actualizar_direccion_con_dialogo(None, cliente))

    def test_proveedor_y_modo_consulta(self):
        for clave in ("", "llave-de-prueba"):
            with self.subTest(clave=clave), patch.object(mapa_dialogo, "clave_api", return_value=clave):
                html = mapa_dialogo._html(Decimal("12.4"), Decimal("-86.8"), False)
                self.assertIn("var EDITABLE = false", html)
                self.assertIn('"lat": 12.4', html)
                self.assertNotIn("__PUNTO__", html)
                self.assertIn("maps.googleapis.com" if clave else "tile.openstreetmap.org", html)

    def test_consulta_sin_punto_y_sin_webengine(self):
        with patch.object(QMessageBox, "information") as aviso, \
             patch.object(mapa_dialogo.QDesktopServices, "openUrl") as abrir:
            mapa_dialogo.ver_ubicacion(None, "Ana", "", None, None)
            aviso.assert_called_once()
            abrir.assert_not_called()
            with patch.object(mapa_dialogo, "WEBENGINE", False):
                mapa_dialogo.ver_ubicacion(None, "Ana", "Centro", 0, 0)
            self.assertIn("destination=0.0000000,0.0000000", abrir.call_args.args[0].toString())
            with patch.object(mapa_dialogo, "WEBENGINE", False):
                mapa_dialogo.ver_ubicacion(None, "Ana", "Barrio nuevo, León", None, None)
            self.assertIn("destination=Barrio%20nuevo,%20Le%C3%B3n",
                          bytes(abrir.call_args.args[0].toEncoded()).decode("ascii"))


if __name__ == "__main__":
    unittest.main()
