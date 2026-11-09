"""Classe abstrata Animal e suas especializações Femea e Macho.

Abstração: no sistema todo animal é fêmea ou macho, então não faz sentido
criar um animal sem saber qual dos dois ele é. Por isso Animal não é
instanciável: ela guarda o que é comum (brinco, nascimento, raça, pesagens,
vacinas) e deixa categoria() e peso_minimo_abate() por conta das subclasses,
por meio de @abstractmethod.

Encapsulamento: todos os atributos são privados e só mudam pelos métodos da
própria classe; a leitura externa passa pelas @property.
"""

from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional, Tuple

from source.domain.entidades.insumo import BaseAlimentacao
from source.domain.entidades.manejo import Pesagem, Vacinacao
from source.domain.excecoes import (
    AnimalVendidoError,
    InseminacaoInvalidaError,
    PesoInsuficienteError,
    PesoNaoRegistradoError,
    RegraNegocioViolation,
)
from source.domain.objetos_valor import Brinco, Peso


class Animal(ABC):
    """O que é comum a todo animal do rebanho."""

    def __init__(self, brinco: str, data_nascimento: date, raca: str) -> None:
        self.__brinco = Brinco(brinco)
        self.__data_nascimento = data_nascimento
        self.__raca = raca
        self.__pesagens: List[Pesagem] = []
        self.__vacinacoes: List[Vacinacao] = []
        self.__vendido = False
        self.__mae_brinco: Optional[str] = None
        self.__pai_brinco: Optional[str] = None
        self.__alimentacao: Optional[BaseAlimentacao] = None

    # ------------------------------------------------------------------
    # Leitura de atributos privados (encapsulamento)
    # ------------------------------------------------------------------
    @property
    def brinco(self) -> Brinco:
        return self.__brinco

    @property
    def data_nascimento(self) -> date:
        return self.__data_nascimento

    @property
    def raca(self) -> str:
        return self.__raca

    @property
    def pesagens(self) -> Tuple[Pesagem, ...]:
        return tuple(self.__pesagens)

    @property
    def vacinacoes(self) -> Tuple[Vacinacao, ...]:
        return tuple(self.__vacinacoes)

    @property
    def vendido(self) -> bool:
        return self.__vendido

    @property
    def mae_brinco(self) -> Optional[str]:
        return self.__mae_brinco

    @property
    def pai_brinco(self) -> Optional[str]:
        return self.__pai_brinco

    # ------------------------------------------------------------------
    # Comportamento concreto
    # ------------------------------------------------------------------
    def registrar_pesagem(self, kg: float, data: Optional[date] = None) -> Pesagem:
        """Composição: a Pesagem nasce e vive dentro do animal."""
        pesagem = Pesagem(data or date.today(), Peso(kg))
        self.__pesagens.append(pesagem)
        return pesagem

    def registrar_vacinacao(
        self, vacina: str, dose: str, data: Optional[date] = None
    ) -> Vacinacao:
        """Composição: a Vacinação nasce e vive dentro do animal."""
        vacinacao = Vacinacao(data or date.today(), vacina, dose)
        self.__vacinacoes.append(vacinacao)
        return vacinacao

    def peso_atual(self) -> float:
        if not self.__pesagens:
            raise PesoNaoRegistradoError(
                f"Animal {self.__brinco.valor} ainda não tem pesagens registradas."
            )
        return self.__pesagens[-1].peso.kg

    def idade_meses(self) -> int:
        hoje = date.today()
        meses = (
            (hoje.year - self.__data_nascimento.year) * 12
            + (hoje.month - self.__data_nascimento.month)
        )
        if hoje.day < self.__data_nascimento.day:
            meses -= 1
        return max(meses, 0)

    def definir_genealogia(
        self, mae_brinco: Optional[str] = None, pai_brinco: Optional[str] = None
    ) -> None:
        """Associação mãe <-> filhos: registra de quem o animal descende."""
        if mae_brinco:
            self.__mae_brinco = mae_brinco
        if pai_brinco:
            self.__pai_brinco = pai_brinco

    def definir_alimentacao(self, base: BaseAlimentacao) -> None:
        """Associação 'animal tem no máximo 1 base de alimentação'."""
        self.__alimentacao = base

    def alimentacao(self) -> Optional[BaseAlimentacao]:
        """Base de alimentação atribuída (máximo 1 por animal)."""
        return self.__alimentacao

    # ------------------------------------------------------------------
    # Comportamento abstrato (polimorfismo: cada subclasse responde à sua
    # própria maneira)
    # ------------------------------------------------------------------
    @abstractmethod
    def categoria(self) -> str:
        """Categoria do animal no rebanho."""

    @abstractmethod
    def peso_minimo_abate(self) -> float:
        """Peso mínimo (kg) para o animal poder ser vendido ao frigorífico."""

    # ------------------------------------------------------------------
    # Regra de negócio 1: venda ao frigorífico
    # ------------------------------------------------------------------
    def pode_vender(self) -> bool:
        """Um animal só pode ser vendido ao frigorífico quando já tem pesagem
        e o peso atual é maior ou igual ao peso mínimo de abate da categoria."""
        if self.__vendido or not self.__pesagens:
            return False
        return self.peso_atual() >= self.peso_minimo_abate()

    def marcar_vendido(self) -> None:
        """Depois da venda o animal é marcado como vendido, para não ser
        vendido de novo. A validação acontece antes de marcar."""
        if self.__vendido:
            raise AnimalVendidoError(
                f"Animal {self.__brinco.valor} já foi vendido e não pode ser vendido de novo."
            )
        if not self.pode_vender():
            peso = self.peso_atual() if self.__pesagens else 0.0
            raise PesoInsuficienteError(
                f"Animal {self.__brinco.valor} tem {peso:.1f} kg e o mínimo de abate "
                f"é {self.peso_minimo_abate():.1f} kg."
            )
        self.__vendido = True

    def restaurar_vendido(self) -> None:
        """Reconstrói o estado salvo no repositório (não é regra de negócio)."""
        self.__vendido = True

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Animal):
            return NotImplemented
        return self.__brinco == other.__brinco

    def __str__(self) -> str:
        return f"{self.__brinco.valor} - {self.__raca} - {self.categoria()}"


