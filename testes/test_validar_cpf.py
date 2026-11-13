"""Testes do domain service de validação do CPF."""

import unittest

from source.domain.excecoes import CPFInvalidoError
from source.domain.servicos.validar_cpf import ValidarCpf


class TestValidarCpf(unittest.TestCase):
    def test_cpf_valido_com_pontuacao(self):
        self.assertEqual(ValidarCpf.validar("529.982.247-25"), "52998224725")

    def test_cpf_valido_so_com_digitos(self):
        self.assertEqual(ValidarCpf.validar("11144477735"), "11144477735")

    def test_cpf_com_espacos_nas_bordas_e_aceito(self):
        self.assertEqual(ValidarCpf.validar("  529.982.247-25  "), "52998224725")

    def test_cpf_com_digito_verificador_errado_e_rejeitado(self):
        with self.assertRaises(CPFInvalidoError):
            ValidarCpf.validar("529.982.247-24")

    def test_cpf_com_digitos_repetidos_e_rejeitado(self):
        for numero in ("111.111.111-11", "000.000.000-00", "999.999.999-99"):
            with self.subTest(numero=numero):
                with self.assertRaises(CPFInvalidoError):
                    ValidarCpf.validar(numero)

    def test_cpf_com_tamanho_errado_e_rejeitado(self):
        for numero in ("529.982.247-2", "529.982.247-250", ""):
            with self.subTest(numero=numero):
                with self.assertRaises(CPFInvalidoError):
                    ValidarCpf.validar(numero)

    def test_cpf_com_letras_e_ignorado_no_calculo(self):
        """Letras não são dígitos: o resto é ignorado como pontuação."""
        self.assertEqual(ValidarCpf.validar("529.982.247-25 CPF"), "52998224725")

    def test_normalizar_reduz_o_cpf_aos_digitos(self):
        self.assertEqual(ValidarCpf.normalizar("529.982.247-25"), "52998224725")


if __name__ == "__main__":
    unittest.main()
