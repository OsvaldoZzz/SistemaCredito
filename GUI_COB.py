from PySide6.QtWidgets import *
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QHeaderView
from clientes_crud import crear_cliente
from prestamos_crud import listar_prestamos


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
        self.btnBuscar.setIcon(QIcon("img/lupa.png"))
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

        botonesLayout = QHBoxLayout()

        self.btnAbonarPrestamo = QPushButton("Abonar Prestamo")
        self.btnAbonarPrestamo.setObjectName(
            "abonar_prestamo"
        )

        self.btnCerrar = QPushButton("Cerrar Sesion")
        self.btnCerrar.setObjectName("cerrarSesion")

        self.btnAbonarPrestamo.clicked.connect(self.abonarPrestamo)
        self.btnCerrar.clicked.connect(self.btnCerrSes)

        botonesLayout.addWidget(self.btnAbonarPrestamo)
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

        self.lblDir = QLabel("Dir: -")
        self.lblDir.setObjectName("lblDir")

        prestamosLayout.addWidget(self.lblCliente)
        prestamosLayout.addWidget(self.lblCorreo)
        prestamosLayout.addWidget(self.lblDir)



        # =====================================================
        # TABLA DE PRÉSTAMOS
        # =====================================================

        self.tablaPrestamos = QTableWidget()

        self.tablaPrestamos.setColumnCount(4)
        self.tablaPrestamos.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )
        self.tablaPrestamos.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )

        self.tablaPrestamos.setHorizontalHeaderLabels([
            "ID",
            "Monto",
            "Plazo",
            "Estado"
        ])

        self.tablaPrestamos.setObjectName("tablaPrestamos")

        # Ejemplo temporal

        self.tablaPrestamos.setRowCount(1)

        self.tablaPrestamos.setItem(
            0, 0, QTableWidgetItem("001")
        )

        self.tablaPrestamos.setItem(
            0, 1, QTableWidgetItem("C$20,000")
        )

        self.tablaPrestamos.setItem(
            0, 2, QTableWidgetItem("10 cuotas")
        )

        self.tablaPrestamos.setItem(
            0, 3, QTableWidgetItem("Activo")
        )

        self.tablaPrestamos.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
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
                f"{prestamo['plazo']} cuotas",
                prestamo["estado"],
            )
            for columna, valor in enumerate(valores):
                self.tablaPrestamos.setItem(
                    fila, columna, QTableWidgetItem(valor)
                )

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

        monto, aceptado = QInputDialog.getDouble(
            self,
            "Abonar prestamo",
            "Monto del abono:",
            0.0,
            0.01,
            100000000.0,
            2
        )
        if not aceptado:
            return

        id_item = self.tablaPrestamos.item(fila, 0)
        QMessageBox.information(
            self,
            "Abono registrado",
            f"Se registro un abono de C$ {monto:,.2f} "
            f"para el prestamo {id_item.text()} de {cliente['nombre']}."
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
                background-color: #f5f5f5;
            }

            QLineEdit {
                background-color: #D3D3D3;
                color: #000;
            }

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
                background-color: green;
            }
        """)

        form_layout = QFormLayout(layoutCC)

        self.infoName = QLineEdit("")
        self.infoName.setPlaceholderText(
            "Ingresa tu nombre..."
        )
        self.infoName.setMaxLength(10)

        self.infoEmail = QLineEdit("")
        self.infoEmail.setPlaceholderText(
            "Ingresa tu correo electronico..."
        )

        self.infoCedula = QLineEdit("")
        self.infoCedula.setPlaceholderText(
            "Ingresa tu cedula"
        )
        self.infoCedula.setMaxLength(16)

        self.infoPassword = QLineEdit("")
        self.infoPassword.setPlaceholderText(
            "Ingresa tu contraseña..."
        )
        self.infoPassword.setMaxLength(8)

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