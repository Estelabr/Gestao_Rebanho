"""Testes do sistema multiusuário: contas com papel, índice, credenciais
de acesso e sincronização do índice com os cadastros.

Os casos de uso são testados com dobras em memória; o índice e a fonte
de cadastros são testados contra arquivos de verdade, em pasta
temporária. A migração do sistema antigo (um usuário só) também é
coberta aqui, porque mora na composição de raiz.
"""

import json
import os
import tempfile
import unittest

from source.domain.entidades.conta import Conta, normalizar_documento
from source.domain.entidades.pessoas import Fornecedor, Frigorifico, Proprietario
from source.domain.excecoes import (
    CadastroNaoPreenchidoError,
    CredencialInvalidaError,
    DocumentoDuplicadoError,
    RegraNegocioViolation,
)
from source.domain.repositorios import (
    CriadorDeArquivos,
    RepositorioContas,
    RepositorioFornecedor,
    RepositorioFrigorifico,
    RepositorioProprietario,
)
from source.infra.repositorio_json import (
    ArquivoDados,
    FonteDeCadastros,
    IndiceContasJson,
)
from source.usecases.casos_de_uso import (
    Autocadastro,
    AutenticarConta,
    CadastrarConta,
    CadastrarFornecedor,
    CadastrarFrigorifico,
)
from source.usecases.senhas import conferir, gerar_credencial


class RepositorioContasMemoria(RepositorioContas):
    """Dobra de teste: guarda as contas em um dicionário em memória.

    Como o contrato manda, as contas são identificadas pelo documento
    comparando só os dígitos."""

    def __init__(self) -> None:
        self._contas: dict = {}

    def adicionar(self, conta: Conta) -> None:
        self._contas[normalizar_documento(conta.documento)] = conta

    def buscar_por_documento(self, documento: str):
        return self._contas.get(normalizar_documento(documento))

    def remover(self, documento: str) -> None:
        self._contas.pop(normalizar_documento(documento), None)

    def listar(self):
        return list(self._contas.values())

    def salvar(self) -> None:
        pass


class CriadorDeArquivosMemoria(CriadorDeArquivos):
    """Dobra de teste: registra a criação e devolve um caminho fictício."""

    def __init__(self) -> None:
        self.criacoes: list = []

    def caminho_de(self, documento: str) -> str:
        return f"dados_{normalizar_documento(documento)}.json"

    def criar(self, papel: str, nome: str, documento: str) -> str:
        caminho = self.caminho_de(documento)
        self.criacoes.append((papel, nome, documento, caminho))
        return caminho


class RepositorioProprietarioMemoria(RepositorioProprietario):
    """Dobra de teste: guarda o cadastro do proprietário em memória."""

    def __init__(self, proprietario: Proprietario) -> None:
        self._proprietario = proprietario

    def carregar(self):
        return self._proprietario

    def salvar(self, proprietario: Proprietario) -> None:
        self._proprietario = proprietario


class RepositorioFornecedorMemoria(RepositorioFornecedor):
    """Dobra de teste: guarda o cadastro do fornecedor em memória."""

    def __init__(self, fornecedor: Fornecedor) -> None:
        self._fornecedor = fornecedor

    def carregar(self):
        return self._fornecedor

    def salvar(self, fornecedor: Fornecedor) -> None:
        self._fornecedor = fornecedor


class RepositorioFrigorificoMemoria(RepositorioFrigorifico):
    """Dobra de teste: guarda o cadastro do frigorífico em memória."""

    def __init__(self, frigorifico: Frigorifico) -> None:
        self._frigorifico = frigorifico

    def carregar(self):
        return self._frigorifico

    def salvar(self, frigorifico: Frigorifico) -> None:
        self._frigorifico = frigorifico


