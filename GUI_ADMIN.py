from PySide6.QtWidgets import *
from PySide6.QtGui import QIcon


class AdminWindow(QMainWindow):
    def __init__(self, clientes):
        super().__init__()
        self.clientes = clientes
        self.setAdmin()

    def setAdmin(self):
        self.showMaximized()
        self.setWindowTitle("Panel Administrador")
        self.setWindowIcon(QIcon("img/logoBG.png"))

        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f6fa;
            }

            QLabel {
                color: #1e293b;
                font-size: 18px;
                font-weight: bold;
            }

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

            QWidget#panelPrestamos {
                background-color: white;
                border: 1px solid #d1d5db;
                border-radius: 10px;
            }

            /* CAMBIO: estilo para el panel izquierdo */
            QWidget#panelClientes {
                background-color: white;
                border: 1px solid #d1d5db;
                border-radius: 10px;
            }

            QPushButton {
                background-color: #3b82f6;
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

            QPushButton#crear_cliente{
                background-color: green;
            }

            QPushButton#eliminar_cliente{
                background-color: red;
            }

            QPushButton#crear_prestamo{
                background-color: green;
            }

            QPushButton#abonar_prestamo{
                background-color: yellow;
            }

            QPushButton#eliminar_prestamo{
                background-color: red;
            }

        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QGridLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # LADO IZQUIERDO - CLIENTES
        # CAMBIO: ahora creamos un panel propio para los clientes
        panelClientes = QWidget()
        panelClientes.setObjectName("panelClientes")

        # CAMBIO: layout propio para el panel izquierdo
        clientesLayout = QVBoxLayout(panelClientes)

        clientesTitulo = QLabel("Clientes")
        clientesLayout.addWidget(clientesTitulo)

        self.listaClientes = QListWidget()

        # Cuando seleccionemos un cliente, mostramos sus datos
        self.listaClientes.itemClicked.connect(self.mostrarCliente)

        for cliente in self.clientes:
            self.listaClientes.addItem(cliente["nombre"])

        clientesLayout.addWidget(self.listaClientes)

        # CAMBIO: botones del panel izquierdo
        self.btnCreate = QPushButton("Crear Cliente")
        self.btnCreate.setObjectName("crear_cliente")

        self.btnDelete = QPushButton("Eliminar Cliente")
        self.btnDelete.setObjectName("eliminar_cliente")

        self.btnCreate.clicked.connect(self.btnsCreate)

        # CAMBIO: los botones se agregan al layout del panel izquierdo
        # y NO al layout principal
        clientesLayout.addWidget(self.btnCreate)
        clientesLayout.addWidget(self.btnDelete)

        # CAMBIO: agregamos el panel completo al Grid
        layout.addWidget(panelClientes, 0, 0)

        
        # LADO DERECHO - PRÉSTAMOS
        panelPrestamos = QWidget()
        panelPrestamos.setObjectName("panelPrestamos")

        prestamosLayout = QVBoxLayout(panelPrestamos)

        prestamosTitulo = QLabel("Préstamos del cliente")
        prestamosLayout.addWidget(prestamosTitulo)

        # Datos del cliente seleccionado
        self.lblCliente = QLabel("Seleccione un cliente")
        self.lblCorreo = QLabel("Correo: -")

        prestamosLayout.addWidget(self.lblCliente)
        prestamosLayout.addWidget(self.lblCorreo)

        # CAMBIO: tabla para los préstamos
        # Todavía no tiene datos, solamente la estructura
        self.tablaPrestamos = QTableWidget()

        self.tablaPrestamos.setColumnCount(4)
        self.tablaPrestamos.setHorizontalHeaderLabels([
            "ID",
            "Monto",
            "Plazo",
            "Estado"
        ])

        prestamosLayout.addWidget(self.tablaPrestamos)

        # CAMBIO: espacio que empuja el botón hacia abajo
        prestamosLayout.addStretch()

        # Botón para crear préstamo
        self.btnCreatePrestamo = QPushButton("Crear Prestamo")
        self.btnCreatePrestamo.setObjectName("crear_prestamo")


        self.btnAbonarPrestamo = QPushButton("Abonar")
        self.btnAbonarPrestamo.setObjectName("abonar_prestamo")

        self.btnEliminarPrestamo = QPushButton("Eliminar Prestamo") 
        self.btnEliminarPrestamo.setObjectName("eliminar_prestamo")


        prestamosLayout.addWidget(self.btnCreatePrestamo)
        prestamosLayout.addWidget(self.btnAbonarPrestamo)
        prestamosLayout.addWidget(self.btnEliminarPrestamo)

        # CAMBIO: agregamos el panel derecho al Grid
        layout.addWidget(panelPrestamos, 0, 1)

        # TAMAÑO DE LAS COLUMNAS
        # CAMBIO: la izquierda ocupa 1 parte
        # y la derecha 3 partes
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 3)

        # CAMBIO: las dos zonas ocupan toda la altura disponible
        layout.setRowStretch(0, 1)

    # ==============================================================
    # MOSTRAR INFORMACIÓN DEL CLIENTE
    # ==============================================================

    def mostrarCliente(self, item):

        nombre = item.text()

        for cliente in self.clientes:

            if cliente["nombre"] == nombre:

                self.lblCliente.setText(
                    f"Cliente: {cliente['nombre']}"
                )

                self.lblCorreo.setText(
                    f"Correo: {cliente['correo']}"
                )

                return

    # ==============================================================
    # BOTÓN CREAR CLIENTE
    # ==============================================================

    def btnsCreate(self):

        createCliente = self.btnCreate