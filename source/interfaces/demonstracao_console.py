"""Demonstração no console: cria os objetos do domínio e mostra a interação
entre eles, sem login e sem gravar nada em arquivo (python main.py --demo)."""

import sys
from datetime import date
from typing import Callable, List, TextIO, Tuple

from source.domain.entidades.animal import Animal, Femea, Macho
from source.domain.entidades.insumo import BaseAlimentacao, Insumo
from source.domain.entidades.pessoas import Fornecedor, Frigorifico, Proprietario
from source.domain.excecoes import RegraNegocioViolation


def rodar_demonstracao(saida: TextIO = sys.stdout) -> None:
    """Roda o cenário completo, do cadastro do rebanho à venda ao frigorífico."""
    proprietario = Proprietario("Maria Silva", "111.222.333-44")
    fornecedor = Fornecedor("Agro Insumos", "33.444.555/0001-66")
    frigorifico = Frigorifico("Frigorífico Pampa Sul", "22.333.444/0001-55")

    _mostrar_abstracao(saida)
    mimosa, touro, novilho = _cadastrar_rebanho(saida, proprietario)
    _registrar_manejo(saida, mimosa, touro, novilho)
    racao, sal = _comprar_insumos(saida, proprietario, fornecedor)
    _montar_nutricao(saida, proprietario, racao, sal, [touro, novilho])
    _reproduzir(saida, proprietario, mimosa, touro)
    _vender(saida, proprietario, frigorifico, touro, novilho)
    _resumir(saida, proprietario)


def _titulo(saida: TextIO, texto: str) -> None:
    print(f"\n=== {texto} ===", file=saida)


def _tentar(saida: TextIO, acao: Callable[[], object]) -> None:
    try:
        acao()
    except RegraNegocioViolation as erro:
        print(f"  Bloqueado pela regra: {erro.mensagem}", file=saida)


def _mostrar_abstracao(saida: TextIO) -> None:
    _titulo(saida, "1. Abstração: Animal é uma classe abstrata")
    try:
        Animal("X0", date(2024, 1, 1), "Nelore")
    except TypeError:
        print("  Animal(...) não pode ser instanciado: todo animal é Femea ou Macho.",
              file=saida)


def _cadastrar_rebanho(
    saida: TextIO, proprietario: Proprietario
) -> Tuple[Femea, Macho, Macho]:
    _titulo(saida, "2. Cadastro do rebanho (agregação e polimorfismo)")
    print(f"  Proprietário: {proprietario.nome} (CPF {proprietario.cpf})", file=saida)
    mimosa = Femea("F1", date(2022, 3, 10), "Nelore")
    touro = Macho("T1", date(2021, 5, 2), "Nelore")
    novilho = Macho("M2", date(2023, 1, 15), "Angus")
    for animal in (mimosa, touro, novilho):
        proprietario.adicionar_animal(animal)
        print(f"  {animal.brinco} ({animal.raca}): categoria {animal.categoria()}, "
              f"peso mínimo de abate {animal.peso_minimo_abate():.0f} kg", file=saida)

    print(f"  O proprietário agrega {len(proprietario.listar_animais())} animais.", file=saida)
    return mimosa, touro, novilho


def _registrar_manejo(saida: TextIO, mimosa: Femea, touro: Macho, novilho: Macho) -> None:
    _titulo(saida, "3. Pesagens e vacinas (composição dentro do animal)")
    for animal, kg in ((mimosa, 380.0), (touro, 520.0), (novilho, 300.0)):
        pesagem = animal.registrar_pesagem(kg, date(2026, 11, 1))
        print(f"  {animal.brinco}: pesagem {pesagem}", file=saida)

    vacinacao = mimosa.registrar_vacinacao("Aftosa", "1ª dose", date(2026, 11, 2))
    print(f"  {mimosa.brinco}: vacinação {vacinacao}", file=saida)
    _tentar(saida, lambda: novilho.registrar_pesagem(-10.0))
    novilho.castrar()
    print(f"  {novilho.brinco} castrado: {novilho.castrado}", file=saida)


