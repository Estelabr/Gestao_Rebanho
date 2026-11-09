"""Testes da persistência em JSON (infraestrutura)."""

import os
import tempfile
import unittest
from datetime import date

from source.domain.entidades.animal import Femea, Macho
from source.domain.entidades.insumo import BaseAlimentacao, Insumo
from source.domain.entidades.pessoas import CompraAnimal, Proprietario
from source.infra.repositorio_json import (
    ArquivoDados,
    RepositorioAnimaisJson,
    RepositorioBasesJson,
    RepositorioCatalogoFornecedorJson,
    RepositorioComprasJson,
    RepositorioInsumosJson,
    RepositorioProprietarioJson,
)


class TestRepositorioAnimaisJson(unittest.TestCase):
    def setUp(self) -> None:
        self.__tmp = tempfile.TemporaryDirectory()
        self.__arquivo = ArquivoDados(os.path.join(self.__tmp.name, "dados.json"))
        self.__repositorio = RepositorioAnimaisJson(self.__arquivo)

    def tearDown(self) -> None:
        self.__tmp.cleanup()

    def test_salvar_e_carregar_animais_de_arquivo(self):
        femea = Femea("F1", date(2023, 1, 1), "Nelore")
        femea.registrar_pesagem(400.0, date(2026, 1, 1))
        femea.registrar_vacinacao("Aftosa", "1 dose", date(2026, 2, 1))
        femea.inseminar(Macho("T1", date(2022, 1, 1), "Nelore"))
        macho = Macho("M1", date(2024, 1, 1), "Nelore")
        macho.registrar_pesagem(500.0, date(2026, 1, 1))
        macho.castrar()
        self.__repositorio.adicionar(femea)
        self.__repositorio.adicionar(macho)
        self.__repositorio.salvar()

        repositorio_reaberto = RepositorioAnimaisJson(self.__arquivo)

        femea_restaurada = repositorio_reaberto.buscar_por_brinco("F1")
        self.assertIsInstance(femea_restaurada, Femea)
        self.assertEqual(femea_restaurada.peso_atual(), 400.0)
        self.assertTrue(femea_restaurada.prenhe)
        self.assertEqual(femea_restaurada.brinco_inseminacao, "T1")
        self.assertEqual(len(femea_restaurada.vacinacoes), 1)

        macho_restaurado = repositorio_reaberto.buscar_por_brinco("M1")
        self.assertIsInstance(macho_restaurado, Macho)
        self.assertTrue(macho_restaurado.castrado)

    def test_vendido_sobrevive_a_reabertura(self):
        macho = Macho("M1", date(2023, 1, 1), "Nelore")
        macho.registrar_pesagem(500.0, date(2026, 1, 1))
        macho.marcar_vendido()
        self.__repositorio.adicionar(macho)
        self.__repositorio.salvar()

        repositorio_reaberto = RepositorioAnimaisJson(self.__arquivo)

        self.assertTrue(repositorio_reaberto.buscar_por_brinco("M1").vendido)

    def test_remover_animal_e_bloqueado_para_brinco_inexistente(self):
        from source.domain.excecoes import AnimalNaoEncontradoError

        with self.assertRaises(AnimalNaoEncontradoError):
            self.__repositorio.remover("F99")


class TestRepositorioInsumosJson(unittest.TestCase):
    def setUp(self) -> None:
        self.__tmp = tempfile.TemporaryDirectory()
        self.__arquivo = ArquivoDados(os.path.join(self.__tmp.name, "dados.json"))
        self.__repositorio = RepositorioInsumosJson(self.__arquivo)

    def tearDown(self) -> None:
        self.__tmp.cleanup()

    def test_salvar_e_carregar_insumos_de_arquivo(self):
        self.__repositorio.adicionar(Insumo("Ração 20%", "Nutricional", 1000.0, 1.80))
        self.__repositorio.salvar()

        repositorio_reaberto = RepositorioInsumosJson(self.__arquivo)

        insumo = repositorio_reaberto.buscar_por_nome("Ração 20%")
        self.assertIsNotNone(insumo)
        self.assertEqual(insumo.estoque, 1000.0)
        self.assertEqual(insumo.preco, 1.80)

    def test_arquivo_antigo_com_chaves_antigas_e_lido(self):
        """Compatibilidade: dados.json escrito antes das renomeações."""
        self.__arquivo.salvar(
            {
                "insumos": [
                    {
                        "nome": "Milho",
                        "tipo": "Nutricional",
                        "quantidade": 100.0,
                        "preco_unitario": 2.0,
                    }
                ]
            }
        )

        repositorio_reaberto = RepositorioInsumosJson(self.__arquivo)

        insumo = repositorio_reaberto.buscar_por_nome("Milho")
        self.assertEqual(insumo.estoque, 100.0)
        self.assertEqual(insumo.preco, 2.0)


