"""Testes dos casos de uso, usando repositórios em memória (dobras de teste).

Como os casos de uso dependem dos contratos de repositório e não da
implementação JSON, dá para testá-los sem tocar em arquivo nenhum.
"""

import unittest
from datetime import date
from typing import Dict, List, Optional

from source.domain.entidades.animal import Animal, Femea, Macho
from source.domain.entidades.insumo import BaseAlimentacao, Insumo
from source.domain.entidades.pessoas import Fornecedor, Frigorifico, Proprietario
from source.domain.excecoes import (
    AnimalNaoEncontradoError,
    BaseDuplicadaError,
    BaseNaoEncontradaError,
    BrincoDuplicadoError,
    EstoqueInsuficienteError,
    InseminacaoInvalidaError,
    InsumoNaoEncontradoError,
    PesoInsuficienteError,
    RegraNegocioViolation,
)
from source.domain.repositorios import (
    RepositorioAnimais,
    RepositorioBases,
    RepositorioCompras,
    RepositorioInsumos,
    RepositorioProprietario,
)
from source.usecases.casos_de_uso import (
    Autocadastro,
    CadastrarAnimal,
    CadastrarInsumo,
    ComprarInsumo,
    ConsultarAlimentacao,
    ConsultarGenetica,
    CriarBaseAlimentacao,
    DefinirAlimentacao,
    HistoricoCompras,
    IdentificarAnimaisParaVenda,
    InseminarFemea,
    RegistrarParto,
    RegistrarPesagem,
    RegistrarVacinacao,
    VenderAnimal,
    VenderInsumo,
)


class RepositorioAnimaisMemoria(RepositorioAnimais):
    """Dobra de teste: guarda os animais em um dicionário em memória."""

    def __init__(self) -> None:
        self._animais: Dict[str, Animal] = {}
        self.chamadas_salvar = 0

    def adicionar(self, animal: Animal) -> None:
        self._animais[animal.brinco.valor] = animal

    def buscar_por_brinco(self, brinco: str) -> Optional[Animal]:
        return self._animais.get(brinco)

    def listar(self) -> List[Animal]:
        return list(self._animais.values())

    def remover(self, brinco: str) -> None:
        del self._animais[brinco]

    def salvar(self) -> None:
        self.chamadas_salvar += 1


class RepositorioInsumosMemoria(RepositorioInsumos):
    """Dobra de teste: guarda os insumos em um dicionário em memória."""

    def __init__(self) -> None:
        self._insumos: Dict[str, Insumo] = {}
        self.chamadas_salvar = 0

    def adicionar(self, insumo: Insumo) -> None:
        self._insumos[insumo.nome] = insumo

    def buscar_por_nome(self, nome: str) -> Optional[Insumo]:
        return self._insumos.get(nome)

    def listar(self) -> List[Insumo]:
        return list(self._insumos.values())

    def salvar(self) -> None:
        self.chamadas_salvar += 1


class RepositorioBasesMemoria(RepositorioBases):
    """Dobra de teste: guarda as bases de alimentação em memória."""

    def __init__(self) -> None:
        self._bases: Dict[str, BaseAlimentacao] = {}
        self.chamadas_salvar = 0

    def adicionar(self, base: BaseAlimentacao) -> None:
        self._bases[base.nome] = base

    def buscar_por_nome(self, nome: str) -> Optional[BaseAlimentacao]:
        return self._bases.get(nome)

    def listar(self) -> List[BaseAlimentacao]:
        return list(self._bases.values())

    def salvar(self) -> None:
        self.chamadas_salvar += 1


class RepositorioComprasMemoria(RepositorioCompras):
    """Dobra de teste: guarda as compras do frigorífico em memória."""

    def __init__(self) -> None:
        self._compras = []
        self.chamadas_salvar = 0

    def adicionar(self, compra) -> None:
        self._compras.append(compra)

    def listar(self) -> List:
        return list(self._compras)

    def salvar(self) -> None:
        self.chamadas_salvar += 1


class RepositorioProprietarioMemoria(RepositorioProprietario):
    """Dobra de teste: guarda o cadastro do proprietário em memória."""

    def __init__(self) -> None:
        self._proprietario: Optional[Proprietario] = None
        self.chamadas_salvar = 0

    def carregar(self) -> Optional[Proprietario]:
        return self._proprietario

    def salvar(self, proprietario: Proprietario) -> None:
        self._proprietario = proprietario
        self.chamadas_salvar += 1


