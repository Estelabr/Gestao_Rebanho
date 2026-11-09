"""Implementação dos repositórios em arquivo JSON.

Só esta camada conhece o formato do arquivo: o resto do sistema fala com
os contratos de repositório, que moram no domínio
(source/domain/repositorios.py) e são cumpridos aqui.

Seções do dados.json:
  animais       -- cadastro de animais (pesagens, vacinas, reprodução, venda)
  insumos       -- estoque da fazenda
  fornecedor    -- catálogo de lotes do fornecedor
  bases         -- bases de alimentação
  compras       -- histórico de compras do frigorífico
  proprietario  -- cadastro do proprietário (autocadastro)

Referências entre objetos (filhos, base do animal, animal da compra,
insumo da base) são re-vinculadas na reconstrução, em segunda passada.
Chaves antigas ("preco_unitario", "quantidade") continuam sendo lidas.
"""

import json
import os
from datetime import date
from typing import Any, Callable, Dict, List, Optional

from source.domain.entidades.animal import Animal, Femea, Macho
from source.domain.entidades.insumo import BaseAlimentacao, Insumo
from source.domain.entidades.pessoas import CompraAnimal, Proprietario
from source.domain.excecoes import AnimalNaoEncontradoError
from source.domain.repositorios import (
    RepositorioAnimais,
    RepositorioBases,
    RepositorioCompras,
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
    """Guarda o cadastro do proprietário, na seção 'proprietario'."""

    SECAO = "proprietario"

    def __init__(self, arquivo: ArquivoDados) -> None:
        self.__arquivo = arquivo

    def carregar(self) -> Optional[Proprietario]:
        item = self.__arquivo.carregar().get(self.SECAO)
        if not item:
            return None
        return Proprietario(item.get("nome", ""), item.get("cpf", ""))

    def salvar(self, proprietario: Proprietario) -> None:
        dados = self.__arquivo.carregar()
        dados[self.SECAO] = {"nome": proprietario.nome, "cpf": proprietario.cpf}
        self.__arquivo.salvar(dados)
