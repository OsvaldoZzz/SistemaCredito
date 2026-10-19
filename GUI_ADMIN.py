from PySide6.QtWidgets import *
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QHeaderView
from pathlib import Path
from mysql.connector import Error as MySQLConnectorError
from reportes_pdf import generar_estado_cartera, generar_reporte_cobranza
from clientes_crud import crear_cliente, eliminar_cliente, listar_clientes
from prestamos_crud import (
    actualizar_prestamo,
    crear_prestamo,
    eliminar_prestamo,
    listar_prestamos,
    listar_todos_los_prestamos,
)
from solicitudes_crud import (
    listar_solicitudes_pendientes,
    resolver_solicitud_prestamo,
)
from validaciones import validar_cliente_unico, validar_datos_cliente
from calculos_prestamo import (
    PORCENTAJE_INTERES,
    calcular_interes,
    calcular_total_prestamo,
)


class AdminWindow(QMainWindow):
    def __init__(self, clientes, ventana_login):
        super().__init__()

        self.clientes = clientes
        self.ventana_login = ventana_login
        self.cliente_cedula = None
        self.prestamos_por_cliente = {
            cliente["cedula"]: [] for cliente in self.clientes
        }

        # Obtiene el usuario directamente del login
        self.usuario = self.ventana_login.input_user.text()

        self.setAdmin()

    def setAdmin(self):
        self.showMaximized()
        self.setWindowTitle("Panel Administrador")
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

            QLineEdit#lineaEdit{
            background-color: #f5f5f5;
                border: 1px solid #d1d5db;
                border-radius: 8px;
                padding: 5px;
                color: #000;
                border-radius: 8px;
                padding: 5px;
            }

            QPushButton#btnBuscar{
                background-color: #3B82F6;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 5px;
                font-size: 14px;
                font-weight: bold;
            }

            QPushButton:hover#btnBuscar{
                background-color: #00BB77;
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

            /* INFORMACION DEL CLIENTE */

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

            QPushButton#acciones{
                background-color: white;
                color: #000;
                padding: 2px;
                min-width: 32px;
                min-height: 32px;
            }

            QPushButton:hover#acciones{
                background-color: #e8f0fe;
                }

            QPushButton:hover {
                background-color: #2563eb;
            }

            QPushButton#btnAcciones {
                background-color: #4f46e5;
                color: white;
                border: 1px solid #4338ca;
                border-radius: 8px;
                padding: 10px 16px;
                font-weight: bold;
            }

            QPushButton#btnAcciones:hover {
                background-color: #4338ca;
                border-color: #3730a3;
            }

            QPushButton#btnAcciones:pressed {
                background-color: #3730a3;
                border-color: #312e81;
            }

            QPushButton#btnAcciones:focus {
                border: 1px solid #a5b4fc;
            }

            QPushButton:hover#crear_cliente {
                background-color: green;
            }

            QPushButton:hover#eliminar_cliente {
                background-color: red;
            }

            QPushButton:hover#cerrarSesion {
                background-color: red;
            }

            QPushButton:hover#crear_prestamo {
                background-color: green;
            }

            QPushButton:hover#abonar_prestamo {
                background-color: #FFD400;
            }

            QPushButton:hover#verSoli_prestamo {
                background-color: gray;
            }

            QPushButton:hover#reporte_pdf {
                background-color: #00BB77;
            }

            QPushButton:hover#eliminar_prestamo {
                background-color: red;
            }

            QPushButton:hover#editar_prestamo {
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

        tituloPanel = QLabel("PANEL ADMINISTRADOR")
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


        self.btnBuscar = QPushButton()
        self.btnBuscar.setObjectName("btnBuscar")
        self.btnBuscar.setIcon(QIcon("img/lupa.png"))
        self.btnBuscar.setIconSize(QSize(24, 24))
        self.btnBuscar.clicked.connect(self.buscarCliente)

        #corregir para que aparezca en la parte de al lado de cliente, y darle qss al boton buscar
        self.buscarCl.addWidget(self.clientesBuscar)
        self.buscarCl.addWidget(self.btnBuscar)

        clientesLayout.addLayout(self.buscarCl)

    #=====================================
    #lista de clientes
    #=====================================

        self.listaClientes = QListWidget()
        self.listaClientes.itemClicked.connect(self.mostrarCliente)

        #Para buscar correctamente los datos del cliente al seleccionar una sola

        for indice, cliente in enumerate(self.clientes):
            item = QListWidgetItem(
                cliente["nombre"] + " - " + cliente["cedula"]
            )
            item.setData(
                Qt.ItemDataRole.UserRole,
                indice
            )
            self.listaClientes.addItem(item)

        clientesLayout.addWidget(self.listaClientes)

        botonesLayout = QHBoxLayout()

        self.btnAcciones = QPushButton("Acciones")
        self.btnAcciones.setObjectName("btnAcciones")
        self.btnAcciones.clicked.connect(self.accionesAdmin)

        self.btnActualizar = QPushButton("Actualizar datos")
        self.btnActualizar.clicked.connect(self.actualizarDatos)

        self.btnCerrar = QPushButton("Cerrar Sesion")
        self.btnCerrar.setObjectName("cerrarSesion")

        self.btnCerrar.clicked.connect(self.btnCerrSes)

        botonesLayout.addWidget(self.btnAcciones)
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

        self.lblCliente = QLabel("Seleccione un cliente")
        self.lblCliente.setObjectName("lblCliente")

        self.lblCorreo = QLabel("Correo: -")
        self.lblCorreo.setObjectName("lblCorreo")

        self.lblDir = QLabel("Direccion: -")
        self.lblDir.setObjectName("lblDir")


        prestamosLayout.addWidget(self.lblCliente)
        prestamosLayout.addWidget(self.lblCorreo)
        prestamosLayout.addWidget(self.lblDir)

