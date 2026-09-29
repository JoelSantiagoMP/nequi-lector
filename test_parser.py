import unittest

from parser import parse_notificacion


# Fixture de pruebas con datos completamente ficticios
FIXTURE_DATOS_NEQUI = [
    # Formato: [tipo_esperado, monto_esperado, fecha_ficticia, texto_notificacion]
    ["Ingreso", 2500.0, "2025-03-15 10:30 AM", "Te enviaron $2.500. Entra a tu app y revisa tu saldo."],
    ["Ingreso", 8000.0, "2025-03-16 02:45 PM", "Te enviaron $8.000. Entra a tu app y revisa tu saldo."],
    ["Ingreso", 12300.0, "2025-03-17 11:20 AM", "Te enviaron $12.300. Entra a tu app y revisa tu saldo."],
    ["Ingreso", 25000.0, "2025-03-18 04:00 PM", "Te enviaron $25.000. Entra a tu app y revisa tu saldo."],
    ["Ingreso", 50000.0, "2025-03-19 09:15 AM", "Te enviaron $50.000. Entra a tu app y revisa tu saldo."],
    ["Ingreso", 3500.0, "2025-03-20 03:30 PM", "ROBERTO SILVA te envió 3500, ¡lo mejor!"],
    ["Ingreso", 7800.0, "2025-03-21 12:00 PM", "LUCIA MENDEZ te envió 7800, ¡lo mejor!"],
    ["Ingreso", 15000.0, "2025-03-22 05:45 PM", "DIEGO TORRES te envió 15000, ¡lo mejor!"],
    ["Ingreso", 4200.0, "2025-03-23 08:30 AM", "Te enviaron $4200.00. Entra a tu app y revisa tu saldo."],
    ["Otro", 0.0, "2025-03-24 01:15 PM", "Envío exitoso, la plata ya está en el Nequi destino.✈ Recuerda que no se puede cancelar."],
    ["Otro", 0.0, "2025-03-25 06:00 PM", "{notification}"],
    ["Otro", 0.0, "2025-03-26 10:45 AM", "{notification}"],
]


class ParserTests(unittest.TestCase):
    def test_historico_nequi(self):
        """Test con fixture de datos ficticios que cubre diferentes formatos de notificaciones Nequi"""
        for tipo, monto, _fecha, detalle in FIXTURE_DATOS_NEQUI:
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
