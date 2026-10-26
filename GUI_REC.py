from PySide6.QtWidgets import *
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QHeaderView
from pathlib import Path
from mysql.connector import Error as MySQLConnectorError
from clientes_crud import crear_cliente, listar_clientes
from citas_crud import (
    listar_todas_las_citas,
)
from prestamos_crud import listar_prestamos, listar_todos_los_prestamos
from pagos_ui import abrir_dialogo_abono
from prestamos_ui import mostrar_detalle_prestamo, mostrar_error_detalle_prestamo
from reportes_pdf import generar_estado_cartera, generar_reporte_cobranza
from solicitudes_crud import crear_solicitud_prestamo
from validaciones import validar_cliente_unico, validar_datos_cliente
from calculos_prestamo import (
    PORCENTAJE_INTERES,
    calcular_interes,
    calcular_total_prestamo,
)


class RecepWindow(QMainWindow):
    def __init__(self, clientes, ventana_login):
        super().__init__()

        self.clientes = clientes
        self.ventana_login = ventana_login

        # Obtiene el usuario directamente del login
        self.usuario = self.ventana_login.input_user.text()

        self.setRecep()

    def setRecep(self):
        self.showMaximized()
        self.setWindowTitle("Panel Recepcionista")
        self.setWindowIcon(QIcon("img/logoBG.png"))

        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f6fa;
            }

            /* ENCABEZADO */

            QWidget#encabezado {
                background-color: white;
                border: 1px solid #d1d5db;
                border-radius: 10px;
            }

            QLabel#tituloPanel {
                color: #1e293b;
                font-size: 22px;
                font-weight: bold;
            }

            QLabel#infoUsuario {
                color: #64748b;
                font-size: 16px;
                font-weight: bold;
            }

            /* TITULOS */

            QLabel {
                color: #1e293b;
                font-size: 18px;
                font-weight: bold;
            }

            QLabel#lblCliente {
                color: #1e293b;
                font-size: 20px;
                font-weight: bold;
            }

            QLabel#lblCorreo {
                color: #64748b;
                font-size: 14px;
                font-weight: normal;
            }

            QLabel#lblDir {
                margin-bottom: 5px;
                color: #64748b;
                font-size: 14px;
                font-weight: normal;
            }

            QLineEdit#lineaEdit {
                background-color: #f5f5f5;
                border: 1px solid #d1d5db;
                border-radius: 8px;
                padding: 5px;
                color: #000;
            }

            QPushButton#btnBuscar {
                padding: 5px;
            }

            /* LISTA DE CLIENTES */

            QListWidget {
                background-color: white;
                border: 1px solid #d1d5db;
                border-radius: 10px;
                padding: 8px;
                color: #1e293b;
                font-size: 15px;
            }

            QListWidget::item {
                padding: 12px;
                border-radius: 6px;
                margin: 2px;
            }

            QListWidget::item:hover {
                background-color: #e8f0fe;
            }

            QListWidget::item:selected {
                background-color: #3b82f6;
                color: white;
            }

            /* PANELES */

            QWidget#panelPrestamos {
                background-color: white;
                border: 1px solid #d1d5db;
                border-radius: 10px;
            }

            QWidget#panelClientes {
                background-color: white;
                border: 1px solid #d1d5db;
                border-radius: 10px;
            }

            QWidget#panelAcciones {
                background-color: white;
            }

            /* TABLA */

            QTableWidget {
                background-color: white;
                border: 1px solid #d1d5db;
                border-radius: 10px;
                color: #1e293b;
                font-size: 15px;
                gridline-color: #e5e7eb;
            }

            QHeaderView::section {
                background-color: #3B82F6;
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
            }

            QPushButton#acciones {
                background-color: #f8fafc;
                color: #1e293b;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 2px;
                min-width: 0px;
                min-height: 0px;
            }

            QPushButton#acciones:hover {
                background-color: #dbeafe;
                border-color: #60a5fa;
            }

            QDialog#detallePrestamo {
                background-color: #f8fafc;
            }

            QLabel#notaPrestamo {
                background-color: #eff6ff;
                border: 1px solid #bfdbfe;
                border-radius: 8px;
                padding: 10px;
                color: #1e3a8a;
                font-size: 13px;
            }

            QLabel#resumenPrestamo {
                background-color: white;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                padding: 10px;
                color: #1e293b;
                font-size: 14px;
            }

            QTableWidget#tablaDetallePrestamo {
                background-color: white;
                alternate-background-color: #f8fafc;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                gridline-color: #e2e8f0;
                font-size: 13px;
            }

            /* BOTONES */

            QPushButton {
                background-color: #3B82F6;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #2563eb;
            }

            QPushButton:hover#crear_cliente {
                background-color: green;
            }

            QPushButton:hover#cerrarSesion {
                background-color: red;
            }

            QPushButton:hover#solicitar_prestamo {
                background-color: green;
            }

            QPushButton:hover#abonar_prestamo {
                background-color: gold;
            }

            QPushButton:hover#reportCart {
                background-color: gold;
            }

            QPushButton:hover#reportCob {
                background-color: gold;
            }

            QPushButton:hover#verCitas {
                background-color: #8B4513;
            }

            QMessageBox {
                background-color: #f5f5f5;
                color: #000;
            }

            QMessageBox QLabel {
                color: #000;
                font-size: 14px;
                font-weight: normal;
            }

            QMessageBox QPushButton {
                background-color: #3B82F6;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
                min-width: 80px;
            }

            QMessageBox QPushButton:hover {
                background-color: green;
            }
        """)

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

        tituloPanel = QLabel("PANEL RECEPCIONISTA")
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

        #============================
            #Buscar clientes.
        #============================
        self.buscarCl = QHBoxLayout()

        self.clientesBuscar = QLineEdit()
        self.clientesBuscar.setPlaceholderText("Ingresar cedula a buscar...")
        self.clientesBuscar.setObjectName("lineaEdit")
        self.clientesBuscar.returnPressed.connect(self.buscarCliente)


        self.btnBuscar = QPushButton()
        self.btnBuscar.setObjectName("btnBuscar")
        self.btnBuscar.setIcon(QIcon("img/lupa.png"))
        self.btnBuscar.setIconSize(QSize(24, 24))
        self.btnBuscar.clicked.connect(self.buscarCliente)

        #corregir para que aparezca en la parte de al lado de cliente, y darle qss al boton buscar
        self.buscarCl.addWidget(self.clientesBuscar)
        self.buscarCl.addWidget(self.btnBuscar)

        clientesLayout.addLayout(self.buscarCl)

        self.listaClientes = QListWidget()

        self.listaClientes.itemClicked.connect(
            self.mostrarCliente
        )

        self.cargarListaClientes()

        clientesLayout.addWidget(self.listaClientes)

        botonesLayout = QHBoxLayout()

        self.btnCreate = QPushButton("Crear Cliente")
        self.btnCreate.setObjectName("crear_cliente")

        self.btnActualizar = QPushButton("Actualizar datos")
        self.btnActualizar.clicked.connect(self.actualizarDatos)

        self.btnCerrar = QPushButton("Cerrar Sesion")
        self.btnCerrar.setObjectName("cerrarSesion")

        self.btnCreate.clicked.connect(self.crearCl)
        self.btnCerrar.clicked.connect(self.btnCerrSes)

        botonesLayout.addWidget(self.btnCreate)
        botonesLayout.addWidget(self.btnActualizar)
        botonesLayout.addWidget(self.btnCerrar)

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

        self.lblDir = QLabel("Direccion: -")
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

        # =====================================================
        # BOTONES DE PRÉSTAMO
        # =====================================================


        self.btnSoliPrestamo = QPushButton("Solicitar Prestamo")
        self.btnSoliPrestamo.setObjectName(
            "solicitar_prestamo"
        )

        self.btnVerCitas = QPushButton("Ver Citas")
        self.btnVerCitas.setObjectName("verCitas")

        self.btnSoliPrestamo.clicked.connect(self.solicitarPrestamo)
        self.btnVerCitas.clicked.connect(self.verCitas)

        self.btnAbonarPrestamo = QPushButton("Abonar Prestamo")
        self.btnAbonarPrestamo.setObjectName(
            "abonar_prestamo"
        )
        self.btnAbonarPrestamo.clicked.connect(self.abonarPrestamo)

        self.btnReporteCartera = QPushButton("Reporte Cartera PDF")
        self.btnReporteCartera.setObjectName("reportCart")
        self.btnReporteCartera.clicked.connect(self.ReporteCartera)

        self.btnReporteCobranza = QPushButton("Reporte Cobranza PDF")
        self.btnReporteCobranza.setObjectName("reporteCob")
        self.btnReporteCobranza.clicked.connect(self.ReporteCobranza)

        botonesLayout2.addWidget(
            self.btnSoliPrestamo
        )

        botonesLayout2.addWidget(
            self.btnAbonarPrestamo
        )

        botonesLayout2.addWidget(
            self.btnReporteCartera
        )

        botonesLayout2.addWidget(
            self.btnReporteCobranza
        )

        botonesLayout2.addWidget(self.btnVerCitas)

        prestamosLayout.addLayout(
            botonesLayout2
        )

        layout.addWidget(
            panelPrestamos,
            1,
            1
        )

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
        except (
            MySQLConnectorError,
            OSError,
            ValueError,
            KeyError,
            TypeError,
        ) as error:
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
            QIcon(str(Path(__file__).resolve().parent / "img" / "ver.png"))
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

    # ==========================================================
    # BOTÓN CREAR CLIENTE
    # ==========================================================

    def crearCl(self):

        layoutCC = QWidget()

        layoutCC.setWindowTitle("Crear Cliente")
        layoutCC.resize(300, 200)

        layoutCC.setObjectName("formCC")

        layoutCC.setStyleSheet("""
    QWidget#formCC {
        background-color: #f8fafc;
    }

    QLineEdit {
        background-color: white;
        color: #1e293b;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        padding: 10px 12px;
        font-size: 14px;
        selection-background-color: #bfdbfe;
        selection-color: #1e293b;
    }

    QLineEdit:hover {
        border-color: #94a3b8;
    }

    QLineEdit:focus {
        border-color: #3b82f6;
    }

    QPushButton#btnEnviar {
        background-color: #2563eb;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px;
        font-size: 14px;
        font-weight: bold;
    }

    QPushButton#btnEnviar:hover {
        background-color: #1d4ed8;
    }

    QPushButton#btnEnviar:pressed {
        background-color: #1e40af;
    }
