"""Testes do domain service de validação do CNPJ."""

import unittest

from source.domain.excecoes import CNPJInvalidoError
from source.domain.servicos.validar_cnpj import ValidarCnpj


class TestValidarCnpj(unittest.TestCase):
    def test_cnpj_valido_com_pontuacao(self):
        self.assertEqual(ValidarCnpj.validar("11.444.777/0001-61"), "11444777000161")

    def test_cnpj_valido_so_com_digitos(self):
        self.assertEqual(ValidarCnpj.validar("00000000000191"), "00000000000191")

    def test_cnpj_com_espacos_nas_bordas_e_aceito(self):
        self.assertEqual(ValidarCnpj.validar("  45.723.174/0001-10  "), "45723174000110")

    def test_cnpj_com_digito_verificador_errado_e_rejeitado(self):
        with self.assertRaises(CNPJInvalidoError):
            ValidarCnpj.validar("11.444.777/0001-62")

    def test_cnpj_com_digitos_repetidos_e_rejeitado(self):
        for numero in ("11.111.111/1111-11", "00.000.000/0000-00"):
            with self.subTest(numero=numero):
                with self.assertRaises(CNPJInvalidoError):
                    ValidarCnpj.validar(numero)

    def test_cnpj_com_tamanho_errado_e_rejeitado(self):
        for numero in ("11.444.777/0001-6", "11.444.777/0001-610", ""):
            with self.subTest(numero=numero):
                with self.assertRaises(CNPJInvalidoError):
                    ValidarCnpj.validar(numero)

    def test_normalizar_reduz_o_cnpj_aos_digitos(self):
        self.assertEqual(ValidarCnpj.normalizar("11.444.777/0001-61"), "11444777000161")


if __name__ == "__main__":
    unittest.main()