class TestPersistenciaCompleta(unittest.TestCase):
    """Round-trip completo: insumos, bases, animais, compras e proprietário,
    com as referências entre objetos re-vinculadas na reabertura."""

    def setUp(self) -> None:
        self.__tmp = tempfile.TemporaryDirectory()
        self.__caminho = os.path.join(self.__tmp.name, "dados.json")
        self.__remontar()

    def tearDown(self) -> None:
        self.__tmp.cleanup()

    def __remontar(self) -> None:
        """Reabre todos os repositórios, simulando uma nova execução."""
        arquivo = ArquivoDados(self.__caminho)
        self.__insumos = RepositorioInsumosJson(arquivo)
        self.__bases = RepositorioBasesJson(arquivo, self.__insumos)
        self.__animais = RepositorioAnimaisJson(arquivo, self.__bases.buscar_por_nome)
        self.__compras = RepositorioComprasJson(arquivo, self.__animais)
        self.__catalogo = RepositorioCatalogoFornecedorJson(arquivo)
        self.__proprietarios = RepositorioProprietarioJson(arquivo)

    def __salvar_tudo(self) -> None:
        self.__insumos.salvar()
        self.__bases.salvar()
        self.__animais.salvar()
        self.__compras.salvar()
        self.__catalogo.salvar()

    def test_round_trip_com_todos_os_vinculos(self):
        racao = Insumo("Ração 20%", "Nutricional", 1000.0, 1.80)
        self.__insumos.adicionar(racao)
        base = BaseAlimentacao("Engorda", "Ração de engorda")
        base.adicionar_insumo(racao, 2.5)
        self.__bases.adicionar(base)

        mae = Femea("F1", date(2021, 1, 1), "Nelore")
        mae.inseminar(Macho("T1", date(2020, 1, 1), "Nelore"))
        bezerro = mae.registrar_parto("F2", macho=True)
        mae.definir_alimentacao(base)
        mae.registrar_pesagem(400.0, date(2026, 1, 1))
        mae.marcar_vendido()
        self.__animais.adicionar(mae)
        self.__animais.adicionar(bezerro)

        self.__compras.adicionar(CompraAnimal(date(2026, 2, 1), mae, 2500.0))
        self.__catalogo.adicionar(Insumo("Sal mineral", "Mineral", 300.0, 0.50))
        self.__proprietarios.salvar(Proprietario("Maria", "123.456.789-00"))

        self.__salvar_tudo()
        self.__remontar()

        mae_restaurada = self.__animais.buscar_por_brinco("F1")
        self.assertTrue(mae_restaurada.vendido)
        self.assertFalse(mae_restaurada.prenhe)
        self.assertEqual(mae_restaurada.partos, 1)
        self.assertEqual(mae_restaurada.alimentacao().nome, "Engorda")

        filhos = mae_restaurada.listar_filhos()
        self.assertEqual([filho.brinco.valor for filho in filhos], ["F2"])
        self.assertEqual(filhos[0].mae_brinco, "F1")
        self.assertEqual(filhos[0].pai_brinco, "T1")

        base_restaurada = self.__bases.buscar_por_nome("Engorda")
        self.assertEqual(base_restaurada.itens[0][0].nome, "Ração 20%")
        self.assertEqual(base_restaurada.consumo_diario_kg(), 2.5)

        compra = self.__compras.listar()[0]
        self.assertEqual(compra.valor, 2500.0)
        self.assertEqual(compra.animal.brinco.valor, "F1")

        lote = self.__catalogo.buscar_por_nome("Sal mineral")
        self.assertEqual(lote.estoque, 300.0)

        proprietario = self.__proprietarios.carregar()
        self.assertEqual(proprietario.nome, "Maria")
        self.assertEqual(proprietario.cpf, "123.456.789-00")

    def test_compra_de_animal_excluido_e_ignorada_ao_recarregar(self):
        macho = Macho("M1", date(2023, 1, 1), "Nelore")
        macho.registrar_pesagem(500.0, date(2026, 1, 1))
        macho.marcar_vendido()
        self.__animais.adicionar(macho)
        self.__animais.salvar()
        self.__compras.adicionar(CompraAnimal(date(2026, 2, 1), macho, 3000.0))
        self.__compras.salvar()
        self.__animais.remover("M1")
        self.__animais.salvar()

        self.__remontar()

        self.assertEqual(self.__compras.listar(), [])
        self.assertIsNone(self.__animais.buscar_por_brinco("M1"))

    def test_sem_arquivo_comeca_vazio(self):
        self.assertEqual(self.__animais.listar(), [])
        self.assertEqual(self.__insumos.listar(), [])
        self.assertEqual(self.__bases.listar(), [])
        self.assertEqual(self.__compras.listar(), [])
        self.assertIsNone(self.__proprietarios.carregar())


if __name__ == "__main__":
    unittest.main()
