"""Formulário do autocadastro (ator Usuário do diagrama de casos de uso).

É o cadastro do proprietário da propriedade, com nome, CPF e senha. O
CPF e a senha salvos são as credenciais de entrada do usuário — no
sistema multiusuário, também do login, e o caso de uso Autocadastro
mantém o índice de contas em dia quando o CPF muda. Serve de gate do
primeiro acesso (quando não há cadastro salvo) e para corrigir o
cadastro depois, pelo menu de seleção — nesse caso o nome e o CPF vêm
preenchidos.
"""

import tkinter as tk
from tkinter import messagebox
from typing import Callable, Optional

from source.domain.excecoes import RegraNegocioViolation
from source.interfaces.formularios import ancorar
from source.usecases.contenedor import CasosDeUso


class JanelaAutocadastro(tk.Toplevel):
    """Formulário nome + CPF + senha do autocadastro do proprietário."""

    def __init__(
        self,
        casos: CasosDeUso,
        ao_salvar: Optional[Callable[[], None]] = None,
        pai: Optional[tk.Misc] = None,
    ) -> None:
        super().__init__(pai)
        self.__casos = casos
        self.__ao_salvar = ao_salvar
        self.title("Autocadastro — Proprietário da fazenda")
        self.resizable(False, False)

        tk.Label(
            self,
            text="Autocadastro: cadastro do proprietário da propriedade.\n"
            "O CPF e a senha são as credenciais de entrada no sistema.",
            justify="left",
        ).pack(padx=12, pady=(10, 4), anchor="w")

        quadro = tk.Frame(self, padx=12, pady=4)
        quadro.pack()
        tk.Label(quadro, text="Nome:").grid(row=0, column=0, sticky="w", pady=2)
        self.__entrada_nome = tk.Entry(quadro, width=28)
        self.__entrada_nome.grid(row=0, column=1, padx=4, pady=2)
        tk.Label(quadro, text="CPF:").grid(row=1, column=0, sticky="w", pady=2)
        self.__entrada_cpf = tk.Entry(quadro, width=28)
        self.__entrada_cpf.grid(row=1, column=1, padx=4, pady=2)
        tk.Label(quadro, text="Senha:").grid(row=2, column=0, sticky="w", pady=2)
        self.__entrada_senha = tk.Entry(quadro, width=28, show="*")
        self.__entrada_senha.grid(row=2, column=1, padx=4, pady=2)
        tk.Label(quadro, text="Confirmar senha:").grid(row=3, column=0, sticky="w", pady=2)
        self.__entrada_confirmacao = tk.Entry(quadro, width=28, show="*")
        self.__entrada_confirmacao.grid(row=3, column=1, padx=4, pady=2)

        nome, cpf = self.__casos.cadastro("proprietario")
        self.__entrada_nome.insert(0, nome)
        self.__entrada_cpf.insert(0, cpf)

        botoes = tk.Frame(self, padx=12, pady=10)
        botoes.pack()
        tk.Button(botoes, text="Salvar", command=self.__salvar).pack(side="left", padx=4)
        tk.Button(botoes, text="Cancelar", command=self.destroy).pack(side="left", padx=4)

        self.__entrada_nome.focus_set()
        self.bind("<Return>", lambda evento: self.__salvar())
        self.bind("<Escape>", lambda evento: self.destroy())
        ancorar(self, pai)

    def __salvar(self) -> None:
        nome = self.__entrada_nome.get().strip()
        cpf = self.__entrada_cpf.get().strip()
        senha = self.__entrada_senha.get()
        confirmacao = self.__entrada_confirmacao.get()
        if senha != confirmacao:
            messagebox.showwarning(
                "Autocadastro", "As senhas digitadas não coincidem.", parent=self
            )
            return
        try:
            proprietario = self.__casos.autocadastro.executar(nome, cpf, senha)
        except RegraNegocioViolation as erro:
            messagebox.showwarning("Autocadastro", erro.mensagem, parent=self)
            return
        messagebox.showinfo(
            "Autocadastro",
            f"Cadastro salvo: {proprietario.nome} ({proprietario.cpf})",
            parent=self,
        )
        if self.__ao_salvar is not None:
            self.__ao_salvar()
        self.destroy()
