from PySide6.QtWidgets import *
from PySide6.QtGui import QIcon


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

        self.tablaPrestamos.setColumnCount(4)

        self.tablaPrestamos.setHorizontalHeaderLabels([
            "ID",
            "Monto",
            "Plazo",
            "Estado"
        ])

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

        self.tablaPrestamos.horizontalHeader().setStretchLastSection(True)

        self.tablaPrestamos.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )

        layoutFrame.addWidget(self.tablaPrestamos)

        layoutFrame.addStretch()

        # =====================================================
        # BOTONES
        # =====================================================

        botonesLayout = QHBoxLayout()

        self.btnAgendar = QPushButton("Agendar cita")
        #self.btnAgendar.clicked.connect(self.btnAgendar)
        self.btnAgendar.setObjectName("agendar")

        self.btnCerrar = QPushButton("Cerrar Sesión")
        self.btnCerrar.clicked.connect(self.btnCerrSes)
        self.btnCerrar.setObjectName("cerrar")

        botonesLayout.addWidget(self.btnAgendar)
        botonesLayout.addWidget(self.btnCerrar)

        layoutFrame.addLayout(botonesLayout)

        layoutPrincipal.addWidget(frame)

    def btnAgendar(self):
        pass

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