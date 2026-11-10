"""Área do Proprietário da fazenda.

É o ator que mais usa o sistema: cadastro de animais, manejo (pesagem e
vacinação), reprodução (inseminação, parto e genética), nutrição e
comércio (venda ao frigorífico e compra de insumos). No sistema
multiusuário, esta é a área do papel da conta logada: o login já provou
quem entra, com o documento e a senha da conta. Sem regra de negócio:
apenas chama casos de uso e exibe o resultado. Ao fechar, o fluxo volta
ao login.
"""

import tkinter as tk
from tkinter import messagebox, simpledialog
from datetime import datetime
from typing import Callable, List, Optional, Tuple

from source.domain.excecoes import RegraNegocioViolation
from source.interfaces.formularios import Formulario, ancorar
from source.interfaces.janela_autocadastro import JanelaAutocadastro
from source.usecases.contenedor import CasosDeUso


class JanelaCadastroAnimal(tk.Toplevel):
    """Formulário do cadastro de animal: brinco, nascimento, raça e tipo."""

    def __init__(
        self,
        casos: CasosDeUso,
        ao_cadastrar: Callable[[str], None],
        pai: Optional[tk.Misc] = None,
    ) -> None:
        super().__init__(pai)
        self.__casos = casos
        self.__ao_cadastrar = ao_cadastrar
        self.title("Cadastrar animal")
        self.resizable(False, False)

        quadro = tk.Frame(self, padx=10, pady=10)
        quadro.pack()
        tk.Label(quadro, text="Brinco:").grid(row=0, column=0, sticky="w", pady=2)
        self.__entry_brinco = tk.Entry(quadro, width=24)
        self.__entry_brinco.grid(row=0, column=1, padx=4, pady=2)

        tk.Label(quadro, text="Nascimento (dd/mm/aaaa):").grid(
            row=1, column=0, sticky="w", pady=2
        )
        self.__entry_nascimento = tk.Entry(quadro, width=24)
        self.__entry_nascimento.grid(row=1, column=1, padx=4, pady=2)

        tk.Label(quadro, text="Raça:").grid(row=2, column=0, sticky="w", pady=2)
        self.__entry_raca = tk.Entry(quadro, width=24)
        self.__entry_raca.grid(row=2, column=1, padx=4, pady=2)

        self.__tipo_selecionado = tk.StringVar(value="femea")
        tk.Radiobutton(
            quadro, text="Fêmea", variable=self.__tipo_selecionado, value="femea"
        ).grid(row=0, column=2, sticky="w")
        tk.Radiobutton(
            quadro, text="Macho", variable=self.__tipo_selecionado, value="macho"
        ).grid(row=1, column=2, sticky="w")

        botoes = tk.Frame(quadro)
        botoes.grid(row=3, column=0, columnspan=3, pady=(10, 0))
        tk.Button(botoes, text="Cadastrar", command=self.__cadastrar).pack(
            side="left", padx=4
        )
        tk.Button(botoes, text="Cancelar", command=self.destroy).pack(side="left", padx=4)

        self.__entry_brinco.focus_set()
        self.bind("<Return>", lambda evento: self.__cadastrar())
        self.bind("<Escape>", lambda evento: self.destroy())
        ancorar(self, pai)

    def __cadastrar(self) -> None:
        brinco = self.__entry_brinco.get().strip()
        texto_data = self.__entry_nascimento.get().strip()
        raca = self.__entry_raca.get().strip()
        try:
            nascimento = (
                datetime.strptime(texto_data, "%d/%m/%Y").date()
                if texto_data
                else datetime.now().date()
            )
            animal = self.__casos.cadastrar_animal.executar(
                brinco, nascimento, raca, self.__tipo_selecionado.get()
            )
        except RegraNegocioViolation as erro:
            messagebox.showwarning("Regra de negócio", erro.mensagem, parent=self)
            return
        except ValueError as erro:
            messagebox.showwarning("Dado inválido", str(erro), parent=self)
            return
        self.destroy()
        self.__ao_cadastrar(str(animal))


