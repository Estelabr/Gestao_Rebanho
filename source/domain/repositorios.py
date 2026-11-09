"""Contratos de repositório usados pela camada de aplicação.

Estes contratos moram no domínio (padrão DDD): os casos de uso dependem
deles, e não da implementação concreta (JSON), que fica na infraestrutura
e apenas os cumpre. É a inversão de dependência do Clean Code mantendo o
domínio isolado da tecnologia de persistência.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from source.domain.entidades.animal import Animal
from source.domain.entidades.insumo import BaseAlimentacao, Insumo
from source.domain.entidades.pessoas import CompraAnimal, Proprietario


class RepositorioAnimais(ABC):
    """Contrato para guardar e buscar animais."""

    @abstractmethod
    def adicionar(self, animal: Animal) -> None:
        """Guarda (ou substitui) um animal, identificado pelo brinco."""

    @abstractmethod
    def buscar_por_brinco(self, brinco: str) -> Optional[Animal]:
        """Devolve o animal com aquele brinco, ou None."""

    @abstractmethod
    def listar(self) -> List[Animal]:
        """Devolve todos os animais cadastrados."""

    @abstractmethod
    def remover(self, brinco: str) -> None:
        """Remove o animal com aquele brinco."""

    @abstractmethod
    def salvar(self) -> None:
        """Persiste o estado atual dos animais."""


class RepositorioInsumos(ABC):
    """Contrato para guardar e buscar insumos."""

    @abstractmethod
    def adicionar(self, insumo: Insumo) -> None:
        """Guarda (ou substitui) um insumo, identificado pelo nome."""

    @abstractmethod
    def buscar_por_nome(self, nome: str) -> Optional[Insumo]:
        """Devolve o insumo com aquele nome, ou None."""

    @abstractmethod
    def listar(self) -> List[Insumo]:
        """Devolve todos os insumos cadastrados."""

    @abstractmethod
    def salvar(self) -> None:
        """Persiste o estado atual dos insumos."""


class RepositorioBases(ABC):
    """Contrato para guardar e buscar bases de alimentação."""

    @abstractmethod
    def adicionar(self, base: BaseAlimentacao) -> None:
        """Guarda (ou substitui) uma base, identificada pelo nome."""

    @abstractmethod
    def buscar_por_nome(self, nome: str) -> Optional[BaseAlimentacao]:
        """Devolve a base com aquele nome, ou None."""

    @abstractmethod
    def listar(self) -> List[BaseAlimentacao]:
        """Devolve todas as bases cadastradas."""

    @abstractmethod
    def salvar(self) -> None:
        """Persiste o estado atual das bases."""


class RepositorioCompras(ABC):
    """Contrato para guardar o histórico de compras do frigorífico."""

    @abstractmethod
    def adicionar(self, compra: CompraAnimal) -> None:
        """Guarda uma nova compra no histórico."""

    @abstractmethod
    def listar(self) -> List[CompraAnimal]:
        """Devolve todas as compras registradas."""

    @abstractmethod
    def salvar(self) -> None:
        """Persiste o estado atual do histórico."""


class RepositorioProprietario(ABC):
    """Contrato para persistir o cadastro do proprietário (autocadastro)."""

    @abstractmethod
    def carregar(self) -> Optional[Proprietario]:
        """Devolve o proprietário salvo, ou None se ainda não houver."""

    @abstractmethod
    def salvar(self, proprietario: Proprietario) -> None:
        """Persiste o cadastro do proprietário."""
