"""Contêiner dos casos de uso, montado pela composição de raiz (main.py).

A apresentação recebe este objeto e só chama casos de uso — nunca toca
direto no domínio ou no repositório. As consultas de listagem (animais,
insumos, bases) são leituras diretas do repositório, sem regra de negócio.
"""

from typing import List, Tuple

from source.domain.entidades.animal import Animal
from source.domain.entidades.conta import Conta
from source.domain.entidades.insumo import BaseAlimentacao, Insumo
from source.domain.entidades.pessoas import Fornecedor, Frigorifico, Proprietario
from source.domain.excecoes import RegraNegocioViolation
from source.domain.repositorios import (
    RepositorioAnimais,
    RepositorioBases,
    RepositorioInsumos,
)
from source.usecases.casos_de_uso import (
    AutenticarConta,
    Autocadastro,
    CadastrarAnimal,
    CadastrarConta,
    CadastrarFornecedor,
    CadastrarFrigorifico,
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


class CasosDeUso:
    """Reúne todos os casos de uso e as listagens do sistema."""

    def __init__(
        self,
        cadastrar_animal: CadastrarAnimal,
        registrar_pesagem: RegistrarPesagem,
        registrar_vacinacao: RegistrarVacinacao,
        inseminar_femea: InseminarFemea,
        registrar_parto: RegistrarParto,
        vender_animal: VenderAnimal,
        criar_base: CriarBaseAlimentacao,
        definir_alimentacao: DefinirAlimentacao,
        consultar_alimentacao: ConsultarAlimentacao,
        consultar_genetica: ConsultarGenetica,
        identificar_para_venda: IdentificarAnimaisParaVenda,
        historico_compras: HistoricoCompras,
        comprar_insumo: ComprarInsumo,
        vender_insumo: VenderInsumo,
        cadastrar_insumo: CadastrarInsumo,
        autocadastro: Autocadastro,
        cadastrar_fornecedor: CadastrarFornecedor,
        cadastrar_frigorifico: CadastrarFrigorifico,
        cadastrar_conta: CadastrarConta,
        autenticar_conta: AutenticarConta,
        conta: Conta,
        proprietario: Proprietario,
        fornecedor: Fornecedor,
        frigorifico: Frigorifico,
        repositorio_animais: RepositorioAnimais,
        repositorio_insumos: RepositorioInsumos,
        repositorio_bases: RepositorioBases,
        repositorio_catalogo: RepositorioInsumos,
    ) -> None:
        self.cadastrar_animal = cadastrar_animal
        self.registrar_pesagem = registrar_pesagem
        self.registrar_vacinacao = registrar_vacinacao
        self.inseminar_femea = inseminar_femea
        self.registrar_parto = registrar_parto
        self.vender_animal = vender_animal
        self.criar_base = criar_base
        self.definir_alimentacao = definir_alimentacao
        self.consultar_alimentacao = consultar_alimentacao
        self.consultar_genetica = consultar_genetica
        self.identificar_para_venda = identificar_para_venda
        self.historico_compras = historico_compras
        self.comprar_insumo = comprar_insumo
        self.vender_insumo = vender_insumo
        self.cadastrar_insumo = cadastrar_insumo
        self.autocadastro = autocadastro
        self.cadastrar_fornecedor = cadastrar_fornecedor
        self.cadastrar_frigorifico = cadastrar_frigorifico
        self.cadastrar_conta = cadastrar_conta
        self.autenticar_conta = autenticar_conta
        self.__conta = conta
        self.__proprietario = proprietario
        self.__fornecedor = fornecedor
        self.__frigorifico = frigorifico
        self.__repositorio_animais = repositorio_animais
        self.__repositorio_insumos = repositorio_insumos
        self.__repositorio_bases = repositorio_bases
        self.__repositorio_catalogo = repositorio_catalogo

    def animais(self) -> List[Animal]:
        """Lista os animais do rebanho (leitura, sem regra de negócio)."""
        return self.__repositorio_animais.listar()

    def insumos(self) -> List[Insumo]:
        """Lista os insumos em estoque (leitura, sem regra de negócio)."""
        return self.__repositorio_insumos.listar()

    def bases(self) -> List[BaseAlimentacao]:
        """Lista as bases de alimentação (leitura, sem regra de negócio)."""
        return self.__repositorio_bases.listar()

    def catalogo_fornecedor(self) -> List[Insumo]:
        """Lista os lotes do catálogo do fornecedor (leitura, sem regra)."""
        return self.__repositorio_catalogo.listar()

    def excluir_animal(self, brinco: str) -> None:
        """Exclui um animal do rebanho pelo brinco."""
        self.__repositorio_animais.remover(brinco)
        self.__repositorio_animais.salvar()

    # ------------------------------------------------------------------
    # Leituras de cadastro (dados do papel, sem regra de negócio)
    # ------------------------------------------------------------------
    def usuario(self) -> Conta:
        """A conta autenticada que está usando o sistema neste momento."""
        return self.__conta

    def cadastro(self, papel: str) -> Tuple[str, str]:
        """Devolve (nome, documento) do cadastro do papel informado.

        O documento é o CPF do proprietário ou o CNPJ do fornecedor e do
        frigorífico — é o cadastro da conta logada, semeado no arquivo
        dela quando a conta nasceu."""
        if papel == "proprietario":
            cadastro = self.__proprietario
            documento = cadastro.cpf
        elif papel == "fornecedor":
            cadastro = self.__fornecedor
            documento = cadastro.cnpj
        elif papel == "frigorifico":
            cadastro = self.__frigorifico
            documento = cadastro.cnpj
        else:
            raise RegraNegocioViolation(f"Papel desconhecido: {papel}.")
        return cadastro.nome, documento

    def resumo_cadastro(self, papel: str) -> str:
        """Resumo do cadastro para exibir na área do papel."""
        nome, documento = self.cadastro(papel)
        if not nome or not documento:
            return "cadastro não preenchido"
        rotulo = "CPF" if papel == "proprietario" else "CNPJ"
        return f"{nome} ({rotulo} {documento})"