class TestCadastrarConta(unittest.TestCase):
    def setUp(self) -> None:
        self.indice = RepositorioContasMemoria()
        self.criador = CriadorDeArquivosMemoria()
        self.cadastrar = CadastrarConta(self.indice, self.criador)

    def test_cria_conta_com_papel_arquivo_e_credencial(self):
        conta = self.cadastrar.executar(
            "Maria Fazendeira", "111.222.333-44", "proprietario", "segredo"
        )

        self.assertEqual(conta.nome, "Maria Fazendeira")
        self.assertEqual(conta.documento, "111.222.333-44")
        self.assertEqual(conta.papel, "proprietario")
        self.assertTrue(conta.arquivo.startswith("dados_"))
        self.assertIn(conta, self.indice.listar())
        # A credencial guardada é o hash da senha, nunca o texto plano.
        self.assertNotEqual(conta.senha, "segredo")
        self.assertTrue(conferir("segredo", conta.senha))
        # O arquivo de dados nasce pelo criador, com o papel declarado.
        self.assertEqual(
            self.criador.criacoes, [("proprietario", "Maria Fazendeira",
                                     "111.222.333-44", conta.arquivo)]
        )

    def test_papel_desconhecido_e_rejeitado(self):
        with self.assertRaises(RegraNegocioViolation):
            self.cadastrar.executar("Fulano", "11122233344", "visitante", "senha")

    def test_documento_repetido_e_rejeitado(self):
        self.cadastrar.executar("Maria", "11122233344", "proprietario", "segredo")
        with self.assertRaises(DocumentoDuplicadoError):
            self.cadastrar.executar("João", "11122233344", "fornecedor", "outra")

    def test_documento_com_pontuacao_diferente_tambem_colide(self):
        self.cadastrar.executar("Maria", "111.222.333-44", "proprietario", "segredo")
        with self.assertRaises(DocumentoDuplicadoError):
            self.cadastrar.executar("João", "11122233344", "fornecedor", "outra")

    def test_campos_obrigatorios(self):
        for nome, documento, papel, senha in [
            ("", "1", "proprietario", "s"),
            ("n", "", "proprietario", "s"),
            ("n", "1", "proprietario", ""),
        ]:
            with self.subTest(nome=nome, documento=documento, senha=senha):
                with self.assertRaises(RegraNegocioViolation):
                    self.cadastrar.executar(nome, documento, papel, senha)


class TestAutenticarConta(unittest.TestCase):
    def setUp(self) -> None:
        self.indice = RepositorioContasMemoria()
        self.cadastrar = CadastrarConta(self.indice, CriadorDeArquivosMemoria())
        self.autenticar = AutenticarConta(self.indice)

    def test_senha_correta_devolve_a_conta_com_o_papel(self):
        criada = self.cadastrar.executar("Maria", "11122233344", "fornecedor", "segredo")
        autenticada = self.autenticar.executar("111.222.333-44", "segredo")
        self.assertEqual(autenticada.arquivo, criada.arquivo)
        self.assertEqual(autenticada.papel, "fornecedor")
        self.assertEqual(autenticada.nome, "Maria")

    def test_senha_errada_e_rejeitada(self):
        self.cadastrar.executar("Maria", "11122233344", "proprietario", "segredo")
        with self.assertRaises(CredencialInvalidaError):
            self.autenticar.executar("11122233344", "errada")

    def test_documento_desconhecido_e_rejeitado(self):
        with self.assertRaises(CredencialInvalidaError):
            self.autenticar.executar("99999999999", "qualquer")


class TestAdocaoDeContaLegada(unittest.TestCase):
    """Contas migradas sem senha: o dono do documento define o acesso em
    'Criar conta' e o arquivo de dados delas é mantido."""

    def setUp(self) -> None:
        self.indice = RepositorioContasMemoria()
        self.indice.adicionar(Conta("Legado", "888", "proprietario", "dados.json"))
        self.cadastrar = CadastrarConta(self.indice, CriadorDeArquivosMemoria())
        self.autenticar = AutenticarConta(self.indice)

    def test_adota_a_conta_sem_senha_e_mantem_papel_e_arquivo(self):
        conta = self.cadastrar.executar("Legado Novo", "888", "frigorifico", "primeira")

        self.assertEqual(conta.arquivo, "dados.json")
        self.assertEqual(conta.papel, "proprietario")
        self.assertEqual(conta.nome, "Legado Novo")
        self.assertTrue(conferir("primeira", conta.senha))
        self.assertEqual(self.autenticar.executar("888", "primeira").arquivo, "dados.json")

    def test_adocao_nao_deixa_mudar_o_papel(self):
        conta = self.cadastrar.executar("Legado Novo", "888", "proprietario", "primeira")
        self.assertEqual(conta.papel, "proprietario")

    def test_conta_com_senha_nao_pode_ser_recriada(self):
        self.indice.adicionar(
            Conta("Existente", "777", "fornecedor", "dados_777.json",
                  gerar_credencial("antiga"))
        )
        with self.assertRaises(DocumentoDuplicadoError):
            self.cadastrar.executar("Outro", "777", "fornecedor", "nova")

    def test_login_sem_senha_antes_da_adocao_explica_o_caminho(self):
        with self.assertRaises(CadastroNaoPreenchidoError):
            self.autenticar.executar("888", "qualquer")


