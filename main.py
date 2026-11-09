"""Ponto de entrada do sistema de gestão de rebanho.

Aqui é a composição de raiz: as dependências de todas as camadas são
montadas e passadas para quem precisa. Nenhuma regra de negócio vive aqui.

Sistema multiusuário: primeiro o login autentica (ou cria) uma conta —
cada conta declara o papel dela (proprietário, fornecedor ou frigorífico)
e tem o seu arquivo de dados, dados_<documento>.json, com o trabalho
dela. Autenticada a conta, o sistema inteiro é montado com o arquivo
dela e a área do papel abre direto; ao encerrar a sessão, o fluxo volta
ao login para a entrada de outro usuário.

Uso:
    python main.py            -> abre a interface gráfica (Tkinter)
    python main.py --console  -> roda o menu de texto no terminal
"""

import sys

from source.domain.entidades.conta import Conta
from source.domain.entidades.pessoas import Fornecedor, Frigorifico, Proprietario
from source.infra.repositorio_json import (
    ArquivoDados,
    FonteDeCadastros,
    IndiceContasJson,
    RepositorioAnimaisJson,
    RepositorioBasesJson,
    RepositorioCatalogoFornecedorJson,
    RepositorioComprasJson,
    RepositorioFornecedorJson,
    RepositorioFrigorificoJson,
    RepositorioInsumosJson,
    RepositorioProprietarioJson,
)
from source.interfaces.presenter_console import AplicacaoConsole, AutenticacaoConsole
from source.usecases.casos_de_uso import (
    AutenticarConta,
    Autocadastro,
    CadastrarAnimal,
    CadastrarConta,
    CadastrarFornecedor,
    CadastrarFrigorifico,
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

ARQUIVO_DE_CONTAS = "usuarios.json"


def montar_indice_de_contas() -> IndiceContasJson:
    """Índice de contas do sistema (usuarios.json).

    Migração do sistema de um usuário só: quando ainda não há índice, o
    cadastro salvo em dados.json se torna a primeira conta, do papel
    Proprietário, com a credencial que já estava no arquivo — e ela
    continua usando o mesmo arquivo. Nada é perdido nem renomeado."""
    indice = IndiceContasJson(ArquivoDados(ARQUIVO_DE_CONTAS))
    if not indice.listar():
        legado = RepositorioProprietarioJson(ArquivoDados("dados.json")).carregar()
        if legado is not None:
            indice.adicionar(
                Conta(legado.nome, legado.cpf, "proprietario", "dados.json", legado.senha)
            )
            indice.salvar()
    return indice


def montar_casos_de_uso(
    conta: Conta,
    indice_de_contas: IndiceContasJson,
    criador_de_arquivos: FonteDeCadastros,
) -> CasosDeUso:
    """Monta todas as dependências do sistema para a conta autenticada.

    A ordem importa: bases dependem dos insumos, animais das bases e
    compras dos animais — cada repositório re-vincula as referências do
    seu estado persistido na reconstrução. Tudo vem do arquivo de dados
    da conta: o trabalho de um usuário fica isolado do dos outros. As
    seções do papel da conta (o cadastro dela) vêm do arquivo; contas
    nascem com o cadastro semeado, então a área abre de cara.
    """
    arquivo = ArquivoDados(conta.arquivo)
    repositorio_insumos = RepositorioInsumosJson(arquivo)
    repositorio_bases = RepositorioBasesJson(arquivo, repositorio_insumos)
    repositorio_animais = RepositorioAnimaisJson(arquivo, repositorio_bases.buscar_por_nome)
    repositorio_compras = RepositorioComprasJson(arquivo, repositorio_animais)
    repositorio_catalogo = RepositorioCatalogoFornecedorJson(arquivo)
    repositorio_proprietario = RepositorioProprietarioJson(arquivo)
    repositorio_fornecedor = RepositorioFornecedorJson(arquivo)
    repositorio_frigorifico = RepositorioFrigorificoJson(arquivo)

    proprietario = repositorio_proprietario.carregar() or Proprietario("", "")
    for animal in repositorio_animais.listar():
        proprietario.adicionar_animal(animal)

    fornecedor = repositorio_fornecedor.carregar() or Fornecedor("", "")
    for lote in repositorio_catalogo.listar():
        fornecedor.cadastrar_insumo(lote)

    frigorifico = repositorio_frigorifico.carregar() or Frigorifico("", "")
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
        autocadastro=Autocadastro(
            proprietario, repositorio_proprietario, indice_de_contas
        ),
        cadastrar_fornecedor=CadastrarFornecedor(
            fornecedor, repositorio_fornecedor, indice_de_contas
        ),
        cadastrar_frigorifico=CadastrarFrigorifico(
            frigorifico, repositorio_frigorifico, indice_de_contas
        ),
        cadastrar_conta=CadastrarConta(indice_de_contas, criador_de_arquivos),
        autenticar_conta=AutenticarConta(indice_de_contas),
        conta=conta,
        proprietario=proprietario,
        fornecedor=fornecedor,
        frigorifico=frigorifico,
        repositorio_animais=repositorio_animais,
        repositorio_insumos=repositorio_insumos,
        repositorio_bases=repositorio_bases,
        repositorio_catalogo=repositorio_catalogo,
    )


def main() -> None:
    indice = montar_indice_de_contas()
    criador_de_arquivos = FonteDeCadastros()

    def montar(conta: Conta) -> CasosDeUso:
        return montar_casos_de_uso(conta, indice, criador_de_arquivos)

    if "--console" in sys.argv[1:]:
        login = AutenticacaoConsole(
            CadastrarConta(indice, criador_de_arquivos),
            AutenticarConta(indice),
        )
        while True:
            conta = login.entrar()
            if conta is None:
                print("Até logo!")
                return
            AplicacaoConsole(montar(conta)).rodar()
    try:
        from source.interfaces.interface_tkinter import iniciar_interface

        iniciar_interface(
            CadastrarConta(indice, criador_de_arquivos),
            AutenticarConta(indice),
            montar,
        )
    except ModuleNotFoundError:
        print(
            "O Tkinter não está instalado neste sistema. "
            "Use 'python main.py --console' para rodar o menu de texto, "
            "ou instale o pacote tkinter (no Fedora: sudo dnf install python3-tkinter)."
        )


if __name__ == "__main__":
    main()
