"""Testes das regras de negócio do domínio (as duas regras principais do sistema)."""

import unittest
from datetime import date

from source.domain.entidades.animal import Animal, Femea, Macho
from source.domain.entidades.insumo import BaseAlimentacao, Insumo
from source.domain.entidades.pessoas import Fornecedor, Frigorifico, Proprietario
from source.domain.excecoes import (
    AnimalVendidoError,
    EstoqueInsuficienteError,
    InseminacaoInvalidaError,
    PesoInvalidoError,
    PesoInsuficienteError,
    QuantidadeInvalidaError,
    RegraNegocioViolation,
)
from source.domain.objetos_valor import Peso


class TestAbstracaoEHeranca(unittest.TestCase):
    def test_nao_pode_instanciar_animal(self):
        """Animal é abstrata: todo animal do sistema é fêmea ou macho."""
        with self.assertRaises(TypeError):
            Animal("1", date(2024, 1, 1), "Nelore")

    def test_femea_e_macho_sobrescrevem_os_metodos_abstratos(self):
        """Polimorfismo: categoria e peso mínimo de abate respondem por
        conta de cada subclasse."""
        femea = Femea("F1", date(2024, 1, 1), "Nelore")
        macho = Macho("M1", date(2024, 1, 1), "Nelore")
        self.assertEqual(femea.categoria(), "Fêmea")
        self.assertEqual(macho.categoria(), "Macho")
        self.assertEqual(femea.peso_minimo_abate(), 350.0)
        self.assertEqual(macho.peso_minimo_abate(), 450.0)


class TestRegraVenda(unittest.TestCase):
    def test_animal_sem_pesagem_nao_pode_ser_vendido(self):
        macho = Macho("M1", date(2024, 1, 1), "Nelore")
        self.assertFalse(macho.pode_vender())

    def test_animal_abaixo_do_peso_minimo_nao_pode_ser_vendido(self):
        macho = Macho("M1", date(2024, 1, 1), "Nelore")
        macho.registrar_pesagem(300.0, date(2026, 1, 1))
        self.assertFalse(macho.pode_vender())
        with self.assertRaises(PesoInsuficienteError):
            macho.marcar_vendido()

    def test_animal_com_peso_suficiente_pode_ser_vendido(self):
        femea = Femea("F1", date(2024, 1, 1), "Nelore")
        femea.registrar_pesagem(400.0, date(2026, 1, 1))
        self.assertTrue(femea.pode_vender())
        femea.marcar_vendido()
        self.assertTrue(femea.vendido)

    def test_animal_vendido_nao_pode_ser_vendido_de_novo(self):
        femea = Femea("F1", date(2024, 1, 1), "Nelore")
        femea.registrar_pesagem(400.0, date(2026, 1, 1))
        femea.marcar_vendido()
        with self.assertRaises(AnimalVendidoError):
            femea.marcar_vendido()

    def test_frigorifico_so_compra_animal_que_pode_ser_vendido(self):
        frigorifico = Frigorifico("Frigorífico Pampa Sul", "12.345.678/0001-90")
        macho = Macho("M1", date(2024, 1, 1), "Nelore")
        macho.registrar_pesagem(500.0, date(2026, 1, 1))
        compra = frigorifico.comprar_animal(macho, 2500.0)
        self.assertEqual(compra.animal.brinco.valor, "M1")
        self.assertTrue(macho.vendido)
        self.assertIn("M1", compra.resumo())

    def test_frigorifico_nao_compra_animal_ja_vendido(self):
        """Regressão: a segunda compra acusava peso insuficiente, embora o
        animal tivesse peso de abate; o motivo certo é a venda anterior."""
        frigorifico = Frigorifico("Frigorífico Pampa Sul", "12.345.678/0001-90")
        macho = Macho("M1", date(2024, 1, 1), "Nelore")
        macho.registrar_pesagem(500.0, date(2026, 1, 1))
        frigorifico.comprar_animal(macho, 2500.0)
        with self.assertRaises(AnimalVendidoError):
            frigorifico.comprar_animal(macho, 2500.0)
        self.assertEqual(len(frigorifico.historico_compras()), 1)

    def test_frigorifico_nao_compra_animal_abaixo_do_peso(self):
        frigorifico = Frigorifico("Frigorífico Pampa Sul", "12.345.678/0001-90")
        macho = Macho("M1", date(2024, 1, 1), "Nelore")
        macho.registrar_pesagem(300.0, date(2026, 1, 1))
        with self.assertRaises(PesoInsuficienteError):
            frigorifico.comprar_animal(macho, 2500.0)
        self.assertEqual(frigorifico.historico_compras(), ())


