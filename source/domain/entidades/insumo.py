"""Insumos da fazenda e as bases de alimentação que os usam."""

from typing import List, Tuple

from source.domain.excecoes import EstoqueInsuficienteError, QuantidadeInvalidaError

DIAS_NO_MES = 30


class Insumo:
    """Insumo da fazenda (ração, vacina, medicamento) com o seu estoque."""

    def __init__(self, nome: str, tipo: str, estoque: float, preco: float) -> None:
        self.__nome = nome
        self.__tipo = tipo
        self.__estoque = float(estoque)
        self.__preco = float(preco)

    @property
    def nome(self) -> str:
        return self.__nome

    @property
    def tipo(self) -> str:
        return self.__tipo

    @property
    def estoque(self) -> float:
        return self.__estoque

    @property
    def preco(self) -> float:
        return self.__preco

    def baixar_estoque(self, quantidade: float) -> None:
        """Regra de negócio: o estoque nunca fica negativo."""
        if quantidade <= 0:
            raise QuantidadeInvalidaError("A quantidade a baixar deve ser maior que zero.")
        if quantidade > self.__estoque:
            raise EstoqueInsuficienteError(
                f"Estoque de {self.__nome} insuficiente: há {self.__estoque:.2f} "
                f"e pediu {quantidade:.2f}."
            )
        self.__estoque -= quantidade

    def adicionar_estoque(self, quantidade: float) -> None:
        if quantidade <= 0:
            raise QuantidadeInvalidaError("A quantidade a adicionar deve ser maior que zero.")
        self.__estoque += quantidade

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Insumo):
            return NotImplemented
        return self.__nome == other.__nome

    def __str__(self) -> str:
        return f"{self.__nome} ({self.__tipo}) - {self.__estoque:.2f} un"


class BaseAlimentacao:
    """Base de alimentação: mistura de insumos com uma quantidade por insumo.

    A associação 'usa' do diagrama: a base usa insumos de 1..*, guardados
    por referência ao objeto, junto da quantidade usada por animal/dia.
    """

    def __init__(self, nome: str, descricao: str) -> None:
        self.__nome = nome
        self.__descricao = descricao
        self.__itens: List[Tuple[Insumo, float]] = []

    @property
    def nome(self) -> str:
        return self.__nome

    @property
    def descricao(self) -> str:
        return self.__descricao

    @property
    def itens(self) -> Tuple[Tuple[Insumo, float], ...]:
        """Cópia da lista de (insumo, quantidade usada por animal/dia)."""
        return tuple(self.__itens)

    def adicionar_insumo(self, insumo: Insumo, quantidade: float) -> None:
        if quantidade <= 0:
            raise QuantidadeInvalidaError("A quantidade na base deve ser maior que zero.")
        for indice, (existente, _) in enumerate(self.__itens):
            if existente.nome == insumo.nome:
                self.__itens[indice] = (insumo, quantidade)
                return
        self.__itens.append((insumo, quantidade))

    def remover_insumo(self, nome_insumo: str) -> None:
        self.__itens = [
            (insumo, quantidade)
            for insumo, quantidade in self.__itens
            if insumo.nome != nome_insumo
        ]

    def consumo_diario_kg(self) -> float:
        """Consumo total da base, em kg por animal por dia."""
        return sum(quantidade for _, quantidade in self.__itens)

    def custo_mensal(self, qtd_animais: int) -> float:
        """Custo mensal da base para alimentar uma quantidade de animais:
        soma de (quantidade x preço do insumo) por dia, x 30 dias."""
        if qtd_animais < 0:
            raise QuantidadeInvalidaError(
                "A quantidade de animais não pode ser negativa."
            )
        custo_diario = sum(insumo.preco * quantidade for insumo, quantidade in self.__itens)
        return custo_diario * DIAS_NO_MES * qtd_animais

    def __str__(self) -> str:
        return f"{self.__nome} - {len(self.__itens)} insumo(s)"
