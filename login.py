from PySide6.QtWidgets import *
from PySide6.QtGui import QIcon
import sys

app = QApplication([])


class login(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setUpUi()
        self.usuarios = [
            {"usuario": "Marvin" , "password": "58101169"},
            {"usuario": "Yavar", "password": "84635922"},
            {"usuario": "Celia", "password": "87253629"},
            {"usuario": "Ariel", "password": "89268598"}
        ]

        self.clientes = [
            {"correo": "elhh1985@gmail.com", "password": "Familia1"},
            {"correo": "didi@gmail.com", "password": "Familia2"}
        ]

        self.intentosLogIn = 0

    def setUpUi(self):

        self.setFixedSize(500, 500)

        self.setWindowTitle("Sistema Crediticio")
        self.setWindowIcon(QIcon("img/logoBG.png"))

        self.setStyleSheet("""
            QMainWindow {
                background-color: #121826;
            }

            #frame1 {
                background-color: #1E293B;
                border-radius: 15px;
            }

            #loginTxt {
                color: #F8FAFC;
                font-size: 28px;
                font-weight: bold;
                padding: 10px;
                margin-left: 40px;
            }

            QLineEdit {
                background-color: #0F172A;
                color: #F8FAFC;
                border: 2px solid #334155;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
            }

            QLineEdit:focus {
                border: 2px solid #3B82F6;
            }

            QLineEdit::placeholder {
                color: #64748B;
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

        self.frame1 = QFrame(self)
        self.frame1.setObjectName("frame1")
        self.frame1.setGeometry(50, 70, 400, 330)

        layout = QVBoxLayout(self.frame1)

        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)

        # Título
        self.loginTxt = QLabel("Sistema Crediticio")
        self.loginTxt.setObjectName("loginTxt")

        self.input_user = QLineEdit()
        self.input_user.setPlaceholderText("Ingresar usuario o correo")

        self.input_password = QLineEdit()
        self.input_password.setPlaceholderText("Ingresar contraseña")
        self.input_password.setEchoMode(QLineEdit.Password)
        self.input_password.setMaxLength(8)

        self.btnIni = QPushButton("Iniciar Sesion")
        self.btnIni.clicked.connect(self.iniciarSesion)

        layout.addWidget(self.loginTxt)
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
                QMessageBox(
                    self,
                    "Inicio de Sesion",
                    "Inicio de sesion como administrador exitoso."
                )

        for cliente in self.clientes:
            if cliente["correo"] == correo and cliente["password"] == password:
                QMessageBox.information(
                    self,
                    "Inicio de Sesion",
                    "Inicio de sesion como cliente exitosa."
                )

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


window = login()

window.show()
app.exec()