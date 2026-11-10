"""Interface gráfica em Tkinter (Parte 3 do trabalho).

Sistema multiusuário: a entrada é o login (JanelaLogin), que autentica
uma conta por documento (CPF ou CNPJ) e senha — ou cria a conta nova,
já declarando o papel dela. O papel acompanha a conta: autenticada a
conta, a composição de raiz (main.py) monta os casos de uso com o
arquivo de dados dela e abre direto a área do papel (Proprietário,
Frigorífico ou Fornecedor de Insumos) — não há seleção de perfil depois
do login. Ao fechar a área, o fluxo volta ao login, para que outro
usuário entre com a conta dele. As janelas não contêm regra de negócio:
apenas instanciam, listam e modificam objetos chamando os casos de uso,
que por sua vez chamam as classes do sistema.
"""

import tkinter as tk
from typing import Callable, List, Optional

from source.domain.entidades.conta import Conta
from source.interfaces.janela_fornecedor import JanelaFornecedor
from source.interfaces.janela_frigorifico import JanelaFrigorifico
from source.interfaces.janela_login import JanelaLogin
from source.interfaces.janela_proprietario import JanelaProprietario
from source.usecases.casos_de_uso import AutenticarConta, CadastrarConta
from source.usecases.contenedor import CasosDeUso

_AREAS = {
    "proprietario": JanelaProprietario,
    "fornecedor": JanelaFornecedor,
    "frigorifico": JanelaFrigorifico,
}


def iniciar_interface(
    cadastrar_conta: CadastrarConta,
    autenticar_conta: AutenticarConta,
    montar: Callable[[Conta], CasosDeUso],
) -> None:
    """Abre o login e, com a conta autenticada, a área do papel dela.

    O login roda até entregar uma conta (ou até o usuário desistir e
    fechar a janela). A conta é entregue a `montar`, que monta os casos
    de uso com os dados dela; a área do papel abre sobre uma raiz
    oculta, e ao fechá-la o fluxo volta ao login."""
    while True:
        autenticada: List[Conta] = []

        def guardar(conta: Optional[Conta]) -> None:
            if conta is not None:
                autenticada.append(conta)

        JanelaLogin(cadastrar_conta, autenticar_conta, guardar).mainloop()
        if not autenticada:
            return
        casos = montar(autenticada[0])
        raiz = tk.Tk()
        raiz.withdraw()
        _AREAS[casos.usuario().papel](casos, ao_fechar=raiz.destroy)
        raiz.mainloop()
