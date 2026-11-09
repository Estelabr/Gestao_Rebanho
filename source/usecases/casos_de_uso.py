"""Casos de uso do sistema de gestão de rebanho.

Um caso de uso por classe (uma bolha do diagrama de casos de uso), com o
nome falando a mesma língua do domínio (linguagem onipresente do DDD). Eles
são a única porta de entrada para a apresentação (console e Tkinter), que
nunca chama o domínio diretamente.
"""

from datetime import date
from typing import List, Optional, Tuple

from source.domain.entidades.animal import Animal, Femea, Macho
from source.domain.entidades.insumo import BaseAlimentacao, Insumo
from source.domain.entidades.manejo import Pesagem, Vacinacao
from source.domain.entidades.pessoas import CompraAnimal, Fornecedor, Frigorifico, Proprietario
from source.domain.excecoes import (
    AnimalNaoEncontradoError,
    BaseDuplicadaError,
    BaseNaoEncontradaError,
    BrincoDuplicadoError,
    InseminacaoInvalidaError,
    InsumoNaoEncontradoError,
    RegraNegocioViolation,
)
from source.domain.repositorios import (
    RepositorioAnimais,
    RepositorioBases,
    RepositorioCompras,
    RepositorioInsumos,
    RepositorioProprietario,
)


class CadastrarAnimal:
    """Cadastrar animal: cria a Femea ou o Macho e guarda no rebanho."""

    def __init__(
        self, repositorio_animais: RepositorioAnimais, proprietario: Proprietario
    ) -> None:
        self.__repositorio = repositorio_animais
        self.__proprietario = proprietario

    def executar(self, brinco: str, data_nascimento: date, raca: str, tipo: str) -> Animal:
        if tipo == "femea":
            animal: Animal = Femea(brinco, data_nascimento, raca)
        elif tipo == "macho":
            animal = Macho(brinco, data_nascimento, raca)
        else:
            raise RegraNegocioViolation(f"Tipo de animal inválido: {tipo}.")
        if self.__repositorio.buscar_por_brinco(brinco) is not None:
            raise BrincoDuplicadoError(f"Já existe um animal com o brinco {brinco}.")
        self.__repositorio.adicionar(animal)
        self.__proprietario.adicionar_animal(animal)
        return animal


class RegistrarPesagem:
    """Registrar pesagem de um animal do rebanho."""

    def __init__(self, repositorio_animais: RepositorioAnimais) -> None:
        self.__repositorio = repositorio_animais

    def executar(self, brinco: str, kg: float, data: Optional[date] = None) -> Pesagem:
        animal = self.__repositorio.buscar_por_brinco(brinco)
        if animal is None:
            raise AnimalNaoEncontradoError(f"Animal {brinco} não encontrado.")
        pesagem = animal.registrar_pesagem(kg, data or date.today())
        self.__repositorio.salvar()
        return pesagem


class RegistrarVacinacao:
    """Registrar vacinação de um animal do rebanho."""

    def __init__(self, repositorio_animais: RepositorioAnimais) -> None:
        self.__repositorio = repositorio_animais

    def executar(
        self, brinco: str, vacina: str, dose: str, data: Optional[date] = None
    ) -> Vacinacao:
        animal = self.__repositorio.buscar_por_brinco(brinco)
        if animal is None:
            raise AnimalNaoEncontradoError(f"Animal {brinco} não encontrado.")
        vacinacao = animal.registrar_vacinacao(vacina, dose, data or date.today())
        self.__repositorio.salvar()
        return vacinacao


