import calendar
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, ROUND_DOWN
from app.logica.validaciones import validar_condiciones_prestamo, validar_fecha, validar_monto


TASA_INTERES = Decimal("0.02")
TASA_MORA_MENSUAL = Decimal("0.02")
PORCENTAJE_INTERES = TASA_INTERES * 100
CENTAVO = Decimal("0.01")
FRECUENCIAS_PAGO = ("Semanal", "Quincenal", "Mensual")


def _importe_no_negativo(valor):
    try:
        importe = Decimal(str(valor))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError("El importe debe ser un número válido.") from None
    if not importe.is_finite() or importe < 0:
        raise ValueError("El importe debe ser finito y no negativo.")
    return importe


def calcular_interes(monto: Decimal | int | float | str) -> Decimal:
    principal = validar_monto(monto, permitir_cero=True)
    if not principal.is_finite() or principal < 0:
        raise ValueError("El monto debe ser un número positivo válido.")
    return (principal * TASA_INTERES).quantize(
        CENTAVO,
        rounding=ROUND_HALF_UP,
    )


def calcular_total_prestamo(monto: Decimal | int | float | str) -> Decimal:
    principal = validar_monto(monto, permitir_cero=True).quantize(
        CENTAVO,
        rounding=ROUND_HALF_UP,
    )
    return principal + calcular_interes(principal)


def generar_cuotas(
    monto: Decimal | int | float | str,
    plazo: int,
    fecha_primer_pago: date,
    frecuencia_pago: str = "Mensual",
) -> list[dict[str, Decimal | date | int]]:
    validar_condiciones_prestamo(monto, plazo)
    validar_fecha(fecha_primer_pago, permitir_pasada=True)
    if frecuencia_pago not in FRECUENCIAS_PAGO:
        raise ValueError("La frecuencia debe ser semanal, quincenal o mensual.")

    principal_total = Decimal(str(monto)).quantize(
        CENTAVO,
        rounding=ROUND_HALF_UP,
    )
    interes_total = calcular_interes(principal_total)
    capital_base = (principal_total / plazo).quantize(
        CENTAVO,
        rounding=ROUND_DOWN,
    )
    interes_base = (interes_total / plazo).quantize(
        CENTAVO,
        rounding=ROUND_DOWN,
    )
    cuotas = []

    for numero in range(1, plazo + 1):
        capital = (
            principal_total - capital_base * (plazo - 1)
            if numero == plazo
            else capital_base
        )
        interes = (
            interes_total - interes_base * (plazo - 1)
            if numero == plazo
            else interes_base
        )
        mes = fecha_primer_pago.month - 1 + numero - 1
        anio = fecha_primer_pago.year + mes // 12
        mes = mes % 12 + 1
        dia = min(
            fecha_primer_pago.day,
            calendar.monthrange(anio, mes)[1],
        )
        vencimiento = (
            date(anio, mes, dia)
            if frecuencia_pago == "Mensual"
            else fecha_primer_pago + timedelta(
                days=(numero - 1) * (7 if frecuencia_pago == "Semanal" else 15)
            )
        )
        cuotas.append({
            "numero": numero,
            "fecha_vencimiento": vencimiento,
            "capital": capital,
            "interes": interes,
            "monto": capital + interes,
        })

    return cuotas


def calcular_mora(
    monto_pendiente: Decimal | int | float | str,
    fecha_vencimiento: date,
    fecha_corte: date,
) -> tuple[int, Decimal]:
    validar_fecha(fecha_vencimiento, permitir_pasada=True)
    validar_fecha(fecha_corte, permitir_pasada=True)
    pendiente = _importe_no_negativo(monto_pendiente)
    dias_mora = max((fecha_corte - fecha_vencimiento).days, 0)
    mora = (
        pendiente
        * TASA_MORA_MENSUAL
        * Decimal(dias_mora)
        / Decimal(30)
    ).quantize(CENTAVO, rounding=ROUND_HALF_UP)
    return dias_mora, mora


def calcular_estado_cuota(
    monto_cuota: Decimal | int | float | str,
    fecha_vencimiento: date,
    pagos: list[dict],
    fecha_corte: date,
) -> dict[str, Decimal | int]:
    validar_fecha(fecha_vencimiento, permitir_pasada=True)
    validar_fecha(fecha_corte, permitir_pasada=True)
    saldo_cuota = _importe_no_negativo(monto_cuota).quantize(
        CENTAVO,
        rounding=ROUND_HALF_UP,
    )
    mora_pendiente = Decimal("0.00")
    mora_generada = Decimal("0.00")
    fecha_calculo = fecha_vencimiento

    for pago in sorted(pagos, key=lambda registro: registro["fecha_pago"]):
        fecha_pago = pago["fecha_pago"]
        fecha_pago = (
            fecha_pago.date()
            if isinstance(fecha_pago, datetime)
            else fecha_pago
        )
        validar_fecha(fecha_pago, permitir_pasada=True)
        if fecha_pago > fecha_corte:
            continue

        dias = max((fecha_pago - fecha_calculo).days, 0)
        if saldo_cuota > 0 and dias:
            mora_periodo = (
                saldo_cuota
                * TASA_MORA_MENSUAL
                * Decimal(dias)
                / Decimal(30)
            ).quantize(CENTAVO, rounding=ROUND_HALF_UP)
            mora_pendiente += mora_periodo
            mora_generada += mora_periodo
        fecha_calculo = max(fecha_calculo, fecha_pago)

        monto_pago = _importe_no_negativo(pago["monto"]).quantize(
            CENTAVO,
            rounding=ROUND_HALF_UP,
        )
        aplicado_a_mora = min(monto_pago, mora_pendiente)
        mora_pendiente -= aplicado_a_mora
        monto_pago -= aplicado_a_mora
        saldo_cuota = max(saldo_cuota - monto_pago, Decimal("0.00"))

    dias_mora = (
        max((fecha_corte - fecha_vencimiento).days, 0)
        if saldo_cuota > 0 or mora_pendiente > 0
        else 0
    )
    if saldo_cuota > 0 and fecha_corte > fecha_calculo:
        dias = max((fecha_corte - fecha_calculo).days, 0)
        mora_periodo = (
            saldo_cuota
            * TASA_MORA_MENSUAL
            * Decimal(dias)
            / Decimal(30)
        ).quantize(CENTAVO, rounding=ROUND_HALF_UP)
        mora_pendiente += mora_periodo
        mora_generada += mora_periodo

    return {
        "saldo_cuota": saldo_cuota,
        "mora_pendiente": mora_pendiente,
        "mora_generada": mora_generada,
        "dias_mora": dias_mora,
        "total_pendiente": saldo_cuota + mora_pendiente,
    }
