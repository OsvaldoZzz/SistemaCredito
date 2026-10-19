from decimal import Decimal, ROUND_HALF_UP


TASA_INTERES = Decimal("0.02")
PORCENTAJE_INTERES = TASA_INTERES * 100
CENTAVO = Decimal("0.01")


def calcular_interes(monto: Decimal | int | float | str) -> Decimal:
    principal = Decimal(str(monto))
    if not principal.is_finite() or principal < 0:
        raise ValueError("El monto debe ser un número positivo válido.")
    return (principal * TASA_INTERES).quantize(
        CENTAVO,
        rounding=ROUND_HALF_UP,
    )


def calcular_total_prestamo(monto: Decimal | int | float | str) -> Decimal:
    principal = Decimal(str(monto)).quantize(
        CENTAVO,
        rounding=ROUND_HALF_UP,
    )
    return principal + calcular_interes(principal)