class InseminarFemea:
    """Realizar inseminação de uma fêmea com um touro do rebanho."""

    def __init__(self, repositorio_animais: RepositorioAnimais) -> None:
        self.__repositorio = repositorio_animais

    def executar(self, brinco_femea: str, brinco_touro: str) -> None:
        femea = self.__repositorio.buscar_por_brinco(brinco_femea)
        touro = self.__repositorio.buscar_por_brinco(brinco_touro)
        if femea is None or touro is None:
            faltando = brinco_femea if femea is None else brinco_touro
            raise AnimalNaoEncontradoError(f"Animal {faltando} não encontrado.")
        if not isinstance(femea, Femea):
            raise InseminacaoInvalidaError(
                f"Animal {brinco_femea} não é fêmea, então não pode ser inseminado."
            )
        if not isinstance(touro, Macho):
            raise InseminacaoInvalidaError(
                f"Animal {brinco_touro} não é macho, então não pode ser touro."
            )
        femea.inseminar(touro)
        self.__repositorio.salvar()


class RegistrarParto:
    """Registrar o parto de uma fêmea: o bezerro nasce já vinculado à mãe
    e à genealogia, e entra no rebanho."""

    def __init__(
        self, repositorio_animais: RepositorioAnimais, proprietario: Proprietario
    ) -> None:
        self.__repositorio = repositorio_animais
        self.__proprietario = proprietario

    def executar(self, brinco_femea: str, brinco_filho: str, macho: bool) -> Animal:
        femea = self.__repositorio.buscar_por_brinco(brinco_femea)
        if femea is None:
            raise AnimalNaoEncontradoError(f"Animal {brinco_femea} não encontrado.")
        if not isinstance(femea, Femea):
            raise RegraNegocioViolation(
                f"Animal {brinco_femea} não é fêmea, então não tem parto a registrar."
            )
        if self.__repositorio.buscar_por_brinco(brinco_filho) is not None:
            raise BrincoDuplicadoError(f"Já existe um animal com o brinco {brinco_filho}.")
        bezerro = femea.registrar_parto(brinco_filho, macho)
        self.__repositorio.adicionar(bezerro)
        self.__proprietario.adicionar_animal(bezerro)
        self.__repositorio.salvar()
        return bezerro


class VenderAnimal:
    """Vender um animal ao frigorífico."""

    def __init__(
        self,
        repositorio_animais: RepositorioAnimais,
        frigorifico: Frigorifico,
        repositorio_compras: RepositorioCompras,
    ) -> None:
        self.__repositorio_animais = repositorio_animais
        self.__frigorifico = frigorifico
        self.__repositorio_compras = repositorio_compras

    def executar(self, brinco: str, valor: float) -> CompraAnimal:
        animal = self.__repositorio_animais.buscar_por_brinco(brinco)
        if animal is None:
            raise AnimalNaoEncontradoError(f"Animal {brinco} não encontrado.")
        compra = self.__frigorifico.comprar_animal(animal, valor)
        self.__repositorio_compras.adicionar(compra)
        self.__repositorio_compras.salvar()
        self.__repositorio_animais.salvar()
        return compra


class IdentificarAnimaisParaVenda:
    """Identificar animais para venda: lista quem já atingiu o peso mínimo
    de abate. Serve tanto ao Proprietário (Identificar Animais para Venda)
    quanto ao Frigorífico (Consultar Animais Disponíveis para Compra), como
    no diagrama de casos de uso."""

    def __init__(self, repositorio_animais: RepositorioAnimais) -> None:
        self.__repositorio = repositorio_animais

    def executar(self) -> Tuple[Animal, ...]:
        return tuple(animal for animal in self.__repositorio.listar() if animal.pode_vender())


class HistoricoCompras:
    """Histórico de compras do frigorífico."""

    def __init__(self, frigorifico: Frigorifico) -> None:
        self.__frigorifico = frigorifico

    def executar(self) -> Tuple[CompraAnimal, ...]:
        return self.__frigorifico.historico_compras()