class TestCadastrarAnimal(unittest.TestCase):
    def setUp(self) -> None:
        self.repositorio = RepositorioAnimaisMemoria()
        self.proprietario = Proprietario("Fulano", "000.000.000-00")
        self.cadastrar = CadastrarAnimal(self.repositorio, self.proprietario)

    def test_cadastrar_femea_e_macho(self):
        femea = self.cadastrar.executar("F1", date(2024, 1, 1), "Nelore", "femea")
        macho = self.cadastrar.executar("M1", date(2024, 2, 1), "Nelore", "macho")
        self.assertEqual(len(self.repositorio.listar()), 2)
        self.assertEqual(len(self.proprietario.listar_animais()), 2)
        self.assertIsInstance(femea, Femea)
        self.assertIsInstance(macho, Macho)

    def test_brinco_duplicado_e_bloqueado(self):
        self.cadastrar.executar("F1", date(2024, 1, 1), "Nelore", "femea")
        with self.assertRaises(BrincoDuplicadoError):
            self.cadastrar.executar("F1", date(2024, 2, 1), "Nelore", "femea")

    def test_tipo_invalido_e_bloqueado(self):
        with self.assertRaises(RegraNegocioViolation):
            self.cadastrar.executar("F1", date(2024, 1, 1), "Nelore", "ave")


class TestRegistrarPesagemEVacinacao(unittest.TestCase):
    def setUp(self) -> None:
        self.repositorio = RepositorioAnimaisMemoria()
        CadastrarAnimal(self.repositorio, Proprietario("Fulano", "000.000.000-00")).executar(
            "F1", date(2024, 1, 1), "Nelore", "femea"
        )
        self.pesagem = RegistrarPesagem(self.repositorio)
        self.vacinacao = RegistrarVacinacao(self.repositorio)

    def test_registrar_pesagem_chama_o_repositorio_salvar(self):
        self.pesagem.executar("F1", 380.0, date(2026, 1, 1))
        self.assertEqual(self.repositorio.chamadas_salvar, 1)
        animal = self.repositorio.buscar_por_brinco("F1")
        self.assertEqual(animal.peso_atual(), 380.0)

    def test_registrar_pesagem_de_animal_inexistente(self):
        with self.assertRaises(AnimalNaoEncontradoError):
            self.pesagem.executar("F99", 380.0)

    def test_registrar_vacinacao(self):
        self.vacinacao.executar("F1", "Aftosa", "1 dose", date(2026, 2, 1))
        animal = self.repositorio.buscar_por_brinco("F1")
        self.assertEqual(len(animal.vacinacoes), 1)
        self.assertEqual(animal.vacinacoes[0].vacina, "Aftosa")


class TestInseminarFemea(unittest.TestCase):
    def setUp(self) -> None:
        self.repositorio = RepositorioAnimaisMemoria()
        cadastrar = CadastrarAnimal(self.repositorio, Proprietario("Fulano", "000.000.000-00"))
        cadastrar.executar("F1", date(2023, 1, 1), "Nelore", "femea")
        cadastrar.executar("M1", date(2022, 1, 1), "Nelore", "macho")
        cadastrar.executar("M2", date(2022, 1, 1), "Nelore", "macho")
        self.inseminar = InseminarFemea(self.repositorio)

    def test_inseminar_femea_com_touro(self):
        self.inseminar.executar("F1", "M1")
        self.assertTrue(self.repositorio.buscar_por_brinco("F1").prenhe)

    def test_inseminar_macho_e_bloqueado(self):
        with self.assertRaises(InseminacaoInvalidaError):
            self.inseminar.executar("M1", "M2")

    def test_inseminar_com_touro_femea_e_bloqueado(self):
        cadastrar = CadastrarAnimal(self.repositorio, Proprietario("Fulano", "000.000.000-00"))
        cadastrar.executar("F2", date(2023, 1, 1), "Nelore", "femea")
        with self.assertRaises(InseminacaoInvalidaError):
            self.inseminar.executar("F1", "F2")

    def test_inseminar_com_touro_inexistente(self):
        with self.assertRaises(AnimalNaoEncontradoError):
            self.inseminar.executar("F1", "T99")


