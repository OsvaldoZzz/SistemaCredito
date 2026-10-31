from mysql.connector import Error as MySQLConnectorError
from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout, QLabel,
    QLineEdit, QMessageBox, QPushButton, QWidget,
)

from app.datos.clientes_crud import actualizar_direccion_cliente
from app.config.rutas import IMAGENES_DIR
from app.ui.mapa_dialogo import elegir_ubicacion


def boton_ubicacion():
    boton = QPushButton()
    boton.setObjectName("btnUbicacion")
    boton.setStyleSheet("""
        QPushButton#btnUbicacion {
            background-color: #F4F2EC;
            border: 1px solid #DDD8CB;
            border-radius: 8px;
            padding: 5px;
        }
        QPushButton#btnUbicacion:hover:enabled:!pressed {
            background-color: #E8E3D7;
            border-color: #C09848;
        }
        QPushButton#btnUbicacion:pressed:enabled {
            background-color: #D9D2C2;
            border-color: #A69D89;
        }
    """)
    boton.setIcon(QIcon(str(IMAGENES_DIR / "ubicacion.svg")))
    boton.setIconSize(QSize(24, 24))
    boton.setFixedSize(44, 44)
    boton.setToolTip("Ver ubicación en el mapa")
    boton.setAccessibleName("Ver ubicación en el mapa")
    return boton


class CampoUbicacion(QWidget):
    def __init__(self, lat=None, lng=None, parent=None, direccion=None):
        super().__init__(parent)
        self.lat, self.lng = lat, lng
        self.direccion = direccion
        if direccion is not None:
            direccion.textChanged.connect(self._direccion_cambiada)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.boton = boton_ubicacion()
        self.boton.clicked.connect(self._abrir)
        self.estado = QLabel()
        self.estado.setWordWrap(True)
        layout.addWidget(self.estado, 1)
        layout.addWidget(self.boton)
        self._refrescar()

    def _abrir(self):
        direccion = self.direccion.text().strip() if self.direccion is not None else ""
        punto = elegir_ubicacion(self.window(), self.lat, self.lng, direccion=direccion)
        if punto is not None:
            self.lat, self.lng = punto
            self._refrescar()

    def _direccion_cambiada(self):
        self.lat, self.lng = None, None
        self._refrescar()

    def _refrescar(self):
        marcada = self.lat is not None and self.lng is not None
        ayuda = "Cambiar ubicación" if marcada else "Buscar dirección en el mapa"
        self.boton.setToolTip(ayuda)
        self.boton.setAccessibleName(ayuda)
        self.estado.setText(
            f"Punto seleccionado ({float(self.lat):.5f}, {float(self.lng):.5f})"
            if marcada else "Ubicación sin marcar (opcional)"
        )


def actualizar_direccion_con_dialogo(parent, cliente):
    dialogo = QDialog(parent)
    dialogo.setWindowTitle("Mi dirección y ubicación")
    dialogo.setMinimumWidth(560)
    formulario = QFormLayout(dialogo)
    direccion = QLineEdit(cliente.get("direccion") or "")
    direccion.setMaxLength(40)
    formulario.addRow("Dirección:", direccion)
    ubicacion = CampoUbicacion(cliente.get("latitud"), cliente.get("longitud"), direccion=direccion)
    formulario.addRow("Ubicación:", ubicacion)
    botones = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
    formulario.addRow(botones)
    botones.rejected.connect(dialogo.reject)

    def guardar():
        try:
            actualizar_direccion_cliente(
                int(cliente["id"]), direccion.text(), ubicacion.lat, ubicacion.lng,
            )
        except (MySQLConnectorError, OSError, ValueError, TypeError) as error:
            QMessageBox.critical(dialogo, "Error al guardar", str(error))
            return
        cliente.update(direccion=direccion.text().strip(),
                       latitud=ubicacion.lat, longitud=ubicacion.lng)
        dialogo.accept()

    botones.accepted.connect(guardar)
    return dialogo.exec() == QDialog.Accepted
