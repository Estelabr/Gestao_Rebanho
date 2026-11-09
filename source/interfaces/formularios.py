"""Formulários da interface gráfica: campos Label + Entry em janela Toplevel.

O formulário é modal: fica na frente até ser confirmado ou cancelado, e
nasce ancorado na janela que o abriu (o pai), para que ele e os diálogos
de erro apareçam sobre a janela em foco, e não sobre o menu. Ele não
contém regra de negócio — entrega os valores digitados para a função que
o abriu e permanece aberto quando os dados são rejeitados (por regra de
negócio ou por valor inválido), para que possam ser corrigidos sem
digitar tudo de novo.

Cada campo é um par (rótulo, exibição): a exibição "" mostra o texto
digitado e "*" o esconde (campos de senha).
"""

import tkinter as tk
from tkinter import messagebox
from typing import Callable, List, Optional, Tuple

from source.domain.excecoes import RegraNegocioViolation


def centralizar_sobre(janela: tk.Misc, pai: tk.Misc) -> None:
    """Posiciona uma janela Toplevel sobre a janela que a abriu."""
    janela.update_idletasks()
    x = pai.winfo_rootx() + (pai.winfo_width() - janela.winfo_reqwidth()) // 2
    y = pai.winfo_rooty() + (pai.winfo_height() - janela.winfo_reqheight()) // 3
    janela.geometry(f"+{max(x, 0)}+{max(y, 0)}")


def ancorar(janela: tk.Toplevel, pai: Optional[tk.Misc]) -> None:
    """Prende uma janela Toplevel ao pai: mesma posição na barra de
    tarefas, centralizada sobre ele, modal e com o foco no primeiro campo."""
    if pai is None:
        return
    janela.transient(pai)
    centralizar_sobre(janela, pai)
    janela.wait_visibility()
    janela.grab_set()


class Formulario(tk.Toplevel):
    """Janela com campos Label + Entry; entrega os valores no confirmar."""

    def __init__(
        self,
        titulo: str,
        campos: List[Tuple[str, str]],
        ao_confirmar: Callable[[List[str]], None],
        valores_iniciais: Optional[List[str]] = None,
        pai: Optional[tk.Misc] = None,
    ) -> None:
        super().__init__(pai)
        self.title(titulo)
        self.resizable(False, False)
        self.__ao_confirmar = ao_confirmar

        quadro = tk.Frame(self, padx=10, pady=10)
        quadro.pack()
        preenchidos = valores_iniciais or []
        self.__entradas: List[tk.Entry] = []
        for linha, (rotulo, exibicao) in enumerate(campos):
            tk.Label(quadro, text=rotulo).grid(row=linha, column=0, sticky="w", pady=2)
            entrada = tk.Entry(quadro, width=28, show=exibicao)
            if linha < len(preenchidos):
                entrada.insert(0, preenchidos[linha])
            entrada.grid(row=linha, column=1, padx=4, pady=2)
            self.__entradas.append(entrada)
        if self.__entradas:
            self.__entradas[0].focus_set()

        botoes = tk.Frame(quadro)
        botoes.grid(row=len(campos), column=0, columnspan=2, pady=(10, 0))
        tk.Button(botoes, text="Confirmar", command=self.__confirmar).pack(
            side="left", padx=4
        )
        tk.Button(botoes, text="Cancelar", command=self.destroy).pack(side="left", padx=4)

        self.bind("<Return>", lambda evento: self.__confirmar())
        self.bind("<Escape>", lambda evento: self.destroy())
        ancorar(self, pai)

    def __confirmar(self) -> None:
        """Confirma o formulário: roda a ação e fecha; em erro, fica aberto."""
        valores = [entrada.get().strip() for entrada in self.__entradas]
        try:
            self.__ao_confirmar(valores)
        except RegraNegocioViolation as erro:
            messagebox.showwarning("Regra de negócio", erro.mensagem, parent=self)
            return
        except ValueError as erro:
            messagebox.showwarning("Dado inválido", str(erro), parent=self)
            return
        self.destroy()
