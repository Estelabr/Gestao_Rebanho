"""Domain services do sistema: regras de negócio que não pertencem a uma
entidade ou objeto de valor específico.

Cada serviço é uma classe sem estado (métodos estáticos), para que os
casos de uso e as entidades possam chamá-los sem precisar instanciar."""

from source.domain.servicos.validar_cnpj import ValidarCnpj
from source.domain.servicos.validar_cpf import ValidarCpf

__all__ = ["ValidarCnpj", "ValidarCpf"]
