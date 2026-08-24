from PySide6.QtWidgets import *
from PySide6.QtGui import QIcon


class AdminWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setAdmin()

    def setAdmin(self):
        self.setFixedSize(1000, 1000)
        self.setWindowTitle("Panel Administrador")
        self.setWindowIcon(QIcon("img/logoBG.png"))

        layout = QGridLayout()

        layout.addWidget(QLabel("Nombre:"), 0, 0)
        layout.addWidget(QLineEdit(),       0, 1)

        layout.addWidget(QLabel("Correo:"), 1, 0)
        layout.addWidget(QLineEdit(),       1, 1)

        boton = QPushButton("Guardar")
        layout.addWidget(boton, 2, 0, 1, 2)

