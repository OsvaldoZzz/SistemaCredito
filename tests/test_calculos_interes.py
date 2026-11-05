import unittest
from decimal import Decimal

from app.logica.calculos_prestamo import (
    PORCENTAJE_INTERES,
    calcular_interes,
    calcular_total_prestamo,
)


class CalculosInteresTest(unittest.TestCase):
    def test_interes_total_es_quince_por_ciento_del_capital(self):
        self.assertEqual(PORCENTAJE_INTERES, Decimal("15.00"))
        self.assertEqual(calcular_interes("1000.00"), Decimal("150.00"))
        self.assertEqual(calcular_total_prestamo("1000.00"), Decimal("1150.00"))


if __name__ == "__main__":
    unittest.main()