class TestRegraInseminacao(unittest.TestCase):
    def test_femea_pode_ser_inseminada(self):
        femea = Femea("F1", date(2023, 1, 1), "Nelore")
        touro = Macho("T1", date(2022, 1, 1), "Nelore")
        femea.inseminar(touro)
        self.assertTrue(femea.prenhe)

    def test_inseminar_registra_o_brinco_do_touro(self):
        """O atributo brinco_inseminacao do diagrama guarda o touro da gestação."""
        femea = Femea("F1", date(2023, 1, 1), "Nelore")
        femea.inseminar(Macho("T1", date(2022, 1, 1), "Nelore"))
        self.assertEqual(femea.brinco_inseminacao, "T1")

    def test_macho_nao_tem_metodo_de_inseminacao(self):
        """A regra vive no domínio: apenas a classe Femea tem inseminar()."""
        macho = Macho("M1", date(2023, 1, 1), "Nelore")
        touro = Macho("T1", date(2022, 1, 1), "Nelore")
        self.assertFalse(hasattr(macho, "inseminar"))
        with self.assertRaises(AttributeError):
            macho.inseminar(touro)  # type: ignore[attr-defined]

    def test_femea_prenhe_nao_pode_ser_inseminada_de_novo(self):
        femea = Femea("F1", date(2023, 1, 1), "Nelore")
        femea.inseminar(Macho("T1", date(2022, 1, 1), "Nelore"))
        outro_touro = Macho("T2", date(2022, 1, 1), "Nelore")
        with self.assertRaises(InseminacaoInvalidaError):
            femea.inseminar(outro_touro)

    def test_inseminacao_com_o_pai_e_bloqueada_por_genealogia(self):
        femea = Femea("F1", date(2023, 1, 1), "Nelore")
        femea.definir_genealogia(mae_brinco="F0", pai_brinco="T1")
        touro = Macho("T1", date(2021, 1, 1), "Nelore")
        self.assertFalse(femea.pode_inseminar(touro))
        with self.assertRaises(InseminacaoInvalidaError):
            femea.inseminar(touro)

    def test_inseminacao_com_um_filho_e_bloqueada_por_genealogia(self):
        mae = Femea("F1", date(2021, 1, 1), "Nelore")
        mae.inseminar(Macho("T1", date(2020, 1, 1), "Nelore"))
        filho = mae.registrar_parto("F2", macho=True)
        self.assertFalse(mae.pode_inseminar(filho))
        with self.assertRaises(InseminacaoInvalidaError):
            mae.inseminar(filho)


class TestPartoCriaBezerro(unittest.TestCase):
    """Conforme o diagrama: registrar_parto(brinco_filho, macho) devolve o
    bezerro, já vinculado à genealogia da mãe."""

    def setUp(self) -> None:
        self.mae = Femea("F1", date(2021, 1, 1), "Nelore")
        self.mae.inseminar(Macho("T1", date(2020, 1, 1), "Nelore"))

    def test_parto_cria_o_bezerro_vinculado_a_genealogia(self):
        bezerro = self.mae.registrar_parto("F2", macho=True)
        self.assertIsInstance(bezerro, Macho)
        self.assertEqual(bezerro.mae_brinco, "F1")
        self.assertEqual(bezerro.pai_brinco, "T1")
        self.assertIn(bezerro, self.mae.listar_filhos())

    def test_parto_de_bezerra_cria_uma_femea(self):
        bezerro = self.mae.registrar_parto("F2", macho=False)
        self.assertIsInstance(bezerro, Femea)
        self.assertEqual(bezerro.raca, "Nelore")

    def test_parto_encerra_a_gestacao_e_conta_o_parto(self):
        bezerro = self.mae.registrar_parto("F2", macho=True)
        self.assertFalse(self.mae.prenhe)
        self.assertEqual(self.mae.partos, 1)
        self.assertIsNone(self.mae.brinco_inseminacao)
        self.assertIsNotNone(bezerro)

    def test_parto_sem_estar_prenhe_viola_regra(self):
        femea = Femea("F9", date(2021, 1, 1), "Nelore")
        with self.assertRaises(RegraNegocioViolation):
            femea.registrar_parto("F10", macho=True)


class TestReproducaoMacho(unittest.TestCase):
    def test_castrar_macho_e_nao_castrar_de_novo(self):
        macho = Macho("M1", date(2023, 1, 1), "Nelore")
        macho.castrar()
        self.assertTrue(macho.castrado)
        with self.assertRaises(RegraNegocioViolation):
            macho.castrar()