class TestSincronizacaoDoIndice(unittest.TestCase):
    """Quando o cadastro de uma conta muda pela área dela (nome,
    documento ou senha), o índice de contas acompanha."""

    def test_autocadastro_le_nome_documento_e_senha_ao_indice(self):
        indice = RepositorioContasMemoria()
        indice.adicionar(Conta("Nome antigo", "111", "proprietario", "dados.json",
                               gerar_credencial("velha")))
        proprietario = Proprietario("Nome antigo", "111", gerar_credencial("velha"))
        autocadastro = Autocadastro(
            proprietario, RepositorioProprietarioMemoria(proprietario), indice
        )

        autocadastro.executar("Nome novo", "222", "nova senha")

        self.assertIsNone(indice.buscar_por_documento("111"))
        conta = indice.buscar_por_documento("222")
        self.assertEqual(conta.nome, "Nome novo")
        self.assertEqual(conta.papel, "proprietario")
        self.assertEqual(conta.arquivo, "dados.json")
        self.assertTrue(conferir("nova senha", conta.senha))

    def test_autocadastro_nao_deixa_trocar_para_documento_ocupado(self):
        indice = RepositorioContasMemoria()
        indice.adicionar(Conta("Nome antigo", "111", "proprietario", "dados.json"))
        indice.adicionar(Conta("Outra pessoa", "222", "fornecedor", "dados_222.json"))
        proprietario = Proprietario("Nome antigo", "111", "credencial")
        autocadastro = Autocadastro(
            proprietario, RepositorioProprietarioMemoria(proprietario), indice
        )

        with self.assertRaises(DocumentoDuplicadoError):
            autocadastro.executar("Nome antigo", "222", "nova senha")
        self.assertEqual(indice.buscar_por_documento("111").nome, "Nome antigo")

    def test_cadastro_do_fornecedor_le_o_documento_novo_ao_indice(self):
        indice = RepositorioContasMemoria()
        indice.adicionar(Conta("Insumos Beltrano", "222", "fornecedor", "dados_222.json"))
        fornecedor = Fornecedor("Insumos Beltrano", "222")
        cadastro = CadastrarFornecedor(
            fornecedor, RepositorioFornecedorMemoria(fornecedor), indice
        )

        cadastro.executar("Insumos Beltrano Ltda", "22222222222222")

        self.assertIsNone(indice.buscar_por_documento("222"))
        conta = indice.buscar_por_documento("22222222222222")
        self.assertEqual(conta.nome, "Insumos Beltrano Ltda")
        self.assertEqual(conta.papel, "fornecedor")
        self.assertEqual(conta.arquivo, "dados_222.json")

    def test_cadastro_do_frigorifico_le_o_documento_novo_ao_indice(self):
        indice = RepositorioContasMemoria()
        indice.adicionar(Conta("Frigol S.A.", "555", "frigorifico", "dados_555.json"))
        frigorifico = Frigorifico("Frigol S.A.", "555")
        cadastro = CadastrarFrigorifico(
            frigorifico, RepositorioFrigorificoMemoria(frigorifico), indice
        )

        cadastro.executar("Frigol S.A.", "55555555555555")

        self.assertEqual(indice.buscar_por_documento("55555555555555").papel, "frigorifico")

    def test_documento_novo_ocupado_e_rejeitado_no_cadastro_do_fornecedor(self):
        indice = RepositorioContasMemoria()
        indice.adicionar(Conta("Insumos Beltrano", "222", "fornecedor", "dados_222.json"))
        indice.adicionar(Conta("Outra empresa", "333", "fornecedor", "dados_333.json"))
        fornecedor = Fornecedor("Insumos Beltrano", "222")
        cadastro = CadastrarFornecedor(
            fornecedor, RepositorioFornecedorMemoria(fornecedor), indice
        )

        with self.assertRaises(DocumentoDuplicadoError):
            cadastro.executar("Insumos Beltrano", "333")
        self.assertEqual(indice.buscar_por_documento("222").nome, "Insumos Beltrano")


