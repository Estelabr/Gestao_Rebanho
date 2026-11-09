"""Interface gráfica em Tkinter (Parte 3 do trabalho).

Janela principal com nome do sistema, formulários com Entry, Label,
Button e Frame, e messagebox para o feedback. A interface não contém
regra de negócio: apenas instancia, lista e modifica objetos chamando
os casos de uso, que por sua vez chamam as classes do sistema.
"""

import tkinter as tk
from tkinter import messagebox, simpledialog
from datetime import datetime
from typing import Callable, List, Optional, Tuple

from source.domain.excecoes import RegraNegocioViolation
from source.usecases.contenedor import CasosDeUso


class JanelaPrincipal(tk.Tk):
    """Janela principal do sistema de gestão de rebanho."""

    def __init__(self, casos: CasosDeUso) -> None:
        super().__init__()
        self.__casos = casos
        self.title("Sistema de Gestão de Rebanho")
        self.geometry("720x600")
        self.__montar_formulario()
        self.__montar_lista()
        self.__montar_quadro("Manejo", self.__botoes_manejo())
        self.__montar_quadro("Reprodução", self.__botoes_reproducao())
        self.__montar_quadro("Nutrição", self.__botoes_nutricao())
        self.__montar_quadro("Comércio e cadastro", self.__botoes_comercio())
        self.__atualizar_lista()

    # ------------------------------------------------------------------
    # Montagem da janela
    # ------------------------------------------------------------------
    def __montar_formulario(self) -> None:
        formulario = tk.LabelFrame(self, text="Cadastrar animal", padx=8, pady=8)
        formulario.pack(fill="x", padx=10, pady=4)

        tk.Label(formulario, text="Brinco:").grid(row=0, column=0, sticky="w")
        self.__entry_brinco = tk.Entry(formulario, width=24)
        self.__entry_brinco.grid(row=0, column=1, padx=4, pady=2)

        tk.Label(formulario, text="Nascimento (dd/mm/aaaa):").grid(
            row=1, column=0, sticky="w"
        )
        self.__entry_nascimento = tk.Entry(formulario, width=24)
        self.__entry_nascimento.grid(row=1, column=1, padx=4, pady=2)

        tk.Label(formulario, text="Raça:").grid(row=2, column=0, sticky="w")
        self.__entry_raca = tk.Entry(formulario, width=24)
        self.__entry_raca.grid(row=2, column=1, padx=4, pady=2)

        self.__tipo_selecionado = tk.StringVar(value="femea")
        tk.Radiobutton(
            formulario, text="Fêmea", variable=self.__tipo_selecionado, value="femea"
        ).grid(row=0, column=2, sticky="w")
        tk.Radiobutton(
            formulario, text="Macho", variable=self.__tipo_selecionado, value="macho"
        ).grid(row=1, column=2, sticky="w")

        tk.Button(formulario, text="Cadastrar", command=self.__cadastrar_animal).grid(
            row=2, column=2, padx=4, pady=2
        )

    def __montar_lista(self) -> None:
        quadro = tk.LabelFrame(self, text="Animais do rebanho", padx=8, pady=8)
        quadro.pack(fill="both", expand=True, padx=10, pady=4)

        self.__lista = tk.Listbox(quadro, height=8)
        self.__lista.pack(side="left", fill="both", expand=True)
        barra = tk.Scrollbar(quadro, command=self.__lista.yview)
        barra.pack(side="right", fill="y")
        self.__lista.config(yscrollcommand=barra.set)

    def __montar_quadro(
        self, titulo: str, botoes: Tuple[Tuple[str, Callable[[], None]], ...]
    ) -> None:
        quadro = tk.LabelFrame(self, text=titulo, padx=8, pady=4)
        quadro.pack(fill="x", padx=10, pady=2)
        for texto, acao in botoes:
            tk.Button(quadro, text=texto, command=acao).pack(side="left", padx=4)

    def __botoes_manejo(self) -> Tuple[Tuple[str, Callable[[], None]], ...]:
        return (
            ("Registrar pesagem", self.__registrar_pesagem),
            ("Registrar vacinação", self.__registrar_vacinacao),
            ("Excluir animal", self.__excluir_animal),
        )

    def __botoes_reproducao(self) -> Tuple[Tuple[str, Callable[[], None]], ...]:
        return (
            ("Inseminar", self.__inseminar),
            ("Registrar parto", self.__registrar_parto),
            ("Consultar genética", self.__consultar_genetica),
        )

    def __botoes_nutricao(self) -> Tuple[Tuple[str, Callable[[], None]], ...]:
        return (
            ("Criar base", self.__criar_base),
            ("Definir alimentação", self.__definir_alimentacao),
            ("Consultar alimentação", self.__consultar_alimentacao),
        )

    def __botoes_comercio(self) -> Tuple[Tuple[str, Callable[[], None]], ...]:
        return (
            ("Vender ao frigorífico", self.__vender),
            ("Animais para venda", self.__identificar_para_venda),
            ("Histórico de compras", self.__historico_compras),
            ("Comprar insumo", self.__comprar_insumo),
            ("Cadastrar insumo (Fornecedor)", self.__cadastrar_insumo),
            ("Vender insumo (Fornecedor)", self.__vender_insumo),
            ("Meu cadastro (Autocadastro)", self.__autocadastro),
        )

    # ------------------------------------------------------------------
    # Ações: só chamam casos de uso e mostram o resultado
    # ------------------------------------------------------------------
    def __brinco_selecionado(self) -> Optional[str]:
        selecao = self.__lista.curselection()
        if not selecao:
            return None
        return self.__lista.get(selecao[0]).split(" - ")[0]

    def __atualizar_lista(self) -> None:
        self.__lista.delete(0, "end")
        for animal in self.__casos.animais():
            peso = f"{animal.peso_atual():.1f} kg" if animal.pesagens else "sem pesagem"
            estado = "vendido" if animal.vendido else "no rebanho"
            self.__lista.insert("end", f"{animal} - {peso} - {estado}")

    def __executar(self, acao) -> None:
        """Roda o caso de uso e traduz erros de negócio em messagebox."""
        try:
            acao()
        except RegraNegocioViolation as erro:
            messagebox.showwarning("Regra de negócio", erro.mensagem)
        except ValueError as erro:
            messagebox.showwarning("Dado inválido", str(erro))
        self.__atualizar_lista()

    def __cadastrar_animal(self) -> None:
        def acao() -> None:
            brinco = self.__entry_brinco.get().strip()
            texto_data = self.__entry_nascimento.get().strip()
            raca = self.__entry_raca.get().strip()
            nascimento = (
                datetime.strptime(texto_data, "%d/%m/%Y").date()
                if texto_data
                else datetime.now().date()
            )
            animal = self.__casos.cadastrar_animal.executar(
                brinco, nascimento, raca, self.__tipo_selecionado.get()
            )
            messagebox.showinfo("Cadastro", f"Animal cadastrado:\n{animal}")
            self.__entry_brinco.delete(0, "end")
            self.__entry_nascimento.delete(0, "end")
            self.__entry_raca.delete(0, "end")

        self.__executar(acao)

    def __registrar_pesagem(self) -> None:
        brinco = self.__brinco_selecionado()
        if brinco is None:
            messagebox.showinfo("Pesagem", "Selecione um animal na lista.")
            return
        texto = simpledialog.askstring("Pesagem", f"Peso (kg) do animal {brinco}:")
        if texto is None:
            return

        def acao() -> None:
            pesagem = self.__casos.registrar_pesagem.executar(
                brinco, float(texto.replace(",", "."))
            )
            messagebox.showinfo("Pesagem", f"Pesagem registrada:\n{pesagem}")

        self.__executar(acao)

    def __registrar_vacinacao(self) -> None:
        brinco = self.__brinco_selecionado()
        if brinco is None:
            messagebox.showinfo("Vacinação", "Selecione um animal na lista.")
            return
        vacina = simpledialog.askstring("Vacinação", "Nome da vacina:")
        if vacina is None:
            return
        dose = simpledialog.askstring("Vacinação", "Dose:") or "1 dose"

        def acao() -> None:
            vacinacao = self.__casos.registrar_vacinacao.executar(brinco, vacina, dose)
            messagebox.showinfo("Vacinação", f"Vacinação registrada:\n{vacinacao}")

        self.__executar(acao)

    def __inseminar(self) -> None:
        brinco_femea = self.__brinco_selecionado()
        if brinco_femea is None:
            messagebox.showinfo("Inseminação", "Selecione a fêmea na lista.")
            return

        def acao() -> None:
            # Include do diagrama: antes de inseminar, consultar a genética.
            genetica = self.__casos.consultar_genetica.executar(brinco_femea)
            brinco_touro = simpledialog.askstring(
                "Inseminação", f"{genetica}\n\nBrinco do touro:"
            )
            if brinco_touro is None:
                return
            self.__casos.inseminar_femea.executar(brinco_femea, brinco_touro.strip())
            messagebox.showinfo(
                "Inseminação",
                f"Fêmea {brinco_femea} inseminada pelo touro {brinco_touro}.",
            )

        self.__executar(acao)

    def __registrar_parto(self) -> None:
        brinco_femea = self.__brinco_selecionado()
        if brinco_femea is None:
            messagebox.showinfo("Parto", "Selecione a fêmea na lista.")
            return

        def acao() -> None:
            brinco_filho = simpledialog.askstring(
                "Parto", f"Brinco do bezerro de {brinco_femea}:"
            )
            if brinco_filho is None:
                return
            macho = messagebox.askyesno("Parto", "O bezerro é macho?")
            bezerro = self.__casos.registrar_parto.executar(
                brinco_femea, brinco_filho.strip(), macho
            )
            messagebox.showinfo("Parto", f"Bezerro cadastrado:\n{bezerro}")

        self.__executar(acao)

    def __consultar_genetica(self) -> None:
        brinco = self.__brinco_selecionado()
        if brinco is None:
            messagebox.showinfo("Genética", "Selecione um animal na lista.")
            return

        def acao() -> None:
            messagebox.showinfo(
                "Genética", self.__casos.consultar_genetica.executar(brinco)
            )

        self.__executar(acao)

    def __criar_base(self) -> None:
        def acao() -> None:
            nome = simpledialog.askstring("Nutrição", "Nome da base de alimentação:")
            if nome is None:
                return
            descricao = simpledialog.askstring("Nutrição", "Descrição da base:") or ""
            texto = simpledialog.askstring(
                "Nutrição",
                "Insumos da base, no formato nome=quantidade por animal/dia,\n"
                "separados por vírgula. Exemplo:\nRação 20%=2.5, Sal mineral=0.1",
            )
            if texto is None:
                return
            base = self.__casos.criar_base.executar(
                nome.strip(), descricao, self.__ler_itens_da_base(texto)
            )
            messagebox.showinfo("Nutrição", f"Base criada:\n{base}")

        self.__executar(acao)

    def __definir_alimentacao(self) -> None:
        brinco = self.__brinco_selecionado()
        if brinco is None:
            messagebox.showinfo("Nutrição", "Selecione um animal na lista.")
            return

        def acao() -> None:
            nomes = ", ".join(base.nome for base in self.__casos.bases())
            if not nomes:
                messagebox.showinfo("Nutrição", "Nenhuma base de alimentação criada.")
                return
            nome_base = simpledialog.askstring(
                "Nutrição", f"Bases disponíveis: {nomes}\n\nNome da base para {brinco}:"
            )
            if nome_base is None:
                return
            self.__casos.definir_alimentacao.executar(brinco, nome_base.strip())
            messagebox.showinfo(
                "Nutrição",
                f"Animal {brinco} agora se alimenta da base {nome_base.strip()}.",
            )

        self.__executar(acao)

    def __consultar_alimentacao(self) -> None:
        brinco = self.__brinco_selecionado()
        if brinco is None:
            messagebox.showinfo("Nutrição", "Selecione um animal na lista.")
            return

        def acao() -> None:
            messagebox.showinfo(
                "Nutrição", self.__casos.consultar_alimentacao.executar(brinco)
            )

        self.__executar(acao)

    def __ler_itens_da_base(self, texto: str) -> List[Tuple[str, float]]:
        itens: List[Tuple[str, float]] = []
        for parte in texto.split(","):
            if not parte.strip():
                continue
            nome_insumo, _, quantidade = parte.partition("=")
            itens.append((nome_insumo.strip(), float(quantidade.replace(",", "."))))
        return itens

    def __identificar_para_venda(self) -> None:
        def acao() -> None:
            animais = self.__casos.identificar_para_venda.executar()
            if not animais:
                messagebox.showinfo(
                    "Venda", "Nenhum animal com o peso mínimo de abate atingido."
                )
                return
            linhas = [
                f"{animal} - {animal.peso_atual():.1f} kg "
                f"(mínimo de abate: {animal.peso_minimo_abate():.1f} kg)"
                for animal in animais
            ]
            messagebox.showinfo(
                "Venda / Animais disponíveis para compra", "\n".join(linhas)
            )

        self.__executar(acao)

    def __vender(self) -> None:
        brinco = self.__brinco_selecionado()
        if brinco is None:
            messagebox.showinfo("Venda", "Selecione um animal na lista.")
            return
        texto = simpledialog.askstring(
            "Venda", f"Valor da venda (R$) do animal {brinco}:"
        )
        if texto is None:
            return

        def acao() -> None:
            compra = self.__casos.vender_animal.executar(
                brinco, float(texto.replace(",", "."))
            )
            messagebox.showinfo("Venda", f"Venda registrada:\n{compra}")

        self.__executar(acao)

    def __historico_compras(self) -> None:
        def acao() -> None:
            compras = self.__casos.historico_compras.executar()
            if not compras:
                messagebox.showinfo(
                    "Histórico de compras", "Nenhuma compra registrada."
                )
                return
            messagebox.showinfo(
                "Histórico de compras",
                "\n".join(compra.resumo() for compra in compras),
            )

        self.__executar(acao)

    def __comprar_insumo(self) -> None:
        nome = simpledialog.askstring("Insumo", "Nome do insumo:")
        if nome is None:
            return
        texto = simpledialog.askstring("Insumo", "Quantidade comprada:")
        if texto is None:
            return

        def acao() -> None:
            insumo = self.__casos.comprar_insumo.executar(
                nome.strip(), float(texto.replace(",", "."))
            )
            messagebox.showinfo("Insumo", f"Insumo em estoque:\n{insumo}")

        self.__executar(acao)

    def __cadastrar_insumo(self) -> None:
        nome = simpledialog.askstring("Insumo", "Nome do insumo:")
        if nome is None:
            return
        tipo = simpledialog.askstring("Insumo", "Tipo do insumo:") or "Nutricional"
        texto_quantidade = simpledialog.askstring("Insumo", "Quantidade do lote:")
        if texto_quantidade is None:
            return
        texto_preco = simpledialog.askstring("Insumo", "Preço unitário (R$):") or "0"

        def acao() -> None:
            lote = self.__casos.cadastrar_insumo.executar(
                nome.strip(),
                tipo,
                float(texto_quantidade.replace(",", ".")),
                float(texto_preco.replace(",", ".")),
            )
            messagebox.showinfo("Insumo", f"Insumo no catálogo do fornecedor:\n{lote}")

        self.__executar(acao)

    def __vender_insumo(self) -> None:
        nome = simpledialog.askstring("Insumo", "Nome do insumo:")
        if nome is None:
            return
        texto = simpledialog.askstring("Insumo", "Quantidade vendida:")
        if texto is None:
            return

        def acao() -> None:
            insumo = self.__casos.vender_insumo.executar(
                nome.strip(), float(texto.replace(",", "."))
            )
            messagebox.showinfo("Insumo", f"Insumo entregue à fazenda:\n{insumo}")

        self.__executar(acao)

    def __autocadastro(self) -> None:
        nome = simpledialog.askstring("Autocadastro", "Seu nome:")
        if nome is None:
            return
        cpf = simpledialog.askstring("Autocadastro", "Seu CPF:") or ""

        def acao() -> None:
            proprietario = self.__casos.autocadastro.executar(nome.strip(), cpf.strip())
            messagebox.showinfo(
                "Autocadastro",
                f"Cadastro atualizado: {proprietario.nome} ({proprietario.cpf})",
            )

        self.__executar(acao)

    def __excluir_animal(self) -> None:
        brinco = self.__brinco_selecionado()
        if brinco is None:
            messagebox.showinfo("Excluir", "Selecione um animal na lista.")
            return
        if not messagebox.askyesno("Excluir", f"Excluir o animal {brinco}?"):
            return

        def acao() -> None:
            self.__casos.excluir_animal(brinco)
            messagebox.showinfo("Excluir", f"Animal {brinco} excluído.")

        self.__executar(acao)


def iniciar_interface(casos: CasosDeUso) -> None:
    """Abre a janela principal (chamado pelo main.py)."""
    JanelaPrincipal(casos).mainloop()
