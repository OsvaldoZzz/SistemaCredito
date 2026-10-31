import sys
from pathlib import Path

# Permite ejecutar este archivo directamente desde el botón Run del IDE.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.config.rutas import IMAGENES_DIR
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from app.ui.GUI_ADMIN import AdminWindow
from app.ui.GUI_REC import RecepWindow
from app.ui.GUI_CLIENTE import ClienteWindow
from app.ui.GUI_COB import CobWindow
from app.datos.clientes_crud import listar_clientes
from app.logica.validaciones import validar_campos_login


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

        self.clientes = []

        try:
            self.clientes = listar_clientes()
        except Exception as error:
            QMessageBox.warning(
                self,
                "Base de datos no disponible",
                f"No se pudieron cargar los clientes: {error}"
            )

        self.intentosLogIn = 0

    def setUpUi(self):

        self.resize(1200, 700)

        self.setWindowTitle("Sistema Crediticio")
        logo_path = IMAGENES_DIR / "logoBG.png"
        self.setWindowIcon(QIcon(str(logo_path)))

        self.setStyleSheet("""
            QMainWindow {
                background-color: #F4F2EC;
            }    

            #frame1 {
                background-color: white;
                border-radius: 15px;
                border: 2px solid #C09848;
            }

            #logo {
                background-color: transparent;
            }


            QLineEdit {
                background-color: white;
                color: #102848;
                border: 2px solid #33465F;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
            }

            QLineEdit:focus {
                border: 2px solid #C09848;
            }

            QLineEdit, QPushButton {
                min-height: 24px;
            }

            QLineEdit::placeholder {
                color: #65758B;
            }

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

            QPushButton:pressed {
                background-color: #0B1C32;
            }

            QPushButton:hover#IniciarSe{
                background-color: #3F6B36;
            }

            QPushButton:hover#crear{
                background-color: #8A6B2B;
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
        self.input_user.returnPressed.connect(self.iniciarSesion)

        self.input_password = QLineEdit()
        self.input_password.setPlaceholderText("Ingresar contraseña")
        self.input_password.setEchoMode(QLineEdit.Password)
        self.input_password.setMaxLength(12)
        self.input_password.returnPressed.connect(self.iniciarSesion)

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
        if self.intentosLogIn >= 3:
            return
        usuario = self.input_user.text().strip()
        password = self.input_password.text()

        error_validacion = validar_campos_login(usuario, password)
        if error_validacion:
            QMessageBox.warning(
                self,
                "Datos incompletos",
                error_validacion
            )
            return
        
        for rol in self.usuarios:
            if (
                rol["usuario"].strip().casefold() == usuario.casefold()
                and rol["password"] == password
            ):
                self.intentosLogIn = 0
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
            if (
                cliente.get("correo", "").strip().casefold()
                == usuario.casefold()
                and cliente.get("password") == password
            ):
                self.intentosLogIn = 0
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
        

def main():
    app = QApplication(sys.argv)
    window = login()
    window.showMaximized()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