class TestRegistrarParto(unittest.TestCase):
    def setUp(self) -> None:
        self.repositorio = RepositorioAnimaisMemoria()
        self.proprietario = Proprietario("Fulano", "000.000.000-00")
        cadastrar = CadastrarAnimal(self.repositorio, self.proprietario)
        cadastrar.executar("F1", date(2021, 1, 1), "Nelore", "femea")
        cadastrar.executar("T1", date(2020, 1, 1), "Nelore", "macho")
        InseminarFemea(self.repositorio).executar("F1", "T1")
        self.parto = RegistrarParto(self.repositorio, self.proprietario)

    def test_parto_cadastra_o_bezerro_no_rebanho(self):
        bezerro = self.parto.executar("F1", "F2", macho=True)
        self.assertIsNotNone(self.repositorio.buscar_por_brinco("F2"))
        self.assertEqual(bezerro.mae_brinco, "F1")
        self.assertEqual(bezerro.pai_brinco, "T1")
        self.assertEqual(len(self.proprietario.listar_animais()), 3)

    def test_parto_com_brinco_duplicado_e_bloqueado(self):
        with self.assertRaises(BrincoDuplicadoError):
            self.parto.executar("F1", "T1", macho=True)

    def test_parto_de_macho_e_bloqueado(self):
        with self.assertRaises(RegraNegocioViolation):
            self.parto.executar("T1", "F9", macho=False)


class TestConsultarGenetica(unittest.TestCase):
    def setUp(self) -> None:
        self.repositorio = RepositorioAnimaisMemoria()
        self.proprietario = Proprietario("Fulano", "000.000.000-00")
        cadastrar = CadastrarAnimal(self.repositorio, self.proprietario)
        cadastrar.executar("F1", date(2021, 1, 1), "Nelore", "femea")
        cadastrar.executar("T1", date(2020, 1, 1), "Nelore", "macho")
        InseminarFemea(self.repositorio).executar("F1", "T1")
        RegistrarParto(self.repositorio, self.proprietario).executar("F1", "F2", macho=True)
        self.genetica = ConsultarGenetica(self.repositorio)

    def test_genetica_do_bezerro_mostra_mae_e_pai(self):
        resumo = self.genetica.executar("F2")
        self.assertIn("F1", resumo)
        self.assertIn("T1", resumo)

    def test_genetica_da_mae_mostra_os_filhos(self):
        resumo = self.genetica.executar("F1")
        self.assertIn("F2", resumo)

    def test_genetica_de_animal_inexistente_e_bloqueada(self):
        with self.assertRaises(AnimalNaoEncontradoError):
            self.genetica.executar("F99")


class TestVenderAnimal(unittest.TestCase):
    def test_vender_animal_com_peso_suficiente(self):
        repositorio = RepositorioAnimaisMemoria()
        cadastrar = CadastrarAnimal(repositorio, Proprietario("Fulano", "000.000.000-00"))
        cadastrar.executar("F1", date(2023, 1, 1), "Nelore", "femea")
        RegistrarPesagem(repositorio).executar("F1", 400.0, date(2026, 1, 1))

        frigorifico = Frigorifico("Frigorífico Pampa Sul", "12.345.678/0001-90")
        compras = RepositorioComprasMemoria()
        compra = VenderAnimal(repositorio, frigorifico, compras).executar("F1", 2500.0)

        self.assertEqual(compra.animal.brinco.valor, "F1")
        self.assertTrue(repositorio.buscar_por_brinco("F1").vendido)
        self.assertEqual(len(frigorifico.historico_compras()), 1)
        self.assertEqual(len(compras.listar()), 1)

    def test_vender_animal_abaixo_do_peso_e_bloqueado(self):
        repositorio = RepositorioAnimaisMemoria()
        cadastrar = CadastrarAnimal(repositorio, Proprietario("Fulano", "000.000.000-00"))
        cadastrar.executar("F1", date(2025, 1, 1), "Nelore", "femea")
        RegistrarPesagem(repositorio).executar("F1", 200.0, date(2026, 1, 1))

        frigorifico = Frigorifico("Frigorífico Pampa Sul", "12.345.678/0001-90")
        with self.assertRaises(PesoInsuficienteError):
            VenderAnimal(repositorio, frigorifico, RepositorioComprasMemoria()).executar(
                "F1", 2500.0
            )


