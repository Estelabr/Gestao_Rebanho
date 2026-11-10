"""Implementação dos repositórios em arquivo JSON.

Só esta camada conhece o formato do arquivo: o resto do sistema fala com
os contratos de repositório, que moram no domínio
(source/domain/repositorios.py) e são cumpridos aqui.

Sistema multiusuário: cada conta de usuário tem o seu próprio arquivo de
dados ("dados_<documento>.json"), com as seções abaixo. O índice de
contas ("usuarios.json") é global: diz quem pode entrar, com qual papel
e qual arquivo — a senha entra nele apenas como credencial (hash).

Seções do dados_<cpf>.json:
  animais              -- cadastro de animais (pesagens, vacinas, reprodução, venda)
  insumos              -- estoque da fazenda
  fornecedor           -- catálogo de lotes do fornecedor
  fornecedor_cadastro  -- cadastro do fornecedor (nome e CNPJ)
  bases                -- bases de alimentação
  compras              -- histórico de compras do frigorífico
  frigorifico          -- cadastro do frigorífico (nome e CNPJ)
  proprietario         -- cadastro do proprietário (autocadastro: nome,
                          CPF e hash da senha)

Seções do usuarios.json:
  contas               -- índice de usuários (nome, documento, papel,
                          credencial da senha e arquivo de dados)

Referências entre objetos (filhos, base do animal, animal da compra,
insumo da base) são re-vinculadas na reconstrução, em segunda passada.
Chaves antigas ("preco_unitario", "quantidade") continuam sendo lidas.
"""

import json
import os
from datetime import date
from typing import Any, Callable, Dict, List, Optional

from source.domain.entidades.animal import Animal, Femea, Macho
from source.domain.entidades.conta import Conta, normalizar_documento
from source.domain.entidades.insumo import BaseAlimentacao, Insumo
from source.domain.entidades.pessoas import CompraAnimal, Fornecedor, Frigorifico, Proprietario
from source.domain.excecoes import AnimalNaoEncontradoError, RegraNegocioViolation
from source.domain.repositorios import (
    CriadorDeArquivos,
    RepositorioAnimais,
    RepositorioBases,
    RepositorioCompras,
    RepositorioContas,
    RepositorioFornecedor,
    RepositorioFrigorifico,
    RepositorioInsumos,
    RepositorioProprietario,
)


class ArquivoDados:
    """Lê e escreve o arquivo JSON que persiste o estado do sistema."""

    def __init__(self, caminho: str = "dados.json") -> None:
        self.__caminho = caminho

    def carregar(self) -> Dict[str, Any]:
        if not os.path.exists(self.__caminho):
            return {}
        with open(self.__caminho, "r", encoding="utf-8") as arquivo:
            return json.load(arquivo)

    def salvar(self, dados: Dict[str, Any]) -> None:
        with open(self.__caminho, "w", encoding="utf-8") as arquivo:
            json.dump(dados, arquivo, ensure_ascii=False, indent=2)


class RepositorioInsumosJson(RepositorioInsumos):
    """Guarda os insumos em JSON, na seção 'insumos' do arquivo."""

    SECAO = "insumos"

    def __init__(self, arquivo: ArquivoDados) -> None:
        self.__arquivo = arquivo
        self.__insumos: Dict[str, Insumo] = {}
        for item in self.__arquivo.carregar().get(self.SECAO, []):
            insumo = Insumo(
                item["nome"],
                item["tipo"],
                item.get("estoque", item.get("quantidade", 0.0)),
                item.get("preco", item.get("preco_unitario", 0.0)),
            )
            self.__insumos[insumo.nome] = insumo

    def adicionar(self, insumo: Insumo) -> None:
        self.__insumos[insumo.nome] = insumo

    def buscar_por_nome(self, nome: str) -> Optional[Insumo]:
        return self.__insumos.get(nome)

    def listar(self) -> List[Insumo]:
        return list(self.__insumos.values())

    def salvar(self) -> None:
        dados = self.__arquivo.carregar()
        dados[self.SECAO] = [
            {
                "nome": insumo.nome,
                "tipo": insumo.tipo,
                "estoque": insumo.estoque,
                "preco": insumo.preco,
            }
            for insumo in self.__insumos.values()
        ]
        self.__arquivo.salvar(dados)


