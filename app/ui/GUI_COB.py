from app.config.rutas import IMAGENES_DIR
from PySide6.QtWidgets import *
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QHeaderView
from mysql.connector import Error as MySQLConnectorError
from app.datos.clientes_crud import crear_cliente, listar_clientes
from app.datos.prestamos_crud import listar_prestamos, listar_todos_los_prestamos
from app.ui.pagos_ui import abrir_dialogo_abono
from app.ui.prestamos_ui import mostrar_detalle_prestamo, mostrar_error_detalle_prestamo
from app.ui.estilos_botones_panel import ESTILOS_BOTONES_PANEL
from app.reportes.reportes_pdf import generar_estado_cartera, generar_reporte_cobranza
from app.logica.validaciones import validar_cliente_unico, validar_datos_cliente
from app.logica.calculos_prestamo import (
    PORCENTAJE_INTERES,
    calcular_interes,
    calcular_total_prestamo,
)


class CobWindow(QMainWindow):
    def __init__(self, clientes, ventana_login):
        super().__init__()

        self.clientes = clientes
        self.ventana_login = ventana_login

        # Obtiene el usuario directamente del login
        self.usuario = self.ventana_login.input_user.text()

        self.setCob()

    def setCob(self):
        self.showMaximized()
        self.setWindowTitle("Panel Cobrador")
        self.setWindowIcon(QIcon(str(IMAGENES_DIR / "logoBG.png")))

        self.setStyleSheet("""
            QMainWindow {
                background-color: #F6F5F1;
            }

            /* ENCABEZADO */

            QWidget#encabezado {
                background-color: white;
                border: 1px solid #DDD8CB;
                border-radius: 10px;
                border-bottom: 3px solid #C09848;
            }

            QLabel#tituloPanel {
                color: #102848;
                font-size: 22px;
                font-weight: bold;
            }

            QLabel#infoUsuario {
                color: #65758B;
                font-size: 16px;
                font-weight: bold;
            }

            /* TITULOS */

            QLabel {
                color: #102848;
                font-size: 18px;
                font-weight: bold;
            }

            QLabel#lblCliente {
                color: #102848;
                font-size: 20px;
                font-weight: bold;
            }

            QLabel#lblCorreo {
                color: #65758B;
                font-size: 14px;
                font-weight: normal;
            }

            QLabel#lblDir {
            margin-bottom: 5px;
                color: #65758B;
                font-size: 14px;
                font-weight: normal;
            }

            QLineEdit#lineaEdit {
                background-color: #F4F2EC;
                border: 1px solid #DDD8CB;
                border-radius: 8px;
                padding: 5px;
                color: #102848;
            }

            QPushButton#btnBuscar {
                background-color: #F4F2EC;
                border: 1px solid #DDD8CB;
                padding: 5px;
            }

            QPushButton#btnBuscar:hover:enabled:!pressed {
                background-color: #E8E3D7;
                border-color: #C09848;
            }

            QPushButton#btnBuscar:pressed:enabled {
                background-color: #D9D2C2;
                border-color: #A69D89;
            }

            /* LISTA DE CLIENTES */

            QListWidget {
                background-color: white;
                border: 1px solid #DDD8CB;
                border-radius: 10px;
                padding: 8px;
                color: #102848;
                font-size: 15px;
            }

            QListWidget::item {
                padding: 12px;
                border-radius: 6px;
                margin: 2px;
            }

            QListWidget::item:hover {
                background-color: #F4EBD5;
            }

            QListWidget::item:selected {
                background-color: #102848;
                color: white;
            }

            /* PANELES */

            QWidget#panelPrestamos {
                background-color: white;
                border: 1px solid #DDD8CB;
                border-radius: 10px;
            }

            QWidget#panelClientes {
                background-color: white;
                border: 1px solid #DDD8CB;
                border-radius: 10px;
            }

            QWidget#panelAcciones {
                background-color: white;
            }

            /* TABLA */

            QTableWidget {
                background-color: white;
                border: 1px solid #DDD8CB;
                border-radius: 10px;
                color: #102848;
                font-size: 15px;
                gridline-color: #E8E3D7;
            }

            QHeaderView::section {
                background-color: #102848;
                color: white;
                padding: 10px;
                border: none;
                border-bottom: 2px solid #C09848;
                font-weight: bold;
            }

            QPushButton#acciones {
                background-color: #FBFAF6;
                color: #102848;
                border: 1px solid #D9D2C2;
                border-radius: 6px;
                padding: 2px;
                min-width: 0px;
                min-height: 0px;
            }

            QPushButton#acciones:hover {
                background-color: #F4EBD5;
                border-color: #C09848;
            }

            QDialog#detallePrestamo {
                background-color: #FBFAF6;
            }

            QLabel#notaPrestamo {
                background-color: #FAF7EF;
                border: 1px solid #E6D3A5;
                border-radius: 8px;
                padding: 10px;
                color: #102848;
                font-size: 13px;
            }

            QLabel#resumenPrestamo {
                background-color: white;
                border: 1px solid #D9D2C2;
                border-radius: 8px;
                padding: 10px;
                color: #102848;
                font-size: 14px;
            }

            QTableWidget#tablaDetallePrestamo {
                background-color: white;
                alternate-background-color: #FBFAF6;
                border: 1px solid #D9D2C2;
                border-radius: 8px;
                gridline-color: #E8E3D7;
                font-size: 13px;
            }

            /* BOTONES */

            QPushButton {
                background-color: #102848;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #183A60;
            }

            QPushButton:hover#crear_cliente {
                background-color: #3F6B36;
            }

            QPushButton:hover#reportCart {
                background-color: #8A6B2B;
            }

            QPushButton:hover#reportCob {
                background-color: #8A6B2B;
            }

            QPushButton:hover#cerrarSesion {
                background-color: red;
            }

            QPushButton:hover#solicitar_prestamo {
                background-color: #3F6B36;
            }

            QPushButton:hover#abonar_prestamo {
                background-color: #8A6B2B;
            }

            QMessageBox {
                background-color: #F4F2EC;
                color: #102848;
            }

            QMessageBox QLabel {
                color: #102848;
                font-size: 14px;
                font-weight: normal;
            }

            QMessageBox QPushButton {
                background-color: #102848;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
                min-width: 80px;
            }

            QMessageBox QPushButton:hover {
                background-color: #3F6B36;
            }
        """ + ESTILOS_BOTONES_PANEL)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QGridLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # =====================================================
        # ENCABEZADO
        # =====================================================

        encabezado = QWidget()
        encabezado.setObjectName("encabezado")

        encabezadoLayout = QHBoxLayout(encabezado)
        encabezadoLayout.setContentsMargins(20, 12, 20, 12)

        tituloPanel = QLabel("PANEL COBRADOR")
        tituloPanel.setObjectName("tituloPanel")

        infoUsuario = QLabel(self.usuario)
        infoUsuario.setObjectName("infoUsuario")

        encabezadoLayout.addWidget(tituloPanel)
        encabezadoLayout.addStretch()
        encabezadoLayout.addWidget(infoUsuario)

        layout.addWidget(encabezado, 0, 0, 1, 2)

        # =====================================================
        # LADO IZQUIERDO - CLIENTES
        # =====================================================

        panelClientes = QWidget()
        panelClientes.setObjectName("panelClientes")

        clientesLayout = QVBoxLayout(panelClientes)

        clientesTitulo = QLabel("Clientes")
        clientesLayout.addWidget(clientesTitulo)

        buscarCl = QHBoxLayout()
        self.clientesBuscar = QLineEdit()
        self.clientesBuscar.setPlaceholderText("Ingresar cedula a buscar...")
        self.clientesBuscar.setObjectName("lineaEdit")
        self.clientesBuscar.returnPressed.connect(self.buscarCliente)

        self.btnBuscar = QPushButton()
        self.btnBuscar.setObjectName("btnBuscar")
        self.btnBuscar.setIcon(QIcon(str(IMAGENES_DIR / "lupa.png")))
        self.btnBuscar.setIconSize(QSize(24, 24))
        self.btnBuscar.clicked.connect(self.buscarCliente)

        buscarCl.addWidget(self.clientesBuscar)
        buscarCl.addWidget(self.btnBuscar)
        clientesLayout.addLayout(buscarCl)

        self.listaClientes = QListWidget()

        self.listaClientes.itemClicked.connect(
            self.mostrarCliente
        )

        self.cargarListaClientes()

        clientesLayout.addWidget(self.listaClientes)

        botonesLayout = QGridLayout()
        botonesLayout.setSpacing(8)

        self.btnAbonarPrestamo = QPushButton("Abonar Prestamo")
        self.btnAbonarPrestamo.setObjectName(
            "abonar_prestamo"
        )

        self.btnReporteCartera = QPushButton("Reporte Cartera PDF")
        self.btnReporteCartera.setObjectName("reportCart")

        self.btnReporteCobrador = QPushButton("Reporte Cobranza PDF")
        self.btnReporteCobrador.setObjectName("reportCob")

        self.btnCerrar = QPushButton("Cerrar Sesion")
        self.btnCerrar.setObjectName("cerrarSesion")



        self.btnAbonarPrestamo.clicked.connect(self.abonarPrestamo)
        self.btnReporteCartera.clicked.connect(self.generarReporteCartera)
        self.btnReporteCobrador.clicked.connect(self.generarReporteCobranza)
        self.btnCerrar.clicked.connect(self.btnCerrSes)

        botones = (
            self.btnAbonarPrestamo,
            self.btnReporteCartera,
            self.btnReporteCobrador,
            self.btnCerrar,
        )
        for boton in botones:
            boton.setMinimumHeight(42)

        botonesLayout.addWidget(self.btnAbonarPrestamo, 0, 0)
        botonesLayout.addWidget(self.btnReporteCartera, 0, 1)
        botonesLayout.addWidget(self.btnReporteCobrador, 1, 0)
        botonesLayout.addWidget(self.btnCerrar, 1,1)

        clientesLayout.addLayout(botonesLayout)

        layout.addWidget(panelClientes, 1, 0)

        # =====================================================
        # LADO DERECHO - PRÉSTAMOS
        # =====================================================

        panelPrestamos = QWidget()
        panelPrestamos.setObjectName("panelPrestamos")

        prestamosLayout = QVBoxLayout(panelPrestamos)

        botonesLayout2 = QHBoxLayout()

        prestamosTitulo = QLabel("Préstamos del cliente")
        prestamosLayout.addWidget(prestamosTitulo)

        # Datos del cliente seleccionado

        self.lblCliente = QLabel("Seleccione un cliente")
        self.lblCliente.setObjectName("lblCliente")

        self.lblCorreo = QLabel("Correo: -")
        self.lblCorreo.setObjectName("lblCorreo")

        self.lblDir = QLabel("Dir: -")
        self.lblDir.setObjectName("lblDir")

        prestamosLayout.addWidget(self.lblCliente)
        prestamosLayout.addWidget(self.lblCorreo)
        prestamosLayout.addWidget(self.lblDir)



        # =====================================================
        # TABLA DE PRÉSTAMOS
        # =====================================================

        self.tablaPrestamos = QTableWidget()

        self.tablaPrestamos.setColumnCount(7)
        self.tablaPrestamos.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )
        self.tablaPrestamos.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )

        self.tablaPrestamos.setHorizontalHeaderLabels([
            "ID",
            "Monto inicial",
            f"Interés ({PORCENTAJE_INTERES:.0f}%)",
            "Total a pagar",
            "Cuotas pendientes",
            "Estado",
            "Acciones",
        ])

        self.tablaPrestamos.setObjectName("tablaPrestamos")

        self.tablaPrestamos.setRowCount(0)

        self.tablaPrestamos.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )
        self.tablaPrestamos.horizontalHeader().setSectionResizeMode(
            6, QHeaderView.ResizeToContents
        )

        prestamosLayout.addWidget(
            self.tablaPrestamos,
            1
        )

        prestamosLayout.addStretch()



        prestamosLayout.addLayout(
            botonesLayout2
        )

        layout.addWidget(
            panelPrestamos,
            1,
            1
        )

        botonesLayout = QHBoxLayout()


        # =====================================================
        # PROPORCIONES
        # =====================================================

        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 3)

        layout.setRowStretch(0, 0)
        layout.setRowStretch(1, 1)

        if self.listaClientes.count() > 0:
            self.listaClientes.setCurrentRow(0)
            self.mostrarCliente(self.listaClientes.currentItem())

    def cargarListaClientes(self):
        self.listaClientes.clear()
        for indice, cliente in enumerate(self.clientes):
            item = QListWidgetItem(
                cliente["nombre"] + " - " + cliente["cedula"]
            )
            item.setData(Qt.ItemDataRole.UserRole, indice)
            self.listaClientes.addItem(item)

    def actualizarDatos(self):
        cliente_actual = self.clienteSeleccionado()
        cliente_id = cliente_actual.get("id") if cliente_actual else None
        try:
            clientes = listar_clientes()
        except (MySQLConnectorError, OSError, ValueError, TypeError) as error:
            QMessageBox.critical(
                self,
                "Error al actualizar",
                f"No se pudieron cargar los datos actualizados: {error}"
            )
            return

        self.clientes = clientes
        self.clientesBuscar.clear()
        self.cargarListaClientes()
        if not self.clientes:
            self.tablaPrestamos.setRowCount(0)
            self.lblCliente.setText("Seleccione un cliente")
            self.lblCorreo.setText("Correo: -")
            self.lblDir.setText("Direccion: -")
            return

        fila = next(
            (
                indice for indice, cliente in enumerate(self.clientes)
                if cliente.get("id") == cliente_id
            ),
            0,
        )
        self.listaClientes.setCurrentRow(fila)
        self.mostrarCliente(self.listaClientes.currentItem())

    def mostrarCliente(self, item):
        indice_cliente = item.data(Qt.ItemDataRole.UserRole)
        if indice_cliente is None:
            indice_cliente = self.listaClientes.row(item)

        if indice_cliente < 0 or indice_cliente >= len(self.clientes):
            return

        cliente = self.clientes[indice_cliente]
        self.cargarPrestamosCliente(cliente)


        self.lblCliente.setText(
            f"Cliente: {cliente['nombre']}"
        )

        self.lblCorreo.setText(
            f"Correo: {cliente['correo']}"
        )

        self.lblDir.setText(
            f"Direccion: {cliente['direccion']}"
        )
        return

    def cargarPrestamosCliente(self, cliente):
        self.tablaPrestamos.setRowCount(0)
        if cliente.get("id") is None:
            return

        try:
            prestamos = listar_prestamos(int(cliente["id"]))
        except Exception as error:
            QMessageBox.critical(
                self,
                "Error al cargar prestamos",
                f"No se pudieron cargar los prestamos: {error}"
            )
            return

        for prestamo in prestamos:
            fila = self.tablaPrestamos.rowCount()
            self.tablaPrestamos.insertRow(fila)
            valores = (
                str(prestamo["id"]),
                f"C$ {float(prestamo['monto']):,.2f}",
                f"C$ {calcular_interes(prestamo['monto']):,.2f}",
                f"C$ {calcular_total_prestamo(prestamo['monto']):,.2f}",
                f"{prestamo['cuotas_pendientes']} cuotas",
                prestamo["estado"],
            )
            for columna, valor in enumerate(valores):
                self.tablaPrestamos.setItem(
                    fila, columna, QTableWidgetItem(valor)
                )
            self.agregarAccionVerPrestamo(fila)
            self.tablaPrestamos.setRowHeight(fila, 42)

    def agregarAccionVerPrestamo(self, fila):
        acciones = QWidget()
        acciones.setObjectName("panelAcciones")
        layout = QHBoxLayout(acciones)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        boton_ver = QPushButton()
        boton_ver.setObjectName("acciones")
        boton_ver.setFixedSize(34, 34)
        boton_ver.setIcon(
            QIcon(str(IMAGENES_DIR / "ver.png"))
        )
        boton_ver.setIconSize(QSize(25, 25))
        boton_ver.setToolTip("Ver cuotas, pagos y mora")
        boton_ver.clicked.connect(self.verPrestamoDesdeBoton)
        layout.addWidget(boton_ver)
        self.tablaPrestamos.setCellWidget(fila, 6, acciones)

    def verPrestamoDesdeBoton(self):
        boton = self.sender()
        contenedor = boton.parentWidget() if boton is not None else None
        fila = next(
            (
                indice
                for indice in range(self.tablaPrestamos.rowCount())
                if self.tablaPrestamos.cellWidget(indice, 6) is contenedor
            ),
            -1,
        )
        if fila < 0:
            return

        id_item = self.tablaPrestamos.item(fila, 0)
        if id_item is None:
            return
        try:
            mostrar_detalle_prestamo(self, int(id_item.text()))
        except (MySQLConnectorError, OSError, TypeError, ValueError) as error:
            mostrar_error_detalle_prestamo(self, error)

    def buscarCliente(self):
        cedula = self.clientesBuscar.text().strip().casefold()
        self.listaClientes.clear()
        encontrados = 0

        for indice, cliente in enumerate(self.clientes):
            if cedula and cedula not in cliente["cedula"].casefold():
                continue

            item = QListWidgetItem(
                cliente["nombre"] + " - " + cliente["cedula"]
            )
            item.setData(Qt.ItemDataRole.UserRole, indice)
            self.listaClientes.addItem(item)
            encontrados += 1

        if encontrados > 0:
            self.listaClientes.setCurrentRow(0)
            self.mostrarCliente(self.listaClientes.currentItem())

        if cedula and encontrados == 0:
            QMessageBox.information(
                self,
                "Cliente no encontrado",
                f"No se encontro un cliente con la cedula {cedula}."
            )

    def clienteSeleccionado(self):
        item = self.listaClientes.currentItem()
        if item is None:
            return None

        indice = item.data(Qt.ItemDataRole.UserRole)
        if indice is None or indice < 0 or indice >= len(self.clientes):
            return None
        return self.clientes[indice]

    def abonarPrestamo(self):
        cliente = self.clienteSeleccionado()
        fila = self.tablaPrestamos.currentRow()
        if cliente is None:
            QMessageBox.warning(
                self,
                "Cliente no seleccionado",
                "Selecciona un cliente antes de registrar un abono."
            )
            return
        if fila < 0:
            QMessageBox.warning(
                self,
                "Prestamo no seleccionado",
                "Selecciona un prestamo de la tabla para registrar un abono."
            )
            return

        id_item = self.tablaPrestamos.item(fila, 0)
        if id_item is None:
            return

        try:
            registrado = abrir_dialogo_abono(self, int(id_item.text()))
        except (MySQLConnectorError, OSError, ValueError, TypeError) as error:
            QMessageBox.critical(
                self,
                "Error al registrar abono",
                f"No se pudo registrar el abono: {error}",
            )
            return
        if registrado:
            self.cargarPrestamosCliente(cliente)

    def generarReportesGlobales(self):
        prestamos_por_cliente = {
            cliente["cedula"]: []
            for cliente in self.clientes
        }
        clientes_por_id = {
            int(cliente["id"]): cliente
            for cliente in self.clientes
            if cliente.get("id") is not None
        }

        prestamos = listar_todos_los_prestamos()
        for prestamo in prestamos:
            cliente = clientes_por_id.get(int(prestamo["cliente_id"]))
            if cliente is None:
                raise ValueError(
                    "Se encontro un prestamo asociado a un cliente "
                    "que no esta cargado."
                )

            prestamos_por_cliente[cliente["cedula"]].append({
                "id": prestamo["id"],
                "monto": f"C$ {float(prestamo['monto']):,.2f}",
                "interes": f"C$ {calcular_interes(prestamo['monto']):,.2f}",
                "total": f"C$ {calcular_total_prestamo(prestamo['monto']):,.2f}",
                "plazo": f"{prestamo['plazo']} cuotas",
                "estado": prestamo["estado"],
            })

        return prestamos_por_cliente

    def generarReporteCartera(self):
        try:
            prestamos_por_cliente = self.generarReportesGlobales()
            generar_estado_cartera(
                self.clientes,
                prestamos_por_cliente
            )
        except Exception as error:
            QMessageBox.critical(
                self,
                "Error al generar reporte",
                f"No se pudo generar el reporte de cartera: {error}"
            )
            return

        QMessageBox.information(
            self,
            "Reporte generado",
            "El reporte global de cartera se genero correctamente."
        )

    def generarReporteCobranza(self):
        try:
            prestamos_por_cliente = self.generarReportesGlobales()
            generar_reporte_cobranza(
                self.clientes,
                prestamos_por_cliente
            )
        except Exception as error:
            QMessageBox.critical(
                self,
                "Error al generar reporte",
                f"No se pudo generar el reporte de cobranza: {error}"
            )
            return

        QMessageBox.information(
            self,
            "Reporte generado",
            "El reporte global de cobranza se genero correctamente."
        )

    # ==========================================================
    # BOTÓN CREAR CLIENTE
    # ==========================================================

    def crearCl(self):

        layoutCC = QWidget()

        layoutCC.setWindowTitle("Crear Cliente")
        layoutCC.resize(300, 200)

        layoutCC.setObjectName("formCC")

        layoutCC.setStyleSheet("""
            #formCC {
                background-color: #F4F2EC;
            }

            QLineEdit {
                background-color: #F4F1E8;
                color: #102848;
            }

            QPushButton {
                background-color: #102848;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #3F6B36;
            }
        """)

        form_layout = QFormLayout(layoutCC)

        self.infoName = QLineEdit("")
        self.infoName.setPlaceholderText(
            "Ingresa tu nombre..."
        )
        self.infoName.setMaxLength(80)

        self.infoEmail = QLineEdit("")
        self.infoEmail.setMaxLength(100)
        self.infoEmail.setPlaceholderText(
            "Ingresa tu correo electronico..."
        )

        self.infoCedula = QLineEdit("")
        self.infoCedula.setPlaceholderText(
            "Ingresa tu cedula"
        )
        self.infoCedula.setMaxLength(20)

        self.infoPassword = QLineEdit("")
        self.infoPassword.setPlaceholderText(
            "Ingresa tu contraseña..."
        )
        self.infoPassword.setEchoMode(QLineEdit.Password)
        self.infoPassword.setMaxLength(12)

        self.infoDir = QLineEdit("")
        self.infoDir.setPlaceholderText(
            "Ingresa tu direccion..."
        )
        self.infoDir.setMaxLength(40)

        self.btnEnviar = QPushButton("Enviar")
        self.btnEnviar.clicked.connect(
            self.enviarForm
        )
        self.btnEnviar.setObjectName("btnEnviar")

        form_layout.addWidget(self.infoName)
        form_layout.addWidget(self.infoCedula)
        form_layout.addWidget(self.infoEmail)
        form_layout.addWidget(self.infoPassword)
        form_layout.addWidget(self.infoDir)
        form_layout.addWidget(self.btnEnviar)

        layoutCC.show()

        self.ventanaCrear = layoutCC

    def enviarForm(self):

        if (
            not self.infoName.text().strip()
            or not self.infoCedula.text().strip()
            or not self.infoEmail.text().strip()
            or not self.infoPassword.text().strip()
            or not self.infoDir.text().strip()
        ):
            QMessageBox.warning(
                self,
                "Campos Vacios",
                "Debes llenar todos los campos."
            )
            return

        error_validacion = validar_datos_cliente(
            self.infoName.text(),
            self.infoCedula.text(),
            self.infoEmail.text(),
            self.infoPassword.text(),
            self.infoDir.text(),
        )
        if error_validacion:
            QMessageBox.warning(self, "Datos inválidos", error_validacion)
            return
        error_duplicado = validar_cliente_unico(
            self.clientes,
            self.infoCedula.text(),
            self.infoEmail.text(),
        )
        if error_duplicado:
            QMessageBox.warning(self, "Cliente duplicado", error_duplicado)
            return

        self.newCl = {
            "nombre": self.infoName.text().strip(),
            "cedula": self.infoCedula.text().strip(),
            "correo": self.infoEmail.text().strip(),
            "password": self.infoPassword.text(),
            "direccion": self.infoDir.text().strip()
        }

        try:
            cliente_id = crear_cliente(
                self.newCl["nombre"],
                self.newCl["cedula"],
                self.newCl["correo"],
                self.newCl["password"],
                self.newCl["direccion"]
            )
        except Exception as error:
            QMessageBox.critical(
                self,
                "Error al crear cliente",
                f"No se pudo guardar el cliente: {error}"
            )
            return

        self.newCl["id"] = cliente_id
        self.clientes.append(self.newCl)

        QMessageBox.information(
            self,
            "Cliente creado",
            "El cliente se creo correctamente."
        )

        self.ventanaCrear.close()

    def btnCerrSes(self):

        QMessageBox.information(
            self,
            "Cerrando sesion",
            "Saliendo del sistema... :)"
        )

        self.ventana_login.input_user.clear()
        self.ventana_login.input_password.clear()

        self.close()
        self.ventana_login.showMaximized()
