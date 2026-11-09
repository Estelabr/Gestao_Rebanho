"""Objetos de valor da camada de domínio.

No DDD, um objeto de valor não tem identidade própria: dois objetos de
valor são iguais quando os seus valores são iguais. Por isso aqui usamos
dataclasses imutáveis (frozen=True) — uma vez criados, nunca mudam.
"""

from dataclasses import dataclass

from source.domain.excecoes import BrincoInvalidoError, PesoInvalidoError


@dataclass(frozen=True)
class Brinco:
    """Identificador do animal. Sem brinco válido, o animal não existe."""

    valor: str

    def __post_init__(self) -> None:
        if self.valor is None or not self.valor.strip():
            raise BrincoInvalidoError("O brinco informado está vazio.")

    def __str__(self) -> str:
        return self.valor


@dataclass(frozen=True)
class Peso:
    """Peso em quilos. Dois pesos com a mesma quantidade kg são o mesmo peso."""

    kg: float

    def __post_init__(self) -> None:
        if self.kg <= 0:
            raise PesoInvalidoError(f"Um peso precisa ser positivo; recebi {self.kg} kg.")
