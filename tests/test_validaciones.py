import os
import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import patch

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
from app.config.conexion import obtener_sesion
from app.datos.modelos import Cliente
from orm_test_utils import OrmTestCase


class ValidacionesTest(OrmTestCase):
    def setUp(self):
        super().setUp()
        clientes_crud._ubicacion_lista = True

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

    def test_entradas_invalidas_no_abren_sesion(self):
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
            with self.subTest(funcion=funcion.__name__, args=args), patch.object(modulo, "obtener_sesion") as obtener:
                with self.assertRaises(ValueError):
                    funcion(*args)
                obtener.assert_not_called()

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

    def _crear_cliente(self):
        with obtener_sesion() as session, session.begin():
            session.add(Cliente(
                nombre="Ana",
                cedula="12345678",
                correo="ana@example.com",
                password="clave1234",
                direccion="Centro",
                monto=0,
            ))

    def test_cliente_con_prestamo_pendiente_no_puede_crear_otro(self):
        self._crear_cliente()
        prestamos_crud.crear_prestamo(1, 100, 1, fecha_primer_pago=date.today())
        with self.assertRaisesRegex(ValueError, "saldo pendiente"):
            prestamos_crud.crear_prestamo(1, 100, 1)

    def test_solicitud_rechaza_cliente_con_saldo_pendiente(self):
        self._crear_cliente()
        prestamos_crud.crear_prestamo(1, 100, 1, fecha_primer_pago=date.today())
        with self.assertRaisesRegex(ValueError, "saldo pendiente"):
            solicitudes_crud.crear_solicitud_prestamo(1, 100, 4, 50)

    def test_cliente_puede_crear_prestamo_despues_de_liquidar(self):
        self._crear_cliente()
        prestamos_crud.crear_prestamo(
            1, 100, 1, fecha_primer_pago=date.today() + timedelta(days=1)
        )
        prestamos_crud.registrar_abono_cuota(
            1, 1, calcular_total_prestamo(100)
        )
        self.assertEqual(prestamos_crud.crear_prestamo(1, 100, 1), 2)

    def test_prestamo_con_abonos_protege_monto_y_plazo(self):
        self._crear_cliente()
        prestamos_crud.crear_prestamo(1, 100, 4)
        prestamos_crud.registrar_abono_cuota(1, 1, 1)
        with self.assertRaisesRegex(ValueError, "ya tiene abonos"):
            prestamos_crud.actualizar_prestamo(1, 200, 4, "Activo")

    def test_no_marcar_pagado_con_saldo(self):
        self._crear_cliente()
        prestamos_crud.crear_prestamo(1, 100, 1)
        with self.assertRaisesRegex(ValueError, "saldo pendiente"):
            prestamos_crud.actualizar_prestamo(1, 100, 1, "Pagado")

    def test_solicitud_resuelta_no_crea_prestamo(self):
        self._crear_cliente()
        solicitudes_crud.crear_solicitud_prestamo(1, 100, 4, 50)
        self.assertIsNone(solicitudes_crud.resolver_solicitud_prestamo(1, False))
        with self.assertRaisesRegex(ValueError, "ya fue resuelta"):
            solicitudes_crud.resolver_solicitud_prestamo(1, True, date.today())

    def test_cliente_duplicado_compara_datos_normalizados(self):
        clientes_crud.crear_cliente(
            " Ana ", "12345678", " ana@example.com ", "claveLarga12", " Centro "
        )
        with self.assertRaisesRegex(ValueError, "Ya existe un cliente"):
            clientes_crud.crear_cliente(
                "Ana", "12345678", "otra@example.com", "claveLarga12", "Centro"
            )
        with self.assertRaisesRegex(ValueError, "Ya existe un cliente"):
            clientes_crud.crear_cliente(
                "Ana", "87654321", "ANA@example.com", "claveLarga12", "Centro"
            )
        cliente = clientes_crud.listar_clientes()[0]
        self.assertEqual(
            (cliente["nombre"], cliente["cedula"], cliente["correo"], cliente["direccion"]),
            ("Ana", "12345678", "ana@example.com", "Centro"),
        )

    def test_cita_duplicada_no_se_guarda(self):
        self._crear_cliente()
        fecha = date.today()
        if fecha.weekday() == 6:
            fecha += timedelta(days=1)
        citas_crud.crear_cita(1, fecha)
        with self.assertRaisesRegex(ValueError, "Ya tienes una cita"):
            citas_crud.crear_cita(1, fecha)

    def test_cita_en_domingo_no_abre_sesion(self):
        hoy = date.today()
        domingo = hoy + timedelta(days=(6 - hoy.weekday()) % 7)
        with patch.object(citas_crud, "obtener_sesion") as obtener:
            with self.assertRaisesRegex(ValueError, "domingos"):
                citas_crud.crear_cita(1, domingo)
            obtener.assert_not_called()

    def test_citas_de_lunes_a_sabado_se_guardan(self):
        self._crear_cliente()
        hoy = date.today()
        lunes = hoy + timedelta(days=(7 - hoy.weekday()) % 7)
        for dias in range(6):
            fecha = lunes + timedelta(days=dias)
            with self.subTest(fecha=fecha):
                self.assertIsInstance(citas_crud.crear_cita(1, fecha), int)
        self.assertEqual(len(citas_crud.listar_citas(1)), 6)

    def test_abono_superior_al_saldo_se_rechaza(self):
        self._crear_cliente()
        prestamos_crud.crear_prestamo(1, 100, 1)
        with self.assertRaisesRegex(ValueError, "no puede superar"):
            prestamos_crud.registrar_abono_cuota(1, 1, 116)


class FormulariosTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])

    def test_agendar_cita_bloquea_domingo_y_permite_cambiar_fecha(self):
        from PySide6.QtCore import QDate
        from PySide6.QtWidgets import QDateEdit, QDialog, QMainWindow, QPushButton
        from app.ui import GUI_CLIENTE

        def revisar_dialogo(dialogo):
            fecha = dialogo.findChild(QDateEdit)
            confirmar = dialogo.findChild(QPushButton, "confirmarCita")
            hoy = QDate.currentDate()
            domingo = hoy.addDays((7 - hoy.dayOfWeek()) % 7)
            fecha.setDate(domingo)
            self.assertFalse(confirmar.isEnabled())
            confirmar.click()
            self.assertEqual(dialogo.result(), QDialog.Rejected)
            fecha.setDate(domingo.addDays(1))
            self.assertTrue(confirmar.isEnabled())
            return QDialog.Rejected

        ventana = QMainWindow()
        try:
            with patch.object(QDialog, "exec", new=revisar_dialogo), \
                 patch.object(GUI_CLIENTE, "crear_cita") as crear:
                GUI_CLIENTE.ClienteWindow.abrirDialogoAgendarCita(ventana)
                crear.assert_not_called()
        finally:
            ventana.close()

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
                    window.infoUbicacion.lat = 12.4379
                    window.infoUbicacion.lng = -86.878
                    window.enviarForm()
                    crear.assert_called_once()
                    self.assertEqual(crear.call_args.args[0], "Ana Perez")
                    self.assertEqual(crear.call_args.kwargs, {"latitud": 12.4379, "longitud": -86.878})
                    self.assertEqual(window.clientes[0]["latitud"], 12.4379)
                    self.assertEqual(window.clientes[0]["password"], "claveLarga12")
                finally:
                    window.ventanaCrear.close()
                    window.close()

    def test_crear_rol_valida_limites_de_contrasena_y_nombre(self):
        from PySide6.QtWidgets import QMessageBox
        from app.ui import login as login_module, GUI_ADMIN as admin
        with patch.object(login_module, "listar_clientes", return_value=[]), \
             patch.object(login_module, "listar_usuarios", return_value=[
                 dict(id="1", rol="administrador", usuario="Marvin", password="12345678")
             ]), \
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
             patch.object(login_module, "listar_usuarios", return_value=[
                 dict(id="1", rol="administrador", usuario="Marvin", password="12345678")
             ]), \
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