#===========================
#tablas prestamos
#===========================
        
        self.tablaPrestamos = QTableWidget()

        self.tablaPrestamos.setColumnCount(7)
        self.tablaPrestamos.setRowCount(0)
        self.tablaPrestamos.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tablaPrestamos.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )

        self.tablaPrestamos.setHorizontalHeaderLabels([
            "ID",
            "Monto inicial",
            f"Interés ({PORCENTAJE_INTERES:.0f}%)",
            "Total a pagar",
            "Plazo",
            "Estado",
            "Acciones"
        ])

        self.tablaPrestamos.setObjectName("tablaPrestamos")

        self.tablaPrestamos.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )
        self.tablaPrestamos.setColumnWidth(6, 120)


        prestamosLayout.addWidget(self.tablaPrestamos, 1)

        prestamosLayout.addStretch()

        # BOTONES DE PRÉSTAMO

        self.btnCreatePrestamo = QPushButton("Crear Prestamo")
        self.btnCreatePrestamo.setObjectName("crear_prestamo")
        self.btnCreatePrestamo.clicked.connect(self.crearPrestamo)

        self.btnVerSolicitudes = QPushButton("Ver Solicitudes")
        self.btnVerSolicitudes.setObjectName("verSoli_prestamo")
        self.btnVerSolicitudes.clicked.connect(self.verSolicitudes)


        self.btnAbonarPrestamo = QPushButton("Abonar Prestamo")
        self.btnAbonarPrestamo.setObjectName("abonar_prestamo")
        self.btnAbonarPrestamo.clicked.connect(self.abonarPrestamo)

        self.btnReporteCartera = QPushButton("Reporte Cartera PDF")
        self.btnReporteCartera.setObjectName("reporte_pdf")
        self.btnReporteCartera.clicked.connect(self.generarReporteCartera)

        self.btnReporteCobranza = QPushButton("Reporte Cobranza PDF")
        self.btnReporteCobranza.setObjectName("reporte_pdf")
        self.btnReporteCobranza.clicked.connect(self.generarReporteCobranza)

        botonesLayout2.addWidget(self.btnCreatePrestamo)
        botonesLayout2.addWidget(self.btnAbonarPrestamo)
        botonesLayout2.addWidget(self.btnVerSolicitudes)
        botonesLayout2.addWidget(self.btnReporteCartera)
        botonesLayout2.addWidget(self.btnReporteCobranza)

        prestamosLayout.addLayout(botonesLayout2)

        layout.addWidget(panelPrestamos, 1, 1)

        # PROPORCIONES

        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 3)

        layout.setRowStretch(0, 0)
        layout.setRowStretch(1, 1)

        if self.listaClientes.count() > 0:
            self.listaClientes.setCurrentRow(0)
            self.mostrarCliente(self.listaClientes.currentItem())

    def guardarPrestamosCliente(self):
        if self.cliente_cedula is None:
            return

        prestamos = []
        for fila in range(self.tablaPrestamos.rowCount()):
            valores = [
                self.tablaPrestamos.item(fila, columna)
                for columna in range(6)
            ]
            if all(valores):
                prestamos.append({
                    "id": valores[0].text(),
                    "monto": valores[1].text(),
                    "interes": valores[2].text(),
                    "total": valores[3].text(),
                    "plazo": valores[4].text(),
                    "estado": valores[5].text(),
                })
        self.prestamos_por_cliente[self.cliente_cedula] = prestamos

    def cargarPrestamosCliente(self, cedula):
        self.tablaPrestamos.setRowCount(0)
        cliente = next(
            (cliente for cliente in self.clientes if cliente["cedula"] == cedula),
            None
        )
        if cliente is None or cliente.get("id") is None:
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
            monto = prestamo["monto"]
            interes = calcular_interes(monto)
            total = calcular_total_prestamo(monto)
            valores = (
                str(prestamo["id"]),
                f"C$ {float(monto):,.2f}",
                f"C$ {interes:,.2f}",
                f"C$ {total:,.2f}",
                f"{prestamo['plazo']} cuotas",
                str(prestamo["estado"]),
            )
            for columna, valor in enumerate(valores):
                self.tablaPrestamos.setItem(
                    fila,
                    columna,
                    QTableWidgetItem(valor)
                )
            self.agregarAccionesPrestamo(fila)
            self.tablaPrestamos.setRowHeight(fila, 42)

    def mostrarCliente(self, item):
        indice_cliente = item.data(Qt.ItemDataRole.UserRole)
        if indice_cliente is None:
            indice_cliente = self.listaClientes.row(item)

        if indice_cliente < 0 or indice_cliente >= len(self.clientes):
            return

        cliente = self.clientes[indice_cliente]
        self.guardarPrestamosCliente()
        self.cliente_cedula = cliente["cedula"]
        self.cargarPrestamosCliente(self.cliente_cedula)

        self.lblCliente.setText(
            f"Cliente: {cliente['nombre']}"
        )

        self.lblCorreo.setText(
            f"Correo: {cliente['correo']}"
        )

        self.lblDir.setText(
            f"Direccion: {cliente['direccion']}"
        )

        print(
            f"Imprimiendo datos del cliente: {cliente['nombre']} - "
            f"{cliente['correo']} - {cliente['direccion']}"
        )

    def accionesAdmin(self):
        dialogo = QDialog(self)
        dialogo.setWindowTitle("Acciones de clientes")
        dialogo.setModal(True)
        dialogo.resize(440, 180)

        layout = QGridLayout(dialogo)

        btn_crear = QPushButton("Crear Cliente")
        btn_crear.setObjectName("crear_cliente")
        btn_eliminar = QPushButton("Eliminar Cliente")
        btn_eliminar.setObjectName("eliminar_cliente")
        btn_crearRol = QPushButton("Crear Rol")
        btn_eliminarRol = QPushButton("Eliminar Rol")
        btn_cancelar = QPushButton("Cancelar")

        accion_seleccionada = {"tipo": None}

        def seleccionar_accion(accion):
            accion_seleccionada["tipo"] = accion
            dialogo.accept()

        btn_crear.clicked.connect(
            lambda: seleccionar_accion("crear")
        )
        btn_eliminar.clicked.connect(
            lambda: seleccionar_accion("eliminar") #lambda crea una pequeña funcion que, al hacer clic, llama a seleccionar_accion()
        )
        btn_crearRol.clicked.connect(
            lambda: seleccionar_accion("crearRol")
        )
        btn_eliminarRol.clicked.connect(
            lambda: seleccionar_accion("eliminarRol")
        )
        btn_cancelar.clicked.connect(dialogo.reject)

        layout.addWidget(btn_crear, 0, 0)
        layout.addWidget(btn_crearRol, 0, 1)
        layout.addWidget(btn_eliminar, 1, 0)
        layout.addWidget(btn_eliminarRol, 1, 1)
        layout.addWidget(btn_cancelar, 2, 0, 1, 2, Qt.AlignmentFlag.AlignCenter)

        dialogo.exec()

        if accion_seleccionada["tipo"] == "crear":
            self.crearCl()
        elif accion_seleccionada["tipo"] == "eliminar":
            self.eliminarCliente()
        elif accion_seleccionada["tipo"] == "crearRol":
            self.crearRol()
        elif accion_seleccionada["tipo"] == "eliminarRol":
            self.eliminarRol()

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

        self.clientes[:] = clientes
        self.clientesBuscar.clear()
        self.cliente_cedula = None
        self.prestamos_por_cliente = {
            cliente["cedula"]: [] for cliente in self.clientes
        }
        self.listaClientes.clear()
        fila_seleccionada = 0
        for indice, cliente in enumerate(self.clientes):
            item = QListWidgetItem(
                f"{cliente['nombre']} - {cliente['cedula']}"
            )
            item.setData(Qt.ItemDataRole.UserRole, indice)
            self.listaClientes.addItem(item)
            if cliente.get("id") == cliente_id:
                fila_seleccionada = indice

        if self.listaClientes.count():
            self.listaClientes.setCurrentRow(fila_seleccionada)
            self.mostrarCliente(self.listaClientes.currentItem())
        else:
            self.tablaPrestamos.setRowCount(0)
            self.lblCliente.setText("Seleccione un cliente")
            self.lblCorreo.setText("Correo: -")
            self.lblDir.setText("Direccion: -")

    # Confirma la eliminacion y actualiza la lista de clientes.
    def eliminarCliente(self):
        item_seleccionado = self.listaClientes.currentItem()
        indice_cliente = (
            item_seleccionado.data(Qt.ItemDataRole.UserRole)
            if item_seleccionado
            else -1
        )

        if indice_cliente < 0 or indice_cliente >= len(self.clientes):
            QMessageBox.warning(
                self,
                "Cliente no seleccionado",
                "Selecciona un cliente para eliminarlo."
            )
            return

        cliente = self.clientes[indice_cliente]
        respuesta = QMessageBox.question(
            self,
            "Confirmar eliminacion",
            f"Estas seguro de eliminar al cliente {cliente['nombre']}?",
            QMessageBox.Yes | QMessageBox.No
        )

        if respuesta != QMessageBox.Yes:
            return

        cliente_id = cliente.get("id")
        if cliente_id is None:
            QMessageBox.warning(
                self,
                "Cliente no valido",
                "El cliente seleccionado no tiene un identificador de base de datos."
            )
            return

        try:
            eliminado = eliminar_cliente(int(cliente_id))
        except Exception as error:
            QMessageBox.critical(
                self,
                "Error al eliminar cliente",
                f"No se pudo eliminar el cliente: {error}"
            )
            return

        if not eliminado:
            QMessageBox.warning(
                self,
                "Cliente no encontrado",
                "El cliente no existe en la base de datos."
            )
            return

        self.clientes.pop(indice_cliente)
        self.buscarCliente()
        self.lblCliente.setText("Seleccione un cliente")
        self.lblCorreo.setText("Correo: -")
        self.lblDir.setText("Direccion: -")

        QMessageBox.information(
            self,
            "Cliente eliminado",
            f"El cliente {cliente['nombre']} fue eliminado."
        )

    

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
        self.btnEnviar.clicked.connect(self.enviarForm)
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
        except Exception as error:
            QMessageBox.critical(
                self,
                "Error al crear cliente",
                f"No se pudo guardar el cliente: {error}"
            )
            return

        self.newCl["id"] = cliente_id
        self.clientes.append(self.newCl)
        self.prestamos_por_cliente[self.newCl["cedula"]] = (
            []
        )

        self.buscarCliente()

        print(
            f"Lista de clientes actualizada: {self.clientes}"
        )

        QMessageBox.information(
            self,
            "Cliente creado",
            "El cliente se creo correctamente."
        )

        self.ventanaCrear.close()

    def eliminarCl(self):
        item_seleccionado = self.listaClientes.currentItem()
        if not item_seleccionado:
            QMessageBox.warning(
                self,
                "Seleccionar cliente",
                "Selecciona un cliente para eliminar."
            )
            return
            indice_cliente = self.listaClientes.row(item_seleccionado)
            if indice_cliente < 0 or indice_cliente >= len(self.clientes):
                return

            cliente = self.clientes[indice_cliente]

            respuesta = QMessageBox.question(
                self,
                "Confirmar eliminacion",
                f"Estas seguro de eliminar al cliente {cliente['nombre']}?",
                QMessageBox.Yes | QMessageBox.No
            )

            if respuesta == QMessageBox.Yes:
                del self.clientes[indice_cliente]
                self.listaClientes.takeItem(indice_cliente)

                QMessageBox.information(
                    self,
                    "Cliente eliminado",
                    f"El cliente {cliente['nombre']} fue eliminado."
                )

    def crearRol(self):
        layoutCC = QWidget()

        layoutCC.setWindowTitle("Crear Rol")
        layoutCC.resize(300, 200)

        layoutCC.setObjectName("formCC")

        layoutCC.setStyleSheet("""
            #formCC {
                background-color: #f5f5f5;
                color: #000000;
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

        self.infoRol = QComboBox()
        self.infoRol.addItems(
            ["recepcionista", "cobrador"]
        )

        self.infoName = QLineEdit("")
        self.infoName.setPlaceholderText("Ingresa el nombre de usuario...")
        self.infoName.setMaxLength(100)

        self.infoPassword = QLineEdit("")
        self.infoPassword.setPlaceholderText(
            "Ingresa tu contraseña..."
        )
        self.infoPassword.setEchoMode(QLineEdit.Password)
        self.infoPassword.setMaxLength(128)

        self.btnEnviar = QPushButton("Enviar")
        self.btnEnviar.setObjectName("btnEnviar")

        form_layout.addRow("Rol:", self.infoRol)
        form_layout.addRow("Nombre de usuario:", self.infoName)
        form_layout.addRow("Contraseña:", self.infoPassword)
        form_layout.addRow(self.btnEnviar)

        layoutCC.show()

        self.ventanaCrear = layoutCC

    def eliminarRol(self):
        pass

    def agregarAccionesPrestamo(self, fila):
        acciones = QWidget()
        acciones_layout = QHBoxLayout(acciones)
        acciones_layout.setContentsMargins(4, 2, 4, 2)
        acciones_layout.setSpacing(6)
        acciones_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        boton_editar = QPushButton()
        boton_editar.setObjectName("acciones")
        boton_editar.setFixedSize(34, 34)
        boton_editar.setIcon(
            QIcon(str(Path(__file__).resolve().parent / "img" / "editar.png"))
        )
        boton_editar.setIconSize(QSize(25, 25))
        boton_editar.setToolTip("Editar préstamo")
        boton_editar.clicked.connect(self.editarPrestamoDesdeBoton)

        boton_eliminar = QPushButton()
        boton_eliminar.setObjectName("acciones")
        ruta_basurita = (
            Path(__file__).resolve().parent / "img" / "basurita.png"
        )
        icono_basurita = QIcon(str(ruta_basurita))
        if icono_basurita.isNull():
            icono_basurita = self.style().standardIcon(
                QStyle.StandardPixmap.SP_TrashIcon
            )
        boton_eliminar.setFixedSize(34, 34)
        boton_eliminar.setIcon(icono_basurita)
        boton_eliminar.setIconSize(QSize(25, 25))
        boton_eliminar.setToolTip("Eliminar préstamo")
        boton_eliminar.clicked.connect(self.eliminarPrestamoDesdeBoton)

        acciones_layout.addWidget(boton_editar)
        acciones_layout.addWidget(boton_eliminar)
        self.tablaPrestamos.setCellWidget(fila, 6, acciones)

    def filaDeAccion(self, boton):
        contenedor = boton.parentWidget()
        for fila in range(self.tablaPrestamos.rowCount()):
            if self.tablaPrestamos.cellWidget(fila, 6) is contenedor:
                return fila
        return -1

    def editarPrestamoDesdeBoton(self):
        fila = self.filaDeAccion(self.sender())
        if fila >= 0:
            self.editarPrestamo(fila)

    def eliminarPrestamoDesdeBoton(self):
        fila = self.filaDeAccion(self.sender())
        if fila < 0:
            return

        id_item = self.tablaPrestamos.item(fila, 0)
        if id_item is None:
            return

        id_prestamo = id_item.text()
        respuesta = QMessageBox.question(
            self,
            "Confirmar eliminacion",
            f"Estas seguro de eliminar el prestamo {id_prestamo}?",
            QMessageBox.Yes | QMessageBox.No
        )
        if respuesta == QMessageBox.Yes:
            try:
                eliminado = eliminar_prestamo(int(id_prestamo))
            except (MySQLConnectorError, OSError, ValueError, TypeError) as error:
                QMessageBox.critical(
                    self,
                    "Error al eliminar préstamo",
                    f"No se pudo eliminar el préstamo: {error}"
                )
                return
            if not eliminado:
                QMessageBox.warning(
                    self,
                    "Préstamo no encontrado",
                    "El préstamo ya no existe en la base de datos."
                )
                self.cargarPrestamosCliente(self.cliente_cedula)
                return

            self.tablaPrestamos.removeRow(fila)
            self.guardarPrestamosCliente()
            QMessageBox.information(
                self,
                "Prestamo eliminado",
                f"El prestamo {id_prestamo} fue eliminado."
            )

    def EyD(self):
        botonAcc = self.sender() #sender es un metodo de QT, devuelve el objeto que emitio la senal que activo el metodo actual.
        fila = next(
            (
                indice
                for indice in range(self.tablaPrestamos.rowCount())
                if self.tablaPrestamos.cellWidget(indice, 6) is botonAcc
            ),
            -1
        )

        if fila < 0:
            return

        id_item = self.tablaPrestamos.item(fila, 0)
        if id_item is None:
            return

        id_prestamo = id_item.text()

        layoutEyD = QMessageBox()

        layoutEyD.setWindowTitle("Opciones")
        layoutEyD.setText(f"Que deseas realizar con el prestamo {id_prestamo}?")
        layoutEyD.setIcon(QMessageBox.Information)

        btnEditarP = layoutEyD.addButton("Editar prestamo", QMessageBox.ActionRole)
        btnEliminarP = layoutEyD.addButton("Eliminar prestamo", QMessageBox.DestructiveRole)

        layoutEyD.exec()

        if layoutEyD.clickedButton() == btnEditarP:
            self.editarPrestamo(fila)

        elif layoutEyD.clickedButton() == btnEliminarP:
            respuesta = QMessageBox.question(
                self,
                "Confirmar eliminacion",
                f"Estas seguro de eliminar el prestamo {id_prestamo}?",
                QMessageBox.Yes | QMessageBox.No
            )

            if respuesta == QMessageBox.Yes:
                try:
                    eliminado = eliminar_prestamo(int(id_prestamo))
                except (MySQLConnectorError, OSError, ValueError, TypeError) as error:
                    QMessageBox.critical(
                        self,
                        "Error al eliminar préstamo",
                        f"No se pudo eliminar el préstamo: {error}"
                    )
                    return
                if not eliminado:
                    QMessageBox.warning(
                        self,
                        "Préstamo no encontrado",
                        "El préstamo ya no existe en la base de datos."
                    )
                    return
                self.tablaPrestamos.removeRow(fila)
                self.guardarPrestamosCliente()
                QMessageBox.information(
                    self,
                    "Prestamo eliminado",
                    f"El prestamo {id_prestamo} fue eliminado."
                )

    def editarPrestamo(self, fila):
        monto_item = self.tablaPrestamos.item(fila, 1)
        plazo_item = self.tablaPrestamos.item(fila, 4)
        estado_item = self.tablaPrestamos.item(fila, 5)

        if not monto_item or not plazo_item or not estado_item:
            return

        dialogo = QDialog(self)
        dialogo.setWindowTitle("Editar prestamo")
        dialogo.setModal(True)

        formulario = QFormLayout(dialogo)
        formulario.setObjectName("LayoutFEDIT")

        monto_input = QDoubleSpinBox()
        monto_input.setRange(0.01, 100_000_000)
        monto_input.setDecimals(2)
        monto_input.setValue(
            float(monto_item.text().replace("C$", "").replace(",", "").strip())
        )
        plazo_input = QSpinBox()
        plazo_input.setRange(1, 360)
        plazo_input.setValue(
            int(plazo_item.text().casefold().replace("cuotas", "").strip())
        )
        estado_input = QComboBox()
        estados = ["Activo", "Pagado", "Vencido"]
        estado_input.addItems(estados)
        if estado_item.text() in estados:
            estado_input.setCurrentText(estado_item.text())

        interes_label = QLabel(
            f"C$ {calcular_interes(monto_input.value()):,.2f}"
        )
        formulario.addRow("Monto:", monto_input)
        formulario.addRow(
            f"Interés ({PORCENTAJE_INTERES:.0f}%):", interes_label
        )
        formulario.addRow("Plazo:", plazo_input)
        formulario.addRow("Estado:", estado_input)
        monto_input.valueChanged.connect(
            lambda valor: interes_label.setText(
                f"C$ {calcular_interes(valor):,.2f}"
            )
        )

        botones = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        botones.accepted.connect(dialogo.accept)
        botones.rejected.connect(dialogo.reject)
        formulario.addRow(botones)

        if dialogo.exec() != QDialog.Accepted:
            return

        prestamo_id = int(self.tablaPrestamos.item(fila, 0).text())
        try:
            actualizado = actualizar_prestamo(
                prestamo_id,
                monto_input.value(),
                plazo_input.value(),
                estado_input.currentText(),
            )
        except (MySQLConnectorError, OSError, ValueError, TypeError) as error:
            QMessageBox.critical(
                self,
                "Error al actualizar préstamo",
                f"No se pudo guardar el cambio: {error}"
            )
            return
        if not actualizado:
            QMessageBox.warning(
                self,
                "Préstamo no encontrado",
                "El préstamo ya no existe en la base de datos."
            )
            self.cargarPrestamosCliente(self.cliente_cedula)
            return

        monto_item.setText(f"C$ {monto_input.value():,.2f}")
        self.tablaPrestamos.item(fila, 2).setText(
            f"C$ {calcular_interes(monto_input.value()):,.2f}"
        )
        self.tablaPrestamos.item(fila, 3).setText(
            f"C$ {calcular_total_prestamo(monto_input.value()):,.2f}"
        )
        plazo_item.setText(f"{plazo_input.value()} cuotas")
        estado_item.setText(estado_input.currentText())
        self.guardarPrestamosCliente()

        QMessageBox.information(
            self,
            "Prestamo actualizado",
            "Los datos del prestamo fueron actualizados."
        )

    def clienteSeleccionado(self):
        item = self.listaClientes.currentItem()
        if item is None:
            return None

        indice = item.data(Qt.ItemDataRole.UserRole)
        if indice is None or indice < 0 or indice >= len(self.clientes):
            return None
        return self.clientes[indice]

    def crearPrestamo(self):
        cliente = self.clienteSeleccionado()
        if cliente is None:
            QMessageBox.warning(
                self,
                "Cliente no seleccionado",
                "Selecciona un cliente para crearle un prestamo."
            )
            return

        dialogo = QDialog(self)
        dialogo.setWindowTitle("Crear prestamo")
        formulario = QFormLayout(dialogo)

        monto_input = QDoubleSpinBox()
        monto_input.setRange(0.01, 100_000_000)
        monto_input.setDecimals(2)
        monto_input.setPrefix("C$ ")
        interes_preview = QLabel(f"C$ {calcular_interes(monto_input.value()):,.2f}")
        total_preview = QLabel(
            f"C$ {calcular_total_prestamo(monto_input.value()):,.2f}"
        )
        monto_input.valueChanged.connect(
            lambda valor: interes_preview.setText(
                f"C$ {calcular_interes(valor):,.2f}"
            )
        )
        monto_input.valueChanged.connect(
            lambda valor: total_preview.setText(
                f"C$ {calcular_total_prestamo(valor):,.2f}"
            )
        )
        plazo_input = QSpinBox()
        plazo_input.setRange(1, 360)
        botones = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        botones.accepted.connect(dialogo.accept)
        botones.rejected.connect(dialogo.reject)

        formulario.addRow("Monto:", monto_input)
        formulario.addRow(f"Interés ({PORCENTAJE_INTERES:.0f}%):", interes_preview)
        formulario.addRow("Total a pagar:", total_preview)
        formulario.addRow("Plazo:", plazo_input)
        formulario.addRow(botones)

        if dialogo.exec() != QDialog.Accepted:
            return

        try:
            if cliente.get("id") is None:
                raise ValueError("El cliente no tiene un ID válido.")
            nuevo_id = crear_prestamo(
                int(cliente["id"]),
                monto_input.value(),
                plazo_input.value(),
            )
        except (ValueError, TypeError) as error:
            QMessageBox.warning(
                self,
                "Datos invalidos",
                f"El monto y el plazo deben ser validos: {error}"
            )
            return
        except Exception as error:
            QMessageBox.critical(
                self,
                "Error al crear prestamo",
                f"No se pudo guardar el prestamo: {error}"
            )
            return

        self.cargarPrestamosCliente(cliente["cedula"])

        QMessageBox.information(
            self,
            "Prestamo creado",
            f"El prestamo {nuevo_id} fue creado para {cliente['nombre']}."
        )

    def abonarPrestamo(self):
        fila = self.tablaPrestamos.currentRow()
        if fila < 0:
            QMessageBox.warning(
                self,
                "Prestamo no seleccionado",
                "Selecciona un prestamo de la tabla para registrar un abono."
            )
            return

        id_item = self.tablaPrestamos.item(fila, 0)
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

        QMessageBox.information(
            self,
            "Abono registrado",
            f"Se registro un abono de C$ {monto:,.2f} "
            f"para el prestamo {id_item.text()}."
        )

    def verSolicitudes(self):
        try:
            solicitudes = listar_solicitudes_pendientes()
        except (MySQLConnectorError, OSError, ValueError, TypeError) as error:
            QMessageBox.critical(
                self,
                "Error al cargar solicitudes",
                f"No se pudieron cargar las solicitudes: {error}"
            )
            return

        if not solicitudes:
            QMessageBox.information(
                self, "Solicitudes", "No hay solicitudes pendientes."
            )
            return

        dialogo = QDialog(self)
        dialogo.setWindowTitle("Solicitudes de préstamo")
        dialogo.resize(1000, 440)
        layout = QVBoxLayout(dialogo)
        tabla = QTableWidget(len(solicitudes), 9)
        tabla.setHorizontalHeaderLabels(
            [
                "ID", "Cliente", "Cédula", "Ingreso mensual", "Monto solicitado",
                "Interés (2%)", "Total", "Plazo", "Fecha"
            ]
        )
        tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        for fila, solicitud in enumerate(solicitudes):
            fecha = solicitud["fecha_solicitud"]
            valores = (
                str(solicitud["id"]),
                solicitud["nombre"],
                solicitud["cedula"],
                (
                    f"C$ {float(solicitud['ingreso_mensual']):,.2f}"
                    if solicitud.get("ingreso_mensual") is not None
                    else "No registrado"
                ),
                f"C$ {float(solicitud['monto']):,.2f}",
                f"C$ {calcular_interes(solicitud['monto']):,.2f}",
                f"C$ {calcular_total_prestamo(solicitud['monto']):,.2f}",
                f"{solicitud['plazo']} cuotas",
                fecha.strftime("%d/%m/%Y"),
            )
            for columna, valor in enumerate(valores):
                tabla.setItem(fila, columna, QTableWidgetItem(valor))
        layout.addWidget(tabla)

        botones = QHBoxLayout()
        btn_aprobar = QPushButton("Aprobar y crear préstamo")
        btn_rechazar = QPushButton("Rechazar")
        btn_cerrar = QPushButton("Cerrar")
        botones.addWidget(btn_aprobar)
        botones.addWidget(btn_rechazar)
        botones.addWidget(btn_cerrar)
        layout.addLayout(botones)

        def resolver(aprobada):
            fila = tabla.currentRow()
            if fila < 0:
                QMessageBox.warning(
                    dialogo,
                    "Solicitud no seleccionada",
                    "Selecciona una solicitud."
                )
                return
            solicitud_id = int(tabla.item(fila, 0).text())
            cliente_id = int(solicitudes[fila]["cliente_id"])
            try:
                prestamo_id = resolver_solicitud_prestamo(
                    solicitud_id, aprobada
                )
            except (MySQLConnectorError, OSError, ValueError, TypeError) as error:
                QMessageBox.critical(
                    dialogo,
                    "Error al resolver solicitud",
                    f"No se pudo actualizar la solicitud: {error}"
                )
                return
            tabla.removeRow(fila)
            solicitudes.pop(fila)
            if aprobada:
                QMessageBox.information(
                    dialogo,
                    "Solicitud aprobada",
                    f"Se creó el préstamo #{prestamo_id}."
                )
                cliente_fila = next(
                    (
                        indice
                        for indice, cliente in enumerate(self.clientes)
                        if int(cliente["id"]) == cliente_id
                    ),
                    None,
                )
                if cliente_fila is not None:
                    self.listaClientes.setCurrentRow(cliente_fila)
                    self.mostrarCliente(self.listaClientes.currentItem())
            else:
                QMessageBox.information(
                    dialogo, "Solicitud rechazada", "La solicitud fue rechazada."
                )
            if tabla.rowCount() == 0:
                dialogo.accept()

        btn_aprobar.clicked.connect(lambda: resolver(True))
        btn_rechazar.clicked.connect(lambda: resolver(False))
        btn_cerrar.clicked.connect(dialogo.accept)
        dialogo.exec()

    def generarReporteCartera(self):
        try:
            generar_estado_cartera(
                self.clientes,
                self.obtenerPrestamosGlobales()
            )
        except (MySQLConnectorError, OSError, ValueError, KeyError) as error:
            QMessageBox.critical(
                self,
                "Error al generar reporte",
                f"No se pudo generar el reporte de cartera: {error}"
            )
            return

        QMessageBox.information(
            self,
            "Reporte generado",
            "El reporte de cartera se genero correctamente."
        )

    def generarReporteCobranza(self):
        try:
            generar_reporte_cobranza(
                self.clientes,
                self.obtenerPrestamosGlobales()
            )
        except (MySQLConnectorError, OSError, ValueError, KeyError) as error:
            QMessageBox.critical(
                self,
                "Error al generar reporte",
                f"No se pudo generar el reporte de cobranza: {error}"
            )
            return

        QMessageBox.information(
            self,
            "Reporte generado",
            "El reporte de cobranza se genero correctamente."
        )

    def obtenerPrestamosGlobales(self):
        prestamos_por_cliente = {
            cliente["cedula"]: [] for cliente in self.clientes
        }
        clientes_por_id = {
            int(cliente["id"]): cliente
            for cliente in self.clientes
            if cliente.get("id") is not None
        }
        for prestamo in listar_todos_los_prestamos():
            cliente = clientes_por_id.get(int(prestamo["cliente_id"]))
            if cliente is None:
                raise ValueError("Hay un préstamo asociado a un cliente no cargado.")
            prestamos_por_cliente[cliente["cedula"]].append({
                "id": prestamo["id"],
                "monto": f"C$ {float(prestamo['monto']):,.2f}",
                "interes": f"C$ {calcular_interes(prestamo['monto']):,.2f}",
                "total": f"C$ {calcular_total_prestamo(prestamo['monto']):,.2f}",
                "plazo": f"{prestamo['plazo']} cuotas",
                "estado": prestamo["estado"],
            })
        return prestamos_por_cliente

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

        if cedula and encontrados == 0:
            QMessageBox.information(
                self,
                "Cliente no encontrado",
                f"No se encontro un cliente con la cedula {cedula}."
            )

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
