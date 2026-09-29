import json
import unittest
from pathlib import Path

from parser import parse_notificacion


FIXTURE = Path(__file__).with_name("response_data.json")


class ParserTests(unittest.TestCase):
    def test_historico_nequi(self):
        registros = json.loads(FIXTURE.read_text())
        for tipo, monto, _fecha, detalle in registros:
            resultado = parse_notificacion(detalle, "nequi")
            if tipo == "Ingreso" and monto > 0:
                self.assertIsNotNone(resultado, detalle)
                self.assertEqual(resultado["monto"], monto)
                self.assertEqual(resultado["banco"], "nequi")
            else:
                self.assertIsNone(resultado, detalle)

    def test_remitente_sin_pesos(self):
        resultado = parse_notificacion(
            "AURA ROBLES te envió 1000, ¡lo mejor!", "nequi"
        )
        self.assertEqual(resultado["remitente"], "AURA ROBLES")
        self.assertEqual(resultado["monto"], 1000)

    def test_salida_nequi_no_cuenta(self):
        self.assertIsNone(
            parse_notificacion(
                "Envío exitoso, la plata ya está en el Nequi destino.",
                "nequi",
            )
        )

    def test_nu_con_nombre(self):
        resultado = parse_notificacion("Recibiste $50.000 de Ana Gómez", "nu")
        self.assertEqual(resultado["monto"], 50000)
        self.assertEqual(resultado["banco"], "nu")
        self.assertEqual(resultado["remitente"], "Ana Gómez")

    def test_nu_sin_nombre(self):
        resultado = parse_notificacion("Te llegó $12.500", "nu")
        self.assertEqual(resultado["monto"], 12500)
        self.assertEqual(resultado["remitente"], "")

    def test_salidas_nu(self):
        for texto in ("Enviaste $20.000 a Pedro", "Pagaste $15.000", "Transferiste $8.000"):
            self.assertIsNone(parse_notificacion(texto, "nu"), texto)

    def test_decimal_colombiano(self):
        resultado = parse_notificacion("Te enviaron $1.000,50. Entra a tu app.", "nequi")
        self.assertEqual(resultado["monto"], 1000.50)

    def test_aviso_vacio(self):
        self.assertIsNone(parse_notificacion("{notification}", "nequi"))
        self.assertIsNone(parse_notificacion("", "nu"))


if __name__ == "__main__":
    unittest.main()
