"""Pessoas e organizações do sistema: Proprietário, Fornecedor e Frigorífico.

Agregação: o Proprietário agrega animais e bases de alimentação, e o
Fornecedor agrega insumos — as partes continuam existindo sem o todo.
Composição: o Frigorífico agrega as CompraAnimal, que não existem sem ele.
"""

from datetime import date
from typing import List, Optional, Tuple

from source.domain.entidades.animal import Animal
from source.domain.entidades.insumo import BaseAlimentacao, Insumo
from source.domain.excecoes import (
    InsumoNaoEncontradoError,
    PesoInsuficienteError,
    RegraNegocioViolation,
)


class Proprietario:
    """Proprietário da propriedade rural, quem mais usa o sistema."""

    def __init__(self, nome: str, cpf: str, senha: str = "") -> None:
        self.__nome = nome
        self.__cpf = cpf
        self.__senha = senha
        self.__animais: List[Animal] = []
        self.__bases: List[BaseAlimentacao] = []

    @property
    def nome(self) -> str:
        return self.__nome

    @property
    def cpf(self) -> str:
        return self.__cpf

    @property
    def senha(self) -> str:
        """Credencial de acesso do autocadastro (hash, nunca texto plano)."""
        return self.__senha

    def atualizar_cadastro(self, nome: str, cpf: str, senha: str) -> None:
        """Autocadastro do usuário: define (ou corrige) nome, CPF e senha.

        A senha chega já como credencial (hash gerado pela camada de
        aplicação); o domínio só exige que ela exista."""
        if not nome.strip() or not cpf.strip() or not senha.strip():
            raise RegraNegocioViolation(
                "Nome, CPF e senha são obrigatórios no autocadastro."
            )
        self.__nome = nome.strip()
        self.__cpf = cpf.strip()
        self.__senha = senha.strip()

    def adicionar_animal(self, animal: Animal) -> None:
        self.__animais.append(animal)

    def listar_animais(self) -> Tuple[Animal, ...]:
        return tuple(self.__animais)

    def adicionar_base(self, base: BaseAlimentacao) -> None:
        self.__bases.append(base)

    def listar_bases(self) -> Tuple[BaseAlimentacao, ...]:
        return tuple(self.__bases)

    def comprar_insumo(self, insumo: Insumo, quantidade: float) -> None:
        """O proprietário compra e recebe o insumo no estoque da fazenda."""
        insumo.adicionar_estoque(quantidade)


class Fornecedor:
    """Fornecedor que vende insumos para a fazenda."""

    def __init__(self, nome: str, cnpj: str) -> None:
        self.__nome = nome
        self.__cnpj = cnpj
        self.__insumos: List[Insumo] = []

    @property
    def nome(self) -> str:
        return self.__nome

    @property
    def cnpj(self) -> str:
        return self.__cnpj

    def atualizar_cadastro(self, nome: str, cnpj: str) -> None:
        """Cadastro no primeiro acesso: define (ou corrige) nome e CNPJ."""
        if not nome.strip() or not cnpj.strip():
            raise RegraNegocioViolation("Nome e CNPJ são obrigatórios no cadastro.")
        self.__nome = nome.strip()
        self.__cnpj = cnpj.strip()

    def cadastrar_insumo(self, insumo: Insumo) -> None:
        """Agrega o insumo ao catálogo do fornecedor, sem duplicar."""
        if not any(catalogado.nome == insumo.nome for catalogado in self.__insumos):
            self.__insumos.append(insumo)

    def buscar_insumo(self, nome: str) -> Optional[Insumo]:
        return next((i for i in self.__insumos if i.nome == nome), None)

    def listar_insumos(self) -> Tuple[Insumo, ...]:
        return tuple(self.__insumos)

    def vender_insumo(self, nome: str, quantidade: float) -> Insumo:
        """O fornecedor vende do lote dele: valida a existência no catálogo
        e baixa o estoque (o baixar_estoque do diagrama, em uso real)."""
        insumo = self.buscar_insumo(nome)
        if insumo is None:
            raise InsumoNaoEncontradoError(
                f"O fornecedor {self.__nome} não tem o insumo {nome} no catálogo."
            )
        insumo.baixar_estoque(quantidade)
        return insumo


class CompraAnimal:
    """Compra de um animal pelo frigorífico. Composição: não existe sem o
    frigorífico que a fez."""

    def __init__(self, data: date, animal: Animal, valor: float) -> None:
        self.__data = data
        self.__animal = animal
        self.__valor = valor

    @property
    def data(self) -> date:
        return self.__data

    @property
    def animal(self) -> Animal:
        return self.__animal

    @property
    def valor(self) -> float:
        return self.__valor

    def resumo(self) -> str:
        return (
            f"{self.__data.isoformat()} - animal {self.__animal.brinco.valor} "
            f"por R$ {self.__valor:.2f}"
        )

    def __str__(self) -> str:
        return self.resumo()


class Frigorifico:
    """Frigorífico que compra animais do rebanho."""

    def __init__(self, nome: str, cnpj: str) -> None:
        self.__nome = nome
        self.__cnpj = cnpj
        self.__compras: List[CompraAnimal] = []

    @property
    def nome(self) -> str:
        return self.__nome

    @property
    def cnpj(self) -> str:
        return self.__cnpj

    def atualizar_cadastro(self, nome: str, cnpj: str) -> None:
        """Cadastro no primeiro acesso: define (ou corrige) nome e CNPJ."""
        if not nome.strip() or not cnpj.strip():
            raise RegraNegocioViolation("Nome e CNPJ são obrigatórios no cadastro.")
        self.__nome = nome.strip()
        self.__cnpj = cnpj.strip()

    def comprar_animal(
        self, animal: Animal, valor: float, data: Optional[date] = None
    ) -> CompraAnimal:
        """Regra de negócio 1: o frigorífico só compra animais que podem ser
        vendidos (peso mínimo de abate atingido). O próprio animal é quem
        valida e se marca como vendido."""
        if not animal.pode_vender():
            raise PesoInsuficienteError(
                f"Animal {animal.brinco.valor} não pode ser vendido: o mínimo de "
                f"abate é {animal.peso_minimo_abate():.1f} kg."
            )
        animal.marcar_vendido()
        compra = CompraAnimal(data or date.today(), animal, valor)
        self.__compras.append(compra)
        return compra

    def historico_compras(self) -> Tuple[CompraAnimal, ...]:
        return tuple(self.__compras)

    def restaurar_compras(self, compras: List[CompraAnimal]) -> None:
        """Reconstrói o histórico salvo no repositório (não é regra de negócio)."""
        self.__compras = list(compras)
