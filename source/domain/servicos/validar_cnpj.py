"""Domain service de validação do CNPJ.

O CNPJ tem 14 dígitos: os 12 primeiros identificam a organização (os 8
primeiros são a raiz, os 4 seguintes são a ordem da matriz/filial) e os
2 últimos são dígitos verificadores, calculados pelo módulo 11 com pesos
que percorrem a sequência 6543 298765432 (1º DV) e 5432 98765432 (2º DV).
Este serviço confere esse cálculo e devolve o CNPJ só com dígitos —
pontuação (pontos, barra e hífen) é apresentação, não conteúdo.

O serviço não guarda estado: tudo o que ele precisa vem do argumento,
por isso os métodos são estáticos e o uso é direto — ValidarCnpj.validar(cnpj).

Instituições de referência do algoritmo: Receita Federal do Brasil."""

from source.domain.excecoes import CNPJInvalidoError

TAMANHO = 14
# Pesos dos DVs: 6543298765432 para o 1º DV e 543298765432 para o 2º.
_PESOS = "6543298765432543298765432"


class ValidarCnpj:
    """Serviço de domínio que valida o CNPJ e o reduz aos dígitos."""

    @staticmethod
    def validar(cnpj: str) -> str:
        """Valida o CNPJ e devolve o mesmo só com dígitos.

        Levanta CNPJInvalidoError quando o documento não tem 14 dígitos,
        tem todos os dígitos iguais (ex.: '00.000.000/0000-00') ou os
        dígitos verificadores não batem com o cálculo."""
        numero = ValidarCnpj.normalizar(cnpj)
        if len(numero) != TAMANHO:
            raise CNPJInvalidoError(
                f"O CNPJ precisa ter 14 dígitos; recebi {len(numero)} em '{cnpj.strip()}'."
            )
        if numero == numero[0] * TAMANHO:
            raise CNPJInvalidoError(
                f"O CNPJ '{cnpj.strip()}' tem todos os dígitos iguais."
            )
        digitos_base = numero[:12]
        primeiro_dv = ValidarCnpj._digito_verificador(digitos_base)
        segundo_dv = ValidarCnpj._digito_verificador(digitos_base + str(primeiro_dv))
        if numero[12:] != f"{primeiro_dv}{segundo_dv}":
            raise CNPJInvalidoError(
                f"O CNPJ '{cnpj.strip()}' tem dígitos verificadores inválidos."
            )
        return numero

    @staticmethod
    def normalizar(cnpj: str) -> str:
        """Reduz o CNPJ aos dígitos: pontuação é só apresentação."""
        return "".join(caractere for caractere in cnpj if caractere.isdigit())

    @staticmethod
    def _digito_verificador(digitos: str) -> int:
        """Calcula um dígito verificador do CNPJ pelo módulo 11, usando
        os pesos da sequência 6543 298765432 (e 5432 98765432 para o
        2º DV), cortados da direita para caber nos dígitos dados."""
        pesos = _PESOS[13 - len(digitos):]
        soma = sum(int(digito) * int(peso) for digito, peso in zip(digitos, pesos))
        resto = soma % 11
        return 0 if resto < 2 else 11 - resto
