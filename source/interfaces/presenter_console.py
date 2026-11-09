"""Apresentação em console (menu de texto), organizada pelos atores do
diagrama de casos de uso.

Não contém regra de negócio: lê o usuário, chama casos de uso e mostra
o resultado. Os erros de negócio chegam como exceções do domínio e são
apenas exibidos.
"""

from datetime import date, datetime

from source.domain.excecoes import RegraNegocioViolation
from source.usecases.contenedor import CasosDeUso

MENU = """
=========================================
  Sistema de Gestão de Rebanho
-----------------------------------------
  PROPRIETÁRIO
  1 - Cadastrar animal
  2 - Registrar pesagem
  3 - Registrar vacinação
  4 - Realizar inseminação
  5 - Registrar parto
  6 - Gerenciar nutrição do gado
  7 - Identificar animais para venda
  8 - Vender animal ao frigorífico
  9 - Comprar insumo do fornecedor
  FRIGORÍFICO
 10 - Consultar animais disponíveis
 11 - Histórico de compras
  FORNECEDOR DE INSUMOS
 12 - Cadastrar insumo
 13 - Vender insumo
  USUÁRIO
 14 - Autocadastro
  LISTAGENS
 15 - Listar animais
 16 - Listar insumos da fazenda
 17 - Listar catálogo do fornecedor
  0 - Sair
=========================================
Opção: """

MENU_NUTRICAO = """
----- Gerenciar nutrição do gado -----
 a - Criar base de alimentação
 b - Definir alimentação de um animal
 c - Consultar alimentação do animal
 v - Voltar
Opção: """


