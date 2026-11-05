from PySide6.QtCore import Qt
from PySide6.QtWidgets import QStyledItemDelegate, QTableWidget


class _DelegateTextoCentrado(QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        option.displayAlignment = Qt.AlignmentFlag.AlignCenter


def centrar_tabla(tabla: QTableWidget) -> None:
    tabla.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
    tabla.setItemDelegate(_DelegateTextoCentrado(tabla))
