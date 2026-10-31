from app.config.rutas import IMAGENES_DIR
from datetime import date
from PySide6.QtWidgets import *
from PySide6.QtGui import QIcon
from PySide6.QtCore import QDate, QSize, Qt
from PySide6.QtWidgets import QHeaderView
from mysql.connector import Error as MySQLConnectorError
from app.reportes.reportes_pdf import generar_estado_cartera, generar_reporte_cobranza
from app.datos.clientes_crud import actualizar_cliente, crear_cliente, eliminar_cliente, listar_clientes
from app.datos.prestamos_crud import (
    actualizar_prestamo,
    crear_prestamo,
    eliminar_prestamo,
    listar_prestamos,
    listar_todos_los_prestamos,
)
from app.ui.pagos_ui import abrir_dialogo_abono
from app.ui.prestamos_ui import mostrar_detalle_prestamo, mostrar_error_detalle_prestamo
from app.ui.estilos_botones_panel import ESTILOS_BOTONES_PANEL
from app.datos.solicitudes_crud import (
    listar_solicitudes_pendientes,
    resolver_solicitud_prestamo,
)
from app.logica.validaciones import validar_cliente_unico, validar_datos_cliente, validar_datos_rol
from app.logica.calculos_prestamo import (
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
        self.setWindowIcon(QIcon(str(IMAGENES_DIR / "logoBG.png")))

        self.setStyleSheet("""
            QMainWindow {
                background-color: #F6F5F1;
            }

            QDialog#accionesAdmin, QDialog#eliminarRol, QDialog#asignarClientesRol {
                background-color: #FBFAF6;
            }

            QDialog#eliminarRol QLabel {
                color: #33465F;
                font-size: 14px;
                font-weight: normal;
            }

            QDialog#eliminarRol QComboBox {
                background-color: white;
                color: #102848;
                border: 1px solid #D9D2C2;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                min-height: 24px;
            }

            QDialog#eliminarRol QComboBox:focus {
                border-color: #C09848;
            }

            QDialog#eliminarRol QComboBox QAbstractItemView {
                background-color: white;
                color: #102848;
                selection-background-color: #F4EBD5;
                selection-color: #102848;
                border: 1px solid #D9D2C2;
            }

            QPushButton#crear_rol:hover {
                background-color: #3F6B36;
            }

            QPushButton#eliminar_rol {
                background-color: #dc2626;
            }

            QPushButton#eliminar_rol:hover {
                background-color: #b91c1c;
            }

            QPushButton#actualizar_clientes:hover,
            QPushButton#actualizar_roles:hover {
                background-color: #3F6B36;
            }

            QPushButton#cancelar_accion {
                background-color: white;
                color: #33465F;
                border: 1px solid #D9D2C2;
            }

            QPushButton#cancelar_accion:hover {
                background-color: #E8E3D7;
                border-color: #A69D89;
            }

            QPushButton:disabled {
                background-color: #D9D2C2;
                color: #65758B;
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

            QLineEdit#lineaEdit{
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

            /* LISTA DE CLIENTES */

            QListWidget {
                outline: none;
                background-color: white;
                border: 1px solid #DDD8CB;
                border-radius: 10px;
                padding: 8px;
                color: #102848;
                font-size: 15px;
            }

            QListWidget::item {
                border: none;
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

            /* Tarjeta de informacion del rol */
            QWidget#tarjetaInfoRol {
                background-color: #FAF7EF;
                border: 1px solid #F4EBD5;
                border-radius: 14px;
            }
            QLabel#tituloInfoRol {
                color: #102848; font-size: 14px; font-weight: bold;
            }
            QLabel#nombreInfoRol {
                color: #102848; font-size: 26px; font-weight: bold;
            }
            QLabel#tipoInfoRol {
                color: #183A60; background-color: #F4EBD5;
                border: none; border-radius: 10px; padding: 6px 12px;
                font-size: 13px; font-weight: bold;
            }
            QLabel#idInfoRol {
                color: #65758B; font-size: 13px; font-weight: normal;
            }
            QLabel#ayudaInfoRol {
                color: #65758B; font-size: 14px; font-weight: normal;
            }
            QLabel#totalClientesRol, QLabel#tituloPrestamosCliente {
                color: #102848; font-size: 18px; font-weight: bold;
            }
            QLabel#sinClientesRol {
                color: #65758B; background-color: #FBFAF6;
                border-radius: 10px; padding: 14px;
                font-size: 14px; font-weight: normal;
            }
            QPushButton#asignar_clientes {
                background-color: #102848; color: white;
                border-radius: 10px; padding: 12px 18px; font-size: 14px;
            }
            QPushButton#asignar_clientes:hover { background-color: #183A60; }
            QPushButton#asignar_clientes:pressed { background-color: #0B1C32; }
            QPushButton#asignar_clientes:disabled {
                background-color: #E8E3D7; color: #65758B;
            }
            QTabWidget::pane {
                border: none;
                background-color: white;
            }

            QTabBar {
                border: none;
                background-color: transparent;
            }

            QTabBar::tab {
                background-color: #F4EBD5;
                color: #102848;
                border: none;
                padding: 10px 18px;
                margin-right: 4px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }

            QTabBar::tab:selected {
                background-color: #102848;
                color: white;
            }

            QTabBar::tab:hover:!selected {
                background-color: #E6D3A5;
                color: #102848;
            }

            /* PANELES */

            QWidget#panelPrestamos {
                background-color: white;
                border: 1px solid #DDD8CB;
                border-radius: 10px;
            }

            QWidget#panelRol {
                background-color: white;
                border: 1px solid #DDD8CB;
                border-radius: 10px;
            }

            QWidget#panelClientes {
                background-color: white;
                border: 1px solid #DDD8CB;
                border-radius: 10px;
            }

            /* INFORMACION DEL CLIENTE */

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

            QWidget#panelAcciones {
                background-color: white;
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

            QPushButton#acciones[tipoAccion="editar"]:hover {
                background-color: #fef3c7;
                border-color: #fbbf24;
            }

            QPushButton#acciones[tipoAccion="eliminar"]:hover {
                background-color: #fee2e2;
                border-color: #f87171;
            }

            QPushButton#acciones:pressed {
                background-color: #E8E3D7;
                border-color: #A69D89;
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

            QPushButton:hover {
                background-color: #183A60;
            }

            QPushButton#btnAcciones {
                background-color: #102848;
                color: white;
                border-radius: 8px;
                padding: 10px 16px;
                font-weight: bold;
            }

            QPushButton#btnAcciones:hover {
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

            QPushButton#crear_cliente {
                background-color: green;
            }

            QPushButton:hover#eliminar_cliente {
                background-color: red;
            }

            QPushButton:hover#cerrarSesion {
                background-color: red;
            }

            QPushButton:hover#crear_prestamo {
                background-color: #3F6B36;
            }

            QPushButton:hover#abonar_prestamo {
                background-color: #8A6B2B;
            }

            QPushButton:hover#verSoli_prestamo {
                background-color: #8A6B2B;
            }

            QPushButton:hover#reporte_pdf {
                background-color: #8A6B2B;
            }

            QPushButton:hover#eliminar_prestamo {
                background-color: red;
            }

            QPushButton:hover#editar_prestamo {
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

        tituloPanel = QLabel("PANEL ADMINISTRADOR")
        tituloPanel.setObjectName("tituloPanel")

        infoUsuario = QLabel(self.usuario)
        infoUsuario.setObjectName("infoUsuario")

        encabezadoLayout.addWidget(tituloPanel)
        encabezadoLayout.addStretch()
        encabezadoLayout.addWidget(infoUsuario)

        layout.addWidget(encabezado, 0, 0, 1, 2)

        # =====================================================
        # LADO IZQUIERDO - CLIENTES / COBRADORES / RECEPCIONISTAS
        # =====================================================



        panelClientes = QWidget()
        panelClientes.setObjectName("panelClientes")
        panelClientes.setMinimumWidth(420)

        clientesLayout = QVBoxLayout(panelClientes)

        clientesTitulo = QLabel("Usuarios")
        clientesLayout.addWidget(clientesTitulo)

        self.tabs = QTabWidget()
        paginaClientes = QWidget()
        paginaClientesLayout = QVBoxLayout(paginaClientes)
        paginaClientesLayout.setContentsMargins(0, 0, 0, 0)

        #============================
            #Buscar clientes.
        #============================
        self.buscarCl = QHBoxLayout()

        self.clientesBuscar = QLineEdit()
        self.clientesBuscar.setPlaceholderText("Ingresar cedula a buscar...")
        self.clientesBuscar.setObjectName("lineaEdit")


        self.btnBuscar = QPushButton()
        self.btnBuscar.setObjectName("btnBuscar")
        self.btnBuscar.setIcon(QIcon(str(IMAGENES_DIR / "lupa.png")))
        self.btnBuscar.setIconSize(QSize(24, 24))
        self.btnBuscar.clicked.connect(self.buscarCliente)

        #corregir para que aparezca en la parte de al lado de cliente, y darle qss al boton buscar
        self.buscarCl.addWidget(self.clientesBuscar)
        self.buscarCl.addWidget(self.btnBuscar)

        paginaClientesLayout.addLayout(self.buscarCl)

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

        paginaClientesLayout.addWidget(self.listaClientes)

        self.listaCobradores = QListWidget()
        self.listaRecep = QListWidget()
        self.tabs.addTab(paginaClientes, "Clientes")
        self.tabs.addTab(self.listaCobradores, "Cobradores")
        self.tabs.addTab(self.listaRecep, "Recepcionistas")
        self.actualizarListasRoles()
        clientesLayout.addWidget(self.tabs)

        botonesLayout = QHBoxLayout()

        self.btnAcciones = QPushButton("Acciones")
        self.btnAcciones.setObjectName("btnAcciones")
        self.btnAcciones.clicked.connect(self.accionesAdmin)

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
        self.panelPrestamos = panelPrestamos

        prestamosLayout = QVBoxLayout(panelPrestamos)

        botonesLayout2 = QHBoxLayout()

        prestamosTitulo = QLabel("Préstamos del cliente")
        prestamosTitulo.setObjectName("tituloPrestamosCliente")
        prestamosLayout.addWidget(prestamosTitulo)

        self.lblCliente = QLabel("Seleccione un cliente")
        self.lblCliente.setObjectName("lblCliente")

        self.lblCorreo = QLabel("Correo: -")
        self.lblCorreo.setObjectName("lblCorreo")

        self.lblDir = QLabel("Direccion: -")
        self.lblDir.setObjectName("lblDir")


        for etiqueta in (self.lblCliente, self.lblCorreo, self.lblDir):
            etiqueta.setTextFormat(Qt.TextFormat.PlainText)
            etiqueta.setWordWrap(True)
            prestamosLayout.addWidget(etiqueta)

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
            "Cuotas pendientes",
            "Estado",
            "Acciones"
        ])

        self.tablaPrestamos.setObjectName("tablaPrestamos")
        self.tablaPrestamos.setAlternatingRowColors(True)
        self.tablaPrestamos.setShowGrid(False)
        self.tablaPrestamos.verticalHeader().setVisible(False)
        self.tablaPrestamos.verticalHeader().setDefaultSectionSize(48)

        self.tablaPrestamos.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )
        self.tablaPrestamos.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeToContents
        )
        self.tablaPrestamos.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.ResizeToContents
        )
        self.tablaPrestamos.horizontalHeader().setSectionResizeMode(
            6, QHeaderView.ResizeToContents
        )


        prestamosLayout.addWidget(self.tablaPrestamos, 1)

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
        self.crearPanelRol()
        layout.addWidget(self.panelRol, 1, 1)

        # PROPORCIONES

        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 3)

        layout.setRowStretch(0, 0)
        layout.setRowStretch(1, 1)

        self.tabs.currentChanged.connect(self.cambioPestana)
        self.listaCobradores.currentItemChanged.connect(self.mostrarRol)
        self.listaRecep.currentItemChanged.connect(self.mostrarRol)
        self.cambioPestana(self.tabs.currentIndex())

        if self.listaClientes.count() > 0:
            self.listaClientes.setCurrentRow(0)
            self.mostrarCliente(self.listaClientes.currentItem())

    def cambioPestana(self, indice):
        self.panelPrestamos.setVisible(indice == 0)
        self.panelRol.setVisible(indice != 0)
        self.mostrarRol()

    def rolActual(self):
        return {1: "cobrador", 2: "recepcionista"}.get(self.tabs.currentIndex())

    def usuarioRolSeleccionado(self):
        rol = self.rolActual()
        if rol is None:
            return None
        lista = self.listaCobradores if rol == "cobrador" else self.listaRecep
        item = lista.currentItem()
        if item is None:
            return None
        return next((u for u in getattr(self.ventana_login, "usuarios", [])
                     if u["id"] == item.data(Qt.ItemDataRole.UserRole) and u["rol"] == rol), None)

    def crearPanelRol(self):
        self.panelRol = QWidget()
        self.panelRol.setObjectName("panelRol")
        contenido = QVBoxLayout(self.panelRol)
        contenido.setContentsMargins(24, 24, 24, 24)
        contenido.setSpacing(18)
        tarjeta = QWidget()
        tarjeta.setObjectName("tarjetaInfoRol")
        tarjetaLayout = QVBoxLayout(tarjeta)
        tarjetaLayout.setContentsMargins(24, 22, 24, 22)
        tarjetaLayout.setSpacing(12)
        self.tituloRol = QLabel()
        self.tituloRol.setObjectName("tituloInfoRol")
        self.lblNombreRol = QLabel()
        self.lblNombreRol.setObjectName("nombreInfoRol")
        self.lblTipoRol = QLabel()
        self.lblTipoRol.setObjectName("tipoInfoRol")
        self.lblIdRol = QLabel()
        self.lblIdRol.setObjectName("idInfoRol")
        for etiqueta in (self.tituloRol, self.lblNombreRol, self.lblTipoRol, self.lblIdRol):
            etiqueta.setTextFormat(Qt.TextFormat.PlainText)
            etiqueta.setWordWrap(True)
        tarjetaLayout.addWidget(self.tituloRol)
        tarjetaLayout.addWidget(self.lblNombreRol)
        metadatos = QHBoxLayout()
        metadatos.setSpacing(14)
        metadatos.addWidget(self.lblTipoRol)
        metadatos.addWidget(self.lblIdRol)
        metadatos.addStretch()
        tarjetaLayout.addLayout(metadatos)
        contenido.addWidget(tarjeta)

        encabezadoClientes = QHBoxLayout()
        self.lblTotalAsignados = QLabel("Clientes asignados: 0")
        self.lblTotalAsignados.setObjectName("totalClientesRol")
        self.btnAsignarClientes = QPushButton("Asignar clientes")
        self.btnAsignarClientes.setObjectName("asignar_clientes")
        self.btnAsignarClientes.clicked.connect(self.asignarClientesRol)
        encabezadoClientes.addWidget(self.lblTotalAsignados)
        encabezadoClientes.addStretch()
        encabezadoClientes.addWidget(self.btnAsignarClientes)
        contenido.addLayout(encabezadoClientes)

        self.tablaClientesRol = QTableWidget(0, 4)
        self.tablaClientesRol.setObjectName("tablaClientesRol")
        self.tablaClientesRol.setHorizontalHeaderLabels(["Nombre", "Cédula", "Correo", "Dirección"])
        self.tablaClientesRol.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tablaClientesRol.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tablaClientesRol.setAlternatingRowColors(True)
        self.tablaClientesRol.setShowGrid(False)
        self.tablaClientesRol.verticalHeader().setDefaultSectionSize(48)
        self.tablaClientesRol.verticalHeader().setVisible(False)
        self.tablaClientesRol.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        contenido.addWidget(self.tablaClientesRol, 1)
        self.lblSinAsignados = QLabel()
        self.lblSinAsignados.setObjectName("sinClientesRol")
        self.lblSinAsignados.setWordWrap(True)
        contenido.addWidget(self.lblSinAsignados)

    def mostrarRol(self, *_):
        rol = self.rolActual()
        if rol is None:
            return
        usuario = self.usuarioRolSeleccionado()
        self.tituloRol.setText(f"Datos del {rol}")
        self.lblNombreRol.setText(f"Usuario: {usuario['usuario']}" if usuario else f"Selecciona un {rol} de la lista.")
        self.lblTipoRol.setText(f"Rol: {rol.capitalize()}" if usuario else "")
        self.lblIdRol.setText(f"ID: {usuario['id']}" if usuario else "")
        self.lblTipoRol.setVisible(usuario is not None)
        self.lblIdRol.setVisible(usuario is not None)
        self.mostrarClientesRol(usuario)

    def claveClienteAsignado(self, cliente):
        if cliente.get("id") is not None:
            return f"id:{cliente['id']}"
        # El prototipo también admite clientes sin ID de base de datos.
        from uuid import uuid4
        return "local:" + cliente.setdefault("_id_asignacion", uuid4().hex)

    def mostrarClientesRol(self, usuario):
        rol = self.rolActual()
        if rol == "recepcionista":
            self.tablaClientesRol.setColumnCount(4)
            self.tablaClientesRol.setHorizontalHeaderLabels(
                ["Nombre", "Cédula", "Correo", "Dirección"]
            )
            clientes = self.clientes
        else:
            asignados = set(usuario.get("clientes_asignados", [])) if usuario else set()
            self.tablaClientesRol.setColumnCount(4)
            self.tablaClientesRol.setHorizontalHeaderLabels([
                "Nombre", "Cédula", "Correo", "Dirección"
            ])
            clientes = [
                cliente
                for cliente in self.clientes
                if self.claveClienteAsignado(cliente) in asignados
            ]

        self.tablaClientesRol.setRowCount(len(clientes))
        for fila, cliente in enumerate(clientes):
            for columna, clave in enumerate(("nombre", "cedula", "correo", "direccion")):
                item = QTableWidgetItem(str(cliente.get(clave) or ""))
                item.setToolTip(item.text())
                self.tablaClientesRol.setItem(fila, columna, item)
        etiqueta_total = (
            "Clientes disponibles para recepcionistas"
            if rol == "recepcionista" else "Clientes asignados"
        )
        self.lblTotalAsignados.setText(f"{etiqueta_total}: {len(clientes)}")
        self.btnAsignarClientes.setVisible(rol != "recepcionista")
        self.btnAsignarClientes.setEnabled(usuario is not None)
        self.lblSinAsignados.setText(
            (
                "No hay clientes registrados."
                if rol == "recepcionista" else
                "Selecciona un usuario para ver sus clientes."
                if usuario is None else
                "No hay clientes asignados. Usa Asignar clientes para agregarlos."
            )
        )
        self.lblSinAsignados.setVisible(not clientes)

    def asignarClientesRol(self):
        usuario = self.usuarioRolSeleccionado()
        if usuario is None or self.rolActual() == "recepcionista":
            return
        dialogo = QDialog(self)
        dialogo.setObjectName("asignarClientesRol")
        dialogo.setWindowTitle(f"Asignar clientes a {usuario['usuario']}")
        dialogo.resize(600, 440)
        layout = QVBoxLayout(dialogo)
        ayuda = QLabel("Marca los clientes que atiende este usuario. Desmarca para quitar una asignación.")
        ayuda.setWordWrap(True)
        layout.addWidget(ayuda)
        lista = QListWidget()
        lista.setObjectName("clientesAsignables")
        asignados = set(usuario.get("clientes_asignados", []))
        for cliente in self.clientes:
            clave = self.claveClienteAsignado(cliente)
            item = QListWidgetItem(f"{cliente['nombre']} — {cliente['cedula']}")
            item.setData(Qt.ItemDataRole.UserRole, clave)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if clave in asignados else Qt.CheckState.Unchecked)
            lista.addItem(item)
        layout.addWidget(lista, 1)
        if not self.clientes:
            layout.addWidget(QLabel("No hay clientes registrados. Créalos en la pestaña Clientes."))
        botones = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        botones.button(QDialogButtonBox.Save).setText("Guardar asignación")
        botones.button(QDialogButtonBox.Cancel).setText("Cancelar")
        botones.accepted.connect(dialogo.accept)
        botones.rejected.connect(dialogo.reject)
        layout.addWidget(botones)
        if dialogo.exec() == QDialog.Accepted:
            usuario["clientes_asignados"] = [
                lista.item(fila).data(Qt.ItemDataRole.UserRole)
                for fila in range(lista.count())
                if lista.item(fila).checkState() == Qt.CheckState.Checked
            ]
            self.mostrarRol()

    def actualizarListasRoles(self):
        for rol, lista in (
            ("cobrador", self.listaCobradores),
            ("recepcionista", self.listaRecep),
        ):
            seleccionado = lista.currentItem()
            usuario_id = seleccionado.data(Qt.ItemDataRole.UserRole) if seleccionado else None
            lista.blockSignals(True)
            lista.clear()
            for usuario in getattr(self.ventana_login, "usuarios", []):
                if usuario["rol"] == rol:
                    item = QListWidgetItem(usuario["usuario"])
                    item.setData(Qt.ItemDataRole.UserRole, usuario["id"])
                    lista.addItem(item)
                    if usuario["id"] == usuario_id:
                        lista.setCurrentItem(item)
            if lista.currentItem() is None and lista.count():
                lista.setCurrentRow(0)
            lista.blockSignals(False)
        if hasattr(self, "panelRol"):
            self.mostrarRol()

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
        if hasattr(self, "btnCreatePrestamo"):
            self.btnCreatePrestamo.setEnabled(False)
            self.btnCreatePrestamo.setToolTip(
                "Selecciona un cliente para revisar sus préstamos."
            )
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

        tiene_pendiente = any(
            prestamo["saldo_pendiente"] > 0
            for prestamo in prestamos
        )
        if hasattr(self, "btnCreatePrestamo"):
            self.btnCreatePrestamo.setEnabled(not tiene_pendiente)
            self.btnCreatePrestamo.setToolTip(
                "Debe liquidar su préstamo actual antes de crear otro."
                if tiene_pendiente
                else "Crear un préstamo para el cliente seleccionado."
            )

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
                f"{prestamo['cuotas_pendientes']} cuotas",
                str(prestamo["estado"]),
            )
            for columna, valor in enumerate(valores):
                self.tablaPrestamos.setItem(
                    fila,
                    columna,
                    QTableWidgetItem(valor)
                )
            self.tablaPrestamos.item(fila, 0).setData(
                Qt.ItemDataRole.UserRole,
                prestamo["fecha_primer_pago"].isoformat(),
            )
            self.tablaPrestamos.item(fila, 4).setData(
                Qt.ItemDataRole.UserRole + 1,
                prestamo["plazo"],
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
        rol = self.rolActual()
        usuario = self.usuarioRolSeleccionado()
        entidad = rol or "cliente"
        dialogo = QDialog(self)
        dialogo.setObjectName("accionesAdmin")
        dialogo.setWindowTitle(f"Acciones de {entidad}")
        dialogo.setMinimumWidth(360)
        layout = QVBoxLayout(dialogo)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)
        seleccionado = usuario is not None if rol else self.clienteSeleccionado() is not None
        if rol:
            opciones = [
                (f"Crear {rol}", "crear_rol", lambda: self.crearRol(rol), True),
                (f"Editar {rol}", "actualizar_roles", lambda: self.actualizarRol(rol, usuario["id"]), seleccionado),
                (f"Eliminar {rol}", "eliminar_rol", lambda: self.eliminarRol(rol, usuario["id"]), seleccionado),
            ]
        else:
            opciones = [
                ("Crear cliente", "crear_cliente", self.crearCl, True),
                ("Editar cliente", "actualizar_clientes", self.actualizarCliente, seleccionado),
                ("Eliminar cliente", "eliminar_cliente", self.eliminarCliente, seleccionado),
                ("Recargar clientes", "recargar_clientes", self.actualizarDatos, True),
            ]
        accion = []

        def elegir(funcion):
            accion.append(funcion)
            dialogo.accept()

        for texto, identificador, funcion, habilitado in opciones:
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
                selection-background-color: #F4EBD5;
                selection-color: #102848;
            }
            QLineEdit:hover, QComboBox:hover { border-color: #A69D89; }
            QLineEdit:focus, QComboBox:focus {
                border-color: #C09848;
            }
            QComboBox QAbstractItemView {
                background-color: white; color: #102848;
                selection-background-color: #F4EBD5;
                selection-color: #102848;
            }
            QPushButton {
                background-color: #102848; color: white;
                border: none; border-radius: 8px; padding: 10px;
                font-size: 14px; font-weight: bold;
            }
            QPushButton:hover:enabled:!pressed {
                background-color: #285580;
            }
            QPushButton:pressed:enabled {
                background-color: #0B1C32;
            }
            QPushButton#cancelar_accion {
                background-color: white; color: #33465F;
                border: 1px solid #D9D2C2;
            }
            QPushButton#cancelar_accion:hover:enabled:!pressed {
                background-color: #E8E3D7;
                border-color: #A69D89;
            }
            QPushButton#guardarCambios:hover:enabled:!pressed {
                background-color: #78B85B;
                color: #102848;
            }
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
        password.setMaxLength(12)
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
            self.cliente_cedula = None
            self.prestamos_por_cliente.pop(cliente["cedula"], None)
            cliente.update(datos)
            self.prestamos_por_cliente[cliente["cedula"]] = []
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

    def actualizarRol(self, rol_filtro=None, usuario_id=None):
        usuarios = self.ventana_login.usuarios
        candidatos = [u for u in usuarios
                      if (rol_filtro is None or u["rol"] == rol_filtro)
                      and (usuario_id is None or u["id"] == usuario_id)]
        if not candidatos:
            QMessageBox.information(self, "Sin usuarios", "No hay usuarios con rol para actualizar.")
            return
        dialogo, formulario = self.formularioActualizacion(
            f"Editar {rol_filtro}" if rol_filtro else "Actualizar rol de usuario")
        selector = QComboBox()
        selector.setObjectName("usuarioActualizarRol")
        for usuario in candidatos:
            selector.addItem(f"{usuario['usuario']} — {usuario['rol']}", usuario["id"])
        nombre = QLineEdit()
        nombre.setObjectName("usuario")
        nombre.setMaxLength(100)
        rol = QComboBox()
        rol.setObjectName("rol")
        rol.addItems(["administrador", "recepcionista", "cobrador"])
        password = QLineEdit()
        password.setObjectName("password")
        password.setEchoMode(QLineEdit.Password)
        password.setMaxLength(12)
        password.setPlaceholderText("Dejar vacío para conservar la actual")
        if usuario_id is None:
            formulario.addRow("Seleccionar usuario:", selector)
        formulario.addRow("Usuario:", nombre)
        formulario.addRow("Rol:", rol)
        formulario.addRow("Nueva contraseña:", password)
        aviso = QLabel("Los cambios de usuarios con rol duran hasta reiniciar la aplicación.")
        aviso.setWordWrap(True)
        formulario.addRow(aviso)

        def usuario_actual():
            return next((u for u in usuarios if u["id"] == selector.currentData()), None)

        def cargar():
            usuario = usuario_actual()
            if usuario is not None:
                nombre.setText(usuario["usuario"])
                rol.setCurrentText(usuario["rol"])
                password.clear()
                rol.setEnabled(rol_filtro is None and usuario["usuario"].strip().casefold() != self.usuario.strip().casefold())

        def guardar():
            usuario = usuario_actual()
            if usuario is None:
                return
            nuevo_nombre = nombre.text().strip()
            nuevo_rol = rol.currentText()
            nueva_password = password.text()
            error = validar_datos_rol(
                nuevo_nombre, nueva_password or usuario["password"], nuevo_rol,
                usuarios, excluir_id=usuario["id"]
            )
            if usuario["rol"] == "administrador" and nuevo_rol != "administrador" and sum(u["rol"] == "administrador" for u in usuarios) <= 1:
                error = "Debe permanecer al menos un administrador."
            es_actual = usuario["usuario"].strip().casefold() == self.usuario.strip().casefold()
            if es_actual and nuevo_rol != usuario["rol"]:
                error = "No puedes cambiar el rol de tu sesión activa."
            if error:
                QMessageBox.warning(dialogo, "Datos inválidos", error)
                return
            usuario.update(usuario=nuevo_nombre, rol=nuevo_rol)
            self.actualizarListasRoles()
            if nueva_password:
                usuario["password"] = nueva_password
            if es_actual:
                self.usuario = nuevo_nombre
                self.ventana_login.input_user.setText(nuevo_nombre)
                self.findChild(QLabel, "infoUsuario").setText(nuevo_nombre)
            dialogo.accept()
            QMessageBox.information(self, "Rol actualizado", "Los cambios están disponibles durante esta sesión.")

        selector.currentIndexChanged.connect(cargar)
        cargar()
        self.botonesActualizacion(dialogo, formulario, guardar)
        dialogo.exec()

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

        QMessageBox.information(
            self,
            "Datos actualizados",
            "Se actualizó la lista de clientes desde la base de datos."
        )

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
    QWidget#formCC {
        background-color: #FBFAF6;
    }

    QLabel {
        color: #102848;
    }

    QLineEdit {
        background-color: white;
        color: #102848;
        border: 1px solid #D9D2C2;
        border-radius: 8px;
        padding: 10px 12px;
        font-size: 14px;
        selection-background-color: #F4EBD5;
        selection-color: #102848;
    }

    QLineEdit:hover {
        border-color: #A69D89;
    }

    QLineEdit:focus {
        border-color: #C09848;
    }

    QPushButton#btnEnviar {
        background-color: #102848;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px;
        font-size: 14px;
        font-weight: bold;
    }

    QPushButton#btnEnviar:hover:enabled:!pressed {
        background-color: #285580;
    }

    QPushButton#btnEnviar:pressed:enabled {
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
        self.infoPassword.setMaxLength(12)

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
        self.prestamos_por_cliente[self.newCl["cedula"]] = (
            []
        )

        self.buscarCliente()

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

    def crearRol(self, rol=None):
        layoutCC = QWidget()

        layoutCC.setWindowTitle(f"Crear {rol}" if rol else "Crear Rol")
        layoutCC.resize(300, 200)

        layoutCC.setObjectName("formCC")

        layoutCC.setStyleSheet("""
    QWidget#formCC {
        background-color: #FBFAF6;
    }

    QLabel {
        color: #102848;
    }

    QLineEdit {
        background-color: white;
        color: #102848;
        border: 1px solid #D9D2C2;
        border-radius: 8px;
        padding: 10px 12px;
        font-size: 14px;
        selection-background-color: #F4EBD5;
        selection-color: #102848;
    }

    QLineEdit:hover {
        border-color: #A69D89;
    }

    QLineEdit:focus {
        border-color: #C09848;
    }

    QPushButton#btnEnviar {
        background-color: #102848;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px;
        font-size: 14px;
        font-weight: bold;
    }

    QPushButton#btnEnviar:hover:enabled:!pressed {
        background-color: #285580;
    }

    QPushButton#btnEnviar:pressed:enabled {
        background-color: #0B1C32;
    }
