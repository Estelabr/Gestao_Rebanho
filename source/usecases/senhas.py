"""Geração e conferência da credencial de acesso (senha com hash).

A senha nunca é guardada em texto plano: o autocadastro salva um hash
PBKDF2 com salt aleatório, no formato "pbkdf2$iterações$salt$hash". O
domínio enxerga apenas uma credencial opaca (a propriedade `senha` das
entidades); a criptografia é responsabilidade desta camada de aplicação.
"""

import hashlib
import hmac
import os

ITERACOES = 100_000
_ALGORITMO = "sha256"


def gerar_credencial(senha: str) -> str:
    """Gera a credencial a partir da senha: hash PBKDF2 com salt novo."""
    salt = os.urandom(16).hex()
    hash_hex = hashlib.pbkdf2_hmac(
        _ALGORITMO, senha.encode("utf-8"), bytes.fromhex(salt), ITERACOES
    ).hex()
    return f"pbkdf2${ITERACOES}${salt}${hash_hex}"


def conferir(senha: str, credencial_salva: str) -> bool:
    """Diz se a senha digitada bate com a credencial salva."""
    try:
        algoritmo, iteracoes, salt, hash_salvo = credencial_salva.split("$")
        if algoritmo != "pbkdf2":
            return False
        hash_tentativa = hashlib.pbkdf2_hmac(
            _ALGORITMO, senha.encode("utf-8"), bytes.fromhex(salt), int(iteracoes)
        ).hex()
        return hmac.compare_digest(hash_tentativa, hash_salvo)
    except (ValueError, AttributeError):
        return False
