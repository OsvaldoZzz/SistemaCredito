from PySide6.QtWidgets import *
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from GUI_ADMIN import AdminWindow
from GUI_CLIENTE import ClienteWindow
from pathlib import Path #
import sys


class login(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setUpUi()
        self.usuarios = [
            {"usuario": "Marvin" , "password": "12345678"},
            {"usuario": "Yavar", "password": "84635922"},
            {"usuario": "Celia", "password": "87253629"},
            {"usuario": "Ariel", "password": "89268598"}
        ]

        self.clientes = [
            {"nombre": "Cliente 1","correo": "ejemplo2@gmail.com", "password": "87654321", "monto" : "1000"},
            {"nombre": "Cliente 2", "correo": "ejemplo@gmail.com", "password": "12345678", "monto": "20000"}
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

        self.btnIni = QPushButton("Iniciar Sesion")
        self.btnIni.clicked.connect(self.iniciarSesion)

        layout.addWidget(self.logo)
        layout.addWidget(self.input_user)
        layout.addWidget(self.input_password)
        layout.addWidget(self.btnIni)

    def iniciarSesion(self):
        usuario = self.input_user.text()
        password = self.input_password.text()
        correo = self.input_user.text()

        if len(password) != 8:
            QMessageBox.warning(
                self,
                "Error",
                "La contraseña debe tener 8 caracteres maximo."
            )
            return
        
        for admin in self.usuarios:
            if admin["usuario"] == usuario and admin["password"] == password:
                QMessageBox.information(
                    self,
                    "Inicio de Sesion",
                    "Inicio de sesion como administrador exitoso."
                )

                self.ventana_admin = AdminWindow(self.clientes)
                self.ventana_admin.show()
                self.close()
                
                return

        for cliente in self.clientes:
            if cliente["correo"] == correo and cliente["password"] == password:
                QMessageBox.information(
                    self,
                    "Inicio de Sesion",
                    "Inicio de sesion como cliente exitosa."
                )

                self.ventana_cliente = ClienteWindow(cliente)
                self.ventana_cliente.show()
                self.close
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