class TestIndiceContasJson(unittest.TestCase):
    def setUp(self) -> None:
        self.__tmp = tempfile.TemporaryDirectory()
        self.__arquivo = ArquivoDados(os.path.join(self.__tmp.name, "usuarios.json"))
        self.__indice = IndiceContasJson(self.__arquivo)

    def tearDown(self) -> None:
        self.__tmp.cleanup()

    def test_salvar_e_reabrir_o_indice(self):
        self.__indice.adicionar(
            Conta("Maria", "111", "proprietario", "dados_111.json",
                  gerar_credencial("segredo"))
        )
        self.__indice.adicionar(Conta("João", "222", "fornecedor", "dados_222.json"))
        self.__indice.salvar()

        reaberto = IndiceContasJson(self.__arquivo)
        conta = reaberto.buscar_por_documento("111")
        self.assertEqual(conta.nome, "Maria")
        self.assertEqual(conta.papel, "proprietario")
        self.assertTrue(conferir("segredo", conta.senha))
        # Busca ignora a pontuação do documento digitado.
        self.assertEqual(reaberto.buscar_por_documento("2-2-2").nome, "João")

    def test_remover_some_da_persistencia(self):
        self.__indice.adicionar(Conta("Maria", "111", "proprietario", "dados_111.json"))
        self.__indice.salvar()
        self.__indice.remover("111")
        self.__indice.salvar()

        reaberto = IndiceContasJson(self.__arquivo)
        self.assertEqual(reaberto.listar(), [])

    def test_indice_no_formato_antigo_ainda_e_lido(self):
        with open(os.path.join(self.__tmp.name, "usuarios.json"),
                  "w", encoding="utf-8") as arquivo:
            json.dump(
                {"contas": [{"nome": "Antiga", "cpf": "123", "arquivo": "dados.json"}]},
                arquivo,
            )

        reaberto = IndiceContasJson(self.__arquivo)
        conta = reaberto.buscar_por_documento("123")
        self.assertEqual(conta.nome, "Antiga")
        self.assertEqual(conta.papel, "proprietario")  # papel padrão do formato antigo

    def test_credencial_do_formato_antigo_vem_do_arquivo_da_conta(self):
        """Índices antigos guardavam só nome, documento e arquivo: a
        credencial morava no cadastro do Proprietário. Na carga, ela é
        recuperada para o índice e persistida — a transição é uma vez só."""
        credencial = gerar_credencial("senha do passado")
        arquivo_de_dados = os.path.join(self.__tmp.name, "dados.json")
        dados = {"proprietario": {"nome": "Antiga", "cpf": "123", "senha": credencial}}
        with open(arquivo_de_dados, "w", encoding="utf-8") as destino:
            json.dump(dados, destino)
        with open(os.path.join(self.__tmp.name, "usuarios.json"),
                  "w", encoding="utf-8") as arquivo:
            json.dump(
                {"contas": [{"nome": "Antiga", "cpf": "123",
                             "arquivo": arquivo_de_dados}]},
                arquivo,
            )

        reaberto = IndiceContasJson(self.__arquivo)
        conta = reaberto.buscar_por_documento("123")
        self.assertTrue(conferir("senha do passado", conta.senha))

        reaberto_de_novo = IndiceContasJson(self.__arquivo)
        self.assertTrue(
            conferir("senha do passado", reaberto_de_novo.buscar_por_documento("123").senha)
        )


