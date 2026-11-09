"""Manejo produtivo do rebanho.

Pesagem e Vacinação são composição de Animal (conforme justificativa
teórica): uma pesagem ou vacina registrada não faz sentido sem o animal.
"""

from datetime import date

from source.domain.objetos_valor import Peso


class Pesagem:
    """Registro de um pesar: data + peso, sempre ligado ao animal dono."""

    def __init__(self, data: date, peso: Peso) -> None:
        self.__data = data
        self.__peso = peso

    @property
    def data(self) -> date:
        return self.__data

    @property
    def peso(self) -> Peso:
        return self.__peso

    def __str__(self) -> str:
        return f"{self.__data.isoformat()} - {self.__peso.kg:.1f} kg"


class Vacinacao:
    """Registro de uma vacina aplicada no animal com a dose usada."""

    def __init__(self, data: date, vacina: str, dose: str) -> None:
        self.__data = data
        self.__vacina = vacina
        self.__dose = dose

    @property
    def data(self) -> date:
        return self.__data

    @property
    def vacina(self) -> str:
        return self.__vacina

    @property
    def dose(self) -> str:
        return self.__dose

    def __str__(self) -> str:
        return f"{self.__data.isoformat()} - {self.__vacina} ({self.__dose})"