class RepositorioCatalogoFornecedorJson(RepositorioInsumosJson):
    """Catálogo de lotes do fornecedor: mesma estrutura de insumos, em
    outra seção do arquivo."""

    SECAO = "fornecedor"


class RepositorioBasesJson(RepositorioBases):
    """Guarda as bases de alimentação em JSON, na seção 'bases'.

    A base guarda insumos por referência; na reconstrução os objetos
    Insumo são re-vinculados pelo nome a partir do repositório da fazenda.
    """

    SECAO = "bases"

    def __init__(self, arquivo: ArquivoDados, repositorio_insumos: RepositorioInsumos) -> None:
        self.__arquivo = arquivo
        self.__bases: Dict[str, BaseAlimentacao] = {}
        for item in self.__arquivo.carregar().get(self.SECAO, []):
            base = BaseAlimentacao(item["nome"], item.get("descricao", ""))
            for entrada in item.get("itens", []):
                insumo = repositorio_insumos.buscar_por_nome(entrada["insumo"])
                if insumo is not None:
                    base.adicionar_insumo(insumo, entrada["quantidade"])
            self.__bases[base.nome] = base

    def adicionar(self, base: BaseAlimentacao) -> None:
        self.__bases[base.nome] = base

    def buscar_por_nome(self, nome: str) -> Optional[BaseAlimentacao]:
        return self.__bases.get(nome)

    def listar(self) -> List[BaseAlimentacao]:
        return list(self.__bases.values())

    def salvar(self) -> None:
        dados = self.__arquivo.carregar()
        dados[self.SECAO] = [
            {
                "nome": base.nome,
                "descricao": base.descricao,
                "itens": [
                    {"insumo": insumo.nome, "quantidade": quantidade}
                    for insumo, quantidade in base.itens
                ],
            }
            for base in self.__bases.values()
        ]
        self.__arquivo.salvar(dados)


