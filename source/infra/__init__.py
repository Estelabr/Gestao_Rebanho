"""Camada de infraestrutura: como os dados são guardados.

Os contratos de repositório moram no domínio (source/domain/repositorios.py);
aqui fica apenas a implementação concreta em JSON. O domínio não sabe que
existe JSON: ele só conhece os contratos, e a implementação os cumpre.
"""
