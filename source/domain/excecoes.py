"""Exceções de negócio da camada de domínio.

Cada regra violada tem a sua própria exceção, para que as camadas de
aplicação e apresentação tratem erros com mensagens claras, sem precisar
conhecer os detalhes internos de como cada erro é detectado.
"""


class RegraNegocioViolation(Exception):
    """Exceção base para todas as regras de negócio do sistema."""

    def __init__(self, mensagem: str) -> None:
        super().__init__(mensagem)
        self.mensagem = mensagem


class AnimalVendidoError(RegraNegocioViolation):
    """O animal já foi vendido e não pode ser vendido de novo."""


class PesoInsuficienteError(RegraNegocioViolation):
    """O peso atual está abaixo do peso mínimo de abate da categoria."""


class PesoNaoRegistradoError(RegraNegocioViolation):
    """O animal ainda não tem nenhuma pesagem registrada."""


class EstoqueInsuficienteError(RegraNegocioViolation):
    """A saída pedida é maior do que o estoque disponível."""


class InseminacaoInvalidaError(RegraNegocioViolation):
    """A inseminação não respeita genealogia ou estado reprodutivo."""


class AnimalNaoEncontradoError(RegraNegocioViolation):
    """Não existe animal com o brinco informado."""


class BrincoDuplicadoError(RegraNegocioViolation):
    """Já existe um animal cadastrado com o mesmo brinco."""


class BrincoInvalidoError(RegraNegocioViolation):
    """O valor usado como brinco não serve de identificador (vazio)."""


class PesoInvalidoError(RegraNegocioViolation):
    """Um peso só faz sentido se for positivo."""


class QuantidadeInvalidaError(RegraNegocioViolation):
    """Uma quantidade precisa ser positiva para ter efeito no sistema."""


class InsumoNaoEncontradoError(RegraNegocioViolation):
    """Não existe insumo com o nome informado no catálogo consultado."""


class BaseNaoEncontradaError(RegraNegocioViolation):
    """Não existe base de alimentação com o nome informado."""


class BaseDuplicadaError(RegraNegocioViolation):
    """Já existe uma base de alimentação com o mesmo nome."""


class CadastroNaoPreenchidoError(RegraNegocioViolation):
    """O ator ainda não tem cadastro: nome e documento são obrigatórios."""


class CredencialInvalidaError(RegraNegocioViolation):
    """O documento informado não corresponde ao cadastro do perfil."""


class DocumentoDuplicadoError(RegraNegocioViolation):
    """Já existe uma conta de usuário cadastrada com o mesmo documento."""


class CPFInvalidoError(RegraNegocioViolation):
    """O CPF informado não é válido (tamanho, dígitos repetidos ou DV)."""


class CNPJInvalidoError(RegraNegocioViolation):
    """O CNPJ informado não é válido (tamanho, dígitos repetidos ou DV)."""
