from PySide6.QtWidgets import *
from PySide6.QtCore import QDate
from PySide6.QtGui import QIcon
from datetime import date
from mysql.connector import Error as MySQLConnectorError
from citas_crud import crear_cita
from prestamos_crud import listar_prestamos
from calculos_prestamo import (
    PORCENTAJE_INTERES,
    calcular_interes,
    calcular_total_prestamo,
)


class ClienteWindow(QMainWindow):

    def __init__(self, cliente, ventana_login):
        super().__init__()

        self.cliente = cliente
        self.ventana_login = ventana_login

        self.setWindowTitle("Panel del Cliente")
        self.setWindowIcon(QIcon("img/logoBG.png"))
        self.showMaximized()

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

            /* FRAME PRINCIPAL */

            QFrame#frameCliente {
                background-color: white;
                border: 1px solid #d1d5db;
                border-radius: 15px;
            }

            /* TITULOS */

            QLabel {
                color: #1e293b;
                font-size: 18px;
                font-weight: bold;
            }

            QLabel#lblNombre {
                color: #1e293b;
                font-size: 18px;
                font-weight: bold;
            }

            QLabel#lblCorreo {
                color: #64748b;
                font-size: 14px;
                font-weight: normal;
            }

            QLabel#tituloPrestamo {
                color: #1e293b;
                font-size: 20px;
                font-weight: bold;
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

            QPushButton:hover#agendar {
                background-color: green;
            }

            QPushButton:hover#cerrar {
                background-color: red;
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
        layoutFrame.setContentsMargins(30, 30, 30, 30)
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

        tituloPrestamo = QLabel("Mi Préstamo")
        tituloPrestamo.setObjectName("tituloPrestamo")

        layoutFrame.addWidget(tituloPrestamo)

        # =====================================================
        # TABLA DE PRÉSTAMOS
        # =====================================================

        self.tablaPrestamos = QTableWidget()

        self.tablaPrestamos.setColumnCount(6)
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
            "Estado"
        ])

        self.tablaPrestamos.horizontalHeader().setStretchLastSection(True)

        self.tablaPrestamos.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )

        layoutFrame.addWidget(self.tablaPrestamos)
        self.cargarPrestamos()

        layoutFrame.addStretch()

        # =====================================================
        # BOTONES
        # =====================================================

        botonesLayout = QHBoxLayout()

        self.btnAgendar = QPushButton("Agendar cita")
        self.btnAgendar.clicked.connect(self.abrirDialogoAgendarCita)
        self.btnAgendar.setObjectName("agendar")

        self.btnCerrar = QPushButton("Cerrar Sesión")
        self.btnCerrar.clicked.connect(self.btnCerrSes)
        self.btnCerrar.setObjectName("cerrar")

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
        self.tablaPrestamos.setRowCount(0)
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