"""Ponto de entrada do sistema de gestão de rebanho.

Aqui é a composição de raiz: as dependências de todas as camadas são
montadas e passadas para quem precisa. Nenhuma regra de negócio vive aqui.

Uso:
    python main.py            -> abre a interface gráfica (Tkinter)
    python main.py --console  -> roda o menu de texto no terminal
"""

import sys

from source.domain.entidades.pessoas import Fornecedor, Frigorifico, Proprietario
from source.infra.repositorio_json import (
    ArquivoDados,
    RepositorioAnimaisJson,
    RepositorioBasesJson,
    RepositorioCatalogoFornecedorJson,
    RepositorioComprasJson,
    RepositorioInsumosJson,
    RepositorioProprietarioJson,
)
from source.interfaces.presenter_console import AplicacaoConsole
from source.usecases.casos_de_uso import (
    Autocadastro,
    CadastrarAnimal,
    CadastrarInsumo,
    ComprarInsumo,
    ConsultarAlimentacao,
    ConsultarGenetica,
    CriarBaseAlimentacao,
    DefinirAlimentacao,
    HistoricoCompras,
    IdentificarAnimaisParaVenda,
    InseminarFemea,
    RegistrarParto,
    RegistrarPesagem,
    RegistrarVacinacao,
    VenderAnimal,
    VenderInsumo,
)
from source.usecases.contenedor import CasosDeUso


def montar_casos_de_uso() -> CasosDeUso:
    """Monta todas as dependências do sistema (composição de raiz).

    A ordem importa: bases dependem dos insumos, animais das bases e
    compras dos animais — cada repositório re-vincula as referências do
    seu estado persistido na reconstrução.
    """
    arquivo = ArquivoDados("dados.json")
    repositorio_insumos = RepositorioInsumosJson(arquivo)
    repositorio_bases = RepositorioBasesJson(arquivo, repositorio_insumos)
    repositorio_animais = RepositorioAnimaisJson(arquivo, repositorio_bases.buscar_por_nome)
    repositorio_compras = RepositorioComprasJson(arquivo, repositorio_animais)
    repositorio_catalogo = RepositorioCatalogoFornecedorJson(arquivo)
    repositorio_proprietario = RepositorioProprietarioJson(arquivo)

    proprietario = repositorio_proprietario.carregar() or Proprietario(
        "Fazenda Boa Esperança", "000.000.000-00"
    )
    for animal in repositorio_animais.listar():
        proprietario.adicionar_animal(animal)

    fornecedor = Fornecedor("Agropecuária Central", "12.345.678/0001-90")
    for lote in repositorio_catalogo.listar():
        fornecedor.cadastrar_insumo(lote)

    frigorifico = Frigorifico("Frigorífico Pampa Sul", "12.345.678/0001-90")
    frigorifico.restaurar_compras(repositorio_compras.listar())

    return CasosDeUso(
        cadastrar_animal=CadastrarAnimal(repositorio_animais, proprietario),
        registrar_pesagem=RegistrarPesagem(repositorio_animais),
        registrar_vacinacao=RegistrarVacinacao(repositorio_animais),
        inseminar_femea=InseminarFemea(repositorio_animais),
        registrar_parto=RegistrarParto(repositorio_animais, proprietario),
        vender_animal=VenderAnimal(repositorio_animais, frigorifico, repositorio_compras),
        criar_base=CriarBaseAlimentacao(
            repositorio_bases, repositorio_insumos, proprietario
        ),
        definir_alimentacao=DefinirAlimentacao(repositorio_animais, repositorio_bases),
        consultar_alimentacao=ConsultarAlimentacao(repositorio_animais),
        consultar_genetica=ConsultarGenetica(repositorio_animais),
        identificar_para_venda=IdentificarAnimaisParaVenda(repositorio_animais),
        historico_compras=HistoricoCompras(frigorifico),
        comprar_insumo=ComprarInsumo(
            repositorio_insumos, repositorio_catalogo, fornecedor, proprietario
        ),
        vender_insumo=VenderInsumo(
            repositorio_insumos, repositorio_catalogo, fornecedor, proprietario
        ),
        cadastrar_insumo=CadastrarInsumo(repositorio_catalogo, fornecedor),
        autocadastro=Autocadastro(proprietario, repositorio_proprietario),
        repositorio_animais=repositorio_animais,
        repositorio_insumos=repositorio_insumos,
        repositorio_bases=repositorio_bases,
        repositorio_catalogo=repositorio_catalogo,
    )


def main() -> None:
    casos = montar_casos_de_uso()
    if "--console" in sys.argv[1:]:
        AplicacaoConsole(casos).rodar()
        return
    try:
        from source.interfaces.interface_tkinter import iniciar_interface

        iniciar_interface(casos)
    except ModuleNotFoundError:
        print(
            "O Tkinter não está instalado neste sistema. "
            "Use 'python main.py --console' para rodar o menu de texto, "
            "ou instale o pacote tkinter (no Fedora: sudo dnf install python3-tkinter)."
        )


if __name__ == "__main__":
    main()
