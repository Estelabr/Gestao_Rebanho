"""Janela de login do sistema multiusuário.

É a primeira janela do programa: identifica o usuário por documento
(CPF ou CNPJ) e senha, confere a credencial pelo caso de uso
AutenticarConta e entrega a conta autenticada para quem a abriu — que
abre direto a área do papel da conta, sem seleção de perfil.

A criação de conta (autocadastro multiusuário) também acontece aqui: a
conta nova declara o papel dela (proprietário, fornecedor ou
frigorífico), nasce com arquivo de dados próprio e o usuário já entra
com ela.

As janelas não contêm regra de negócio: apenas leem o que foi digitado
e chamam casos de uso.
"""

import tkinter as tk
from tkinter import messagebox
from typing import Callable, Optional

from source.domain.entidades.conta import Conta
from source.domain.excecoes import RegraNegocioViolation
from source.interfaces.formularios import ancorar


class JanelaLogin(tk.Tk):
    """Janela raiz da entrada: login por documento e senha, ou conta nova."""

    def __init__(
        self,
        cadastrar_conta,
        autenticar_conta,
        ao_entrar: Callable[[Conta], None],
    ) -> None:
        """Recebe os casos de uso CadastrarConta e AutenticarConta e a
        ação a executar com a conta autenticada."""
        super().__init__()
        self.__cadastrar_conta = cadastrar_conta
        self.__autenticar_conta = autenticar_conta
        self.__ao_entrar = ao_entrar
        self.title("Acesso ao sistema — Gestão de Rebanho")
        self.geometry("380x220")
        self.resizable(False, False)

        tk.Label(
            self,
            text="Entre com a sua conta (CPF ou CNPJ e senha).\n"
            "O papel da conta abre a área correspondente.",
            justify="center",
            font=("TkDefaultFont", 10, "bold"),
        ).pack(pady=(14, 8))

        quadro = tk.Frame(self, padx=12)
        quadro.pack()
        tk.Label(quadro, text="Documento (CPF ou CNPJ):").grid(
            row=0, column=0, sticky="w", pady=2
        )
        self.__entrada_documento = tk.Entry(quadro, width=24)
        self.__entrada_documento.grid(row=0, column=1, padx=4, pady=2)
        tk.Label(quadro, text="Senha:").grid(row=1, column=0, sticky="w", pady=2)
        self.__entrada_senha = tk.Entry(quadro, width=24, show="*")
        self.__entrada_senha.grid(row=1, column=1, padx=4, pady=2)

        botoes = tk.Frame(self, pady=10)
        botoes.pack()
        tk.Button(botoes, text="Entrar", width=14, command=self.__entrar).pack(
            side="left", padx=4
        )
        tk.Button(
            botoes, text="Criar conta", width=14, command=self.__criar_conta
        ).pack(side="left", padx=4)
        tk.Button(botoes, text="Sair", width=14, command=self.destroy).pack(
            side="left", padx=4
        )

        self.__entrada_documento.focus_set()
        self.bind("<Return>", lambda evento: self.__entrar())
        self.bind("<Escape>", lambda evento: self.destroy())

    # ------------------------------------------------------------------
    # Entrada e criação de conta
    # ------------------------------------------------------------------
    def __entrar(self) -> None:
        documento = self.__entrada_documento.get().strip()
        senha = self.__entrada_senha.get()
        try:
            conta = self.__autenticar_conta.executar(documento, senha)
        except RegraNegocioViolation as erro:
            messagebox.showwarning("Acesso", erro.mensagem, parent=self)
            return
        self.__concluir(conta)

    def __criar_conta(self) -> None:
        """Autocadastro multiusuário: papel + cadastro + senha, e já entra."""
        JanelaCriarConta(self.__cadastrar_conta, self.__concluir, pai=self)

    def __concluir(self, conta: Optional[Conta]) -> None:
        """Entrega a conta a quem abriu a janela e fecha o login.

        O fechamento é agendado (after) para que uma janela de criação
        de conta aberta por cima se feche primeiro, sem tentar se
        destruir depois que a janela raiz já se foi."""
        if conta is None:
            return
        self.__ao_entrar(conta)
        self.after(0, self.destroy)


