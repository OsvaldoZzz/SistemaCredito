from decimal import Decimal

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QMessageBox,
)

from app.datos.prestamos_crud import listar_cuotas_prestamo, registrar_abono_cuota


def abrir_dialogo_abono(parent, prestamo_id: int) -> bool:
    cuotas = listar_cuotas_prestamo(prestamo_id)
    cuotas_pendientes = [
        cuota for cuota in cuotas if cuota["total_pendiente"] > 0
    ]
    if not cuotas_pendientes:
        QMessageBox.information(
            parent,
            "Préstamo pagado",
            "Este préstamo no tiene cuotas pendientes.",
        )
        return False

    dialogo = QDialog(parent)
    dialogo.setWindowTitle(f"Registrar abono al préstamo #{prestamo_id}")
    formulario = QFormLayout(dialogo)

    cuota_input = QComboBox()
    for cuota in cuotas_pendientes:
        cuota_input.addItem(
            f"Cuota {cuota['numero']} - vence "
            f"{cuota['fecha_vencimiento'].strftime('%d/%m/%Y')} - "
            f"pendiente C$ {cuota['total_pendiente']:,.2f}",
            cuota["numero"],
        )

    monto_input = QDoubleSpinBox()
    monto_input.setDecimals(2)
    monto_input.setPrefix("C$ ")

    def actualizar_limite():
        cuota = cuotas_pendientes[cuota_input.currentIndex()]
        maximo = float(cuota["total_pendiente"])
        monto_input.setRange(0.01, maximo)
        monto_input.setValue(maximo)

    cuota_input.currentIndexChanged.connect(actualizar_limite)
    actualizar_limite()

    formulario.addRow("Cuota:", cuota_input)
    formulario.addRow("Monto del abono:", monto_input)
    formulario.addRow(QLabel(
        "El abono se aplica primero a la mora acumulada y luego al saldo "
        "de la cuota. La fecha y hora se guardan automáticamente."
    ))
    botones = QDialogButtonBox(
        QDialogButtonBox.Save | QDialogButtonBox.Cancel
    )
    botones.accepted.connect(dialogo.accept)
    botones.rejected.connect(dialogo.reject)
    formulario.addRow(botones)

    if dialogo.exec() != QDialog.Accepted:
        return False

    numero_cuota = int(cuota_input.currentData())
    monto = Decimal(str(monto_input.value()))
    pago = registrar_abono_cuota(prestamo_id, numero_cuota, monto)
    QMessageBox.information(
        parent,
        "Abono registrado",
        f"Se registró un abono de C$ {monto:,.2f} a la cuota "
        f"{numero_cuota}.\nFecha y hora: "
        f"{pago['fecha_pago'].strftime('%d/%m/%Y %H:%M:%S')}.",
    )
    return True