class RepositorioAnimaisJson(RepositorioAnimais):
    """Guarda os animais em JSON, na seção 'animais' do arquivo.

    Opcionalmente recebe um resolvedor de bases (a base é persistida pelo
    nome junto ao animal e re-vinculada ao carregar).
    """

    SECAO = "animais"

    def __init__(
        self,
        arquivo: ArquivoDados,
        resolver_base: Optional[Callable[[str], Optional[BaseAlimentacao]]] = None,
    ) -> None:
        self.__arquivo = arquivo
        self.__animais: Dict[str, Animal] = {}
        itens = self.__arquivo.carregar().get(self.SECAO, [])
        for item in itens:
            animal = self.__desserializar(item, resolver_base)
            self.__animais[animal.brinco.valor] = animal
        # Segunda passada: os filhos (objetos Animal) só podem ser
        # re-vinculados quando todos os animais já foram reconstruídos.
        for item in itens:
            animal = self.__animais.get(item.get("brinco", ""))
            if isinstance(animal, Femea) and item.get("filhos"):
                filhos = [self.__animais[b] for b in item["filhos"] if b in self.__animais]
                animal.restaurar_filhos(filhos)

    def adicionar(self, animal: Animal) -> None:
        self.__animais[animal.brinco.valor] = animal

    def buscar_por_brinco(self, brinco: str) -> Optional[Animal]:
        return self.__animais.get(brinco)

    def listar(self) -> List[Animal]:
        return list(self.__animais.values())

    def remover(self, brinco: str) -> None:
        if brinco not in self.__animais:
            raise AnimalNaoEncontradoError(f"Animal {brinco} não encontrado.")
        del self.__animais[brinco]

    def salvar(self) -> None:
        dados = self.__arquivo.carregar()
        dados[self.SECAO] = [
            self.__serializar(animal) for animal in self.__animais.values()
        ]
        self.__arquivo.salvar(dados)

    # ------------------------------------------------------------------
    # Conversão objeto <-> JSON
    # ------------------------------------------------------------------
    @staticmethod
    def __serializar(animal: Animal) -> Dict[str, Any]:
        item: Dict[str, Any] = {
            "tipo": "femea" if isinstance(animal, Femea) else "macho",
            "brinco": animal.brinco.valor,
            "data_nascimento": animal.data_nascimento.isoformat(),
            "raca": animal.raca,
            "vendido": animal.vendido,
            "mae_brinco": animal.mae_brinco,
            "pai_brinco": animal.pai_brinco,
            "base": animal.alimentacao().nome if animal.alimentacao() else None,
            "pesagens": [
                {"data": pesagem.data.isoformat(), "kg": pesagem.peso.kg}
                for pesagem in animal.pesagens
            ],
            "vacinacoes": [
                {
                    "data": vacinacao.data.isoformat(),
                    "vacina": vacinacao.vacina,
                    "dose": vacinacao.dose,
                }
                for vacinacao in animal.vacinacoes
            ],
        }
        if isinstance(animal, Femea):
            item["prenhe"] = animal.prenhe
            item["partos"] = animal.partos
            item["brinco_inseminacao"] = animal.brinco_inseminacao
            item["filhos"] = [filho.brinco.valor for filho in animal.listar_filhos()]
        if isinstance(animal, Macho):
            item["castrado"] = animal.castrado
        return item

    def __desserializar(
        self, item: Dict[str, Any], resolver_base: Optional[Callable]
    ) -> Animal:
        data = date.fromisoformat(item["data_nascimento"])
        if item.get("tipo") == "femea":
            animal: Animal = Femea(item["brinco"], data, item["raca"])
        else:
            animal = Macho(item["brinco"], data, item["raca"])
        animal.definir_genealogia(item.get("mae_brinco"), item.get("pai_brinco"))
        for pesagem in item.get("pesagens", []):
            animal.registrar_pesagem(pesagem["kg"], date.fromisoformat(pesagem["data"]))
        for vacinacao in item.get("vacinacoes", []):
            animal.registrar_vacinacao(
                vacinacao["vacina"],
                vacinacao["dose"],
                date.fromisoformat(vacinacao["data"]),
            )
        if isinstance(animal, Femea):
            animal.restaurar_reproducao(
                item.get("prenhe", False),
                item.get("partos", 0),
                item.get("brinco_inseminacao"),
            )
        if isinstance(animal, Macho) and item.get("castrado"):
            animal.restaurar_castrado()
        if item.get("vendido"):
            animal.restaurar_vendido()
        nome_base = item.get("base")
        if resolver_base is not None and nome_base:
            base = resolver_base(nome_base)
            if base is not None:
                animal.definir_alimentacao(base)
        return animal


class RepositorioComprasJson(RepositorioCompras):
    """Guarda o histórico de compras do frigorífico, na seção 'compras'.

    Na reconstrução, cada compra é re-vinculada ao Animal carregado.
    Compras cujo animal foi excluído do rebanho são ignoradas.
    """

    SECAO = "compras"

    def __init__(self, arquivo: ArquivoDados, repositorio_animais: RepositorioAnimais) -> None:
        self.__arquivo = arquivo
        self.__compras: List[CompraAnimal] = []
        for item in self.__arquivo.carregar().get(self.SECAO, []):
            animal = repositorio_animais.buscar_por_brinco(item["brinco"])
            if animal is not None:
                self.__compras.append(
                    CompraAnimal(date.fromisoformat(item["data"]), animal, item["valor"])
                )

    def adicionar(self, compra: CompraAnimal) -> None:
        self.__compras.append(compra)

    def listar(self) -> List[CompraAnimal]:
        return list(self.__compras)

    def salvar(self) -> None:
        dados = self.__arquivo.carregar()
        dados[self.SECAO] = [
            {
                "data": compra.data.isoformat(),
                "valor": compra.valor,
                "brinco": compra.animal.brinco.valor,
            }
            for compra in self.__compras
        ]
        self.__arquivo.salvar(dados)


