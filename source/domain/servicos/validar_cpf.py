"""Domain service de validação do CPF.

O CPF tem 11 dígitos: os 9 primeiros são o número de inscrição e os 2
últimos são dígitos verificadores, calculados pelo algoritmo de módulo
11. Este serviço confere esse cálculo e devolve o CPF só com dígitos —
pontuação (pontos e hífen) é apresentação, não conteúdo.

O serviço não guarda estado: tudo o que ele precisa vem do argumento,
por isso os métodos são estáticos e o uso é direto — ValidarCpf.validar(cpf).

Instituições de referência do algoritmo: Receita Federal do Brasil."""

from source.domain.excecoes import CPFInvalidoError

TAMANHO = 11


class ValidarCpf:
    """Serviço de domínio que valida o CPF e o reduz aos dígitos."""

    @staticmethod
    def validar(cpf: str) -> str:
        """Valida o CPF e devolve o mesmo só com dígitos.

        Levanta CPFInvalidoError quando o documento não tem 11 dígitos,
        tem todos os dígitos iguais (ex.: '111.111.111-11') ou os
        dígitos verificadores não batem com o cálculo."""
        numero = ValidarCpf.normalizar(cpf)
        if len(numero) != TAMANHO:
            raise CPFInvalidoError(
                f"O CPF precisa ter 11 dígitos; recebi {len(numero)} em '{cpf.strip()}'."
            )
        if numero == numero[0] * TAMANHO:
            raise CPFInvalidoError(f"O CPF '{cpf.strip()}' tem todos os dígitos iguais.")
        digitos_base = numero[:9]
        primeiro_dv = ValidarCpf._digito_verificador(digitos_base)
        segundo_dv = ValidarCpf._digito_verificador(digitos_base + str(primeiro_dv))
        if numero[9:] != f"{primeiro_dv}{segundo_dv}":
            raise CPFInvalidoError(
                f"O CPF '{cpf.strip()}' tem dígitos verificadores inválidos."
            )
        return numero

    @staticmethod
    def normalizar(cpf: str) -> str:
        """Reduz o CPF aos dígitos: pontuação é só apresentação."""
        return "".join(caractere for caractere in cpf if caractere.isdigit())

    @staticmethod
    def _digito_verificador(digitos: str) -> int:
        """Calcula um dígito verificador pelo módulo 11: cada dígito é
        multiplicado pelo peso (de trás para frente), a soma é dividida
        por 11 e o resto vira o DV (0 quando o resto é menor que 2)."""
        soma = sum(
            int(digito) * peso
            for digito, peso in zip(digitos, range(len(digitos) + 1, 1, -1))
        )
        resto = soma % 11
        return 0 if resto < 2 else 11 - resto