def _comprar_insumos(
    saida: TextIO, proprietario: Proprietario, fornecedor: Fornecedor
) -> Tuple[Insumo, Insumo]:
    _titulo(saida, "4. Compra de insumos do fornecedor")
    fornecedor.cadastrar_insumo(Insumo("Ração 20%", "Nutricional", 1000.0, 1.80))
    fornecedor.cadastrar_insumo(Insumo("Sal mineral", "Nutricional", 200.0, 3.00))
    print(f"  Catálogo de {fornecedor.nome}: "
          f"{', '.join(lote.nome for lote in fornecedor.listar_insumos())}", file=saida)

    estoque_fazenda: List[Insumo] = []
    for nome, quantidade in (("Ração 20%", 100.0), ("Sal mineral", 20.0)):
        lote = fornecedor.vender_insumo(nome, quantidade)
        insumo = Insumo(lote.nome, lote.tipo, 0.0, lote.preco)
        proprietario.comprar_insumo(insumo, quantidade)
        estoque_fazenda.append(insumo)
        print(f"  Fazenda recebeu {insumo}; no fornecedor sobrou {lote.estoque:.2f}",
              file=saida)

    _tentar(saida, lambda: fornecedor.vender_insumo("Ração 20%", 5000.0))
    return estoque_fazenda[0], estoque_fazenda[1]


def _montar_nutricao(
    saida: TextIO,
    proprietario: Proprietario,
    racao: Insumo,
    sal: Insumo,
    animais: List[Animal],
) -> None:
    _titulo(saida, "5. Base de alimentação (associação com os insumos)")
    base = BaseAlimentacao("Engorda", "Ração e sal para terminação")
    base.adicionar_insumo(racao, 2.5)
    base.adicionar_insumo(sal, 0.1)
    proprietario.adicionar_base(base)
    for animal in animais:
        animal.definir_alimentacao(base)

    brincos = ", ".join(str(animal.brinco) for animal in animais)
    print(f"  Base {base.nome}: {base.consumo_diario_kg():.2f} kg por animal/dia", file=saida)
    print(f"  Animais na base: {brincos}", file=saida)
    print(f"  Custo mensal para {len(animais)} animais: "
          f"R$ {base.custo_mensal(len(animais)):.2f}", file=saida)


def _reproduzir(
    saida: TextIO, proprietario: Proprietario, mimosa: Femea, touro: Macho
) -> None:
    _titulo(saida, "6. Reprodução (regra 2: só fêmea, depois de pode_inseminar)")
    print(f"  Macho tem método inseminar? {hasattr(touro, 'inseminar')}", file=saida)
    print(f"  {mimosa.brinco}.pode_inseminar({touro.brinco}) = "
          f"{mimosa.pode_inseminar(touro)}", file=saida)
    mimosa.inseminar(touro)
    print(f"  {mimosa.brinco} inseminada pelo touro {mimosa.brinco_inseminacao}; "
          f"prenhe: {mimosa.prenhe}", file=saida)
    _tentar(saida, lambda: mimosa.inseminar(touro))

    bezerra = mimosa.registrar_parto("B1", macho=False)
    proprietario.adicionar_animal(bezerra)
    print(f"  Parto: nasceu {bezerra}", file=saida)
    print(f"  Genealogia de {bezerra.brinco}: mãe {bezerra.mae_brinco}, "
          f"pai {bezerra.pai_brinco}", file=saida)
    filhos = ", ".join(str(filho.brinco) for filho in mimosa.listar_filhos())
    print(f"  Filhos de {mimosa.brinco}: {filhos}", file=saida)


def _vender(
    saida: TextIO,
    proprietario: Proprietario,
    frigorifico: Frigorifico,
    touro: Macho,
    novilho: Macho,
) -> None:
    _titulo(saida, "7. Venda ao frigorífico (regra 1: pode_vender)")
    prontos = [animal for animal in proprietario.listar_animais() if animal.pode_vender()]
    print(f"  Prontos para abate: {', '.join(str(a.brinco) for a in prontos)}", file=saida)
    _tentar(saida, lambda: frigorifico.comprar_animal(novilho, 2000.0, date(2026, 11, 13)))
    compra = frigorifico.comprar_animal(touro, 3200.0, date(2026, 11, 13))
    print(f"  Compra registrada: {compra}", file=saida)
    _tentar(saida, lambda: frigorifico.comprar_animal(touro, 3200.0, date(2026, 11, 13)))
    print(f"  Histórico de {frigorifico.nome} (composição): "
          f"{len(frigorifico.historico_compras())} compra(s)", file=saida)


def _resumir(saida: TextIO, proprietario: Proprietario) -> None:
    _titulo(saida, "8. Rebanho no fim da demonstração")
    for animal in proprietario.listar_animais():
        peso = f"{animal.peso_atual():.1f} kg" if animal.pesagens else "sem pesagem"
        estado = "vendido" if animal.vendido else "no rebanho"
        print(f"  {animal} - {peso} - {estado}", file=saida)