""")

        form_layout = QFormLayout(layoutCC)

        self.infoRol = QComboBox()
        self.infoRol.addItems(
            ["recepcionista", "cobrador"]
        )
        if rol is not None:
            self.infoRol.setCurrentText(rol)
            self.infoRol.setEnabled(False)

        self.infoName = QLineEdit("")
        self.infoName.setPlaceholderText("Ingresa el nombre de usuario...")
        self.infoName.setMaxLength(100)

        self.infoPassword = QLineEdit("")
        self.infoPassword.setPlaceholderText(
            "Ingresa tu contraseña..."
        )
        self.infoPassword.setEchoMode(QLineEdit.Password)
        self.infoPassword.setMaxLength(12)

        self.btnEnviar = QPushButton("Enviar")
        self.btnEnviar.setObjectName("btnEnviar")

        etiqueta_rol = QLabel("Rol:")
        etiqueta_nombre = QLabel("Nombre de usuario:")
        etiqueta_password = QLabel("Contraseña:")
        form_layout.addRow(etiqueta_rol, self.infoRol)
        form_layout.addRow(etiqueta_nombre, self.infoName)
        form_layout.addRow(etiqueta_password, self.infoPassword)
        form_layout.addRow(self.btnEnviar)

        nombre_rol, password_rol, selector_rol = self.infoName, self.infoPassword, self.infoRol

        def guardar_rol():
            usuarios = self.ventana_login.usuarios
            nombre = nombre_rol.text().strip()
            password = password_rol.text()
            rol = selector_rol.currentText()
            error = validar_datos_rol(nombre, password, rol, usuarios)
            if error:
                QMessageBox.warning(layoutCC, "Datos inválidos", error)
                return
            nuevo_id = str(max((int(u["id"]) for u in usuarios), default=1000) + 1)
            usuarios.append(dict(id=nuevo_id, usuario=nombre, password=password, rol=rol))
            self.actualizarListasRoles()
            layoutCC.close()
            QMessageBox.information(
                self, "Rol creado", "El usuario puede iniciar sesión. Los roles se conservan hasta reiniciar la aplicación."
            )

        self.btnEnviar.clicked.connect(guardar_rol)

        layoutCC.show()

        self.ventanaCrear = layoutCC

    def eliminarRol(self, rol=None, usuario_id=None):
        usuarios = self.ventana_login.usuarios
        candidatos = [
            usuario for usuario in usuarios
            if (rol is None or usuario["rol"] == rol)
            and (usuario_id is None or usuario["id"] == usuario_id)
            and usuario["usuario"].strip().casefold() != self.usuario.strip().casefold()
            and (
                usuario["rol"] != "administrador"
                or sum(u["rol"] == "administrador" for u in usuarios) > 1
            )
        ]
        if not candidatos:
            QMessageBox.information(
                self,
                "Sin roles disponibles",
                "No hay usuarios que se puedan eliminar. Se conserva tu cuenta "
                "y al menos un administrador."
            )
            return

        dialogo = QDialog(self)
        dialogo.setObjectName("eliminarRol")
        dialogo.setWindowTitle(f"Eliminar {rol}" if rol else "Eliminar rol de usuario")
        dialogo.setMinimumWidth(460)
        layout = QVBoxLayout(dialogo)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        aviso = QLabel(
            "Selecciona el usuario que deseas eliminar. Perderá el acceso "
            "durante esta sesión; los usuarios se restablecen al reiniciar la aplicación."
        )
        aviso.setWordWrap(True)
        layout.addWidget(aviso)

        selector = QComboBox()
        selector.setObjectName("usuarioEliminarRol")
        for usuario in candidatos:
            selector.addItem(
                f"{usuario['usuario']} — {usuario['rol']}", usuario["id"]
            )
        if usuario_id is None:
            layout.addWidget(selector)
        else:
            nombre = QLabel(f"Usuario: {candidatos[0]['usuario']}")
            nombre.setTextFormat(Qt.TextFormat.PlainText)
            layout.addWidget(nombre)

        botones = QHBoxLayout()
        cancelar = QPushButton("Cancelar")
        cancelar.setObjectName("cancelar_accion")
        cancelar.clicked.connect(dialogo.reject)
        eliminar = QPushButton("Eliminar rol")
        eliminar.setObjectName("eliminar_rol")
        eliminar.setAutoDefault(False)
        botones.addWidget(cancelar)
        botones.addWidget(eliminar)
        layout.addLayout(botones)

        def confirmar_eliminacion():
            usuario = next(
                (u for u in usuarios if u["id"] == selector.currentData()), None
            )
            if usuario is None:
                return
            if usuario["usuario"].strip().casefold() == self.usuario.strip().casefold():
                return
            if usuario["rol"] == "administrador" and sum(
                u["rol"] == "administrador" for u in usuarios
            ) <= 1:
                QMessageBox.warning(
                    dialogo, "Administrador requerido",
                    "Debe permanecer al menos un administrador."
                )
                return
            respuesta = QMessageBox.question(
                dialogo,
                "Confirmar eliminación",
                f"¿Eliminar al usuario {usuario['usuario']} con rol {usuario['rol']}?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if respuesta != QMessageBox.Yes:
                return
            usuarios.remove(usuario)
            self.actualizarListasRoles()
            dialogo.accept()
            QMessageBox.information(
                self, "Rol eliminado",
                f"Se eliminó el acceso del usuario {usuario['usuario']} durante esta sesión."
            )

        eliminar.clicked.connect(confirmar_eliminacion)
        dialogo.exec()

    def agregarAccionesPrestamo(self, fila):
        acciones = QWidget()
        acciones.setObjectName("panelAcciones")
        acciones_layout = QHBoxLayout(acciones)
        acciones_layout.setContentsMargins(4, 2, 4, 2)
        acciones_layout.setSpacing(6)
        acciones_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        boton_ver = QPushButton()
        boton_ver.setObjectName("acciones")
        boton_ver.setProperty("tipoAccion", "ver")
        boton_ver.setFixedSize(34, 34)
        boton_ver.setIcon(
            QIcon(str(IMAGENES_DIR / "ver.png"))
        )
        boton_ver.setIconSize(QSize(25, 25))
        boton_ver.setToolTip("Ver préstamo")
        boton_ver.clicked.connect(self.verPrestamoDesdeBoton)

        boton_editar = QPushButton()
        boton_editar.setObjectName("acciones")
        boton_editar.setProperty("tipoAccion", "editar")
        boton_editar.setFixedSize(34, 34)
        boton_editar.setIcon(
            QIcon(str(IMAGENES_DIR / "editar.png"))
        )
        boton_editar.setIconSize(QSize(25, 25))
        boton_editar.setToolTip("Editar préstamo")
        boton_editar.clicked.connect(self.editarPrestamoDesdeBoton)

        boton_eliminar = QPushButton()
        boton_eliminar.setObjectName("acciones")
        ruta_basurita = (
            IMAGENES_DIR / "basurita.png"
        )
        icono_basurita = QIcon(str(ruta_basurita))
        if icono_basurita.isNull():
            icono_basurita = self.style().standardIcon(
                QStyle.StandardPixmap.SP_TrashIcon
            )
        boton_eliminar.setFixedSize(34, 34)
        boton_eliminar.setObjectName("acciones")
        boton_eliminar.setProperty("tipoAccion", "eliminar")
        boton_eliminar.setIcon(icono_basurita)
        boton_eliminar.setIconSize(QSize(25, 25))
        boton_eliminar.setToolTip("Eliminar préstamo")
        boton_eliminar.clicked.connect(self.eliminarPrestamoDesdeBoton)

        acciones_layout.addWidget(boton_ver)
        acciones_layout.addWidget(boton_editar)
        acciones_layout.addWidget(boton_eliminar)
        self.tablaPrestamos.setCellWidget(fila, 6, acciones)

    def filaDeAccion(self, boton):
        contenedor = boton.parentWidget()
        for fila in range(self.tablaPrestamos.rowCount()):
            if self.tablaPrestamos.cellWidget(fila, 6) is contenedor:
                return fila
        return -1

    def verPrestamoDesdeBoton(self):
        fila = self.filaDeAccion(self.sender())
        if fila < 0:
            return

        id_item = self.tablaPrestamos.item(fila, 0)
        if id_item is None:
            return

        try:
            mostrar_detalle_prestamo(self, int(id_item.text()))
        except (MySQLConnectorError, OSError, TypeError, ValueError) as error:
            mostrar_error_detalle_prestamo(self, error)

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
        dialogo.setObjectName("editarPrestamo")
        dialogo.setWindowTitle("Editar prestamo")
        dialogo.setModal(True)
        dialogo.setStyleSheet("""
            QDialog#editarPrestamo {
                background-color: #FBFAF6;
                color: #102848;
            }

            QDialog#editarPrestamo QLabel {
                color: #33465F;
                font-size: 14px;
            }

            QDialog#editarPrestamo QDoubleSpinBox,
            QDialog#editarPrestamo QSpinBox,
            QDialog#editarPrestamo QComboBox {
                background-color: white;
                color: #102848;
                border: 1px solid #D9D2C2;
                border-radius: 8px;
                padding: 9px 10px;
                font-size: 14px;
                selection-background-color: #F4EBD5;
                selection-color: #102848;
            }

            QDialog#editarPrestamo QDoubleSpinBox:hover,
            QDialog#editarPrestamo QSpinBox:hover,
            QDialog#editarPrestamo QComboBox:hover {
                border-color: #A69D89;
            }

            QDialog#editarPrestamo QDoubleSpinBox:focus,
            QDialog#editarPrestamo QSpinBox:focus,
            QDialog#editarPrestamo QComboBox:focus {
                border: 1px solid #C09848;
            }

            QDialog#editarPrestamo QComboBox QAbstractItemView {
                background-color: white;
                color: #102848;
                selection-background-color: #F4EBD5;
                selection-color: #102848;
            }

            QDialog#editarPrestamo QDialogButtonBox QPushButton {
                min-width: 100px;
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 14px;
                font-weight: bold;
            }

            QDialog#editarPrestamo QPushButton#btnGuardarEdicion {
                background-color: #102848;
                color: white;
                border: 1px solid #102848;
            }

            QDialog#editarPrestamo QPushButton#btnGuardarEdicion:hover {
                background-color: #183A60;
                border-color: #183A60;
            }

            QDialog#editarPrestamo QPushButton#btnCancelarEdicion {
                background-color: white;
                color: #33465F;
                border: 1px solid #D9D2C2;
            }

            QDialog#editarPrestamo QPushButton#btnCancelarEdicion:hover {
                background-color: #F4F2EC;
                border-color: #A69D89;
            }
        """)

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
        plazo_original = plazo_item.data(Qt.ItemDataRole.UserRole + 1)
        if plazo_original is None:
            plazo_original = int(
                plazo_item.text().split(" de ", 1)[-1]
                .casefold()
                .replace("cuotas", "")
                .strip()
            )
        plazo_input.setValue(
            int(plazo_original)
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
        guardar = botones.button(QDialogButtonBox.Save)
        guardar.setObjectName("btnGuardarEdicion")
        guardar.setText("Guardar cambios")
        cancelar = botones.button(QDialogButtonBox.Cancel)
        cancelar.setObjectName("btnCancelarEdicion")
        cancelar.setText("Cancelar")
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

        self.cargarPrestamosCliente(self.cliente_cedula)

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
        dialogo.setObjectName("crearPrestamo")
        dialogo.setWindowTitle("Crear prestamo")
        dialogo.setMinimumWidth(500)
        dialogo.setStyleSheet("""
            QDialog#crearPrestamo {
                background-color: #FBFAF6;
                color: #102848;
            }

            QDialog#crearPrestamo QLabel {
                color: #33465F;
                font-size: 14px;
            }

            QDialog#crearPrestamo QDoubleSpinBox,
            QDialog#crearPrestamo QSpinBox,
            QDialog#crearPrestamo QDateEdit {
                background-color: white;
                color: #102848;
                border: 1px solid #D9D2C2;
                border-radius: 8px;
                padding: 9px 10px;
                font-size: 14px;
                selection-background-color: #E6D3A5;
                selection-color: #102848;
            }

            QDialog#crearPrestamo QDoubleSpinBox:hover,
            QDialog#crearPrestamo QSpinBox:hover,
            QDialog#crearPrestamo QDateEdit:hover {
                border-color: #A69D89;
            }

            QDialog#crearPrestamo QDoubleSpinBox:focus,
            QDialog#crearPrestamo QSpinBox:focus,
            QDialog#crearPrestamo QDateEdit:focus {
                border: 1px solid #C09848;
            }

            QDialog#crearPrestamo QLabel#resumenPrestamo,
            QDialog#crearPrestamo QLabel#totalPrestamo {
                background-color: white;
                border: 1px solid #D9D2C2;
                border-radius: 8px;
                padding: 9px 10px;
                color: #102848;
                font-weight: bold;
            }

            QDialog#crearPrestamo QLabel#totalPrestamo {
                background-color: #FAF7EF;
                border: 1px solid #E6D3A5;
                color: #183A60;
                font-size: 15px;
            }

            QDialog#crearPrestamo QLabel#ayudaPrestamo {
                background-color: #FAF7EF;
                border: 1px solid #E6D3A5;
                border-radius: 8px;
                padding: 10px;
                color: #102848;
                font-size: 13px;
            }

            QDialog#crearPrestamo QPushButton {
                min-width: 110px;
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 14px;
                font-weight: bold;
            }

            QDialog#crearPrestamo QPushButton#btnGuardarPrestamo {
                background-color: #102848;
                color: white;
                border: 1px solid #102848;
            }

            QDialog#crearPrestamo QPushButton#btnGuardarPrestamo:hover {
                background-color: #183A60;
                border-color: #183A60;
            }

            QDialog#crearPrestamo QPushButton#btnCancelarPrestamo {
                background-color: white;
                color: #33465F;
                border: 1px solid #D9D2C2;
            }

            QDialog#crearPrestamo QPushButton#btnCancelarPrestamo:hover {
                background-color: #F4F2EC;
                border-color: #A69D89;
            }
        """)
        formulario = QFormLayout(dialogo)
        formulario.setContentsMargins(24, 24, 24, 24)
        formulario.setSpacing(14)
        formulario.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        monto_input = QDoubleSpinBox()
        monto_input.setObjectName("montoPrestamo")
        monto_input.setRange(0.01, 100_000_000)
        monto_input.setDecimals(2)
        monto_input.setPrefix("C$ ")
        monto_input.setGroupSeparatorShown(True)
        interes_preview = QLabel(f"C$ {calcular_interes(monto_input.value()):,.2f}")
        interes_preview.setObjectName("resumenPrestamo")
        total_preview = QLabel(
            f"C$ {calcular_total_prestamo(monto_input.value()):,.2f}"
        )
        total_preview.setObjectName("totalPrestamo")
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
        plazo_input.setObjectName("plazoPrestamo")
        plazo_input.setRange(1, 360)
        plazo_input.setSuffix(" cuotas")
        fecha_primer_pago_input = QDateEdit()
        fecha_primer_pago_input.setObjectName("fechaPrimerPagoPrestamo")
        fecha_primer_pago_input.setCalendarPopup(True)
        fecha_primer_pago_input.setMinimumDate(QDate.currentDate())
        fecha_primer_pago_input.setDate(QDate.currentDate().addMonths(1))
        fecha_primer_pago_input.setDisplayFormat("dd/MM/yyyy")
        ayuda = QLabel(
            "Las próximas cuotas vencerán mensualmente en esta misma fecha."
        )
        ayuda.setObjectName("ayudaPrestamo")
        ayuda.setWordWrap(True)
        botones = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        guardar = botones.button(QDialogButtonBox.Save)
        guardar.setObjectName("btnGuardarPrestamo")
        guardar.setText("Crear préstamo")
        cancelar = botones.button(QDialogButtonBox.Cancel)
        cancelar.setObjectName("btnCancelarPrestamo")
        cancelar.setText("Cancelar")
        botones.accepted.connect(dialogo.accept)
        botones.rejected.connect(dialogo.reject)

        formulario.addRow("Monto:", monto_input)
        formulario.addRow(f"Interés ({PORCENTAJE_INTERES:.0f}%):", interes_preview)
        formulario.addRow("Total a pagar:", total_preview)
        formulario.addRow("Plazo:", plazo_input)
        formulario.addRow("Fecha de la primera cuota:", fecha_primer_pago_input)
        formulario.addRow(ayuda)
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
                fecha_primer_pago=date.fromisoformat(
                    fecha_primer_pago_input.date().toString("yyyy-MM-dd")
                ),
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
            self.cargarPrestamosCliente(self.cliente_cedula)

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
        dialogo.setObjectName("solicitudesPrestamo")
        dialogo.setWindowTitle("Solicitudes de préstamo")
        dialogo.resize(1000, 440)
        dialogo.setStyleSheet("""
            QDialog#solicitudesPrestamo {
                background-color: #FBFAF6;
                color: #102848;
            }

            QDialog#solicitudesPrestamo QLabel {
                color: #33465F;
                font-size: 14px;
            }

            QDialog#solicitudesPrestamo QLabel#fechaPrimeraCuota {
                color: #102848;
                font-weight: bold;
            }

            QDialog#solicitudesPrestamo QDateEdit {
                background-color: white;
                color: #102848;
                border: 1px solid #D9D2C2;
                border-radius: 8px;
                padding: 8px 10px;
                selection-background-color: #E6D3A5;
                selection-color: #102848;
            }

            QDialog#solicitudesPrestamo QDateEdit:hover {
                border-color: #A69D89;
            }

            QDialog#solicitudesPrestamo QDateEdit:focus {
                border: 1px solid #C09848;
            }

            QTableWidget#tablaSolicitudes {
                background-color: white;
                alternate-background-color: #FBFAF6;
                border: 1px solid #D9D2C2;
                border-radius: 8px;
                color: #102848;
                gridline-color: #E8E3D7;
                font-size: 13px;
            }

            QDialog#solicitudesPrestamo QHeaderView::section {
                background-color: #102848;
                color: white;
                padding: 9px;
                border: none;
                font-weight: bold;
            }

            QDialog#solicitudesPrestamo QPushButton {
                min-width: 120px;
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 14px;
                font-weight: bold;
            }

            QDialog#solicitudesPrestamo QPushButton#btnAprobarSolicitud {
                background-color: #102848;
                color: white;
                border: 1px solid #102848;
            }

            QDialog#solicitudesPrestamo QPushButton#btnAprobarSolicitud:hover {
                background-color: #183A60;
                border-color: #183A60;
            }

            QDialog#solicitudesPrestamo QPushButton#btnRechazarSolicitud {
                background-color: #fff1f2;
                color: #be123c;
                border: 1px solid #fecdd3;
            }

            QDialog#solicitudesPrestamo QPushButton#btnRechazarSolicitud:hover {
                background-color: #ffe4e6;
                border-color: #fda4af;
            }

            QDialog#solicitudesPrestamo QPushButton#btnCerrarSolicitudes {
                background-color: white;
                color: #33465F;
                border: 1px solid #D9D2C2;
            }

            QDialog#solicitudesPrestamo QPushButton#btnCerrarSolicitudes:hover {
                background-color: #F4F2EC;
                border-color: #A69D89;
            }
        """)
        layout = QVBoxLayout(dialogo)
        tabla = QTableWidget(len(solicitudes), 10)
        tabla.setObjectName("tablaSolicitudes")
        tabla.setAlternatingRowColors(True)
        tabla.setHorizontalHeaderLabels(
            [
                "ID", "Cliente", "Cédula", "Ingreso mensual", "Monto solicitado",
                "Interés (2%)", "Total", "Plazo", "Frecuencia", "Fecha"
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
                solicitud.get("frecuencia_pago", "Mensual"),
                fecha.strftime("%d/%m/%Y"),
            )
            for columna, valor in enumerate(valores):
                tabla.setItem(fila, columna, QTableWidgetItem(valor))
        layout.addWidget(tabla)

        fecha_primer_pago_input = QDateEdit()
        fecha_primer_pago_input.setCalendarPopup(True)
        fecha_primer_pago_input.setMinimumDate(QDate.currentDate())
        fecha_primer_pago_input.setDate(QDate.currentDate().addMonths(1))
        fecha_primer_pago_input.setDisplayFormat("dd/MM/yyyy")
        fecha_label = QLabel(
            "Fecha de la primera cuota para préstamos aprobados:"
        )
        fecha_label.setObjectName("fechaPrimeraCuota")
        layout.addWidget(fecha_label)
        layout.addWidget(fecha_primer_pago_input)

        botones = QHBoxLayout()
        btn_aprobar = QPushButton("Aprobar y crear préstamo")
        btn_aprobar.setObjectName("btnAprobarSolicitud")
        btn_rechazar = QPushButton("Rechazar")
        btn_rechazar.setObjectName("btnRechazarSolicitud")
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setObjectName("btnCerrarSolicitudes")
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
                    solicitud_id,
                    aprobada,
                    date.fromisoformat(
                        fecha_primer_pago_input.date().toString("yyyy-MM-dd")
                    ) if aprobada else None,
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