class RepositorioProprietarioJson(RepositorioProprietario):
    """Guarda o cadastro do proprietário, na seção 'proprietario'.

    O cadastro padrão antigo ("Fazenda Boa Esperança" com CPF zerado) é
    tratado como vazio, para que arquivos de execuções anteriores também
    passem pelo autocadastro obrigatório do primeiro acesso.
    """

    SECAO = "proprietario"
    CADASTRO_PADRAO_ANTIGO = ("Fazenda Boa Esperança", "000.000.000-00")

    def __init__(self, arquivo: ArquivoDados) -> None:
        self.__arquivo = arquivo

    def carregar(self) -> Optional[Proprietario]:
        item = self.__arquivo.carregar().get(self.SECAO)
        if not item:
            return None
        proprietario = Proprietario(
            item.get("nome", ""), item.get("cpf", ""), item.get("senha", "")
        )
        if (proprietario.nome, proprietario.cpf) == self.CADASTRO_PADRAO_ANTIGO:
            return None
        return proprietario

    def salvar(self, proprietario: Proprietario) -> None:
        dados = self.__arquivo.carregar()
        dados[self.SECAO] = {
            "nome": proprietario.nome,
            "cpf": proprietario.cpf,
            "senha": proprietario.senha,
        }
        self.__arquivo.salvar(dados)


class RepositorioFornecedorJson(RepositorioFornecedor):
    """Guarda o cadastro do fornecedor, na seção 'fornecedor_cadastro'.

    A seção 'fornecedor' guarda o catálogo de lotes; o cadastro (nome e
    CNPJ, credencial de entrada do ator) fica em uma seção própria.
    """

    SECAO = "fornecedor_cadastro"

    def __init__(self, arquivo: ArquivoDados) -> None:
        self.__arquivo = arquivo

    def carregar(self) -> Optional[Fornecedor]:
        item = self.__arquivo.carregar().get(self.SECAO)
        if not item:
            return None
        return Fornecedor(item.get("nome", ""), item.get("cnpj", ""))

    def salvar(self, fornecedor: Fornecedor) -> None:
        dados = self.__arquivo.carregar()
        dados[self.SECAO] = {"nome": fornecedor.nome, "cnpj": fornecedor.cnpj}
        self.__arquivo.salvar(dados)


class RepositorioFrigorificoJson(RepositorioFrigorifico):
    """Guarda o cadastro do frigorífico, na seção 'frigorifico'."""

    SECAO = "frigorifico"

    def __init__(self, arquivo: ArquivoDados) -> None:
        self.__arquivo = arquivo

    def carregar(self) -> Optional[Frigorifico]:
        item = self.__arquivo.carregar().get(self.SECAO)
        if not item:
            return None
        return Frigorifico(item.get("nome", ""), item.get("cnpj", ""))

    def salvar(self, frigorifico: Frigorifico) -> None:
        dados = self.__arquivo.carregar()
        dados[self.SECAO] = {"nome": frigorifico.nome, "cnpj": frigorifico.cnpj}
        self.__arquivo.salvar(dados)


# ----------------------------------------------------------------------
# Multiusuário: índice de contas e criação do arquivo de cada conta
# ----------------------------------------------------------------------
def caminho_de_dados(documento: str) -> str:
    """Arquivo de dados da conta daquele documento: dados_<dígitos>.json.

    Cada usuário tem o seu próprio arquivo — é por aí que o sistema
    isola o trabalho de um usuário do do outro."""
    return f"dados_{normalizar_documento(documento)}.json"