class Femea(Animal):
    """Fêmea do rebanho: sobrescreve os métodos abstratos e adiciona a
    lógica de reprodução (inseminação, parto e genealogia dos filhos)."""

    PESO_MINIMO_ABATE = 350.0

    def __init__(self, brinco: str, data_nascimento: date, raca: str) -> None:
        super().__init__(brinco, data_nascimento, raca)
        self.__prenhe = False
        self.__partos = 0
        self.__brinco_inseminacao: Optional[str] = None
        self.__filhos: List[Animal] = []

    @property
    def prenhe(self) -> bool:
        return self.__prenhe

    @property
    def partos(self) -> int:
        return self.__partos

    @property
    def brinco_inseminacao(self) -> Optional[str]:
        """Brinco do touro da gestação atual (None quando não está prenhe)."""
        return self.__brinco_inseminacao

    def categoria(self) -> str:
        return "Fêmea"

    def peso_minimo_abate(self) -> float:
        return self.PESO_MINIMO_ABATE

    # ------------------------------------------------------------------
    # Regra de negócio 2: inseminação
    # ------------------------------------------------------------------
    def pode_inseminar(self, touro: "Macho") -> bool:
        """Só fêmeas podem ser inseminadas e, antes disso, a genealogia é
        verificada: o touro não pode ser o próprio animal, nem o pai, nem
        um filho dela."""
        if touro is None or self.__prenhe or self.vendido:
            return False
        brinco_touro = touro.brinco.valor
        return (
            brinco_touro != self.brinco.valor
            and brinco_touro != self.pai_brinco
            and not any(filho.brinco.valor == brinco_touro for filho in self.__filhos)
        )

    def inseminar(self, touro: "Macho") -> None:
        """Regra de negócio 2: a fêmea fica prenhe somente se a inseminação
        com aquele touro for possível."""
        if not self.pode_inseminar(touro):
            raise InseminacaoInvalidaError(
                f"Fêmea {self.brinco.valor} não pode ser inseminada pelo touro "
                f"{touro.brinco.valor if touro else '?'} (genealogia ou estado reprodutivo)."
            )
        self.__prenhe = True
        self.__brinco_inseminacao = touro.brinco.valor

    def registrar_parto(self, brinco_filho: str, macho: bool) -> Animal:
        """O parto cria o bezerro já vinculado à mãe (associação mãe-filhos
        do diagrama) e à genealogia, e encerra a gestação."""
        if not self.__prenhe:
            raise RegraNegocioViolation(
                f"Fêmea {self.brinco.valor} não está prenhe, então não há parto a registrar."
            )
        bezerro: Animal = Macho(brinco_filho, date.today(), self.raca)
        if not macho:
            bezerro = Femea(brinco_filho, date.today(), self.raca)
        bezerro.definir_genealogia(
            mae_brinco=self.brinco.valor, pai_brinco=self.__brinco_inseminacao
        )
        self.__filhos.append(bezerro)
        self.__prenhe = False
        self.__partos += 1
        self.__brinco_inseminacao = None
        return bezerro

    def listar_filhos(self) -> List[Animal]:
        """Filhos dessa fêmea (associação mãe 0..1 -- filhos 0..*)."""
        return list(self.__filhos)

    def restaurar_reproducao(
        self, prenhe: bool, partos: int, brinco_inseminacao: Optional[str] = None
    ) -> None:
        """Reconstrói o estado salvo no repositório (não é regra de negócio)."""
        self.__prenhe = prenhe
        self.__partos = partos
        self.__brinco_inseminacao = brinco_inseminacao

    def restaurar_filhos(self, filhos: List[Animal]) -> None:
        """Re-vincula os filhos ao reconstruir o rebanho do repositório."""
        self.__filhos = list(filhos)


class Macho(Animal):
    """Macho do rebanho: sobrescreve os métodos abstratos e adiciona a
    castração."""

    PESO_MINIMO_ABATE = 450.0

    def __init__(self, brinco: str, data_nascimento: date, raca: str) -> None:
        super().__init__(brinco, data_nascimento, raca)
        self.__castrado = False

    @property
    def castrado(self) -> bool:
        return self.__castrado

    def categoria(self) -> str:
        return "Macho"

    def peso_minimo_abate(self) -> float:
        return self.PESO_MINIMO_ABATE

    def castrar(self) -> None:
        if self.__castrado:
            raise RegraNegocioViolation(
                f"Macho {self.brinco.valor} já está castrado."
            )
        self.__castrado = True

    def restaurar_castrado(self) -> None:
        """Reconstrói o estado salvo no repositório (não é regra de negócio)."""
        self.__castrado = True
