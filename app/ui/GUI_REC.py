from app.config.rutas import IMAGENES_DIR
from PySide6.QtWidgets import *
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QHeaderView
from mysql.connector import Error as MySQLConnectorError
from app.datos.clientes_crud import actualizar_cliente, crear_cliente, eliminar_cliente, listar_clientes
from app.datos.citas_crud import (
    listar_todas_las_citas,
)
from app.datos.prestamos_crud import listar_prestamos, listar_todos_los_prestamos
from app.ui.pagos_ui import abrir_dialogo_abono
from app.ui.prestamos_ui import mostrar_detalle_prestamo, mostrar_error_detalle_prestamo
from app.reportes.reportes_pdf import generar_estado_cartera, generar_reporte_cobranza
from app.datos.solicitudes_crud import crear_solicitud_prestamo
from app.logica.validaciones import validar_cliente_unico, validar_datos_cliente
from app.logica.calculos_prestamo import (
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

            QDialog#accionesClientes { background-color: #FBFAF6; }
            QPushButton:disabled { background-color: #D9D2C2; color: #65758B; }
            QPushButton#cancelar_accion {
                background-color: white; color: #33465F;
                border: 1px solid #D9D2C2;
            }

            /* BOTONES */

            QPushButton#btnAcciones {
                background-color: #102848;
                color: white;
                border-radius: 8px;
                padding: 10px 16px;
                font-weight: bold;
            }

            QPushButton#btnAcciones {
                background-color: #183A60;
                border-color: #0B1C32;
            }

            QPushButton#btnAcciones:pressed {
                background-color: #0B1C32;
                border-color: #0B1C32;
            }

            QPushButton#btnAcciones:focus {
                border: 1px solid #E6D3A5;
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

            QPushButton:hover:enabled:!pressed {
                background-color: #285580;
            }

            QPushButton#btnAcciones:hover:enabled:!pressed {
                background-color: #285580;
            }

            QPushButton:pressed {
                background-color: #0B1C32;
            }

            QPushButton#crear_cliente:enabled,
            QPushButton#solicitar_prestamo:enabled {
                background-color: #78B85B;
                color: #102848;
            }

            QPushButton#crear_cliente:hover:enabled:!pressed,
            QPushButton#solicitar_prestamo:hover:enabled:!pressed {
                background-color: #69A64D;
                color: #102848;
            }

            QPushButton#crear_cliente:pressed:enabled,
            QPushButton#solicitar_prestamo:pressed:enabled {
                background-color: #58963F;
                color: #102848;
            }

            QPushButton#actualizar_clientes:enabled,
            QPushButton#abonar_prestamo:enabled {
                background-color: #E8BD45;
                color: #102848;
            }

            QPushButton#actualizar_clientes:hover:enabled:!pressed,
            QPushButton#abonar_prestamo:hover:enabled:!pressed {
                background-color: #D8AC34;
                color: #102848;
            }

            QPushButton#actualizar_clientes:pressed:enabled,
            QPushButton#abonar_prestamo:pressed:enabled {
                background-color: #C99A28;
                color: #102848;
            }

            QPushButton#eliminar_cliente:enabled,
            QPushButton#cerrarSesion:enabled {
                background-color: #EF6262;
                color: #102848;
            }

            QPushButton#eliminar_cliente:hover:enabled:!pressed,
            QPushButton#cerrarSesion:hover:enabled:!pressed {
                background-color: #DC4E4E;
                color: #102848;
            }

            QPushButton#eliminar_cliente:pressed:enabled,
            QPushButton#cerrarSesion:pressed:enabled {
                background-color: #C83C3C;
                color: #102848;
            }

            QPushButton#verCitas:enabled {
                background-color: #CBD0D6;
                color: #102848;
            }

            QPushButton#verCitas:hover:enabled:!pressed {
                background-color: #B7BEC6;
                color: #102848;
            }

            QPushButton#verCitas:pressed:enabled {
                background-color: #A3ADB8;
                color: #102848;
            }

            QPushButton#reportCart:enabled,
            QPushButton#reporteCob:enabled {
                background-color: #3973A5;
                color: white;
            }

            QPushButton#reportCart:hover:enabled:!pressed,
            QPushButton#reporteCob:hover:enabled:!pressed {
                background-color: #306491;
                color: white;
            }

            QPushButton#reportCart:pressed:enabled,
            QPushButton#reporteCob:pressed:enabled {
                background-color: #27557D;
                color: white;
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
        self.btnBuscar.setIcon(QIcon(str(IMAGENES_DIR / "lupa.png")))
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

        self.btnAcciones = QPushButton("Acciones")
        self.btnAcciones.setObjectName("btnAcciones")
        self.btnAcciones.clicked.connect(self.accionesClientes)

        self.btnCerrar = QPushButton("Cerrar Sesion")
        self.btnCerrar.setObjectName("cerrarSesion")

        self.btnCerrar.clicked.connect(self.btnCerrSes)

        botonesLayout.addWidget(self.btnAcciones)
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

    # ==========================================================
    # BOTÓN CREAR CLIENTE
    # ==========================================================

    def accionesClientes(self):
        dialogo = QDialog(self)
        dialogo.setObjectName("accionesClientes")
        dialogo.setWindowTitle("Acciones de clientes")
        dialogo.setMinimumWidth(360)
        layout = QVBoxLayout(dialogo)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)
        seleccionado = self.clienteSeleccionado() is not None
        accion = []

        def elegir(funcion):
            accion.append(funcion)
            dialogo.accept()

        for texto, identificador, funcion, habilitado in (
            ("Crear clientes", "crear_cliente", self.crearCl, True),
            ("Editar clientes", "actualizar_clientes", self.actualizarCliente, seleccionado),
            ("Eliminar clientes", "eliminar_cliente", self.eliminarCliente, seleccionado),
        ):
            boton = QPushButton(texto)
            boton.setObjectName(identificador)
            boton.setEnabled(habilitado)
            boton.clicked.connect(lambda checked=False, f=funcion: elegir(f))
            layout.addWidget(boton)
        cancelar = QPushButton("Cancelar")
        cancelar.setObjectName("cancelar_accion")
        cancelar.clicked.connect(dialogo.reject)
        layout.addWidget(cancelar)
        if dialogo.exec() == QDialog.Accepted and accion:
            accion[0]()

    def formularioActualizacion(self, titulo):
        dialogo = QDialog(self)
        dialogo.setWindowTitle(titulo)
        dialogo.setMinimumWidth(480)
        dialogo.setStyleSheet("""
            QDialog { background-color: #FBFAF6; }
            QLabel { color: #33465F; font-size: 14px; font-weight: normal; }
            QLineEdit, QComboBox {
                background-color: white; color: #102848;
                border: 1px solid #D9D2C2; border-radius: 8px;
                padding: 10px; font-size: 14px;
                selection-background-color: #F4EBD5; selection-color: #102848;
            }
            QLineEdit:focus, QComboBox:focus { border-color: #C09848; }
            QComboBox QAbstractItemView {
                background-color: white; color: #102848;
                selection-background-color: #F4EBD5; selection-color: #102848;
            }
            QPushButton#guardarCambios:hover { background-color: #3F6B36; }
        """)
        formulario = QFormLayout(dialogo)
        formulario.setContentsMargins(24, 24, 24, 24)
        formulario.setSpacing(14)
        formulario.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        return dialogo, formulario

    def botonesActualizacion(self, dialogo, formulario, guardar):
        botones = QHBoxLayout()
        cancelar = QPushButton("Cancelar")
        cancelar.setObjectName("cancelar_accion")
        cancelar.clicked.connect(dialogo.reject)
        enviar = QPushButton("Guardar cambios")
        enviar.setObjectName("guardarCambios")
        enviar.clicked.connect(guardar)
        botones.addWidget(cancelar)
        botones.addWidget(enviar)
        formulario.addRow(botones)

    def actualizarCliente(self):
        cliente = self.clienteSeleccionado()
        if cliente is None or cliente.get("id") is None:
            QMessageBox.warning(self, "Cliente no seleccionado", "Selecciona un cliente para actualizar sus datos.")
            return
        dialogo, formulario = self.formularioActualizacion("Actualizar cliente")
        campos = {}
        for clave, etiqueta in (
            ("nombre", "Nombre:"), ("cedula", "Cédula:"),
            ("correo", "Correo:"), ("direccion", "Dirección:")
        ):
            campo = QLineEdit(str(cliente.get(clave) or ""))
            campo.setObjectName(clave)
            campos[clave] = campo
            formulario.addRow(etiqueta, campo)
        password = QLineEdit()
        password.setObjectName("password")
        password.setEchoMode(QLineEdit.Password)
        password.setMaxLength(128)
        password.setPlaceholderText("Dejar vacío para conservar la actual")
        formulario.addRow("Nueva contraseña:", password)

        def guardar():
            datos = {clave: campo.text().strip() for clave, campo in campos.items()}
            nueva_password = password.text()
            error = validar_datos_cliente(
                datos["nombre"], datos["cedula"], datos["correo"],
                nueva_password or "********", datos["direccion"]
            ) or validar_cliente_unico(
                [c for c in self.clientes if c.get("id") != cliente["id"]],
                datos["cedula"], datos["correo"]
            )
            if error:
                QMessageBox.warning(dialogo, "Datos inválidos", error)
                return
            if nueva_password:
                datos["password"] = nueva_password
            if all(cliente.get(clave) == valor for clave, valor in datos.items()):
                dialogo.accept()
                return
            try:
                actualizado = actualizar_cliente(
                    int(cliente["id"]), datos["nombre"], datos["cedula"],
                    datos["correo"], datos["direccion"], cliente.get("monto", 0),
                    password=nueva_password or None
                )
            except (MySQLConnectorError, OSError, ValueError, TypeError) as error:
                QMessageBox.critical(dialogo, "Error al actualizar", f"No se pudo guardar el cliente: {error}")
                return
            if not actualizado:
                QMessageBox.warning(dialogo, "Sin actualización", "No se guardaron cambios. Recarga los clientes e inténtalo de nuevo.")
                return
            cliente.update(datos)
            self.clientesBuscar.clear()
            self.buscarCliente()
            for fila in range(self.listaClientes.count()):
                item = self.listaClientes.item(fila)
                if self.clientes[item.data(Qt.ItemDataRole.UserRole)].get("id") == cliente["id"]:
                    self.listaClientes.setCurrentRow(fila)
                    self.mostrarCliente(item)
                    break
            dialogo.accept()
            QMessageBox.information(self, "Cliente actualizado", "Los cambios se guardaron en la base de datos.")

        self.botonesActualizacion(dialogo, formulario, guardar)
        dialogo.exec()

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
        self.listaClientes.setCurrentRow(-1)
        self.tablaPrestamos.setRowCount(0)
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
    QWidget#formCC {
        background-color: #FBFAF6;
    }

    QLineEdit {
        background-color: white;
        color: #102848;
        border: 1px solid #D9D2C2;
        border-radius: 8px;
        padding: 10px 12px;
        font-size: 14px;
        selection-background-color: #E6D3A5;
        selection-color: #102848;
    }

    QLineEdit:hover {
        border-color: #A69D89;
    }

    QLineEdit:focus {
        border-color: #C09848;
    }

    QPushButton#btnEnviar {
        background-color: #183A60;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px;
        font-size: 14px;
        font-weight: bold;
    }

    QPushButton#btnEnviar:hover {
        background-color: #0B1C32;
    }

    QPushButton#btnEnviar:pressed {
        background-color: #0B1C32;
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
                background-color: #FBFAF6;
                color: #102848;
            }

            QDialog#solicitudPrestamo QLabel {
                color: #33465F;
                font-size: 14px;
                font-weight: normal;
            }

            QDialog#solicitudPrestamo QLabel#clienteSolicitud {
                color: #102848;
                font-size: 15px;
                font-weight: bold;
            }

            QDialog#solicitudPrestamo QDoubleSpinBox,
            QDialog#solicitudPrestamo QSpinBox,
            QDialog#solicitudPrestamo QComboBox {
                background-color: white;
                color: #102848;
                border: 1px solid #D9D2C2;
                border-radius: 8px;
                padding: 9px 10px;
                font-size: 14px;
                selection-background-color: #E6D3A5;
                selection-color: #102848;
            }

            QDialog#solicitudPrestamo QDoubleSpinBox:hover,
            QDialog#solicitudPrestamo QSpinBox:hover,
            QDialog#solicitudPrestamo QComboBox:hover {
                border-color: #A69D89;
            }

            QDialog#solicitudPrestamo QDoubleSpinBox:focus,
            QDialog#solicitudPrestamo QSpinBox:focus,
            QDialog#solicitudPrestamo QComboBox:focus {
                border: 1px solid #C09848;
            }

            QDialog#solicitudPrestamo QComboBox QAbstractItemView {
                background-color: white;
                color: #102848;
                selection-background-color: #F4EBD5;
                selection-color: #102848;
                border: 1px solid #D9D2C2;
            }

            QDialog#solicitudPrestamo QLabel#interesSolicitud,
            QDialog#solicitudPrestamo QLabel#totalSolicitud,
            QDialog#solicitudPrestamo QLabel#cuotaSolicitud {
                background-color: white;
                border: 1px solid #D9D2C2;
                border-radius: 8px;
                padding: 9px 10px;
                color: #102848;
                font-size: 14px;
                font-weight: bold;
            }

            QDialog#solicitudPrestamo QLabel#totalSolicitud {
                background-color: #FAF7EF;
                border-color: #E6D3A5;
                color: #0B1C32;
            }

            QDialog#solicitudPrestamo QLabel#avisoSolicitud {
                background-color: #FAF7EF;
                border: 1px solid #E6D3A5;
                border-radius: 8px;
                padding: 10px;
                color: #102848;
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
                background-color: #183A60;
                color: white;
                border: 1px solid #183A60;
            }

            QDialog#solicitudPrestamo QPushButton#btnEnviarSolicitud:hover {
                background-color: #0B1C32;
                border-color: #0B1C32;
            }

            QDialog#solicitudPrestamo QPushButton#btnCancelarSolicitud {
                background-color: white;
                color: #33465F;
                border: 1px solid #D9D2C2;
            }

            QDialog#solicitudPrestamo QPushButton#btnCancelarSolicitud:hover {
                background-color: #F4F1E8;
                border-color: #A69D89;
            }

            QDialog#solicitudPrestamo QPushButton:disabled {
                background-color: #A69D89;
                border-color: #A69D89;
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
        frecuencia_input = QComboBox()
        frecuencia_input.setObjectName("frecuenciaSolicitud")
        frecuencia_input.addItems(["Semanal", "Quincenal", "Mensual"])
        frecuencia_input.setCurrentText("Mensual")
        frecuencia_input.setToolTip("Semanal: cada 7 días. Quincenal: cada 15 días. Mensual: cada mes.")

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
            cuota_label.setText(
                f"C$ {total / plazo_input.value():,.2f} · {frecuencia_input.currentText().lower()}"
            )
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
                    frecuencia_pago=frecuencia_input.currentText(),
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
                f"Frecuencia de pago: {frecuencia_input.currentText()}\n"
                "Estado: Pendiente de aprobación por administración."
            )

        monto_input.valueChanged.connect(actualizar_resumen)
        ingreso_input.valueChanged.connect(actualizar_resumen)
        plazo_input.valueChanged.connect(actualizar_resumen)
        frecuencia_input.currentTextChanged.connect(actualizar_resumen)
        botones.accepted.connect(enviar_solicitud)
        formulario.addRow("Ingreso mensual del cliente:", ingreso_input)
        formulario.addRow("Monto solicitado:", monto_input)
        formulario.addRow("Plazo:", plazo_input)
        formulario.addRow("Frecuencia de pago:", frecuencia_input)
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
