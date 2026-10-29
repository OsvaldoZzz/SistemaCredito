from decimal import Decimal

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QHeaderView,
    QAbstractItemView,
)
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt

from app.logica.calculos_prestamo import PORCENTAJE_INTERES
from app.datos.prestamos_crud import listar_cuotas_prestamo


def mostrar_detalle_prestamo(parent, prestamo_id: int) -> None:
    cuotas = listar_cuotas_prestamo(prestamo_id)
    dialogo = QDialog(parent)
    dialogo.setObjectName("detallePrestamo")
    dialogo.setWindowTitle(f"Cuotas del préstamo #{prestamo_id}")
    dialogo.resize(1450, 540)
    layout = QVBoxLayout(dialogo)

    encabezado = QLabel(
        f"Interés normal: {PORCENTAJE_INTERES:.0f}% total. "
        "Mora: 2% mensual prorrateada por día sobre el saldo de cada "
        "cuota vencida; cada abono reduce el saldo desde su fecha y hora."
    )
    encabezado.setObjectName("notaPrestamo")
    layout.addWidget(encabezado)

    tabla = QTableWidget(len(cuotas), 12)
    tabla.setHorizontalHeaderLabels([
        "Cuota",
        "Vencimiento",
        "Capital",
        "Interés",
        "Monto cuota",
        "Abonado",
        "Saldo cuota",
        "Días de mora",
        "Mora pendiente",
        "Total pendiente",
        "Último abono",
        "Estado",
    ])
    tabla.setObjectName("tablaDetallePrestamo")
    tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
    tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
    tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    mora_total = Decimal("0.00")
    total_actualizado = Decimal("0.00")
    capital_total = Decimal("0.00")
    interes_total = Decimal("0.00")
    abonado_total = Decimal("0.00")
    for indice, cuota in enumerate(cuotas):
        mora_total += cuota["mora_pendiente"]
        total_actualizado += cuota["total_pendiente"]
        capital_total += cuota["capital"]
        interes_total += cuota["interes"]
        abonado_total += cuota["pagado"]
        estado = (
            "Pagada"
            if cuota["total_pendiente"] == 0
            else "En mora"
            if cuota["dias_mora"] > 0
            else "Pendiente"
        )
        valores = (
            str(cuota["numero"]),
            cuota["fecha_vencimiento"].strftime("%d/%m/%Y"),
            f"C$ {cuota['capital']:,.2f}",
            f"C$ {cuota['interes']:,.2f}",
            f"C$ {cuota['monto']:,.2f}",
            f"C$ {cuota['pagado']:,.2f}",
            f"C$ {cuota['saldo_cuota']:,.2f}",
            str(cuota["dias_mora"]),
            f"C$ {cuota['mora_pendiente']:,.2f}",
            f"C$ {cuota['total_pendiente']:,.2f}",
            (
                cuota["ultimo_pago"].strftime("%d/%m/%Y %H:%M:%S")
                if cuota["ultimo_pago"] is not None
                else "Sin abonos"
            ),
            estado,
        )
        for columna, valor in enumerate(valores):
            item = QTableWidgetItem(valor)
            if columna == 11:
                item.setData(Qt.ItemDataRole.UserRole, estado)
                item.setBackground(QColor(
                    "#dcfce7" if estado == "Pagada"
                    else "#fee2e2" if estado == "En mora"
                    else "#fef3c7"
                ))
                item.setForeground(QColor(
                    "#31552B" if estado == "Pagada"
                    else "#991b1b" if estado == "En mora"
                    else "#92400e"
                ))
            tabla.setItem(indice, columna, item)
    layout.addWidget(tabla)

    resumen = QLabel(
        f"Capital: C$ {capital_total:,.2f}   |   "
        f"Interés: C$ {interes_total:,.2f}   |   "
        f"Abonado: C$ {abonado_total:,.2f}   |   "
        f"Mora pendiente: C$ {mora_total:,.2f}   |   "
        f"Saldo total hoy: C$ {total_actualizado:,.2f}"
    )
    resumen.setObjectName("resumenPrestamo")
    layout.addWidget(resumen)

    botones = QDialogButtonBox(QDialogButtonBox.Close)
    botones.rejected.connect(dialogo.reject)
    botones.accepted.connect(dialogo.accept)
    layout.addWidget(botones)
    dialogo.exec()


def mostrar_error_detalle_prestamo(parent, error: Exception) -> None:
    QMessageBox.critical(
        parent,
        "Error al mostrar préstamo",
        f"No se pudo cargar el detalle de cuotas: {error}",
    )