class CriarBaseAlimentacao:
    """Gerenciar nutrição do gado: cria uma base de alimentação a partir
    dos insumos do estoque da fazenda."""

    def __init__(
        self,
        repositorio_bases: RepositorioBases,
        repositorio_insumos: RepositorioInsumos,
        proprietario: Proprietario,
    ) -> None:
        self.__repositorio_bases = repositorio_bases
        self.__repositorio_insumos = repositorio_insumos
        self.__proprietario = proprietario

    def executar(
        self, nome: str, descricao: str, itens: List[Tuple[str, float]]
    ) -> BaseAlimentacao:
        if self.__repositorio_bases.buscar_por_nome(nome) is not None:
            raise BaseDuplicadaError(f"Já existe uma base de alimentação chamada {nome}.")
        base = BaseAlimentacao(nome, descricao)
        for nome_insumo, quantidade in itens:
            insumo = self.__repositorio_insumos.buscar_por_nome(nome_insumo)
            if insumo is None:
                raise InsumoNaoEncontradoError(
                    f"Insumo {nome_insumo} não encontrado no estoque da fazenda."
                )
            base.adicionar_insumo(insumo, quantidade)
        self.__repositorio_bases.adicionar(base)
        self.__repositorio_bases.salvar()
        self.__proprietario.adicionar_base(base)
        return base


class DefinirAlimentacao:
    """Gerenciar nutrição do gado: atribui uma base de alimentação a um
    animal do rebanho."""

    def __init__(
        self, repositorio_animais: RepositorioAnimais, repositorio_bases: RepositorioBases
    ) -> None:
        self.__repositorio_animais = repositorio_animais
        self.__repositorio_bases = repositorio_bases

    def executar(self, brinco: str, nome_base: str) -> Animal:
        animal = self.__repositorio_animais.buscar_por_brinco(brinco)
        if animal is None:
            raise AnimalNaoEncontradoError(f"Animal {brinco} não encontrado.")
        base = self.__repositorio_bases.buscar_por_nome(nome_base)
        if base is None:
            raise BaseNaoEncontradaError(
                f"Base de alimentação {nome_base} não encontrada."
            )
        if animal.vendido:
            raise RegraNegocioViolation(
                f"Animal {brinco} já foi vendido, então não recebe alimentação."
            )
        animal.definir_alimentacao(base)
        self.__repositorio_animais.salvar()
        return animal


class ConsultarAlimentacao:
    """Consultar alimentação do animal (include de Gerenciar Nutrição):
    devolve o resumo da base atribuída ao animal."""

    def __init__(self, repositorio_animais: RepositorioAnimais) -> None:
        self.__repositorio = repositorio_animais

    def executar(self, brinco: str) -> str:
        animal = self.__repositorio.buscar_por_brinco(brinco)
        if animal is None:
            raise AnimalNaoEncontradoError(f"Animal {brinco} não encontrado.")
        base = animal.alimentacao()
        if base is None:
            return f"O animal {brinco} ainda não tem base de alimentação definida."
        linhas = [f"Base {base.nome} — {base.descricao}"]
        for insumo, quantidade in base.itens:
            linhas.append(f"  - {insumo.nome}: {quantidade:.2f} por animal/dia")
        linhas.append(f"Consumo diário: {base.consumo_diario_kg():.2f} kg por animal")
        linhas.append(f"Custo mensal por animal: R$ {base.custo_mensal(1):.2f}")
        return "\n".join(linhas)


class ConsultarGenetica:
    """Consultar genética (include de Realizar Inseminação): devolve a
    genealogia do animal — mãe, pai e, para fêmeas, os filhos."""

    def __init__(self, repositorio_animais: RepositorioAnimais) -> None:
        self.__repositorio = repositorio_animais

    def executar(self, brinco: str) -> str:
        animal = self.__repositorio.buscar_por_brinco(brinco)
        if animal is None:
            raise AnimalNaoEncontradoError(f"Animal {brinco} não encontrado.")
        linhas = [f"Genética do animal {brinco}:"]
        linhas.append(f"  Mãe: {animal.mae_brinco or 'desconhecida'}")
        linhas.append(f"  Pai: {animal.pai_brinco or 'desconhecido'}")
        if isinstance(animal, Femea):
            filhos = animal.listar_filhos()
            linhas.append(
                "  Filhos: "
                + (", ".join(filho.brinco.valor for filho in filhos) or "nenhum")
            )
        return "\n".join(linhas)


