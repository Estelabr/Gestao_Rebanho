"""Área do Frigorífico: consultar animais disponíveis para compra,
comprar animais e ver o histórico de compras.

A compra usa o mesmo caso de uso da venda (VenderAnimal): é a mesma
transação vista pelo outro ator, como no diagrama de casos de uso —
o mesmo padrão do par ComprarInsumo/VenderInsumo. Sem regra de negócio:
apenas chama casos de uso e exibe o resultado. Ao fechar, devolve o
foco ao menu de seleção.
"""

import tkinter as tk
from tkinter import messagebox
from typing import Callable, List, Optional

from source.interfaces.formularios import Formulario
from source.usecases.contenedor import CasosDeUso


class JanelaFrigorifico(tk.Toplevel):
    """Área do Frigorífico: as funções do papel dele, e só delas."""

    def __init__(self, casos: CasosDeUso, ao_fechar: Optional[Callable[[], None]] = None) -> None:
        super().__init__()
        self.__casos = casos
        self.__ao_fechar = ao_fechar
        self.title("Sistema de Gestão de Rebanho — Área do Frigorífico")
        self.geometry("640x480")
        self.protocol("WM_DELETE_WINDOW", self.__fechar)
        self.__montar_cabecalho()
        self.__montar_disponiveis()
        self.__montar_historico()
        self.__atualizar()

    def __fechar(self) -> None:
        self.destroy()
        if self.__ao_fechar is not None:
            self.__ao_fechar()

    # ------------------------------------------------------------------
    # Montagem da janela
    # ------------------------------------------------------------------
    def __montar_cabecalho(self) -> None:
        cabecalho = tk.Frame(self, padx=10, pady=6)
        cabecalho.pack(fill="x")
        self.__rotulo_cadastro = tk.Label(
            cabecalho,
            text=f"Frigorífico: {self.__casos.resumo_cadastro('frigorifico')}",
            anchor="w",
        )
        self.__rotulo_cadastro.pack(side="left", fill="x", expand=True)
        tk.Button(cabecalho, text="Meu cadastro", command=self.__meu_cadastro).pack(
            side="right"
        )

    def __meu_cadastro(self) -> None:
        nome, cnpj = self.__casos.cadastro("frigorifico")

        def confirmar(valores: List[str]) -> None:
            self.__casos.cadastrar_frigorifico.executar(valores[0], valores[1])
            messagebox.showinfo(
                "Cadastro",
                f"Cadastro salvo: {self.__casos.resumo_cadastro('frigorifico')}",
                parent=self,
            )
            self.__rotulo_cadastro.config(
                text=f"Frigorífico: {self.__casos.resumo_cadastro('frigorifico')}"
            )

        Formulario(
            "Cadastro do frigorífico",
            [("Nome:", ""), ("CNPJ:", "")],
            confirmar,
            valores_iniciais=[nome, cnpj],
            pai=self,
        )

    def __montar_disponiveis(self) -> None:
        quadro = tk.LabelFrame(
            self, text="Animais disponíveis para compra", padx=8, pady=8
        )
        quadro.pack(fill="both", expand=True, padx=10, pady=4)

        botoes = tk.Frame(quadro)
        botoes.pack(fill="x")
        tk.Button(botoes, text="Atualizar", command=self.__atualizar).pack(
            side="left", padx=4
        )
        tk.Button(
            botoes, text="Comprar animal selecionado", command=self.__comprar
        ).pack(side="left", padx=4)

        quadro_lista = tk.Frame(quadro)
        quadro_lista.pack(fill="both", expand=True)
        self.__disponiveis = tk.Listbox(quadro_lista, height=7)
        self.__brincos_disponiveis: List[str] = []
        self.__disponiveis.pack(side="left", fill="both", expand=True)
        barra = tk.Scrollbar(quadro_lista, command=self.__disponiveis.yview)
        barra.pack(side="right", fill="y")
        self.__disponiveis.config(yscrollcommand=barra.set)

    def __montar_historico(self) -> None:
        quadro = tk.LabelFrame(self, text="Histórico de compras", padx=8, pady=8)
        quadro.pack(fill="both", expand=True, padx=10, pady=4)
        self.__historico = tk.Listbox(quadro, height=7)
        self.__historico.pack(side="left", fill="both", expand=True)
        barra = tk.Scrollbar(quadro, command=self.__historico.yview)
        barra.pack(side="right", fill="y")
        self.__historico.config(yscrollcommand=barra.set)

    # ------------------------------------------------------------------
    # Ações: só chamam casos de uso e mostram o resultado
    # ------------------------------------------------------------------
    def __atualizar(self) -> None:
        self.__disponiveis.delete(0, "end")
        disponiveis = self.__casos.identificar_para_venda.executar()
        self.__brincos_disponiveis = [animal.brinco.valor for animal in disponiveis]
        for animal in disponiveis:
            self.__disponiveis.insert(
                "end",
                f"{animal} - {animal.peso_atual():.1f} kg "
                f"(mínimo de abate: {animal.peso_minimo_abate():.1f} kg)",
            )
        self.__historico.delete(0, "end")
        for compra in self.__casos.historico_compras.executar():
            self.__historico.insert("end", compra.resumo())

    def __comprar(self) -> None:
        selecao = self.__disponiveis.curselection()
        if not selecao:
            messagebox.showinfo(
                "Compra", "Selecione um animal na lista de disponíveis.", parent=self
            )
            return
        brinco = self.__brincos_disponiveis[selecao[0]]

        def confirmar(valores: List[str]) -> None:
            # Mesma transação da venda do proprietário, vista pelo frigorífico.
            compra = self.__casos.vender_animal.executar(
                brinco, float(valores[0].replace(",", "."))
            )
            messagebox.showinfo("Compra", f"Compra registrada:\n{compra}", parent=self)
            self.__atualizar()

        Formulario(
            f"Comprar o animal {brinco}",
            [("Valor da compra (R$):", "")],
            confirmar,
            pai=self,
        )
