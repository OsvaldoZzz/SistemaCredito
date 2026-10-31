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
    dialogo.setObjectName("registrarAbono")
    dialogo.setWindowTitle(f"Registrar abono al préstamo #{prestamo_id}")
    dialogo.setStyleSheet("""
        QDialog#registrarAbono {
            background-color: #FBFAF6;
            color: #102848;
        }

        QDialog#registrarAbono QLabel {
            color: #33465F;
            font-size: 14px;
        }

        QDialog#registrarAbono QComboBox,
        QDialog#registrarAbono QDoubleSpinBox {
            background-color: white;
            color: #102848;
            border: 1px solid #D9D2C2;
            border-radius: 8px;
            padding: 9px 10px;
            font-size: 14px;
            selection-background-color: #F4EBD5;
            selection-color: #102848;
        }

        QDialog#registrarAbono QComboBox:hover,
        QDialog#registrarAbono QDoubleSpinBox:hover {
            border-color: #A69D89;
        }

        QDialog#registrarAbono QComboBox:focus,
        QDialog#registrarAbono QDoubleSpinBox:focus {
            border: 1px solid #C09848;
        }

        QDialog#registrarAbono QComboBox QAbstractItemView {
            background-color: white;
            color: #102848;
            selection-background-color: #F4EBD5;
            selection-color: #102848;
        }

        QDialog#registrarAbono QLabel#ayudaAbono {
            background-color: #FAF7EF;
            border: 1px solid #E6D3A5;
            border-radius: 8px;
            padding: 10px;
            color: #102848;
            font-size: 13px;
        }

        QDialog#registrarAbono QDialogButtonBox QPushButton {
            min-width: 100px;
            border-radius: 8px;
            padding: 10px 14px;
            font-size: 14px;
            font-weight: bold;
        }

        QDialog#registrarAbono QPushButton#btnGuardarAbono {
            background-color: #102848;
            color: white;
            border: 1px solid #102848;
        }

        QDialog#registrarAbono QPushButton#btnGuardarAbono:hover {
            background-color: #183A60;
            border-color: #183A60;
        }

        QDialog#registrarAbono QPushButton#btnCancelarAbono {
            background-color: white;
            color: #33465F;
            border: 1px solid #D9D2C2;
        }

        QDialog#registrarAbono QPushButton#btnCancelarAbono:hover {
            background-color: #F4F2EC;
            border-color: #A69D89;
        }
    """)
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
    ayuda = QLabel(
        "El abono se aplica primero a la mora acumulada y luego al saldo "
        "de la cuota. La fecha y hora se guardan automáticamente."
    )
    ayuda.setObjectName("ayudaAbono")
    ayuda.setWordWrap(True)
    formulario.addRow(ayuda)
    botones = QDialogButtonBox(
        QDialogButtonBox.Save | QDialogButtonBox.Cancel
    )
    guardar = botones.button(QDialogButtonBox.Save)
    guardar.setObjectName("btnGuardarAbono")
    guardar.setText("Registrar abono")
    cancelar = botones.button(QDialogButtonBox.Cancel)
    cancelar.setObjectName("btnCancelarAbono")
    cancelar.setText("Cancelar")
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
