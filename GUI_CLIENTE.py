from PySide6.QtWidgets import *
from PySide6.QtGui import QIcon


class ClienteWindow(QMainWindow):

    def __init__(self, cliente):
        super().__init__()

        self.cliente = cliente

        self.setWindowTitle("Panel del Cliente")
        self.setWindowIcon(QIcon("img/logoBG.png"))
        self.showMaximized()

        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f6fa;
            }

            QFrame#frameCliente {
                background-color: white;
                border: 1px solid #d1d5db;
                border-radius: 15px;
            }

            QLabel {
                color: #1e293b;
                font-size: 18px;
                font-weight: bold;
            }

            QTableWidget {
                background-color: white;
                border: 1px solid #d1d5db;
                border-radius: 10px;
                color: #1e293b;
                font-size: 15px;
                gridline-color: #e5e7eb;
            }

            QHeaderView::section {
                background-color: #3b82f6;
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
            }

            QPushButton {
                background-color: #00BB77;
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

            QPushButton:hover#solicitud {
                background-color: green;
            }

            QPushButton:hover#abonar {
                background-color: gold;
            }

            QPushButton:hover#cerrar {
                background-color: red;
            }

        """)

        

        central = QWidget()
        self.setCentralWidget(central)

        layoutPrincipal = QVBoxLayout(central)
        layoutPrincipal.setContentsMargins(30, 30, 30, 30)

    
        # FRAME PRINCIPAL

        frame = QFrame()
        frame.setObjectName("frameCliente")

        layoutFrame = QVBoxLayout(frame)
        layoutFrame.setContentsMargins(30, 30, 30, 30)
        layoutFrame.setSpacing(15)


        titulo = QLabel("Panel del Cliente")
        layoutFrame.addWidget(titulo)

        self.lblNombre = QLabel(
            f"Nombre: {self.cliente['nombre']}"
        )

        self.lblCorreo = QLabel(
            f"Correo: {self.cliente['correo']}"
        )

        layoutFrame.addWidget(self.lblNombre)
        layoutFrame.addWidget(self.lblCorreo)



        tituloPrestamo = QLabel("Mi Préstamo")
        layoutFrame.addWidget(tituloPrestamo)


        # TABLA DE PRÉSTAMOS
        

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

        # Ajustar columnas al espacio disponible
        self.tablaPrestamos.horizontalHeader().setStretchLastSection(True)

        self.tablaPrestamos.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )

        layoutFrame.addWidget(self.tablaPrestamos)


        layoutFrame.addStretch()

        botonesLayout = QHBoxLayout()

        self.btnSoli = QPushButton("Solicitar Prestamo")
        self.btnSoli.setObjectName("solicitud")

        self.btnAbonar = QPushButton("Abonar Prestamo")
        self.btnAbonar.setObjectName("abonar")

        self.btnCerrar = QPushButton("Cerrar Sesión")
        self.btnCerrar.setObjectName("cerrar")


        botonesLayout.addWidget(self.btnSoli)
        botonesLayout.addWidget(self.btnAbonar)
        botonesLayout.addWidget(self.btnCerrar)

        layoutFrame.addLayout(botonesLayout)

        layoutPrincipal.addWidget(frame)