class TestFonteDeCadastros(unittest.TestCase):
    """A criação semeia no arquivo o cadastro do papel da conta."""

    def setUp(self) -> None:
        self.__tmp = tempfile.TemporaryDirectory()
        self.__antigo = os.getcwd()
        os.chdir(self.__tmp.name)
        self.__fonte = FonteDeCadastros()

    def tearDown(self) -> None:
        os.chdir(self.__antigo)
        self.__tmp.cleanup()

    def test_caminho_da_conta_usa_so_digitos_do_documento(self):
        self.assertEqual(
            self.__fonte.caminho_de("111.222.333-44"), "dados_11122233344.json"
        )

    def test_criar_proprietario_semeia_a_secao_proprietario(self):
        arquivo = self.__fonte.criar("proprietario", "Maria", "111")
        cadastro = _ler_json(arquivo)["proprietario"]
        self.assertEqual(cadastro["nome"], "Maria")
        self.assertEqual(cadastro["cpf"], "111")

    def test_criar_fornecedor_semeia_a_secao_fornecedor_cadastro(self):
        arquivo = self.__fonte.criar("fornecedor", "Insumos Beltrano", "222")
        cadastro = _ler_json(arquivo)["fornecedor_cadastro"]
        self.assertEqual(cadastro["nome"], "Insumos Beltrano")
        self.assertEqual(cadastro["cnpj"], "222")

    def test_criar_frigorifico_semeia_a_secao_frigorifico(self):
        arquivo = self.__fonte.criar("frigorifico", "Frigol", "333")
        cadastro = _ler_json(arquivo)["frigorifico"]
        self.assertEqual(cadastro["nome"], "Frigol")
        self.assertEqual(cadastro["cnpj"], "333")

    def test_criar_com_papel_desconhecido_falha_sem_criar_arquivo(self):
        """Antes o papel desconhecido devolvia o caminho de um arquivo que
        nunca era criado, e o erro só aparecia no login seguinte."""
        with self.assertRaises(RegraNegocioViolation):
            self.__fonte.criar("veterinario", "Fulano", "444")
        self.assertFalse(os.path.exists(self.__fonte.caminho_de("444")))


def _ler_json(caminho: str) -> dict:
    """Lê o JSON gerado pela fonte, para conferir o que foi semeado."""
    with open(caminho, "r", encoding="utf-8") as origem:
        return json.load(origem)


class TestMigracaoLegado(unittest.TestCase):
    """O sistema antigo tinha um único cadastro em dados.json: na
    primeira execução multiusuário, ele se torna a primeira conta do
    papel Proprietário, com a credencial que já estava no arquivo."""

    def setUp(self) -> None:
        self.__tmp = tempfile.TemporaryDirectory()
        self.__antigo = os.getcwd()
        os.chdir(self.__tmp.name)

    def tearDown(self) -> None:
        os.chdir(self.__antigo)
        self.__tmp.cleanup()

    def test_cadastro_legado_vira_a_primeira_conta_com_a_credencial(self):
        credencial = gerar_credencial("segredo do legado")
        with open("dados.json", "w", encoding="utf-8") as arquivo:
            json.dump(
                {
                    "proprietario": {
                        "nome": "Legado",
                        "cpf": "123",
                        "senha": credencial,
                    }
                },
                arquivo,
                ensure_ascii=False,
            )

        import main

        indice = main.montar_indice_de_contas()

        conta = indice.buscar_por_documento("123")
        self.assertIsNotNone(conta)
        self.assertEqual(conta.nome, "Legado")
        self.assertEqual(conta.papel, "proprietario")
        self.assertEqual(conta.arquivo, "dados.json")
        self.assertTrue(conferir("segredo do legado", conta.senha))
        # O índice persistido não re-migra na próxima execução:
        self.assertTrue(os.path.exists("usuarios.json"))

    def test_sem_dados_legados_o_indice_nasce_vazio(self):
        import main

        self.assertEqual(main.montar_indice_de_contas().listar(), [])


if __name__ == "__main__":
    unittest.main()
