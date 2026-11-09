"""Área do Fornecedor de Insumos: cadastro de insumos no catálogo,
venda de insumos ao proprietário e listagem do catálogo.

A venda usa o mesmo caso de uso da compra do proprietário
(VenderInsumo): é a mesma transação vista pelo outro ator, como no
diagrama de casos de uso. Sem regra de negócio: apenas chama casos de
uso e exibe o resultado. Ao fechar, devolve o foco ao menu de seleção.
"""

import tkinter as tk
from tkinter import messagebox
from typing import Callable, List, Optional

from source.interfaces.formularios import Formulario
from source.usecases.contenedor import CasosDeUso


class JanelaFornecedor(tk.Toplevel):
    """Área do Fornecedor de Insumos: as funções do papel dele, e só delas."""

    def __init__(self, casos: CasosDeUso, ao_fechar: Optional[Callable[[], None]] = None) -> None:
        super().__init__()
        self.__casos = casos
        self.__ao_fechar = ao_fechar
        self.title("Sistema de Gestão de Rebanho — Área do Fornecedor de Insumos")
        self.geometry("640x480")
        self.protocol("WM_DELETE_WINDOW", self.__fechar)
        self.__montar_cabecalho()
        self.__montar_operacoes()
        self.__montar_catalogo()
        self.__atualizar_catalogo()

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
            text=f"Fornecedor: {self.__casos.resumo_cadastro('fornecedor')}",
            anchor="w",
        )
        self.__rotulo_cadastro.pack(side="left", fill="x", expand=True)
        tk.Button(cabecalho, text="Meu cadastro", command=self.__meu_cadastro).pack(
            side="right"
        )

    def __meu_cadastro(self) -> None:
        nome, cnpj = self.__casos.cadastro("fornecedor")

        def confirmar(valores: List[str]) -> None:
            self.__casos.cadastrar_fornecedor.executar(valores[0], valores[1])
            messagebox.showinfo(
                "Cadastro",
                f"Cadastro salvo: {self.__casos.resumo_cadastro('fornecedor')}",
                parent=self,
            )
            self.__rotulo_cadastro.config(
                text=f"Fornecedor: {self.__casos.resumo_cadastro('fornecedor')}"
            )

        Formulario(
            "Cadastro do fornecedor",
            [("Nome:", ""), ("CNPJ:", "")],
            confirmar,
            valores_iniciais=[nome, cnpj],
            pai=self,
        )

    def __montar_operacoes(self) -> None:
        quadro = tk.LabelFrame(self, text="Operações", padx=8, pady=4)
        quadro.pack(fill="x", padx=10, pady=4)
        for texto, acao in (
            ("Cadastrar insumo", self.__cadastrar_insumo),
            ("Vender insumo", self.__vender_insumo),
            ("Atualizar catálogo", self.__atualizar_catalogo),
        ):
            tk.Button(quadro, text=texto, command=acao).pack(side="left", padx=4)

    def __montar_catalogo(self) -> None:
        quadro = tk.LabelFrame(self, text="Catálogo de insumos", padx=8, pady=8)
        quadro.pack(fill="both", expand=True, padx=10, pady=4)
        self.__catalogo = tk.Listbox(quadro, height=10)
        self.__catalogo.pack(side="left", fill="both", expand=True)
        barra = tk.Scrollbar(quadro, command=self.__catalogo.yview)
        barra.pack(side="right", fill="y")
        self.__catalogo.config(yscrollcommand=barra.set)

    # ------------------------------------------------------------------
    # Ações: só chamam casos de uso e mostram o resultado
    # ------------------------------------------------------------------
    def __atualizar_catalogo(self) -> None:
        self.__catalogo.delete(0, "end")
        for lote in self.__casos.catalogo_fornecedor():
            self.__catalogo.insert("end", str(lote))

    def __cadastrar_insumo(self) -> None:
        def confirmar(valores: List[str]) -> None:
            lote = self.__casos.cadastrar_insumo.executar(
                valores[0],
                valores[1] or "Nutricional",
                float(valores[2].replace(",", ".")),
                float(valores[3].replace(",", ".")),
            )
            messagebox.showinfo(
                "Insumo", f"Insumo no catálogo do fornecedor:\n{lote}", parent=self
            )
            self.__atualizar_catalogo()

        Formulario(
            "Cadastrar insumo no catálogo",
            [
                ("Nome:", ""),
                ("Tipo:", ""),
                ("Quantidade do lote:", ""),
                ("Preço unitário (R$):", ""),
            ],
            confirmar,
            pai=self,
        )

    def __vender_insumo(self) -> None:
        def confirmar(valores: List[str]) -> None:
            # Mesma transação da compra do proprietário, vista pelo fornecedor.
            insumo = self.__casos.vender_insumo.executar(
                valores[0], float(valores[1].replace(",", "."))
            )
            messagebox.showinfo(
                "Insumo", f"Insumo entregue à fazenda:\n{insumo}", parent=self
            )
            self.__atualizar_catalogo()

        Formulario(
            "Vender insumo",
            [("Nome do insumo:", ""), ("Quantidade vendida:", "")],
            confirmar,
            pai=self,
        )