class TestInsumos(unittest.TestCase):
    def test_baixar_estoque_mais_que_o_disponivel_e_bloqueado(self):
        insumo = Insumo("Ração 20%", "Nutricional", 100.0, 1.80)
        with self.assertRaises(EstoqueInsuficienteError):
            insumo.baixar_estoque(150.0)

    def test_baixar_estoque_e_adicionar_estoque(self):
        insumo = Insumo("Ração 20%", "Nutricional", 100.0, 1.80)
        insumo.baixar_estoque(30.0)
        self.assertEqual(insumo.estoque, 70.0)
        insumo.adicionar_estoque(50.0)
        self.assertEqual(insumo.estoque, 120.0)

    def test_quantidade_negativa_e_bloqueada(self):
        insumo = Insumo("Ração 20%", "Nutricional", 100.0, 1.80)
        with self.assertRaises(QuantidadeInvalidaError):
            insumo.baixar_estoque(-10.0)

    def test_base_alimentacao_guarda_os_insumos_por_referencia(self):
        base = BaseAlimentacao("Base engorda", "Ração de engorda")
        racao = Insumo("Ração 20%", "Nutricional", 1000.0, 1.80)
        sal = Insumo("Sal mineral", "Mineral", 500.0, 0.50)
        base.adicionar_insumo(racao, 2.5)
        base.adicionar_insumo(sal, 0.1)
        self.assertEqual(base.itens, ((racao, 2.5), (sal, 0.1)))
        base.remover_insumo("Ração 20%")
        self.assertEqual(base.itens, ((sal, 0.1),))

    def test_consumo_diario_e_custo_mensal_da_base(self):
        base = BaseAlimentacao("Base engorda", "Ração de engorda")
        base.adicionar_insumo(Insumo("Ração 20%", "Nutricional", 1000.0, 1.80), 2.0)
        base.adicionar_insumo(Insumo("Sal mineral", "Mineral", 500.0, 0.50), 0.1)
        self.assertAlmostEqual(base.consumo_diario_kg(), 2.1)
        esperado = (2.0 * 1.80 + 0.1 * 0.50) * 30 * 10
        self.assertAlmostEqual(base.custo_mensal(10), esperado)


class TestProprietario(unittest.TestCase):
    def test_autocadastro_exige_nome_cpf_e_senha(self):
        proprietario = Proprietario("Fulano", "000.000.000-00")
        with self.assertRaises(RegraNegocioViolation):
            proprietario.atualizar_cadastro("  ", "000.000.000-00", "s3cr3t")
        with self.assertRaises(RegraNegocioViolation):
            proprietario.atualizar_cadastro("Fulano", "", "s3cr3t")
        with self.assertRaises(RegraNegocioViolation):
            proprietario.atualizar_cadastro("Fulano", "000.000.000-00", "   ")

    def test_autocadastro_atualiza_os_dados(self):
        proprietario = Proprietario("Fulano", "000.000.000-00")
        proprietario.atualizar_cadastro("Maria", "123.456.789-00", "credencial-salva")
        self.assertEqual(proprietario.nome, "Maria")
        self.assertEqual(proprietario.cpf, "123.456.789-00")
        self.assertEqual(proprietario.senha, "credencial-salva")


class TestObjetosValor(unittest.TestCase):
    def test_peso_negativo_e_rejeitado(self):
        with self.assertRaises(PesoInvalidoError):
            Peso(-10.0)

    def test_pesos_iguais_comparam_por_valor(self):
        self.assertEqual(Peso(100.0), Peso(100.0))

    def test_brinco_vazio_e_rejeitado(self):
        from source.domain.excecoes import BrincoInvalidoError

        with self.assertRaises(BrincoInvalidoError):
            Femea("   ", date(2024, 1, 1), "Nelore")


class TestAtualizarCadastroDeOrganizacoes(unittest.TestCase):
    """O cadastro (nome + documento) é preenchido no primeiro acesso do
    fornecedor e do frigorífico, como o autocadastro do proprietário."""

    def test_fornecedor_atualiza_nome_e_cnpj(self):
        fornecedor = Fornecedor("", "")
        fornecedor.atualizar_cadastro("Agropecuária Central", "12.345.678/0001-90")
        self.assertEqual(fornecedor.nome, "Agropecuária Central")
        self.assertEqual(fornecedor.cnpj, "12.345.678/0001-90")

    def test_frigorifico_atualiza_nome_e_cnpj(self):
        frigorifico = Frigorifico("", "")
        frigorifico.atualizar_cadastro("Frigorífico Pampa Sul", "98.765.432/0001-10")
        self.assertEqual(frigorifico.nome, "Frigorífico Pampa Sul")
        self.assertEqual(frigorifico.cnpj, "98.765.432/0001-10")

    def test_cadastro_sem_nome_ou_cnpj_e_bloqueado(self):
        with self.assertRaises(RegraNegocioViolation):
            Fornecedor("", "").atualizar_cadastro("   ", "12.345.678/0001-90")
        with self.assertRaises(RegraNegocioViolation):
            Frigorifico("", "").atualizar_cadastro("Pampa Sul", "")


if __name__ == "__main__":
    unittest.main()