class TestIdentificarAnimaisParaVenda(unittest.TestCase):
    def test_lista_apenas_os_animais_prontos_para_venda(self):
        repositorio = RepositorioAnimaisMemoria()
        cadastrar = CadastrarAnimal(repositorio, Proprietario("Fulano", "000.000.000-00"))
        cadastrar.executar("F1", date(2023, 1, 1), "Nelore", "femea")
        cadastrar.executar("M1", date(2024, 1, 1), "Nelore", "macho")
        RegistrarPesagem(repositorio).executar("F1", 400.0, date(2026, 1, 1))
        RegistrarPesagem(repositorio).executar("M1", 300.0, date(2026, 1, 1))

        prontos = IdentificarAnimaisParaVenda(repositorio).executar()

        self.assertEqual([animal.brinco.valor for animal in prontos], ["F1"])


class TestHistoricoCompras(unittest.TestCase):
    def test_historico_mostra_as_compras_do_frigorifico(self):
        repositorio = RepositorioAnimaisMemoria()
        cadastrar = CadastrarAnimal(repositorio, Proprietario("Fulano", "000.000.000-00"))
        cadastrar.executar("F1", date(2023, 1, 1), "Nelore", "femea")
        RegistrarPesagem(repositorio).executar("F1", 400.0, date(2026, 1, 1))

        frigorifico = Frigorifico("Frigorífico Pampa Sul", "12.345.678/0001-90")
        VenderAnimal(
            repositorio, frigorifico, RepositorioComprasMemoria()
        ).executar("F1", 2500.0)

        historico = HistoricoCompras(frigorifico).executar()
        self.assertEqual(len(historico), 1)
        self.assertIn("F1", historico[0].resumo())

    def test_historico_sem_compras(self):
        frigorifico = Frigorifico("Frigorífico Pampa Sul", "12.345.678/0001-90")
        self.assertEqual(HistoricoCompras(frigorifico).executar(), ())


class TestNutricao(unittest.TestCase):
    def setUp(self) -> None:
        self.repositorio_animais = RepositorioAnimaisMemoria()
        self.repositorio_bases = RepositorioBasesMemoria()
        self.repositorio_insumos = RepositorioInsumosMemoria()
        self.proprietario = Proprietario("Fulano", "000.000.000-00")
        CadastrarAnimal(self.repositorio_animais, self.proprietario).executar(
            "F1", date(2024, 1, 1), "Nelore", "femea"
        )
        self.repositorio_insumos.adicionar(Insumo("Ração 20%", "Nutricional", 1000.0, 1.80))
        self.criar_base = CriarBaseAlimentacao(
            self.repositorio_bases, self.repositorio_insumos, self.proprietario
        )
        self.definir = DefinirAlimentacao(self.repositorio_animais, self.repositorio_bases)
        self.consultar = ConsultarAlimentacao(self.repositorio_animais)

    def test_criar_base_e_definir_alimentacao_do_animal(self):
        base = self.criar_base.executar("Engorda", "Ração de engorda", [("Ração 20%", 2.5)])
        self.assertEqual(base.consumo_diario_kg(), 2.5)
        self.assertIn(base, self.proprietario.listar_bases())

        self.definir.executar("F1", "Engorda")
        animal = self.repositorio_animais.buscar_por_brinco("F1")
        self.assertEqual(animal.alimentacao().nome, "Engorda")

    def test_base_duplicada_e_bloqueada(self):
        self.criar_base.executar("Engorda", "Ração de engorda", [("Ração 20%", 2.5)])
        with self.assertRaises(BaseDuplicadaError):
            self.criar_base.executar("Engorda", "Outra", [])

    def test_base_com_insumo_inexistente_e_bloqueada(self):
        with self.assertRaises(InsumoNaoEncontradoError):
            self.criar_base.executar("Engorda", "Ração", [("Milho", 3.0)])

    def test_definir_alimentacao_de_base_inexistente_e_bloqueado(self):
        with self.assertRaises(BaseNaoEncontradaError):
            self.definir.executar("F1", "Engorda")

    def test_consultar_alimentacao_sem_base(self):
        resumo = self.consultar.executar("F1")
        self.assertIn("ainda não tem base", resumo)

    def test_consultar_alimentacao_com_base(self):
        self.criar_base.executar("Engorda", "Ração de engorda", [("Ração 20%", 2.5)])
        self.definir.executar("F1", "Engorda")
        resumo = self.consultar.executar("F1")
        self.assertIn("Ração 20%", resumo)
        self.assertIn("2.50", resumo)

    def test_consultar_alimentacao_de_animal_inexistente_e_bloqueado(self):
        with self.assertRaises(AnimalNaoEncontradoError):
            self.consultar.executar("F99")


