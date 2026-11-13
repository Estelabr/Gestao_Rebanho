"""Testes da demonstração no console (python main.py --demo)."""

import io
import os
import subprocess
import sys
import tempfile
import unittest

from source.interfaces.demonstracao_console import rodar_demonstracao

MAIN = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "main.py")


class TestDemonstracao(unittest.TestCase):
    def setUp(self) -> None:
        self.__tmp = tempfile.TemporaryDirectory()
        self.__antigo = os.getcwd()
        os.chdir(self.__tmp.name)

    def tearDown(self) -> None:
        os.chdir(self.__antigo)
        self.__tmp.cleanup()

    def __rodar(self) -> str:
        saida = io.StringIO()
        rodar_demonstracao(saida)
        return saida.getvalue()

    def test_mostra_a_regra_de_venda(self):
        texto = self.__rodar()
        self.assertIn("Animal M2 tem 300.0 kg e o mínimo de abate é 450.0 kg.", texto)
        self.assertIn("Compra registrada: 2026-11-13 - animal T1 por R$ 3200.00", texto)
        self.assertIn("Animal T1 já foi vendido e não pode ser vendido de novo.", texto)

    def test_mostra_a_regra_de_inseminacao(self):
        texto = self.__rodar()
        self.assertIn("Macho tem método inseminar? False", texto)
        self.assertIn("F1.pode_inseminar(T1) = True", texto)
        self.assertIn("Fêmea F1 não pode ser inseminada pelo touro T1", texto)
        self.assertIn("Genealogia de B1: mãe F1, pai T1", texto)

    def test_nao_grava_arquivos(self):
        self.__rodar()
        self.assertEqual(os.listdir(self.__tmp.name), [])

    def test_main_com_demo_roda_sem_login(self):
        resultado = subprocess.run(
            [sys.executable, MAIN, "--demo"],
            cwd=self.__tmp.name,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        self.assertIn("=== 8. Rebanho no fim da demonstração ===", resultado.stdout)
        self.assertEqual(os.listdir(self.__tmp.name), [])


if __name__ == "__main__":
    unittest.main()
