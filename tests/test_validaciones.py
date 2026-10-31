import os
import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from app.logica.validaciones import (
    validar_campos_login, validar_datos_cliente, validar_datos_rol,
    validar_fecha, validar_id, validar_monto, validar_password, validar_plazo,
)
from app.logica.calculos_prestamo import (
    generar_cuotas,
    calcular_estado_cuota,
    calcular_total_prestamo,
    calcular_mora,
)
from app.datos import clientes_crud, citas_crud, prestamos_crud, solicitudes_crud


class ValidacionesTest(unittest.TestCase):
    def test_montos_invalidos(self):
        for valor in (-1, 0, 0.001, 100_000_001, "nan", "inf", "abc", None, True):
            with self.subTest(valor=valor), self.assertRaises(ValueError):
                validar_monto(valor)
        self.assertEqual(validar_monto("10.50"), Decimal("10.50"))
        self.assertEqual(validar_monto(0, permitir_cero=True), 0)

    def test_identificadores_y_plazos(self):
        for valor in (-1, 0, True, 1.5, "2", None):
            with self.subTest(valor=valor), self.assertRaises(ValueError):
                validar_id(valor)
        for valor in (0, -1, 361, True, 1.5, "2"):
            with self.subTest(plazo=valor), self.assertRaises(ValueError):
                validar_plazo(valor)
        validar_id(1)
        validar_plazo(360)

    def test_fechas(self):
        for valor in (None, "2026-01-01", date.today() - timedelta(days=1)):
            with self.subTest(valor=valor), self.assertRaises(ValueError):
                validar_fecha(valor)
        validar_fecha(date.today())
        validar_fecha(date(2020, 1, 1), permitir_pasada=True)

    def test_cliente(self):
        datos = dict(nombre="Ana María Pérez", cedula="12345678A", correo="ana@example.com",
                     password="claveLarga123", direccion="Barrio Centro")
        datos["password"] = "clave1234"
        self.assertIsNone(validar_datos_cliente(**datos))
        for clave, valor in (
            ("nombre", "1234"), ("nombre", "Ana\nPerez"), ("nombre", "A" * 81),
            ("cedula", "123"), ("correo", "ana@"), ("correo", "a" * 101 + "@b.com"),
            ("password", "123"), ("password", " " * 8), ("password", "a" * 13),
            ("direccion", "casa"), ("direccion", "a" * 41), ("direccion", None)
        ):
            with self.subTest(clave=clave, valor=valor):
                self.assertIsNotNone(validar_datos_cliente(**(datos | {clave: valor})))

    def test_roles_y_login(self):
        usuarios = [dict(id="1", usuario="Recepcion")]
        self.assertIsNone(validar_datos_rol("Nuevo", "clave12345", "cobrador", usuarios))
        self.assertIsNone(validar_datos_rol("Yavar Smith", "clave12345", "recepcionista", usuarios))
        self.assertIsNone(validar_datos_rol("ana@example.com", "clave12345", "cobrador", usuarios))
        self.assertIsNotNone(validar_datos_rol("Yavar_Smith", "clave12345", "recepcionista", usuarios))
        self.assertIsNotNone(validar_datos_rol("Yavar-Smith", "clave12345", "recepcionista", usuarios))
        self.assertIsNotNone(validar_datos_rol(" RECEPCION ", "clave12345", "cobrador", usuarios))
        self.assertIsNone(validar_datos_rol("Recepcion", "clave12345", "cobrador", usuarios, excluir_id="1"))
        self.assertIsNotNone(validar_datos_rol("Nuevo", "clave12345", "desconocido", usuarios))
        self.assertIsNotNone(validar_datos_rol("Nuevo", "1234567", "cobrador", usuarios))
        self.assertIsNone(validar_datos_rol("Nuevo", "12345678", "cobrador", usuarios))
        self.assertIsNone(validar_datos_rol("Nuevo", "123456789012", "cobrador", usuarios))
        self.assertIsNotNone(validar_datos_rol("Nuevo", "1234567890123", "cobrador", usuarios))
        self.assertIsNone(validar_password("12345678"))
        self.assertIsNone(validar_password("123456789012"))
        self.assertIsNotNone(validar_password("1234567"))
        self.assertIsNotNone(validar_password("1234567890123"))
        self.assertIsNotNone(validar_campos_login(" ", "12345678"))
        self.assertIsNotNone(validar_campos_login("Admin", " " * 8))
        self.assertIsNone(validar_campos_login("Admin", "clave123"))
        self.assertIsNotNone(validar_campos_login("Admin", "clave123456789"))

    def test_cuotas_sin_saldos_negativos_y_total_exacto(self):
        for monto, plazo in ((1, 180), (100, 6), (1000, 360), ("0.01", 1)):
            for frecuencia in ("Semanal", "Quincenal", "Mensual"):
                with self.subTest(monto=monto, plazo=plazo, frecuencia=frecuencia):
                    if monto == 1:
                        with self.assertRaises(ValueError):
                            generar_cuotas(monto, plazo, date.today(), frecuencia)
                        continue
                    cuotas = generar_cuotas(monto, plazo, date.today(), frecuencia)
                    self.assertTrue(all(c["capital"] > 0 and c["interes"] >= 0 for c in cuotas))
                    self.assertEqual(sum(c["monto"] for c in cuotas), calcular_total_prestamo(monto))
        with self.assertRaises(ValueError):
            generar_cuotas(100, 3, date.today(), "Diario")

    def test_entradas_invalidas_no_conectan_a_mysql(self):
        casos = (
            (clientes_crud, clientes_crud.crear_cliente, ("123", "12345678", "a@example.com", "12345678", "Centro")),
            (clientes_crud, clientes_crud.actualizar_cliente, (0, "Ana", "12345678", "a@example.com", "Centro", 0)),
            (prestamos_crud, prestamos_crud.crear_prestamo, (1, float("nan"), 4)),
            (prestamos_crud, prestamos_crud.crear_prestamo, (1, 100, 361)),
            (prestamos_crud, prestamos_crud.crear_prestamo, (1, 100, 4, "Pagado")),
            (prestamos_crud, prestamos_crud.registrar_abono_cuota, (1, 1, "0.001")),
            (citas_crud, citas_crud.crear_cita, (1, date.today() - timedelta(days=1))),
            (solicitudes_crud, solicitudes_crud.crear_solicitud_prestamo, (1, 100, 4, None)),
            (solicitudes_crud, solicitudes_crud.resolver_solicitud_prestamo, (1, "si")),
        )
        for modulo, funcion, args in casos:
            with self.subTest(funcion=funcion.__name__, args=args), patch.object(modulo, "obtener_conexion") as conectar:
                with self.assertRaises(ValueError):
                    funcion(*args)
                conectar.assert_not_called()

    def test_calendarios_y_mora(self):
        inicio = date(2028, 1, 31)
        for frecuencia, siguiente in (("Semanal", date(2028, 2, 7)), ("Quincenal", date(2028, 2, 15)), ("Mensual", date(2028, 2, 29))):
            self.assertEqual(generar_cuotas(100, 2, inicio, frecuencia)[1]["fecha_vencimiento"], siguiente)
        self.assertEqual(calcular_mora(100, date(2026, 1, 1), date(2026, 1, 31)), (30, Decimal("2.00")))
        for monto in ("nan", "inf", "abc", -1):
            with self.subTest(monto=monto), self.assertRaises(ValueError):
                calcular_mora(monto, inicio, inicio)

    def test_primer_abono_tardio_registra_mora_aunque_se_cubra(self):
        resultado = calcular_estado_cuota(
            Decimal("100.00"),
            date(2026, 1, 1),
            [{
                "fecha_pago": datetime(2026, 1, 31, 12, 0),
                "monto": Decimal("102.00"),
            }],
            date(2026, 1, 31),
        )

        self.assertEqual(resultado["mora_generada"], Decimal("2.00"))
        self.assertEqual(resultado["mora_pendiente"], Decimal("0.00"))
        self.assertEqual(
            resultado["pagos_calculados"][0]["mora_al_abono"],
            Decimal("2.00"),
        )
        self.assertEqual(
            resultado["pagos_calculados"][0]["mora_aplicada"],
            Decimal("2.00"),
        )

    def test_cliente_con_prestamo_pendiente_no_puede_crear_otro(self):
        cursor = MagicMock()
        cursor.fetchone.return_value = {"id": 1}
        cursor.fetchall.return_value = [{"id": 5}]

        with patch.object(
            prestamos_crud,
            "_cargar_cuotas_prestamo",
            return_value=[{"total_pendiente": Decimal("1.00")}],
        ), self.assertRaisesRegex(ValueError, "saldo pendiente"):
            prestamos_crud.validar_cliente_sin_prestamos_pendientes(cursor, 1)

    def test_crear_prestamo_rechaza_cliente_con_saldo_pendiente(self):
        conexion = MagicMock()
        with patch.object(
            prestamos_crud,
            "obtener_conexion",
            return_value=conexion,
        ), patch.object(
            prestamos_crud,
            "asegurar_esquema_prestamos",
        ), patch.object(
            prestamos_crud,
            "validar_cliente_sin_prestamos_pendientes",
            side_effect=ValueError("El cliente ya tiene saldo pendiente."),
        ), self.assertRaisesRegex(ValueError, "saldo pendiente"):
            prestamos_crud.crear_prestamo(1, 100, 4)

        conexion.cursor.assert_called_once_with(dictionary=True)
        conexion.rollback.assert_called_once()

    def test_solicitud_rechaza_cliente_con_saldo_pendiente(self):
        conexion = MagicMock()
        with patch.object(
            solicitudes_crud,
            "obtener_conexion",
            return_value=conexion,
        ), patch.object(
            solicitudes_crud,
            "_crear_tabla_solicitudes",
        ), patch.object(
            solicitudes_crud,
            "asegurar_esquema_prestamos",
        ), patch.object(
            solicitudes_crud,
            "validar_cliente_sin_prestamos_pendientes",
            side_effect=ValueError("El cliente ya tiene saldo pendiente."),
        ), self.assertRaisesRegex(ValueError, "saldo pendiente"):
            solicitudes_crud.crear_solicitud_prestamo(1, 100, 4, 50)

        conexion.rollback.assert_called_once()

    def test_cliente_puede_crear_prestamo_despues_de_liquidar(self):
        cursor = MagicMock()
        cursor.fetchone.return_value = {"id": 1}
        cursor.fetchall.return_value = [{"id": 5}]

        with patch.object(
            prestamos_crud,
            "_cargar_cuotas_prestamo",
            return_value=[{"total_pendiente": Decimal("0.00")}],
        ):
            prestamos_crud.validar_cliente_sin_prestamos_pendientes(cursor, 1)

    def test_prestamo_con_abonos_protege_monto_y_plazo(self):
        conexion = MagicMock()
        cursor = conexion.cursor.return_value
        cursor.fetchone.side_effect = [dict(id=1, monto=100, plazo=4), dict(cantidad=1)]
        with patch.object(prestamos_crud, "obtener_conexion", return_value=conexion), \
             patch.object(prestamos_crud, "asegurar_esquema_prestamos"), self.assertRaises(ValueError):
            prestamos_crud.actualizar_prestamo(1, 200, 4, "Activo")
        conexion.commit.assert_not_called()

    def test_no_marcar_pagado_con_saldo(self):
        conexion = MagicMock()
        conexion.cursor.return_value.fetchone.side_effect = [dict(id=1, monto=100, plazo=4), dict(cantidad=0)]
        with patch.object(prestamos_crud, "obtener_conexion", return_value=conexion), \
             patch.object(prestamos_crud, "asegurar_esquema_prestamos"), \
             patch.object(prestamos_crud, "_cargar_cuotas_prestamo", return_value=[dict(total_pendiente=100)]), self.assertRaises(ValueError):
            prestamos_crud.actualizar_prestamo(1, 100, 4, "Pagado")
        conexion.commit.assert_not_called()

    def test_solicitud_resuelta_no_crea_otro_prestamo(self):
        conexion = MagicMock()
        conexion.cursor.return_value.fetchone.return_value = None
        with patch.object(solicitudes_crud, "obtener_conexion", return_value=conexion), \
             patch.object(solicitudes_crud, "_crear_tabla_solicitudes"), \
             patch.object(solicitudes_crud, "asegurar_esquema_prestamos"), self.assertRaises(ValueError):
            solicitudes_crud.resolver_solicitud_prestamo(1, True, date.today())
        conexion.commit.assert_not_called()

    def test_cliente_duplicado_y_normalizacion(self):
        conexion = MagicMock()
        cursor = conexion.cursor.return_value
        with patch.object(clientes_crud, "obtener_conexion", return_value=conexion):
            cursor.fetchone.return_value = (1,)
            with self.assertRaises(ValueError):
                clientes_crud.crear_cliente("Ana", "12345678", "a@example.com", "12345678", "Centro")
            conexion.rollback.assert_called_once()
            self.assertFalse(any("INSERT" in c.args[0] for c in cursor.execute.call_args_list))
            cursor.fetchone.return_value = None
            clientes_crud.crear_cliente(" Ana ", "12345678", " a@example.com ", "claveLarga12", " Centro ")
            args = cursor.execute.call_args.args[1]
            self.assertEqual(args[:3], ("Ana", "12345678", "a@example.com"))

    def test_cita_duplicada_no_se_guarda(self):
        conexion = MagicMock()
        conexion.cursor.return_value.fetchone.return_value = (1,)
        with patch.object(citas_crud, "obtener_conexion", return_value=conexion), self.assertRaises(ValueError):
            citas_crud.crear_cita(1, date.today())
        conexion.commit.assert_not_called()
        conexion.rollback.assert_called_once()

    def test_abono_superior_al_saldo(self):
        conexion = MagicMock()
        conexion.cursor.return_value.fetchone.return_value = {"id": 1}
        with patch.object(prestamos_crud, "obtener_conexion", return_value=conexion), \
             patch.object(prestamos_crud, "asegurar_esquema_prestamos"), \
             patch.object(prestamos_crud, "_cargar_cuotas_prestamo", return_value=[dict(numero=1, total_pendiente=Decimal("10"))]):
            with self.assertRaises(ValueError):
                prestamos_crud.registrar_abono_cuota(1, 1, 11)
        conexion.commit.assert_not_called()


class FormulariosTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])

    def test_formularios_cliente_en_los_tres_paneles(self):
        from types import SimpleNamespace
        from PySide6.QtWidgets import QLineEdit, QMessageBox
        from app.ui import GUI_ADMIN, GUI_REC, GUI_COB
        for modulo, clase in ((GUI_ADMIN, GUI_ADMIN.AdminWindow), (GUI_REC, GUI_REC.RecepWindow), (GUI_COB, GUI_COB.CobWindow)):
            with self.subTest(panel=clase.__name__), patch.object(clase, "showMaximized"), \
                 patch.object(modulo, "crear_cliente", return_value=11) as crear, \
                 patch.object(QMessageBox, "warning") as aviso, patch.object(QMessageBox, "information"):
                login = SimpleNamespace(input_user=QLineEdit("Admin"))
                window = clase([], login)
                window.crearCl()
                try:
                    window.enviarForm()
                    crear.assert_not_called()
                    aviso.assert_called_once()
                    window.infoName.setText(" Ana Perez ")
                    window.infoCedula.setText("12345678")
                    window.infoEmail.setText("ana@")
                    window.infoPassword.setText("claveLarga12")
                    window.infoDir.setText("Centro")
                    window.enviarForm()
                    crear.assert_not_called()
                    window.infoEmail.setText("ana@example.com")
                    window.enviarForm()
                    crear.assert_called_once()
                    self.assertEqual(crear.call_args.args[0], "Ana Perez")
                    self.assertEqual(window.clientes[0]["password"], "claveLarga12")
                finally:
                    window.ventanaCrear.close()
                    window.close()

    def test_crear_rol_valida_limites_de_contrasena_y_nombre(self):
        from PySide6.QtWidgets import QMessageBox
        from app.ui import login as login_module, GUI_ADMIN as admin
        with patch.object(login_module, "listar_clientes", return_value=[]), \
             patch.object(admin.AdminWindow, "showMaximized"), \
             patch.object(QMessageBox, "information"), patch.object(QMessageBox, "warning") as aviso:
            login = login_module.login()
            login.input_user.setText("Marvin")
            window = admin.AdminWindow([], login)
            window.crearRol()
            try:
                cantidad = len(login.usuarios)
                window.btnEnviar.click()
                self.assertEqual(len(login.usuarios), cantidad)
                aviso.assert_called_once()
                window.infoName.setText("Marvin")
                window.infoPassword.setText("claveLarga12")
                window.btnEnviar.click()
                self.assertEqual(len(login.usuarios), cantidad)
                window.infoName.setText("Nuevo Cobrador")
                window.infoRol.setCurrentText("cobrador")
                window.btnEnviar.click()
                self.assertEqual(len(login.usuarios), cantidad + 1)
                self.assertEqual(login.usuarios[-1]["password"], "claveLarga12")
                login.input_user.setText("Nuevo Cobrador")
                login.input_password.setText("claveLarga12")
                login.intentosLogIn = 2
                with patch.object(login_module, "CobWindow") as panel:
                    login.iniciarSesion()
                    panel.assert_called_once()
                    self.assertEqual(login.intentosLogIn, 0)
            finally:
                window.ventanaCrear.close()
                window.close()
                login.close()

    def test_bloqueo_no_se_evade_llamando_al_metodo(self):
        from PySide6.QtWidgets import QMessageBox
        from app.ui import login as login_module
        with patch.object(login_module, "listar_clientes", return_value=[]), \
             patch.object(QMessageBox, "warning"), patch.object(QMessageBox, "critical"):
            login = login_module.login()
            try:
                login.input_user.setText("Marvin")
                login.input_password.setText("incorrecta")
                for _ in range(3):
                    login.iniciarSesion()
                self.assertFalse(login.btnIni.isEnabled())
                login.input_password.setText("12345678")
                with patch.object(login_module, "AdminWindow") as panel:
                    login.iniciarSesion()
                    panel.assert_not_called()
            finally:
                login.close()


if __name__ == "__main__":
    unittest.main()