class TestInsumosDoFornecedor(unittest.TestCase):
    def setUp(self) -> None:
        self.fazenda = RepositorioInsumosMemoria()
        self.catalogo = RepositorioInsumosMemoria()
        self.fornecedor = Fornecedor("Agropecuária Central", "12.345.678/0002-33")
        self.proprietario = Proprietario("Fulano", "000.000.000-00")
        self.cadastrar = CadastrarInsumo(self.catalogo, self.fornecedor)
        self.comprar = ComprarInsumo(
            self.fazenda, self.catalogo, self.fornecedor, self.proprietario
        )
        self.vender = VenderInsumo(
            self.fazenda, self.catalogo, self.fornecedor, self.proprietario
        )

    def test_cadastrar_insumo_cria_lote_no_catalogo(self):
        lote = self.cadastrar.executar("Ração 20%", "Nutricional", 1000.0, 1.80)
        self.assertEqual(lote.estoque, 1000.0)
        self.assertEqual(len(self.fornecedor.listar_insumos()), 1)

    def test_cadastrar_insumo_existente_repoe_o_lote(self):
        self.cadastrar.executar("Ração 20%", "Nutricional", 1000.0, 1.80)
        lote = self.cadastrar.executar("Ração 20%", "Nutricional", 500.0, 1.80)
        self.assertEqual(lote.estoque, 1500.0)

    def test_comprar_insumo_transfere_do_fornecedor_para_a_fazenda(self):
        self.cadastrar.executar("Ração 20%", "Nutricional", 1000.0, 1.80)
        insumo = self.comprar.executar("Ração 20%", 400.0)
        self.assertEqual(insumo.estoque, 400.0)
        self.assertEqual(self.fornecedor.buscar_insumo("Ração 20%").estoque, 600.0)
        self.assertEqual(len(self.fazenda.listar()), 1)

    def test_comprar_mais_do_que_o_fornecedor_tem_e_bloqueado(self):
        self.cadastrar.executar("Ração 20%", "Nutricional", 100.0, 1.80)
        with self.assertRaises(EstoqueInsuficienteError):
            self.comprar.executar("Ração 20%", 400.0)

    def test_comprar_insumo_fora_do_catalogo_e_bloqueado(self):
        with self.assertRaises(InsumoNaoEncontradoError):
            self.comprar.executar("Milho", 100.0)

    def test_vender_insumo_e_a_mesma_transacao_pelo_lado_do_fornecedor(self):
        self.cadastrar.executar("Sal mineral", "Mineral", 200.0, 0.50)
        insumo = self.vender.executar("Sal mineral", 50.0)
        self.assertEqual(insumo.estoque, 50.0)
        self.assertEqual(self.fornecedor.buscar_insumo("Sal mineral").estoque, 150.0)


class TestAutocadastro(unittest.TestCase):
    def test_autocadastro_atualiza_e_salva_o_cadastro(self):
        proprietario = Proprietario("Fazenda Boa Esperança", "000.000.000-00")
        repositorio = RepositorioProprietarioMemoria()
        Autocadastro(proprietario, repositorio).executar("Maria", "123.456.789-00")
        self.assertEqual(proprietario.nome, "Maria")
        self.assertEqual(repositorio.carregar().cpf, "123.456.789-00")

    def test_autocadastro_com_dados_vazios_e_bloqueado(self):
        proprietario = Proprietario("Fazenda Boa Esperança", "000.000.000-00")
        with self.assertRaises(RegraNegocioViolation):
            Autocadastro(proprietario, RepositorioProprietarioMemoria()).executar("", "")


if __name__ == "__main__":
    unittest.main()
