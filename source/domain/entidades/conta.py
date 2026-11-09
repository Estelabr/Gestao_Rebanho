"""Conta de acesso ao sistema (multiusuário).

A Conta é a credencial de entrada de um usuário: nome, documento (CPF
do proprietário, CNPJ do fornecedor e do frigorífico), o **papel** que
ela exerce no sistema e o arquivo de dados onde vive o trabalho dela.
Cada conta é isolada — tem o seu próprio arquivo de dados — e o papel
acompanha a conta: quem entra como fornecedor cai direto na área do
Fornecedor, sem escolher perfil depois do login.

A senha é guardada aqui apenas como credencial (hash com salt), nunca
em texto plano; a conferência é responsabilidade da camada de
aplicação (usecases/senhas.py).
"""

from typing import Tuple

from source.domain.excecoes import RegraNegocioViolation

PAPEIS: Tuple[str, ...] = ("proprietario", "fornecedor", "frigorifico")


def normalizar_documento(documento: str) -> str:
    """Reduz o documento (CPF ou CNPJ) aos dígitos: pontuação é só
    apresentação. Dois documentos com os mesmos dígitos identificam a
    mesma pessoa ou organização, tenham ou não pontos e hífen."""

    return "".join(caractere for caractere in documento if caractere.isdigit())


class Conta:
    """Usuário do sistema: papel, documento e onde estão os dados dele."""

    def __init__(
        self,
        nome: str,
        documento: str,
        papel: str,
        arquivo: str,
        senha: str = "",
    ) -> None:
        if papel not in PAPEIS:
            raise RegraNegocioViolation(f"Papel desconhecido: {papel}.")
        self.__nome = nome
        self.__documento = documento
        self.__papel = papel
        self.__arquivo = arquivo
        self.__senha = senha

    @property
    def nome(self) -> str:
        return self.__nome

    @property
    def documento(self) -> str:
        """CPF (proprietário) ou CNPJ (fornecedor e frigorífico)."""
        return self.__documento

    @property
    def papel(self) -> str:
        """O ator que esta conta representa no sistema."""
        return self.__papel

    @property
    def arquivo(self) -> str:
        """Arquivo de dados da conta (isolamento entre usuários)."""
        return self.__arquivo

    @property
    def senha(self) -> str:
        """Credencial de acesso (hash, nunca texto plano)."""
        return self.__senha

    def rotulo_documento(self) -> str:
        """Rótulo do documento pelo papel: CPF ou CNPJ."""
        return "CPF" if self.__papel == "proprietario" else "CNPJ"

    def resumo(self) -> str:
        """Resumo para exibir em telas e menus: 'nome (CPF documento)'."""
        return f"{self.__nome} ({self.rotulo_documento()} {self.__documento})"