""")

        form_layout = QFormLayout(layoutCC)

        self.infoName = QLineEdit("")
        self.infoName.setPlaceholderText(
            "Ingresa tu nombre..."
        )
        self.infoName.setMaxLength(80)

        self.infoEmail = QLineEdit("")
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
        self.infoPassword.setMaxLength(128)

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
            "nombre": self.infoName.text(),
            "cedula": self.infoCedula.text(),
            "correo": self.infoEmail.text(),
            "password": self.infoPassword.text(),
            "direccion": self.infoDir.text()
        }

        try:
            cliente_id = crear_cliente(
                self.newCl["nombre"],
                self.newCl["cedula"],
                self.newCl["correo"],
                self.newCl["password"],
                self.newCl["direccion"]
            )
        except (
            MySQLConnectorError,
            OSError,
            ValueError,
            KeyError,
            TypeError,
        ) as error:
            QMessageBox.critical(
                self,
                "Error al crear cliente",
                f"No se pudo guardar el cliente: {error}"
            )
            return

        self.newCl["id"] = cliente_id
        self.clientes.append(self.newCl)
        self.cargarListaClientes()

        QMessageBox.information(
            self,
            "Cliente creado",
            "El cliente se creo correctamente."
        )

        self.ventanaCrear.close()

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

    def solicitarPrestamo(self):
        cliente = self.clienteSeleccionado()
        if cliente is None:
            QMessageBox.warning(
                self,
                "Cliente no seleccionado",
                "Selecciona un cliente para solicitarle un prestamo."
            )
            return

        if cliente.get("id") is None:
            QMessageBox.critical(
                self,
                "Cliente no válido",
                "No se pudo identificar al cliente seleccionado."
            )
            return

        dialogo = QDialog(self)
        dialogo.setObjectName("solicitudPrestamo")
        dialogo.setWindowTitle("Solicitar préstamo")
        dialogo.setMinimumWidth(520)
        dialogo.setStyleSheet("""
            QDialog#solicitudPrestamo {
                background-color: #f8fafc;
                color: #1e293b;
            }

            QDialog#solicitudPrestamo QLabel {
                color: #334155;
                font-size: 14px;
                font-weight: normal;
            }

            QDialog#solicitudPrestamo QLabel#clienteSolicitud {
                color: #1e293b;
                font-size: 15px;
                font-weight: bold;
            }

            QDialog#solicitudPrestamo QDoubleSpinBox,
            QDialog#solicitudPrestamo QSpinBox {
                background-color: white;
                color: #1e293b;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                padding: 9px 10px;
                font-size: 14px;
                selection-background-color: #bfdbfe;
                selection-color: #1e293b;
            }

            QDialog#solicitudPrestamo QDoubleSpinBox:hover,
            QDialog#solicitudPrestamo QSpinBox:hover {
                border-color: #94a3b8;
            }

            QDialog#solicitudPrestamo QDoubleSpinBox:focus,
            QDialog#solicitudPrestamo QSpinBox:focus {
                border: 1px solid #3b82f6;
            }

            QDialog#solicitudPrestamo QLabel#interesSolicitud,
            QDialog#solicitudPrestamo QLabel#totalSolicitud,
            QDialog#solicitudPrestamo QLabel#cuotaSolicitud {
                background-color: white;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                padding: 9px 10px;
                color: #1e293b;
                font-size: 14px;
                font-weight: bold;
            }

            QDialog#solicitudPrestamo QLabel#totalSolicitud {
                background-color: #eff6ff;
                border-color: #bfdbfe;
                color: #1d4ed8;
            }

            QDialog#solicitudPrestamo QLabel#avisoSolicitud {
                background-color: #eff6ff;
                border: 1px solid #bfdbfe;
                border-radius: 8px;
                padding: 10px;
                color: #1e3a8a;
                font-size: 13px;
            }

            QDialog#solicitudPrestamo QPushButton {
                min-width: 110px;
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 14px;
                font-weight: bold;
            }

            QDialog#solicitudPrestamo QPushButton#btnEnviarSolicitud {
                background-color: #2563eb;
                color: white;
                border: 1px solid #2563eb;
            }

            QDialog#solicitudPrestamo QPushButton#btnEnviarSolicitud:hover {
                background-color: #1d4ed8;
                border-color: #1d4ed8;
            }

            QDialog#solicitudPrestamo QPushButton#btnCancelarSolicitud {
                background-color: white;
                color: #334155;
                border: 1px solid #cbd5e1;
            }

            QDialog#solicitudPrestamo QPushButton#btnCancelarSolicitud:hover {
                background-color: #f1f5f9;
                border-color: #94a3b8;
            }

            QDialog#solicitudPrestamo QPushButton:disabled {
                background-color: #94a3b8;
                border-color: #94a3b8;
                color: white;
            }
        """)
        formulario = QFormLayout(dialogo)
        formulario.setContentsMargins(24, 24, 24, 24)
        formulario.setSpacing(16)
        formulario.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        nombre = QLabel(str(cliente["nombre"]))
        nombre.setObjectName("clienteSolicitud")
        nombre.setTextFormat(Qt.TextFormat.PlainText)
        nombre.setWordWrap(True)
        cedula = QLabel(str(cliente["cedula"]))
        cedula.setObjectName("clienteSolicitud")
        cedula.setTextFormat(Qt.TextFormat.PlainText)
        formulario.addRow("Cliente:", nombre)
        formulario.addRow("Cédula:", cedula)

        ingreso_input = QDoubleSpinBox()
        ingreso_input.setObjectName("ingresoMensualSolicitud")
        ingreso_input.setRange(0, 100_000_000)
        ingreso_input.setDecimals(2)
        ingreso_input.setPrefix("C$ ")
        ingreso_input.setSingleStep(100)
        ingreso_input.setGroupSeparatorShown(True)
        ingreso_input.setSpecialValueText("Ingresa el ingreso mensual")
        ingreso_input.setKeyboardTracking(False)

        monto_input = QDoubleSpinBox()
        monto_input.setObjectName("montoSolicitud")
        monto_input.setRange(0, 100_000_000)
        monto_input.setDecimals(2)
        monto_input.setPrefix("C$ ")
        monto_input.setSingleStep(100)
        monto_input.setGroupSeparatorShown(True)
        monto_input.setSpecialValueText("Ingresa el monto")
        monto_input.setKeyboardTracking(False)
        plazo_input = QSpinBox()
        plazo_input.setObjectName("cuotasSolicitud")
        plazo_input.setRange(1, 360)
        plazo_input.setSuffix(" cuotas")
        plazo_input.setKeyboardTracking(False)

        interes_label = QLabel()
        interes_label.setObjectName("interesSolicitud")
        total_label = QLabel()
        total_label.setObjectName("totalSolicitud")
        cuota_label = QLabel()
        cuota_label.setObjectName("cuotaSolicitud")
        aviso = QLabel(
            "La solicitud quedará pendiente de aprobación por administración. "
            "La cuota es estimada; el redondeo puede ajustar la última cuota."
        )
        aviso.setObjectName("avisoSolicitud")
        aviso.setWordWrap(True)

        botones = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        enviar = botones.button(QDialogButtonBox.Save)
        enviar.setObjectName("btnEnviarSolicitud")
        enviar.setText("Enviar solicitud")
        enviar.setAutoDefault(False)
        cancelar = botones.button(QDialogButtonBox.Cancel)
        cancelar.setObjectName("btnCancelarSolicitud")
        cancelar.setText("Cancelar")
        botones.rejected.connect(dialogo.reject)

        def actualizar_resumen():
            monto = monto_input.value()
            total = calcular_total_prestamo(monto)
            interes_label.setText(f"C$ {calcular_interes(monto):,.2f}")
            total_label.setText(f"C$ {total:,.2f}")
            cuota_label.setText(f"C$ {total / plazo_input.value():,.2f}")
            enviar.setEnabled(monto > 0 and ingreso_input.value() > 0)

        def enviar_solicitud():
            monto_input.interpretText()
            plazo_input.interpretText()
            ingreso_input.interpretText()
            if monto_input.value() <= 0:
                QMessageBox.warning(
                    dialogo, "Monto inválido", "Ingresa un monto mayor que cero."
                )
                monto_input.setFocus()
                return
            if ingreso_input.value() <= 0:
                QMessageBox.warning(
                    dialogo,
                    "Ingreso inválido",
                    "Ingresa el ingreso mensual del cliente, mayor que cero."
                )
                ingreso_input.setFocus()
                return
            enviar.setEnabled(False)
            try:
                solicitud_id = crear_solicitud_prestamo(
                    int(cliente["id"]),
                    monto_input.value(),
                    plazo_input.value(),
                    ingreso_mensual=ingreso_input.value(),
                )
            except (MySQLConnectorError, OSError, ValueError, TypeError) as error:
                QMessageBox.critical(
                    dialogo,
                    "Error al registrar solicitud",
                    f"No se pudo guardar la solicitud: {error}"
                )
                enviar.setEnabled(True)
                return

            dialogo.accept()
            QMessageBox.information(
                self,
                "Solicitud registrada",
                f"Solicitud #{solicitud_id} para {cliente['nombre']}.\n"
                f"Monto: C$ {monto_input.value():,.2f}\n"
                f"Ingreso mensual: C$ {ingreso_input.value():,.2f}\n"
                f"Plazo: {plazo_input.value()} cuotas\n"
                "Estado: Pendiente de aprobación por administración."
            )

        monto_input.valueChanged.connect(actualizar_resumen)
        ingreso_input.valueChanged.connect(actualizar_resumen)
        plazo_input.valueChanged.connect(actualizar_resumen)
        botones.accepted.connect(enviar_solicitud)
        formulario.addRow("Ingreso mensual del cliente:", ingreso_input)
        formulario.addRow("Monto solicitado:", monto_input)
        formulario.addRow("Plazo:", plazo_input)
        formulario.addRow(f"Interés ({PORCENTAJE_INTERES:.0f}%):", interes_label)
        formulario.addRow("Total a pagar:", total_label)
        formulario.addRow("Cuota estimada:", cuota_label)
        formulario.addRow(aviso)
        formulario.addRow(botones)
        actualizar_resumen()
        monto_input.setFocus()
        dialogo.exec()

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

    def verCitas(self):
        try:
            citas = listar_todas_las_citas()
        except (MySQLConnectorError, OSError, ValueError, TypeError) as error:
            QMessageBox.critical(
                self,
                "Error al consultar citas",
                f"No se pudieron cargar las citas: {error}"
            )
            return

        if not citas:
            QMessageBox.information(self, "Citas", "No hay citas registradas.")
            return

        dialogo = QDialog(self)
        dialogo.setWindowTitle("Citas agendadas")
        dialogo.resize(720, 420)
        layout = QVBoxLayout(dialogo)
        tabla = QTableWidget(len(citas), 5)
        tabla.setHorizontalHeaderLabels(
            ["ID", "Cliente", "Cédula", "Fecha", "Estado"]
        )
        tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        for fila, cita in enumerate(citas):
            valores = (
                str(cita["id"]),
                cita["nombre"],
                cita["cedula"],
                cita["fecha"].strftime("%d/%m/%Y"),
                cita["estado"],
            )
            for columna, valor in enumerate(valores):
                tabla.setItem(fila, columna, QTableWidgetItem(valor))
        layout.addWidget(tabla)

        botones = QHBoxLayout()
        btn_cerrar = QPushButton("Cerrar")
        botones.addWidget(btn_cerrar)
        layout.addLayout(botones)
        btn_cerrar.clicked.connect(dialogo.accept)
        dialogo.exec()

    def ReporteCartera(self):
        try:
            prestamos_por_cliente = self.obtenerPrestamosGlobales()
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

    def ReporteCobranza(self):
        try:
            prestamos_por_cliente = self.obtenerPrestamosGlobales()
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

    def obtenerPrestamosGlobales(self):
        prestamos_por_cliente = {
            cliente["cedula"]: []
            for cliente in self.clientes
        }
        clientes_por_id = {
            int(cliente["id"]): cliente
            for cliente in self.clientes
            if cliente.get("id") is not None
        }

        for prestamo in listar_todos_los_prestamos():
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
