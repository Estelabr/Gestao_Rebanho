"""Testes da credencial de acesso: hash da senha com salt aleatório."""

import unittest

from source.usecases.senhas import conferir, gerar_credencial


class TestCredencialDeAcesso(unittest.TestCase):
    def test_credencial_nao_guarda_a_senha_em_texto_plano(self):
        credencial = gerar_credencial("s3cr3t")
        self.assertNotIn("s3cr3t", credencial)

    def test_credencial_confere_a_senha_certa(self):
        credencial = gerar_credencial("s3cr3t")
        self.assertTrue(conferir("s3cr3t", credencial))

    def test_credencial_rejeita_a_senha_errada(self):
        credencial = gerar_credencial("s3cr3t")
        self.assertFalse(conferir("errada", credencial))

    def test_salt_aleatorio_gera_credenciais_diferentes_para_a_mesma_senha(self):
        """Duas gerações da mesma senha nunca produzem o mesmo hash."""
        self.assertNotEqual(gerar_credencial("s3cr3t"), gerar_credencial("s3cr3t"))

    def test_credencial_malformada_e_rejeitada(self):
        self.assertFalse(conferir("s3cr3t", "texto-qualquer"))


if __name__ == "__main__":
    unittest.main()