class IndiceContasJson(RepositorioContas):
    """Guarda o índice de contas do sistema, na seção 'contas' do
    usuarios.json: nome, documento, papel, credencial da senha e arquivo
    de dados de cada usuário. É o índice quem alimenta o login.

    Índices antigos, que não guardavam a credencial (ela morava só no
    cadastro do Proprietário, dentro do arquivo de dados da conta), são
    atualizados na carga: a credencial do arquivo é levada ao índice, e
    o índice é salvo de novo — a transição acontece uma vez só."""

    SECAO = "contas"

    def __init__(self, arquivo: ArquivoDados) -> None:
        self.__arquivo = arquivo
        self.__contas: Dict[str, Conta] = {}
        for item in self.__arquivo.carregar().get(self.SECAO, []):
            conta = Conta(
                item.get("nome", ""),
                item.get("documento", item.get("cpf", "")),
                item.get("papel", "proprietario"),
                item.get("arquivo", ""),
                item.get("senha", ""),
            )
            self.__contas[normalizar_documento(conta.documento)] = conta
        self.__recuperar_credenciais_do_formato_antigo()

    def __recuperar_credenciais_do_formato_antigo(self) -> None:
        """Índices antigos sem credencial: toma a do cadastro do
        Proprietário no arquivo de dados de cada conta."""
        atualizadas = False
        for chave, conta in list(self.__contas.items()):
            if conta.senha:
                continue
            cadastro = RepositorioProprietarioJson(
                ArquivoDados(conta.arquivo)
            ).carregar()
            if cadastro is None or not cadastro.senha:
                continue
            self.__contas[chave] = Conta(
                conta.nome, conta.documento, conta.papel, conta.arquivo, cadastro.senha
            )
            atualizadas = True
        if atualizadas:
            self.salvar()

    def adicionar(self, conta: Conta) -> None:
        self.__contas[normalizar_documento(conta.documento)] = conta

    def buscar_por_documento(self, documento: str) -> Optional[Conta]:
        return self.__contas.get(normalizar_documento(documento))

    def remover(self, documento: str) -> None:
        self.__contas.pop(normalizar_documento(documento), None)

    def listar(self) -> List[Conta]:
        return list(self.__contas.values())

    def salvar(self) -> None:
        dados = self.__arquivo.carregar()
        dados[self.SECAO] = [
            {
                "nome": conta.nome,
                "documento": conta.documento,
                "papel": conta.papel,
                "arquivo": conta.arquivo,
                "senha": conta.senha,
            }
            for conta in self.__contas.values()
        ]
        self.__arquivo.salvar(dados)


class FonteDeCadastros(CriadorDeArquivos):
    """Cria o arquivo de dados de uma conta nova, já com o cadastro do
    papel dela semeado nele — o proprietário no 'proprietario', o
    fornecedor no 'fornecedor_cadastro', o frigorífico no 'frigorifico'.

    Com o cadastro semeado, a área do papel abre de cara, sem
    primeiro-acesso: quem cria a conta já se cadastra nela."""

    def caminho_de(self, documento: str) -> str:
        """Arquivo de dados da conta daquele documento."""
        return caminho_de_dados(documento)

    def criar(self, papel: str, nome: str, documento: str) -> str:
        """Cria o arquivo de dados da conta e devolve o caminho criado."""
        caminho = caminho_de_dados(documento)
        arquivo = ArquivoDados(caminho)
        if papel == "proprietario":
            RepositorioProprietarioJson(arquivo).salvar(Proprietario(nome, documento))
        elif papel == "fornecedor":
            RepositorioFornecedorJson(arquivo).salvar(Fornecedor(nome, documento))
        elif papel == "frigorifico":
            RepositorioFrigorificoJson(arquivo).salvar(Frigorifico(nome, documento))
        else:
            raise RegraNegocioViolation(f"Papel desconhecido: {papel}.")
        return caminho