class JanelaCriarConta(tk.Toplevel):
    """Formulário da conta nova: papel (com o documento correspondente),
    nome, documento e senha — o autocadastro multiusuário."""

    PAPEIS = (
        ("proprietario", "Proprietário da fazenda", "CPF:"),
        ("fornecedor", "Fornecedor de insumos", "CNPJ:"),
        ("frigorifico", "Frigorífico", "CNPJ:"),
    )

    def __init__(
        self,
        cadastrar_conta,
        ao_criar: Callable[[Conta], None],
        pai: Optional[tk.Misc] = None,
    ) -> None:
        super().__init__(pai)
        self.__cadastrar_conta = cadastrar_conta
        self.__ao_criar = ao_criar
        self.title("Criar conta")
        self.resizable(False, False)

        tk.Label(
            self,
            text="Quem esta conta representa?\nO papel abre a área correspondente "
            "a cada entrada.",
            justify="left",
        ).pack(padx=12, pady=(10, 4), anchor="w")

        self.__papel_selecionado = tk.StringVar(value=self.PAPEIS[0][0])
        self.__rotulos_documento = {}
        quadro_papeis = tk.Frame(self, padx=12)
        quadro_papeis.pack(anchor="w")
        for linha, (papel, texto, rotulo) in enumerate(self.PAPEIS):
            botao = tk.Radiobutton(
                quadro_papeis,
                text=texto,
                variable=self.__papel_selecionado,
                value=papel,
                command=self.__atualizar_rotulo_documento,
            )
            botao.grid(row=linha, column=0, sticky="w")
            self.__rotulos_documento[papel] = rotulo

        quadro = tk.Frame(self, padx=12, pady=4)
        quadro.pack()
        self.__rotulo_documento = tk.Label(quadro, text=f"{self.PAPEIS[0][2]}")
        self.__rotulo_documento.grid(row=0, column=0, sticky="w", pady=2)
        self.__entrada_documento = tk.Entry(quadro, width=24)
        self.__entrada_documento.grid(row=0, column=1, padx=4, pady=2)
        tk.Label(quadro, text="Nome:").grid(row=1, column=0, sticky="w", pady=2)
        self.__entrada_nome = tk.Entry(quadro, width=24)
        self.__entrada_nome.grid(row=1, column=1, padx=4, pady=2)
        tk.Label(quadro, text="Senha:").grid(row=2, column=0, sticky="w", pady=2)
        self.__entrada_senha = tk.Entry(quadro, width=24, show="*")
        self.__entrada_senha.grid(row=2, column=1, padx=4, pady=2)
        tk.Label(quadro, text="Confirmar senha:").grid(row=3, column=0, sticky="w", pady=2)
        self.__entrada_confirmacao = tk.Entry(quadro, width=24, show="*")
        self.__entrada_confirmacao.grid(row=3, column=1, padx=4, pady=2)

        botoes = tk.Frame(self, padx=12, pady=10)
        botoes.pack()
        tk.Button(botoes, text="Criar", command=self.__criar).pack(side="left", padx=4)
        tk.Button(botoes, text="Cancelar", command=self.destroy).pack(side="left", padx=4)

        self.__entrada_nome.focus_set()
        self.bind("<Return>", lambda evento: self.__criar())
        self.bind("<Escape>", lambda evento: self.destroy())
        ancorar(self, pai)

    # ------------------------------------------------------------------
    # Formulário
    # ------------------------------------------------------------------
    def __atualizar_rotulo_documento(self) -> None:
        papel = self.__papel_selecionado.get()
        self.__rotulo_documento.config(text=f"{self.__rotulos_documento[papel]}")

    def __criar(self) -> None:
        nome = self.__entrada_nome.get().strip()
        documento = self.__entrada_documento.get().strip()
        senha = self.__entrada_senha.get()
        if senha != self.__entrada_confirmacao.get():
            messagebox.showwarning(
                "Criar conta", "As senhas digitadas não coincidem.", parent=self
            )
            return
        try:
            conta = self.__cadastrar_conta.executar(
                nome, documento, self.__papel_selecionado.get(), senha
            )
        except RegraNegocioViolation as erro:
            messagebox.showwarning("Criar conta", erro.mensagem, parent=self)
            return
        messagebox.showinfo(
            "Conta criada",
            f"Conta criada: {conta.resumo()}\nÁrea: {self.__nome_do_papel(conta.papel)}",
            parent=self,
        )
        self.__ao_criar(conta)
        self.destroy()

    @staticmethod
    def __nome_do_papel(papel: str) -> str:
        for valor, texto, _ in JanelaCriarConta.PAPEIS:
            if valor == papel:
                return texto
        return papel
