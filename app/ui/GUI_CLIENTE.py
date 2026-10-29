from app.config.rutas import IMAGENES_DIR
from PySide6.QtWidgets import *
from PySide6.QtCore import QDate, QSize, Qt
from PySide6.QtGui import QIcon
from datetime import date
from mysql.connector import Error as MySQLConnectorError
from app.datos.citas_crud import crear_cita
from app.datos.prestamos_crud import listar_prestamos
from app.ui.prestamos_ui import mostrar_detalle_prestamo, mostrar_error_detalle_prestamo


class ClienteWindow(QMainWindow):

    def __init__(self, cliente, ventana_login):
        super().__init__()

        self.cliente = cliente
        self.ventana_login = ventana_login

        self.setWindowTitle("Panel del Cliente")
        self.setWindowIcon(QIcon(str(IMAGENES_DIR / "logoBG.png")))
        self.showMaximized()

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

            /* FRAME PRINCIPAL */

            QFrame#frameCliente {
                background-color: white;
                border: 1px solid #DDD8CB;
                border-radius: 10px;
            }

            /* TITULOS */

            QLabel {
                color: #102848;
                font-size: 18px;
                font-weight: bold;
            }

            QLabel#lblNombre {
                color: #102848;
                font-size: 18px;
                font-weight: bold;
            }

            QLabel#lblCorreo {
                color: #65758B;
                font-size: 14px;
                font-weight: normal;
            }

            QLabel#tituloPrestamo {
                color: #102848;
                font-size: 20px;
                font-weight: bold;
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

            QTableWidget#tablaPrestamos::item:selected {
                background-color: #F4EBD5;
                color: #102848;
            }

            QWidget#panelAcciones { background-color: white; }

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

            QPushButton#acciones:pressed {
                background-color: #E8E3D7;
                border-color: #A69D89;
            }

            QDialog#detallePrestamo { background-color: #FBFAF6; }
            QLabel#notaPrestamo, QLabel#resumenPrestamo {
                background-color: #FAF7EF;
                color: #102848;
                border: 1px solid #E6D3A5;
                border-radius: 8px;
                padding: 10px;
                font-size: 13px;
                font-weight: normal;
            }
            QLabel#avisoPrestamos {
                color: #65758B;
                font-size: 13px;
                font-weight: normal;
            }
            QTableWidget#tablaDetallePrestamo { font-size: 13px; }
            QPushButton:disabled { background-color: #D9D2C2; color: #65758B; }

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

            QPushButton:hover {
                background-color: #183A60;
            }

            QPushButton#agendar {
                background-color: #3F6B36;
                color: white;
                border: 1px solid #3F6B36;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }

            QPushButton#agendar:hover {
                background-color: #3F6B36;
                border-color: #31552B;
            }

            QPushButton#agendar:pressed {
                background-color: #31552B;
                border-color: #294724;
            }

            QPushButton#agendar:focus {
                border: 2px solid #C8DDBF;
                padding: 9px 19px;
            }

            QPushButton#agendar:disabled {
                background-color: #E8E3D7;
                color: #65758B;
                border-color: #D9D2C2;
            }

            QPushButton:hover#cerrarSesion {
                background-color: red;
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

        central = QWidget()
        self.setCentralWidget(central)

        layoutPrincipal = QVBoxLayout(central)
        layoutPrincipal.setContentsMargins(20, 20, 20, 20)
        layoutPrincipal.setSpacing(20)

        # =====================================================
        # ENCABEZADO
        # =====================================================

        encabezado = QWidget()
        encabezado.setObjectName("encabezado")

        encabezadoLayout = QHBoxLayout(encabezado)
        encabezadoLayout.setContentsMargins(20, 12, 20, 12)

        tituloPanel = QLabel("PANEL DEL CLIENTE")
        tituloPanel.setObjectName("tituloPanel")

        infoUsuario = QLabel(self.cliente["nombre"])
        infoUsuario.setObjectName("infoUsuario")

        encabezadoLayout.addWidget(tituloPanel)
        encabezadoLayout.addStretch()
        encabezadoLayout.addWidget(infoUsuario)

        layoutPrincipal.addWidget(encabezado)

        # =====================================================
        # FRAME PRINCIPAL
        # =====================================================

        frame = QFrame()
        frame.setObjectName("frameCliente")

        layoutFrame = QVBoxLayout(frame)
        layoutFrame.setContentsMargins(20, 20, 20, 20)
        layoutFrame.setSpacing(15)

        # INFORMACION DEL CLIENTE

        titulo = QLabel("Información del cliente")
        layoutFrame.addWidget(titulo)

        self.lblNombre = QLabel(
            f"Nombre: {self.cliente['nombre']}"
        )
        self.lblNombre.setObjectName("lblNombre")

        self.lblCorreo = QLabel(
            f"Correo: {self.cliente['correo']}"
        )
        self.lblCorreo.setObjectName("lblCorreo")

        layoutFrame.addWidget(self.lblNombre)
        layoutFrame.addWidget(self.lblCorreo)

        # PRESTAMO

        tituloPrestamo = QLabel("Mis préstamos")
        tituloPrestamo.setObjectName("tituloPrestamo")

        layoutFrame.addWidget(tituloPrestamo)

        # =====================================================
        # TABLA DE PRÉSTAMOS
        # =====================================================

        self.tablaPrestamos = QTableWidget()
        self.tablaPrestamos.setObjectName("tablaPrestamos")
        self.tablaPrestamos.setWordWrap(False)

        self.tablaPrestamos.setColumnCount(8)
        self.tablaPrestamos.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tablaPrestamos.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )
        self.tablaPrestamos.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )

        self.tablaPrestamos.setHorizontalHeaderLabels([
            "Préstamo",
            "Monto inicial",
            "Saldo pendiente",
            "Frecuencia",
            "Próximo vencimiento",
            "Cuotas pendientes",
            "Estado",
            "Acciones"
        ])

        self.tablaPrestamos.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )
        self.tablaPrestamos.horizontalHeader().setMinimumSectionSize(110)
        for columna in (0, 4, 5, 6, 7):
            self.tablaPrestamos.horizontalHeader().setSectionResizeMode(
                columna, QHeaderView.ResizeToContents
            )

        layoutFrame.addWidget(self.tablaPrestamos, 1)
        self.avisoPrestamos = QLabel()
        self.avisoPrestamos.setObjectName("avisoPrestamos")
        self.avisoPrestamos.setWordWrap(True)
        layoutFrame.addWidget(self.avisoPrestamos)
        self.cargarPrestamos()

        # =====================================================
        # BOTONES
        # =====================================================

        botonesLayout = QHBoxLayout()

        self.btnAgendar = QPushButton("Agendar cita")
        self.btnAgendar.clicked.connect(self.abrirDialogoAgendarCita)
        self.btnAgendar.setObjectName("agendar")
        self.btnAgendar.setCursor(Qt.CursorShape.PointingHandCursor)

        self.btnCerrar = QPushButton("Cerrar Sesión")
        self.btnCerrar.clicked.connect(self.btnCerrSes)
        self.btnCerrar.setObjectName("cerrarSesion")

        botonesLayout.addWidget(self.btnAgendar)
        botonesLayout.addWidget(self.btnCerrar)

        layoutFrame.addLayout(botonesLayout)

        layoutPrincipal.addWidget(frame)

    def abrirDialogoAgendarCita(self):
        dialogo = QDialog(self)
        dialogo.setWindowTitle("Agendar cita")
        dialogo.resize(360, 140)

        formLayoutAC = QFormLayout(dialogo)
        fecha_edit = QDateEdit()
        fecha_edit.setCalendarPopup(True)
        fecha_edit.setDate(QDate.currentDate())
        fecha_edit.setMinimumDate(QDate.currentDate())
        fecha_edit.setDisplayFormat("dd/MM/yyyy")
        formLayoutAC.addRow("Fecha:", fecha_edit)

        botones = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        botones.accepted.connect(dialogo.accept)
        botones.rejected.connect(dialogo.reject)
        formLayoutAC.addRow(botones)

        if dialogo.exec() == QDialog.Accepted:
            cliente_id = self.cliente.get("id")
            if cliente_id is None:
                QMessageBox.critical(
                    self,
                    "Error al agendar cita",
                    "No se pudo identificar al cliente."
                )
                return

            fecha = date.fromisoformat(
                fecha_edit.date().toString("yyyy-MM-dd")
            )
            try:
                cita_id = crear_cita(int(cliente_id), fecha)
            except (MySQLConnectorError, OSError, ValueError, TypeError) as error:
                QMessageBox.critical(
                    self,
                    "Error al agendar cita",
                    f"No se pudo guardar la cita: {error}"
                )
                return

            QMessageBox.information(
                self,
                "Cita agendada",
                f"La cita #{cita_id} quedo agendada para "
                f"{fecha.strftime('%d/%m/%Y')}."
            )

    def cargarPrestamos(self):
        fila_actual = self.tablaPrestamos.currentRow()
        item_actual = self.tablaPrestamos.item(fila_actual, 0)
        prestamo_actual = item_actual.data(Qt.ItemDataRole.UserRole) if item_actual else None
        cliente_id = self.cliente.get("id")
        if cliente_id is None:
            QMessageBox.critical(
                self,
                "Error al cargar préstamos",
                "No se pudo identificar al cliente."
            )
            return

        try:
            prestamos = listar_prestamos(int(cliente_id))
        except (MySQLConnectorError, OSError, ValueError, TypeError) as error:
            QMessageBox.critical(
                self,
                "Error al cargar préstamos",
                f"No se pudieron cargar los préstamos: {error}"
            )
            return

        self.tablaPrestamos.setRowCount(0)
        for prestamo in prestamos:
            fila = self.tablaPrestamos.rowCount()
            self.tablaPrestamos.insertRow(fila)
            valores = (
                str(prestamo["id"]),
                f"C$ {float(prestamo['monto']):,.2f}",
                f"C$ {prestamo['saldo_pendiente']:,.2f}",
                prestamo["frecuencia_pago"],
                (
                    prestamo["proximo_vencimiento"].strftime("%d/%m/%Y")
                    if prestamo["proximo_vencimiento"] else "Sin cuotas pendientes"
                ),
                f"{prestamo['cuotas_pendientes']} cuotas",
                prestamo["estado_actual"],
            )
            for columna, valor in enumerate(valores):
                item = QTableWidgetItem(valor)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tablaPrestamos.setItem(fila, columna, item)
            self.tablaPrestamos.item(fila, 0).setData(
                Qt.ItemDataRole.UserRole, prestamo["id"]
            )
            acciones = QWidget()
            acciones.setObjectName("panelAcciones")
            layout_acciones = QHBoxLayout(acciones)
            layout_acciones.setContentsMargins(4, 2, 4, 2)
            layout_acciones.setAlignment(Qt.AlignmentFlag.AlignCenter)
            ver = QPushButton()
            ver.setObjectName("acciones")
            ver.setFixedSize(34, 34)
            ver.setIcon(QIcon(str(IMAGENES_DIR / "ver.png")))
            ver.setIconSize(QSize(25, 25))
            ver.setToolTip("Ver cuotas, pagos y mora")
            ver.setAccessibleName(f"Ver cuotas del préstamo {prestamo['id']}")
            ver.clicked.connect(
                lambda checked=False, prestamo_id=prestamo["id"]: self.verCuotas(prestamo_id)
            )
            layout_acciones.addWidget(ver)
            self.tablaPrestamos.setCellWidget(fila, 7, acciones)
            self.tablaPrestamos.setRowHeight(fila, 42)
            if prestamo["id"] == prestamo_actual:
                self.tablaPrestamos.setCurrentCell(fila, 0)
        self.avisoPrestamos.setText(
            "El saldo pendiente incluye la mora acumulada a la fecha. "
            "Si hay cuotas vencidas, se muestra la fecha de la más antigua pendiente de pago."
            if prestamos else "Aún no tienes préstamos registrados."
        )

    def verCuotas(self, prestamo_id):
        try:
            mostrar_detalle_prestamo(self, int(prestamo_id))
        except (MySQLConnectorError, OSError, ValueError, TypeError) as error:
            mostrar_error_detalle_prestamo(self, error)

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