class CadastrarInsumo:
    """Cadastrar insumo: o fornecedor cria um produto no catálogo dele
    (ou repõe o estoque do lote, se o insumo já existe)."""

    def __init__(
        self, repositorio_catalogo: RepositorioInsumos, fornecedor: Fornecedor
    ) -> None:
        self.__repositorio = repositorio_catalogo
        self.__fornecedor = fornecedor

    def executar(self, nome: str, tipo: str, quantidade: float, preco: float) -> Insumo:
        lote = self.__fornecedor.buscar_insumo(nome)
        if lote is None:
            lote = Insumo(nome, tipo, quantidade, preco)
            self.__repositorio.adicionar(lote)
        else:
            lote.adicionar_estoque(quantidade)
        self.__fornecedor.cadastrar_insumo(lote)
        self.__repositorio.salvar()
        return lote


def _transacao_insumo(
    fornecedor: Fornecedor,
    repositorio_fazenda: RepositorioInsumos,
    repositorio_catalogo: RepositorioInsumos,
    proprietario: Proprietario,
    nome: str,
    quantidade: float,
) -> Insumo:
    """Núcleo compartilhado por ComprarInsumo (visão do proprietário) e
    VenderInsumo (visão do fornecedor): é a mesma transação vista pelos
    dois atores. O fornecedor baixa o lote dele (baixar_estoque em uso
    real) e a fazenda recebe a quantidade no estoque."""
    lote = fornecedor.vender_insumo(nome, quantidade)
    insumo = repositorio_fazenda.buscar_por_nome(lote.nome)
    if insumo is None:
        insumo = Insumo(lote.nome, lote.tipo, 0.0, lote.preco)
        repositorio_fazenda.adicionar(insumo)
    proprietario.comprar_insumo(insumo, quantidade)
    repositorio_catalogo.salvar()
    repositorio_fazenda.salvar()
    return insumo


class ComprarInsumo:
    """Comprar insumo: o proprietário adquire uma quantidade do estoque do
    fornecedor e guarda no estoque da fazenda."""

    def __init__(
        self,
        repositorio_insumos: RepositorioInsumos,
        repositorio_catalogo: RepositorioInsumos,
        fornecedor: Fornecedor,
        proprietario: Proprietario,
    ) -> None:
        self.__repositorio_insumos = repositorio_insumos
        self.__repositorio_catalogo = repositorio_catalogo
        self.__fornecedor = fornecedor
        self.__proprietario = proprietario

    def executar(self, nome: str, quantidade: float) -> Insumo:
        return _transacao_insumo(
            self.__fornecedor,
            self.__repositorio_insumos,
            self.__repositorio_catalogo,
            self.__proprietario,
            nome,
            quantidade,
        )


class VenderInsumo:
    """Vender insumo: o fornecedor vende um lote do catálogo dele ao
    proprietário, que recebe a mercadoria no estoque da fazenda."""

    def __init__(
        self,
        repositorio_insumos: RepositorioInsumos,
        repositorio_catalogo: RepositorioInsumos,
        fornecedor: Fornecedor,
        proprietario: Proprietario,
    ) -> None:
        self.__repositorio_insumos = repositorio_insumos
        self.__repositorio_catalogo = repositorio_catalogo
        self.__fornecedor = fornecedor
        self.__proprietario = proprietario

    def executar(self, nome: str, quantidade: float) -> Insumo:
        return _transacao_insumo(
            self.__fornecedor,
            self.__repositorio_insumos,
            self.__repositorio_catalogo,
            self.__proprietario,
            nome,
            quantidade,
        )


class Autocadastro:
    """Autocadastro do usuário: define (ou corrige) o cadastro do
    proprietário da propriedade."""

    def __init__(self, proprietario: Proprietario, repositorio: RepositorioProprietario) -> None:
        self.__proprietario = proprietario
        self.__repositorio = repositorio

    def executar(self, nome: str, cpf: str) -> Proprietario:
        self.__proprietario.atualizar_cadastro(nome, cpf)
        self.__repositorio.salvar(self.__proprietario)
        return self.__proprietario