class JanelaProprietario(tk.Toplevel):
    """Área do Proprietário: as funções do papel dele, e só delas."""

    def __init__(self, casos: CasosDeUso, ao_fechar: Optional[Callable[[], None]] = None) -> None:
        super().__init__()
        self.__casos = casos
        self.__ao_fechar = ao_fechar
        self.title("Sistema de Gestão de Rebanho — Área do Proprietário")
        self.geometry("720x600")
        self.protocol("WM_DELETE_WINDOW", self.__fechar)
        self.__montar_cabecalho()
        self.__montar_rebanho()
        self.__montar_quadro("Reprodução", self.__botoes_reproducao())
        self.__montar_quadro("Nutrição", self.__botoes_nutricao())
        self.__montar_quadro("Comércio da fazenda", self.__botoes_comercio())
        self.__atualizar_lista()

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
            text=f"Proprietário: {self.__casos.resumo_cadastro('proprietario')}",
            anchor="w",
        )
        self.__rotulo_cadastro.pack(side="left", fill="x", expand=True)
        tk.Button(cabecalho, text="Meu cadastro", command=self.__meu_cadastro).pack(
            side="right"
        )

    def __meu_cadastro(self) -> None:
        """Corrige o autocadastro: nome, CPF e senha do proprietário."""
        JanelaAutocadastro(
            self.__casos, ao_salvar=self.__atualizar_cabecalho, pai=self
        )

    def __atualizar_cabecalho(self) -> None:
        self.__rotulo_cadastro.config(
            text=f"Proprietário: {self.__casos.resumo_cadastro('proprietario')}"
        )

    def __montar_rebanho(self) -> None:
        quadro = tk.LabelFrame(self, text="Animais do rebanho", padx=8, pady=8)
        quadro.pack(fill="both", expand=True, padx=10, pady=4)

        botoes = tk.Frame(quadro)
        botoes.pack(fill="x")
        for texto, acao in (
            ("Cadastrar animal", self.__abrir_cadastro_animal),
            ("Registrar pesagem", self.__registrar_pesagem),
            ("Registrar vacinação", self.__registrar_vacinacao),
            ("Excluir animal", self.__excluir_animal),
        ):
            tk.Button(botoes, text=texto, command=acao).pack(side="left", padx=4)

        quadro_lista = tk.Frame(quadro)
        quadro_lista.pack(fill="both", expand=True)
        self.__lista = tk.Listbox(quadro_lista, height=8)
        # Brinco de cada linha da lista, na mesma ordem: o texto da linha
        # é só apresentação e pode mudar de formato.
        self.__brincos: List[str] = []
        self.__lista.pack(side="left", fill="both", expand=True)
        barra = tk.Scrollbar(quadro_lista, command=self.__lista.yview)
        barra.pack(side="right", fill="y")
        self.__lista.config(yscrollcommand=barra.set)

    def __montar_quadro(
        self, titulo: str, botoes: Tuple[Tuple[str, Callable[[], None]], ...]
    ) -> None:
        quadro = tk.LabelFrame(self, text=titulo, padx=8, pady=4)
        quadro.pack(fill="x", padx=10, pady=2)
        for texto, acao in botoes:
            tk.Button(quadro, text=texto, command=acao).pack(side="left", padx=4)

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
            ("Comprar insumo", self.__comprar_insumo),
            ("Insumos da fazenda", self.__listar_insumos),
        )

    # ------------------------------------------------------------------
    # Ações: só chamam casos de uso e mostram o resultado
    # ------------------------------------------------------------------
    def __brinco_selecionado(self) -> Optional[str]:
        selecao = self.__lista.curselection()
        if not selecao:
            return None
        return self.__brincos[selecao[0]]

    def __atualizar_lista(self) -> None:
        self.__lista.delete(0, "end")
        animais = self.__casos.animais()
        self.__brincos = [animal.brinco.valor for animal in animais]
        for animal in animais:
            peso = f"{animal.peso_atual():.1f} kg" if animal.pesagens else "sem pesagem"
            estado = "vendido" if animal.vendido else "no rebanho"
            self.__lista.insert("end", f"{animal} - {peso} - {estado}")

    def __executar(self, acao) -> None:
        """Roda o caso de uso e traduz erros de negócio em messagebox."""
        try:
            acao()
        except RegraNegocioViolation as erro:
            messagebox.showwarning("Regra de negócio", erro.mensagem, parent=self)
        except ValueError as erro:
            messagebox.showwarning("Dado inválido", str(erro), parent=self)
        self.__atualizar_lista()

    def __abrir_cadastro_animal(self) -> None:
        JanelaCadastroAnimal(
            self.__casos, ao_cadastrar=self.__mostrar_animal_cadastrado, pai=self
        )

    def __mostrar_animal_cadastrado(self, texto: str) -> None:
        messagebox.showinfo("Cadastro", f"Animal cadastrado:\n{texto}", parent=self)
        self.__atualizar_lista()

    def __registrar_pesagem(self) -> None:
        brinco = self.__brinco_selecionado()
        if brinco is None:
            messagebox.showinfo("Pesagem", "Selecione um animal na lista.", parent=self)
            return
        texto = simpledialog.askstring(
            "Pesagem", f"Peso (kg) do animal {brinco}:", parent=self
        )
        if texto is None:
            return

        def acao() -> None:
            pesagem = self.__casos.registrar_pesagem.executar(
                brinco, float(texto.replace(",", "."))
            )
            messagebox.showinfo("Pesagem", f"Pesagem registrada:\n{pesagem}", parent=self)

        self.__executar(acao)

    def __registrar_vacinacao(self) -> None:
        brinco = self.__brinco_selecionado()
        if brinco is None:
            messagebox.showinfo("Vacinação", "Selecione um animal na lista.", parent=self)
            return
        vacina = simpledialog.askstring(
            "Vacinação", "Nome da vacina:", parent=self
        )
        if vacina is None:
            return
        dose = (
            simpledialog.askstring("Vacinação", "Dose:", parent=self) or "1 dose"
        )

        def acao() -> None:
            vacinacao = self.__casos.registrar_vacinacao.executar(brinco, vacina, dose)
            messagebox.showinfo(
                "Vacinação", f"Vacinação registrada:\n{vacinacao}", parent=self
            )

        self.__executar(acao)

    def __inseminar(self) -> None:
        brinco_femea = self.__brinco_selecionado()
        if brinco_femea is None:
            messagebox.showinfo(
                "Inseminação", "Selecione a fêmea na lista.", parent=self
            )
            return

        def acao() -> None:
            # Include do diagrama: antes de inseminar, consultar a genética.
            genetica = self.__casos.consultar_genetica.executar(brinco_femea)
            brinco_touro = simpledialog.askstring(
                "Inseminação", f"{genetica}\n\nBrinco do touro:", parent=self
            )
            if brinco_touro is None:
                return
            self.__casos.inseminar_femea.executar(brinco_femea, brinco_touro.strip())
            messagebox.showinfo(
                "Inseminação",
                f"Fêmea {brinco_femea} inseminada pelo touro {brinco_touro}.",
                parent=self,
            )

        self.__executar(acao)

    def __registrar_parto(self) -> None:
        brinco_femea = self.__brinco_selecionado()
        if brinco_femea is None:
            messagebox.showinfo("Parto", "Selecione a fêmea na lista.", parent=self)
            return

        def acao() -> None:
            brinco_filho = simpledialog.askstring(
                "Parto", f"Brinco do bezerro de {brinco_femea}:", parent=self
            )
            if brinco_filho is None:
                return
            macho = messagebox.askyesno("Parto", "O bezerro é macho?", parent=self)
            bezerro = self.__casos.registrar_parto.executar(
                brinco_femea, brinco_filho.strip(), macho
            )
            messagebox.showinfo("Parto", f"Bezerro cadastrado:\n{bezerro}", parent=self)

        self.__executar(acao)

    def __consultar_genetica(self) -> None:
        brinco = self.__brinco_selecionado()
        if brinco is None:
            messagebox.showinfo("Genética", "Selecione um animal na lista.", parent=self)
            return

        def acao() -> None:
            messagebox.showinfo(
                "Genética", self.__casos.consultar_genetica.executar(brinco), parent=self
            )

        self.__executar(acao)

    def __criar_base(self) -> None:
        def acao() -> None:
            nome = simpledialog.askstring(
                "Nutrição", "Nome da base de alimentação:", parent=self
            )
            if nome is None:
                return
            descricao = (
                simpledialog.askstring("Nutrição", "Descrição da base:", parent=self)
                or ""
            )
            texto = simpledialog.askstring(
                "Nutrição",
                "Insumos da base, no formato nome=quantidade por animal/dia,\n"
                "separados por vírgula. Exemplo:\nRação 20%=2.5, Sal mineral=0.1",
                parent=self,
            )
            if texto is None:
                return
            base = self.__casos.criar_base.executar(
                nome.strip(), descricao, self.__ler_itens_da_base(texto)
            )
            messagebox.showinfo("Nutrição", f"Base criada:\n{base}", parent=self)

        self.__executar(acao)

    def __definir_alimentacao(self) -> None:
        brinco = self.__brinco_selecionado()
        if brinco is None:
            messagebox.showinfo("Nutrição", "Selecione um animal na lista.", parent=self)
            return

        def acao() -> None:
            nomes = ", ".join(base.nome for base in self.__casos.bases())
            if not nomes:
                messagebox.showinfo(
                    "Nutrição", "Nenhuma base de alimentação criada.", parent=self
                )
                return
            nome_base = simpledialog.askstring(
                "Nutrição",
                f"Bases disponíveis: {nomes}\n\nNome da base para {brinco}:",
                parent=self,
            )
            if nome_base is None:
                return
            self.__casos.definir_alimentacao.executar(brinco, nome_base.strip())
            messagebox.showinfo(
                "Nutrição",
                f"Animal {brinco} agora se alimenta da base {nome_base.strip()}.",
                parent=self,
            )

        self.__executar(acao)

    def __consultar_alimentacao(self) -> None:
        brinco = self.__brinco_selecionado()
        if brinco is None:
            messagebox.showinfo("Nutrição", "Selecione um animal na lista.", parent=self)
            return

        def acao() -> None:
            messagebox.showinfo(
                "Nutrição",
                self.__casos.consultar_alimentacao.executar(brinco),
                parent=self,
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
                    "Venda",
                    "Nenhum animal com o peso mínimo de abate atingido.",
                    parent=self,
                )
                return
            linhas = [
                f"{animal} - {animal.peso_atual():.1f} kg "
                f"(mínimo de abate: {animal.peso_minimo_abate():.1f} kg)"
                for animal in animais
            ]
            messagebox.showinfo("Animais para venda", "\n".join(linhas), parent=self)

        self.__executar(acao)

    def __vender(self) -> None:
        brinco = self.__brinco_selecionado()
        if brinco is None:
            messagebox.showinfo("Venda", "Selecione um animal na lista.", parent=self)
            return
        texto = simpledialog.askstring(
            "Venda", f"Valor da venda (R$) do animal {brinco}:", parent=self
        )
        if texto is None:
            return

        def acao() -> None:
            compra = self.__casos.vender_animal.executar(
                brinco, float(texto.replace(",", "."))
            )
            messagebox.showinfo("Venda", f"Venda registrada:\n{compra}", parent=self)

        self.__executar(acao)

    def __comprar_insumo(self) -> None:
        def confirmar(valores: List[str]) -> None:
            insumo = self.__casos.comprar_insumo.executar(
                valores[0], float(valores[1].replace(",", "."))
            )
            messagebox.showinfo("Insumo", f"Insumo em estoque:\n{insumo}", parent=self)

        Formulario(
            "Comprar insumo do fornecedor",
            [("Nome do insumo:", ""), ("Quantidade:", "")],
            confirmar,
            pai=self,
        )

    def __listar_insumos(self) -> None:
        def acao() -> None:
            insumos = self.__casos.insumos()
            if not insumos:
                messagebox.showinfo(
                    "Estoque da fazenda", "Nenhum insumo em estoque.", parent=self
                )
                return
            messagebox.showinfo(
                "Estoque da fazenda",
                "\n".join(str(insumo) for insumo in insumos),
                parent=self,
            )

        self.__executar(acao)

    def __excluir_animal(self) -> None:
        brinco = self.__brinco_selecionado()
        if brinco is None:
            messagebox.showinfo("Excluir", "Selecione um animal na lista.", parent=self)
            return
        if not messagebox.askyesno("Excluir", f"Excluir o animal {brinco}?", parent=self):
            return

        def acao() -> None:
            self.__casos.excluir_animal(brinco)
            messagebox.showinfo("Excluir", f"Animal {brinco} excluído.", parent=self)

        self.__executar(acao)