class AplicacaoConsole:
    """Roda o menu de texto do sistema."""

    def __init__(self, casos: CasosDeUso) -> None:
        self.__casos = casos
        self.__acoes = {
            "1": self.__cadastrar_animal,
            "2": self.__registrar_pesagem,
            "3": self.__registrar_vacinacao,
            "4": self.__inseminar,
            "5": self.__registrar_parto,
            "6": self.__gerenciar_nutricao,
            "7": self.__identificar_para_venda,
            "8": self.__vender,
            "9": self.__comprar_insumo,
            "10": self.__consultar_disponiveis,
            "11": self.__historico_compras,
            "12": self.__cadastrar_insumo,
            "13": self.__vender_insumo,
            "14": self.__autocadastro,
            "15": self.__listar_animais,
            "16": self.__listar_insumos,
            "17": self.__listar_catalogo,
        }

    def rodar(self) -> None:
        while True:
            opcao = input(MENU).strip()
            if opcao == "0":
                print("Até logo!")
                break
            self.__executar(opcao)

    def __executar(self, opcao: str) -> None:
        acao = self.__acoes.get(opcao)
        if acao is None:
            print("Opção inválida.")
            return
        try:
            acao()
        except RegraNegocioViolation as erro:
            print(f"[Erro] {erro.mensagem}")
        except ValueError as erro:
            print(f"[Erro] Valor inválido: {erro}")

    # ------------------------------------------------------------------
    # Formulários de texto (sem regras de negócio, só chamam casos de uso)
    # ------------------------------------------------------------------
    def __pedir_data(self, texto: str) -> date:
        valor = input(texto).strip()
        if not valor:
            return date.today()
        return datetime.strptime(valor, "%d/%m/%Y").date()

    def __pedir_numero(self, texto: str) -> float:
        return float(input(texto).strip().replace(",", "."))

    def __cadastrar_animal(self) -> None:
        brinco = input("Brinco: ").strip()
        data = self.__pedir_data("Data de nascimento (dd/mm/aaaa, vazio = hoje): ")
        raca = input("Raça: ").strip()
        tipo = input("Tipo (femea/macho): ").strip().lower()
        animal = self.__casos.cadastrar_animal.executar(brinco, data, raca, tipo)
        print(f"Animal cadastrado: {animal}")

    def __registrar_pesagem(self) -> None:
        brinco = input("Brinco: ").strip()
        kg = self.__pedir_numero("Peso (kg): ")
        data = self.__pedir_data("Data da pesagem (dd/mm/aaaa, vazio = hoje): ")
        pesagem = self.__casos.registrar_pesagem.executar(brinco, kg, data)
        print(f"Pesagem registrada: {pesagem}")

    def __registrar_vacinacao(self) -> None:
        brinco = input("Brinco: ").strip()
        vacina = input("Vacina: ").strip()
        dose = input("Dose: ").strip()
        data = self.__pedir_data("Data da vacinação (dd/mm/aaaa, vazio = hoje): ")
        vacinacao = self.__casos.registrar_vacinacao.executar(brinco, vacina, dose, data)
        print(f"Vacinação registrada: {vacinacao}")

    def __inseminar(self) -> None:
        brinco_femea = input("Brinco da fêmea: ").strip()
        # Include do diagrama: antes de inseminar, consultar a genética.
        print(self.__casos.consultar_genetica.executar(brinco_femea))
        brinco_touro = input("Brinco do touro: ").strip()
        self.__casos.inseminar_femea.executar(brinco_femea, brinco_touro)
        print(f"Fêmea {brinco_femea} inseminada pelo touro {brinco_touro}.")

    def __registrar_parto(self) -> None:
        brinco_femea = input("Brinco da fêmea: ").strip()
        brinco_filho = input("Brinco do bezerro: ").strip()
        macho = input("O bezerro é macho? (s/n): ").strip().lower() == "s"
        bezerro = self.__casos.registrar_parto.executar(brinco_femea, brinco_filho, macho)
        print(f"Bezerro cadastrado: {bezerro}")

    def __gerenciar_nutricao(self) -> None:
        while True:
            opcao = input(MENU_NUTRICAO).strip().lower()
            if opcao == "v":
                return
            try:
                if opcao == "a":
                    self.__criar_base()
                elif opcao == "b":
                    self.__definir_alimentacao()
                elif opcao == "c":
                    self.__consultar_alimentacao()
                else:
                    print("Opção inválida.")
            except RegraNegocioViolation as erro:
                print(f"[Erro] {erro.mensagem}")

    def __criar_base(self) -> None:
        nome = input("Nome da base: ").strip()
        descricao = input("Descrição: ").strip()
        itens = []
        print("Insumos da base (quantidade por animal/dia; nome vazio encerra):")
        while True:
            nome_insumo = input("  Insumo: ").strip()
            if not nome_insumo:
                break
            itens.append((nome_insumo, self.__pedir_numero("  Quantidade: ")))
        base = self.__casos.criar_base.executar(nome, descricao, itens)
        print(f"Base criada: {base}")

    def __definir_alimentacao(self) -> None:
        bases = ", ".join(base.nome for base in self.__casos.bases()) or "nenhuma base criada"
        brinco = input(f"Brinco do animal (bases: {bases}): ").strip()
        nome_base = input("Nome da base: ").strip()
        self.__casos.definir_alimentacao.executar(brinco, nome_base)
        print(f"Animal {brinco} agora se alimenta da base {nome_base}.")

    def __consultar_alimentacao(self) -> None:
        brinco = input("Brinco do animal: ").strip()
        print(self.__casos.consultar_alimentacao.executar(brinco))

    def __listar_para_venda(self, titulo: str) -> None:
        animais = self.__casos.identificar_para_venda.executar()
        if not animais:
            print("Nenhum animal com o peso mínimo de abate atingido.")
            return
        print(titulo)
        for animal in animais:
            print(
                f"  {animal} - {animal.peso_atual():.1f} kg "
                f"(mínimo de abate: {animal.peso_minimo_abate():.1f} kg)"
            )

    def __identificar_para_venda(self) -> None:
        self.__listar_para_venda("Animais prontos para venda:")

    def __consultar_disponiveis(self) -> None:
        self.__listar_para_venda("Animais disponíveis para compra:")

    def __vender(self) -> None:
        brinco = input("Brinco: ").strip()
        valor = self.__pedir_numero("Valor da venda (R$): ")
        compra = self.__casos.vender_animal.executar(brinco, valor)
        print(f"Venda registrada: {compra}")

    def __historico_compras(self) -> None:
        compras = self.__casos.historico_compras.executar()
        if not compras:
            print("Nenhuma compra registrada.")
            return
        print("Histórico de compras do frigorífico:")
        for compra in compras:
            print(f"  {compra.resumo()}")

    def __comprar_insumo(self) -> None:
        nome = input("Nome do insumo: ").strip()
        quantidade = self.__pedir_numero("Quantidade: ")
        insumo = self.__casos.comprar_insumo.executar(nome, quantidade)
        print(f"Insumo em estoque: {insumo}")

    def __cadastrar_insumo(self) -> None:
        nome = input("Nome do insumo: ").strip()
        tipo = input("Tipo do insumo: ").strip()
        quantidade = self.__pedir_numero("Quantidade do lote: ")
        preco = self.__pedir_numero("Preço unitário (R$): ")
        lote = self.__casos.cadastrar_insumo.executar(nome, tipo, quantidade, preco)
        print(f"Insumo no catálogo do fornecedor: {lote}")

    def __vender_insumo(self) -> None:
        nome = input("Nome do insumo: ").strip()
        quantidade = self.__pedir_numero("Quantidade vendida: ")
        insumo = self.__casos.vender_insumo.executar(nome, quantidade)
        print(f"Insumo entregue à fazenda: {insumo}")

    def __autocadastro(self) -> None:
        nome = input("Seu nome: ").strip()
        cpf = input("Seu CPF: ").strip()
        proprietario = self.__casos.autocadastro.executar(nome, cpf)
        print(f"Cadastro atualizado: {proprietario.nome} ({proprietario.cpf})")

    def __listar_animais(self) -> None:
        print("Animais cadastrados:")
        for animal in self.__casos.animais():
            peso = f"{animal.peso_atual():.1f} kg" if animal.pesagens else "sem pesagem"
            estado = "vendido" if animal.vendido else "no rebanho"
            print(f"  {animal} - {peso} - {estado}")

    def __listar_insumos(self) -> None:
        print("Insumos cadastrados:")
        for insumo in self.__casos.insumos():
            print(f"  {insumo}")

    def __listar_catalogo(self) -> None:
        print("Catálogo do fornecedor:")
        for lote in self.__casos.catalogo_fornecedor():
            print(f"  {lote}")
