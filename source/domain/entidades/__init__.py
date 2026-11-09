"""Entidades do domínio: o coração do sistema de gestão de rebanho."""

from source.domain.entidades.animal import Animal, Femea, Macho
from source.domain.entidades.insumo import BaseAlimentacao, Insumo
from source.domain.entidades.manejo import Pesagem, Vacinacao
from source.domain.entidades.pessoas import (
    CompraAnimal,
    Fornecedor,
    Frigorifico,
    Proprietario,
)

__all__ = [
    "Animal",
    "Femea",
    "Macho",
    "Pesagem",
    "Vacinacao",
    "Insumo",
    "BaseAlimentacao",
    "Proprietario",
    "Fornecedor",
    "Frigorifico",
    "CompraAnimal",
]
