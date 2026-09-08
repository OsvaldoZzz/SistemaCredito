from PySide6.QtWidgets import *
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize
from PySide6.QtWidgets import QHeaderView


class AdminWindow(QMainWindow):
    def __init__(self, clientes, ventana_login):
        super().__init__()

        self.clientes = clientes
        self.ventana_login = ventana_login

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
                padding-bottom: 5px;
            }

            QPushButton:hover#acciones{
                background-color: #e8f0fe;
                }

            QPushButton:hover {
                background-color: #2563eb;
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

            QPushButton:hover#eliminar_prestamo {
                background-color: red;
            }

            QPushButton:hover#editar_prestamo {
                background-color: gold;
            }

            QMessageBox {
                background-color: white;
                color: #000;
            }

            QMessageBox QLabel {
                color: #000;
            }

            QMessageBox QPushButton {
                background-color: #3B82F6;
                color: white;
                min-width: 80px;
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

        self.listaClientes = QListWidget()
        self.listaClientes.itemClicked.connect(self.mostrarCliente)

        for cliente in self.clientes:
            self.listaClientes.addItem(cliente["nombre"] + " - " + cliente["cedula"])

        clientesLayout.addWidget(self.listaClientes)

        botonesLayout = QHBoxLayout()

        self.btnCreate = QPushButton("Crear Cliente")
        self.btnCreate.setObjectName("crear_cliente")

        self.btnDelete = QPushButton("Eliminar Cliente")
        self.btnDelete.setObjectName("eliminar_cliente")
        self.btnDelete.clicked.connect(self.eliminarCl)

        self.btnCerrar = QPushButton("Cerrar Sesion")
        self.btnCerrar.setObjectName("cerrarSesion")

        self.btnCreate.clicked.connect(self.crearCl)
        self.btnDelete.clicked.connect(self.eliminarCliente)
        self.btnCerrar.clicked.connect(self.btnCerrSes)

        botonesLayout.addWidget(self.btnCreate)
        botonesLayout.addWidget(self.btnDelete)
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

        self.tablaPrestamos.setColumnCount(5)
        self.tablaPrestamos.setRowCount(2)

        for fila in range(2):
            botonAcc = QPushButton()
            botonAcc.clicked.connect(self.EyD)

            botonAcc.setObjectName("acciones")
            botonAcc.setIcon(QIcon("img/ver.png"))
            botonAcc.setIconSize(QSize(24, 24))
            botonAcc.setToolTip("Editar o eliminar préstamo")
            self.tablaPrestamos.setCellWidget(fila, 4, botonAcc)

        self.tablaPrestamos.setHorizontalHeaderLabels([
            "ID",
            "Monto",
            "Plazo",
            "Estado",
            "Acciones"
        ])

        self.tablaPrestamos.setObjectName("tablaPrestamos")

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

#================================================
        #Prestamo 2
#================================================
        self.tablaPrestamos.setItem(
            1, 0, QTableWidgetItem("002")
        )

        self.tablaPrestamos.setItem(
            1, 1, QTableWidgetItem("C$10,000")
        )

        self.tablaPrestamos.setItem(
            1, 2, QTableWidgetItem("5 cuotas")
        )

        self.tablaPrestamos.setItem(
            1, 3, QTableWidgetItem("Activo")
        )


        self.tablaPrestamos.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )


        prestamosLayout.addWidget(self.tablaPrestamos, 1)

        prestamosLayout.addStretch()

        # BOTONES DE PRÉSTAMO

        self.btnCreatePrestamo = QPushButton("Crear Prestamo")
        self.btnCreatePrestamo.setObjectName("crear_prestamo")

        self.btnVerSolicitudes = QPushButton("Ver Solicitudes")
        self.btnVerSolicitudes.setObjectName("verSoli_prestamo")


        self.btnAbonarPrestamo = QPushButton("Abonar Prestamo")
        self.btnAbonarPrestamo.setObjectName("abonar_prestamo")

        botonesLayout2.addWidget(self.btnCreatePrestamo)
        #botonesLayout2.addWidget(self.btnEditPrestamo)
        botonesLayout2.addWidget(self.btnAbonarPrestamo)
        botonesLayout2.addWidget(self.btnVerSolicitudes)
        #botonesLayout2.addWidget(self.btnEliminarPrestamo)

        prestamosLayout.addLayout(botonesLayout2)

        layout.addWidget(panelPrestamos, 1, 1)

        # PROPORCIONES

        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 3)

        layout.setRowStretch(0, 0)
        layout.setRowStretch(1, 1)

    def mostrarCliente(self, item):
        indice_cliente = self.listaClientes.row(item)
        if indice_cliente < 0 or indice_cliente >= len(self.clientes):
            return

        cliente = self.clientes[indice_cliente]

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

    # Confirma la eliminacion y actualiza la lista de clientes.
    def eliminarCliente(self):
        indice_cliente = self.listaClientes.currentRow()

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

        self.clientes.pop(indice_cliente)
        self.listaClientes.takeItem(indice_cliente)
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
        self.infoName.setMaxLength(10)

        self.infoEmail = QLineEdit("")
        self.infoEmail.setPlaceholderText(
            "Ingresa tu correo electronico..."
        )

        self.infoCedula = QLineEdit("")
        self.infoCedula.setPlaceholderText(
            "Ingresa tu cedula"
        )
        self.infoCedula.setMaxLength(14)

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

        self.newCl = {
            "nombre": self.infoName.text(),
            "cedula": self.infoCedula.text(),
            "correo": self.infoEmail.text(),
            "password": self.infoPassword.text(),
            "direccion": self.infoDir.text()
        }

        self.clientes.append(self.newCl)

        # Actualiza la lista visual inmediatamente
        self.listaClientes.addItem(
            self.newCl["nombre"] + " - " + self.newCl["cedula"]
        )

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


    def EyD(self):
        botonAcc = self.sender()
        fila = next(
            (
                indice
                for indice in range(self.tablaPrestamos.rowCount())
                if self.tablaPrestamos.cellWidget(indice, 4) is botonAcc
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
                self.tablaPrestamos.removeRow(fila)
                QMessageBox.information(
                    self,
                    "Prestamo eliminado",
                    f"El prestamo {id_prestamo} fue eliminado."
                )

    def editarPrestamo(self, fila):
        monto_item = self.tablaPrestamos.item(fila, 1)
        plazo_item = self.tablaPrestamos.item(fila, 2)
        estado_item = self.tablaPrestamos.item(fila, 3)

        if not monto_item or not plazo_item or not estado_item:
            return

        dialogo = QDialog(self)
        dialogo.setWindowTitle("Editar prestamo")
        dialogo.setModal(True)

        formulario = QFormLayout(dialogo)
        formulario.setObjectName("LayoutFEDIT")

        monto_input = QLineEdit(monto_item.text())
        plazo_input = QLineEdit(plazo_item.text())
        estado_input = QComboBox()
        estados = ["Activo", "Pagado", "Vencido"]
        estado_input.addItems(estados)
        if estado_item.text() in estados:
            estado_input.setCurrentText(estado_item.text())

        formulario.addRow("Monto:", monto_input)
        formulario.addRow("Plazo:", plazo_input)
        formulario.addRow("Estado:", estado_input)

        botones = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        botones.accepted.connect(dialogo.accept)
        botones.rejected.connect(dialogo.reject)
        formulario.addRow(botones)

        if dialogo.exec() != QDialog.Accepted:
            return

        monto = monto_input.text().strip()
        plazo = plazo_input.text().strip()
        if not monto or not plazo:
            QMessageBox.warning(
                self,
                "Datos incompletos",
                "El monto y el plazo no pueden quedar vacios."
            )
            return

        monto_item.setText(monto.strip())
        plazo_item.setText(plazo.strip())
        estado_item.setText(estado_input.currentText())

        QMessageBox.information(
            self,
            "Prestamo actualizado",
            "Los datos del prestamo fueron actualizados."
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