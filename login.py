from PySide6.QtWidgets import *
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from GUI_ADMIN import AdminWindow
from GUI_REC import RecepWindow
from GUI_CLIENTE import ClienteWindow
from GUI_COB import CobWindow
from pathlib import Path #
import sys


class login(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setUpUi()
        self.usuarios = [
            {"id":"1001","rol": "administrador","usuario": "Marvin" , "password": "12345678"},
            {"id":"1002","rol": "administrador","usuario": "Yavar", "password": "84635922"},
            {"id":"1003","rol": "administrador","usuario": "Celia", "password": "87253629"},
            {"id":"1004","rol": "administrador","usuario": "Ariel", "password": "89268598"},
            {"id":"1005","rol": "recepcionista","usuario": "recepcionista1", "password": "12345678"},
            {"id":"1006","rol": "recepcionista","usuario": "recepcionista2", "password": "12345678"},
            {"id":"1007","rol": "cobrador","usuario": "cobrador1", "password": "12345678"},
            {"id":"1008","rol": "cobrador","usuario": "cobrador2", "password": "12345678"},
        ]

        self.clientes = [
            {"nombre": "Cliente 1", "cedula" : "2811234561000A", "correo": "ejemplo2@gmail.com", "password": "87654321", "direccion": "Iglesia San Isidro 1/2 cuadra bajo", "monto" : "1000"},
            {"nombre": "Cliente 2", "cedula" : "2811234561007W", "correo": "ejemplo@gmail.com", "password": "12345678", "direccion": "Iglesia San Isidro 2 cuadra bajo", "monto": "20000"}
        ]

        self.intentosLogIn = 0

    def setUpUi(self):

        self.resize(1200, 700)

        self.setWindowTitle("Sistema Crediticio")
        logo_path = Path(__file__).resolve().parent / "img" / "logoBG.png"
        self.setWindowIcon(QIcon(str(logo_path)))

        self.setStyleSheet("""
            QMainWindow {
                background-color: #F5F5F5;
            }    

            #frame1 {
                background-color: #D3D3D3;
                border-radius: 15px;
                border: 3px solid #000;
                px solid #000000;
            }

            #logo {
                background-color: transparent;
            }


            QLineEdit {
                background-color: #D3D3D3;
                color: #000;
                border: 2px solid #334155;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
            }

            QLineEdit:focus {
                border: 2px solid #3B82F6;
            }

            QLineEdit, QPushButton {
                min-height: 24px;
            }

            QLineEdit::placeholder {
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
                background-color: #2563EB;
            }

            QPushButton:pressed {
                background-color: #1D4ED8;
            }

            QPushButton:hover#IniciarSe{
                background-color: green;
            }

            QPushButton:hover#crear{
                background-color: gold;
            }


        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        outer_layout = QGridLayout(central_widget)
        outer_layout.setContentsMargins(30, 30, 30, 30)

        self.frame1 = QFrame()
        self.frame1.setObjectName("frame1")
        self.frame1.setFixedWidth(440)
        outer_layout.addWidget(self.frame1, 0, 0, Qt.AlignCenter)

        layout = QVBoxLayout(self.frame1)

        layout.setContentsMargins(40, 32, 40, 40)
        layout.setSpacing(18)

        # Título
        self.logo = QLabel()
        self.logo.setObjectName("logo")
        self.logo.setAlignment(Qt.AlignCenter)
        self.logo.setPixmap(
            QPixmap(str(logo_path)).scaled(
                320, 175, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
        )

        self.input_user = QLineEdit()
        self.input_user.setPlaceholderText("Ingresar usuario o correo")

        self.input_password = QLineEdit()
        self.input_password.setPlaceholderText("Ingresar contraseña")
        self.input_password.setEchoMode(QLineEdit.Password)
        self.input_password.setMaxLength(8)

        botones_layout = QHBoxLayout() #Para poner los botones lado a lado.


        self.btnIni = QPushButton("Iniciar Sesion")
        self.btnIni.clicked.connect(self.iniciarSesion)
        self.btnIni.setObjectName("IniciarSe")



        layout.addWidget(self.logo)
        layout.addWidget(self.input_user)
        layout.addWidget(self.input_password)
        botones_layout.addWidget(self.btnIni)
        layout.addLayout(botones_layout)

    def iniciarSesion(self):
        usuario = self.input_user.text()
        password = self.input_password.text()
        correo = self.input_user.text()
        print(f"Correo user ingresado: {correo}, Contraseña ingresada: {password}")

        if len(password) != 8:
            QMessageBox.warning(
                self,
                "Error",
                "La contraseña debe tener 8 caracteres maximo."
            )
            return
        
        for rol in self.usuarios:
            if rol["usuario"] == usuario and rol["password"] == password:
                QMessageBox.information(
                    self,
                    "Inicio de Sesion",
                    "Inicio de sesion como " + rol["rol"] + " exitoso."
                )

                if rol["rol"] == "administrador":
                    self.ventana_admin = AdminWindow(self.clientes, self)
                    self.ventana_admin.show()
                    self.hide()
                elif rol["rol"] == "recepcionista":
                    self.ventana_recep = RecepWindow(self.clientes, self)
                    self.ventana_recep.show()
                    self.hide() #esconde la ventana de login cuando se abre un nuevo panel
                elif rol["rol"] == "cobrador":
                    self.ventana_cob = CobWindow(self.clientes, self)
                    self.ventana_cob.show()
                    self.hide()
            

                #self.close()
                
                return

        for cliente in self.clientes:
            if cliente["correo"] == correo and cliente["password"] == password:
                QMessageBox.information(
                    self,
                    "Inicio de Sesion",
                    "Inicio de sesion como cliente exitosa."
                )

                self.ventana_cliente = ClienteWindow(cliente, ventana_login=self)
                self.ventana_cliente.show()
                self.close()
                return

        

        self.intentosLogIn += 1

        if self.intentosLogIn >= 3:
            QMessageBox.critical(
                self,
                "Cuenta Bloqueada",
                "Has superado el limite de 3 intentos."
            )

            self.btnIni.setEnabled(False)
            self.input_user.setEnabled(False)
            self.input_password.setEnabled(False)
        else:
            restantes = 3 - self.intentosLogIn
            QMessageBox.warning(
                self,
                "Error",
                F"Correo o contraseña incorrecta.\n"
                f"Te quedan {restantes} intentos."
            )
        

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = login()
    window.showMaximized()
    sys.exit(app.exec())
