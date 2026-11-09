"""Casos de uso do sistema de gestão de rebanho.

Um caso de uso por classe (uma bolha do diagrama de casos de uso), com o
nome falando a mesma língua do domínio (linguagem onipresente do DDD). Eles
são a única porta de entrada para a apresentação (console e Tkinter), que
nunca chama o domínio diretamente.
"""

from datetime import date
from typing import List, Optional, Tuple

from source.domain.entidades.animal import Animal, Femea, Macho
from source.domain.entidades.conta import Conta, PAPEIS, normalizar_documento
from source.domain.entidades.insumo import BaseAlimentacao, Insumo
from source.domain.entidades.manejo import Pesagem, Vacinacao
from source.domain.entidades.pessoas import CompraAnimal, Fornecedor, Frigorifico, Proprietario
from source.domain.excecoes import (
    AnimalNaoEncontradoError,
    BaseDuplicadaError,
    BaseNaoEncontradaError,
    BrincoDuplicadoError,
    CadastroNaoPreenchidoError,
    CredencialInvalidaError,
    DocumentoDuplicadoError,
    InseminacaoInvalidaError,
    InsumoNaoEncontradoError,
    RegraNegocioViolation,
)
from source.domain.repositorios import (
    RepositorioAnimais,
    RepositorioBases,
    RepositorioCompras,
    RepositorioContas,
    RepositorioFornecedor,
    RepositorioFrigorifico,
    RepositorioInsumos,
    RepositorioProprietario,
)
from source.usecases.senhas import conferir, gerar_credencial


class CadastrarAnimal:
    """Cadastrar animal: cria a Femea ou o Macho e guarda no rebanho."""

    def __init__(
        self, repositorio_animais: RepositorioAnimais, proprietario: Proprietario
    ) -> None:
        self.__repositorio = repositorio_animais
        self.__proprietario = proprietario

    def executar(self, brinco: str, data_nascimento: date, raca: str, tipo: str) -> Animal:
        if tipo == "femea":
            animal: Animal = Femea(brinco, data_nascimento, raca)
        elif tipo == "macho":
            animal = Macho(brinco, data_nascimento, raca)
        else:
            raise RegraNegocioViolation(f"Tipo de animal inválido: {tipo}.")
        if self.__repositorio.buscar_por_brinco(brinco) is not None:
            raise BrincoDuplicadoError(f"Já existe um animal com o brinco {brinco}.")
        self.__repositorio.adicionar(animal)
        self.__proprietario.adicionar_animal(animal)
        self.__repositorio.salvar()
        return animal


class RegistrarPesagem:
    """Registrar pesagem de um animal do rebanho."""

    def __init__(self, repositorio_animais: RepositorioAnimais) -> None:
        self.__repositorio = repositorio_animais

    def executar(self, brinco: str, kg: float, data: Optional[date] = None) -> Pesagem:
        animal = self.__repositorio.buscar_por_brinco(brinco)
        if animal is None:
            raise AnimalNaoEncontradoError(f"Animal {brinco} não encontrado.")
        pesagem = animal.registrar_pesagem(kg, data or date.today())
        self.__repositorio.salvar()
        return pesagem


class RegistrarVacinacao:
    """Registrar vacinação de um animal do rebanho."""

    def __init__(self, repositorio_animais: RepositorioAnimais) -> None:
        self.__repositorio = repositorio_animais

    def executar(
        self, brinco: str, vacina: str, dose: str, data: Optional[date] = None
    ) -> Vacinacao:
        animal = self.__repositorio.buscar_por_brinco(brinco)
        if animal is None:
            raise AnimalNaoEncontradoError(f"Animal {brinco} não encontrado.")
        vacinacao = animal.registrar_vacinacao(vacina, dose, data or date.today())
        self.__repositorio.salvar()
        return vacinacao


class InseminarFemea:
    """Realizar inseminação de uma fêmea com um touro do rebanho."""

    def __init__(self, repositorio_animais: RepositorioAnimais) -> None:
        self.__repositorio = repositorio_animais

    def executar(self, brinco_femea: str, brinco_touro: str) -> None:
        femea = self.__repositorio.buscar_por_brinco(brinco_femea)
        touro = self.__repositorio.buscar_por_brinco(brinco_touro)
        if femea is None or touro is None:
            faltando = brinco_femea if femea is None else brinco_touro
            raise AnimalNaoEncontradoError(f"Animal {faltando} não encontrado.")
        if not isinstance(femea, Femea):
            raise InseminacaoInvalidaError(
                f"Animal {brinco_femea} não é fêmea, então não pode ser inseminado."
            )
        if not isinstance(touro, Macho):
            raise InseminacaoInvalidaError(
                f"Animal {brinco_touro} não é macho, então não pode ser touro."
            )
        femea.inseminar(touro)
        self.__repositorio.salvar()


class RegistrarParto:
    """Registrar o parto de uma fêmea: o bezerro nasce já vinculado à mãe
    e à genealogia, e entra no rebanho."""

    def __init__(
        self, repositorio_animais: RepositorioAnimais, proprietario: Proprietario
    ) -> None:
        self.__repositorio = repositorio_animais
        self.__proprietario = proprietario

    def executar(self, brinco_femea: str, brinco_filho: str, macho: bool) -> Animal:
        femea = self.__repositorio.buscar_por_brinco(brinco_femea)
        if femea is None:
            raise AnimalNaoEncontradoError(f"Animal {brinco_femea} não encontrado.")
        if not isinstance(femea, Femea):
            raise RegraNegocioViolation(
                f"Animal {brinco_femea} não é fêmea, então não tem parto a registrar."
            )
        if self.__repositorio.buscar_por_brinco(brinco_filho) is not None:
            raise BrincoDuplicadoError(f"Já existe um animal com o brinco {brinco_filho}.")
        bezerro = femea.registrar_parto(brinco_filho, macho)
        self.__repositorio.adicionar(bezerro)
        self.__proprietario.adicionar_animal(bezerro)
        self.__repositorio.salvar()
        return bezerro


class VenderAnimal:
    """Vender um animal ao frigorífico."""

    def __init__(
        self,
        repositorio_animais: RepositorioAnimais,
        frigorifico: Frigorifico,
        repositorio_compras: RepositorioCompras,
    ) -> None:
        self.__repositorio_animais = repositorio_animais
        self.__frigorifico = frigorifico
        self.__repositorio_compras = repositorio_compras

    def executar(self, brinco: str, valor: float) -> CompraAnimal:
        animal = self.__repositorio_animais.buscar_por_brinco(brinco)
        if animal is None:
            raise AnimalNaoEncontradoError(f"Animal {brinco} não encontrado.")
        compra = self.__frigorifico.comprar_animal(animal, valor)
        self.__repositorio_compras.adicionar(compra)
        self.__repositorio_compras.salvar()
        self.__repositorio_animais.salvar()
        return compra


class IdentificarAnimaisParaVenda:
    """Identificar animais para venda: lista quem já atingiu o peso mínimo
    de abate. Serve tanto ao Proprietário (Identificar Animais para Venda)
    quanto ao Frigorífico (Consultar Animais Disponíveis para Compra), como
    no diagrama de casos de uso."""

    def __init__(self, repositorio_animais: RepositorioAnimais) -> None:
        self.__repositorio = repositorio_animais

    def executar(self) -> Tuple[Animal, ...]:
        return tuple(animal for animal in self.__repositorio.listar() if animal.pode_vender())


class HistoricoCompras:
    """Histórico de compras do frigorífico."""

    def __init__(self, frigorifico: Frigorifico) -> None:
        self.__frigorifico = frigorifico

    def executar(self) -> Tuple[CompraAnimal, ...]:
        return self.__frigorifico.historico_compras()


class CriarBaseAlimentacao:
    """Gerenciar nutrição do gado: cria uma base de alimentação a partir
    dos insumos do estoque da fazenda."""

    def __init__(
        self,
        repositorio_bases: RepositorioBases,
        repositorio_insumos: RepositorioInsumos,
        proprietario: Proprietario,
    ) -> None:
        self.__repositorio_bases = repositorio_bases
        self.__repositorio_insumos = repositorio_insumos
        self.__proprietario = proprietario

    def executar(
        self, nome: str, descricao: str, itens: List[Tuple[str, float]]
    ) -> BaseAlimentacao:
        if self.__repositorio_bases.buscar_por_nome(nome) is not None:
            raise BaseDuplicadaError(f"Já existe uma base de alimentação chamada {nome}.")
        base = BaseAlimentacao(nome, descricao)
        for nome_insumo, quantidade in itens:
            insumo = self.__repositorio_insumos.buscar_por_nome(nome_insumo)
            if insumo is None:
                raise InsumoNaoEncontradoError(
                    f"Insumo {nome_insumo} não encontrado no estoque da fazenda."
                )
            base.adicionar_insumo(insumo, quantidade)
        self.__repositorio_bases.adicionar(base)
        self.__repositorio_bases.salvar()
        self.__proprietario.adicionar_base(base)
        return base


class DefinirAlimentacao:
    """Gerenciar nutrição do gado: atribui uma base de alimentação a um
    animal do rebanho."""

    def __init__(
        self, repositorio_animais: RepositorioAnimais, repositorio_bases: RepositorioBases
    ) -> None:
        self.__repositorio_animais = repositorio_animais
        self.__repositorio_bases = repositorio_bases

    def executar(self, brinco: str, nome_base: str) -> Animal:
        animal = self.__repositorio_animais.buscar_por_brinco(brinco)
        if animal is None:
            raise AnimalNaoEncontradoError(f"Animal {brinco} não encontrado.")
        base = self.__repositorio_bases.buscar_por_nome(nome_base)
        if base is None:
            raise BaseNaoEncontradaError(
                f"Base de alimentação {nome_base} não encontrada."
            )
        if animal.vendido:
            raise RegraNegocioViolation(
                f"Animal {brinco} já foi vendido, então não recebe alimentação."
            )
        animal.definir_alimentacao(base)
        self.__repositorio_animais.salvar()
        return animal


class ConsultarAlimentacao:
    """Consultar alimentação do animal (include de Gerenciar Nutrição):
    devolve o resumo da base atribuída ao animal."""

    def __init__(self, repositorio_animais: RepositorioAnimais) -> None:
        self.__repositorio = repositorio_animais

    def executar(self, brinco: str) -> str:
        animal = self.__repositorio.buscar_por_brinco(brinco)
        if animal is None:
            raise AnimalNaoEncontradoError(f"Animal {brinco} não encontrado.")
        base = animal.alimentacao()
        if base is None:
            return f"O animal {brinco} ainda não tem base de alimentação definida."
        linhas = [f"Base {base.nome} — {base.descricao}"]
        for insumo, quantidade in base.itens:
            linhas.append(f"  - {insumo.nome}: {quantidade:.2f} por animal/dia")
        linhas.append(f"Consumo diário: {base.consumo_diario_kg():.2f} kg por animal")
        linhas.append(f"Custo mensal por animal: R$ {base.custo_mensal(1):.2f}")
        return "\n".join(linhas)


class ConsultarGenetica:
    """Consultar genética (include de Realizar Inseminação): devolve a
    genealogia do animal — mãe, pai e, para fêmeas, os filhos."""

    def __init__(self, repositorio_animais: RepositorioAnimais) -> None:
        self.__repositorio = repositorio_animais

    def executar(self, brinco: str) -> str:
        animal = self.__repositorio.buscar_por_brinco(brinco)
        if animal is None:
            raise AnimalNaoEncontradoError(f"Animal {brinco} não encontrado.")
        linhas = [f"Genética do animal {brinco}:"]
        linhas.append(f"  Mãe: {animal.mae_brinco or 'desconhecida'}")
        linhas.append(f"  Pai: {animal.pai_brinco or 'desconhecido'}")
        if isinstance(animal, Femea):
            filhos = animal.listar_filhos()
            linhas.append(
                "  Filhos: "
                + (", ".join(filho.brinco.valor for filho in filhos) or "nenhum")
            )
        return "\n".join(linhas)


class CadastrarInsumo:
    """Cadastrar insumo: o fornecedor cria um produto no catálogo dele
    (ou repõe o estoque do lote, se o insumo já existe)."""

    def __init__(
        self, repositorio_catalogo: RepositorioInsumos, fornecedor: Fornecedor
    ) -> None:
        self.__repositorio = repositorio_catalogo
        self.__fornecedor = fornecedor

    def executar(self, nome: str, tipo: str, quantidade: float, preco: float) -> Insumo:
        lote = self.__fornecedor.buscar_insumo(nome)
        if lote is None:
            lote = Insumo(nome, tipo, quantidade, preco)
            self.__repositorio.adicionar(lote)
        else:
            lote.adicionar_estoque(quantidade)
        self.__fornecedor.cadastrar_insumo(lote)
        self.__repositorio.salvar()
        return lote


def _transacao_insumo(
    fornecedor: Fornecedor,
    repositorio_fazenda: RepositorioInsumos,
    repositorio_catalogo: RepositorioInsumos,
    proprietario: Proprietario,
    nome: str,
    quantidade: float,
) -> Insumo:
    """Núcleo compartilhado por ComprarInsumo (visão do proprietário) e
    VenderInsumo (visão do fornecedor): é a mesma transação vista pelos
    dois atores. O fornecedor baixa o lote dele (baixar_estoque em uso
    real) e a fazenda recebe a quantidade no estoque."""
    lote = fornecedor.vender_insumo(nome, quantidade)
    insumo = repositorio_fazenda.buscar_por_nome(lote.nome)
    if insumo is None:
        insumo = Insumo(lote.nome, lote.tipo, 0.0, lote.preco)
        repositorio_fazenda.adicionar(insumo)
    proprietario.comprar_insumo(insumo, quantidade)
    repositorio_catalogo.salvar()
    repositorio_fazenda.salvar()
    return insumo


class ComprarInsumo:
    """Comprar insumo: o proprietário adquire uma quantidade do estoque do
    fornecedor e guarda no estoque da fazenda."""

    def __init__(
        self,
        repositorio_insumos: RepositorioInsumos,
        repositorio_catalogo: RepositorioInsumos,
        fornecedor: Fornecedor,
        proprietario: Proprietario,
    ) -> None:
        self.__repositorio_insumos = repositorio_insumos
        self.__repositorio_catalogo = repositorio_catalogo
        self.__fornecedor = fornecedor
        self.__proprietario = proprietario

    def executar(self, nome: str, quantidade: float) -> Insumo:
        return _transacao_insumo(
            self.__fornecedor,
            self.__repositorio_insumos,
            self.__repositorio_catalogo,
            self.__proprietario,
            nome,
            quantidade,
        )


class VenderInsumo:
    """Vender insumo: o fornecedor vende um lote do catálogo dele ao
    proprietário, que recebe a mercadoria no estoque da fazenda."""

    def __init__(
        self,
        repositorio_insumos: RepositorioInsumos,
        repositorio_catalogo: RepositorioInsumos,
        fornecedor: Fornecedor,
        proprietario: Proprietario,
    ) -> None:
        self.__repositorio_insumos = repositorio_insumos
        self.__repositorio_catalogo = repositorio_catalogo
        self.__fornecedor = fornecedor
        self.__proprietario = proprietario

    def executar(self, nome: str, quantidade: float) -> Insumo:
        return _transacao_insumo(
            self.__fornecedor,
            self.__repositorio_insumos,
            self.__repositorio_catalogo,
            self.__proprietario,
            nome,
            quantidade,
        )


def _sincronizar_indice(
    repositorio_contas: Optional[RepositorioContas],
    documento_antigo: str,
    nome: str,
    documento: str,
    credencial: Optional[str] = None,
) -> None:
    """Leva ao índice de contas o cadastro novo de uma conta: nome,
    documento e, quando informado, a credencial nova da senha. O papel e
    o arquivo de dados da conta são preservados."""
    if repositorio_contas is None:
        return
    conta = repositorio_contas.buscar_por_documento(documento_antigo)
    if conta is None:
        return
    mesmo_nome = conta.nome == nome
    mesmo_documento = normalizar_documento(conta.documento) == normalizar_documento(documento)
    mesma_credencial = credencial is None or conta.senha == credencial
    if mesmo_nome and mesmo_documento and mesma_credencial:
        return
    repositorio_contas.remover(conta.documento)
    repositorio_contas.adicionar(
        Conta(
            nome,
            documento,
            conta.papel,
            conta.arquivo,
            credencial if credencial is not None else conta.senha,
        )
    )
    repositorio_contas.salvar()


def _garantir_documento_livre(
    repositorio_contas: Optional[RepositorioContas], documento: str
) -> None:
    """Falha se alguma outra conta já usa o documento informado — o
    documento é a chave de login e é único, pontuação à parte."""
    if repositorio_contas is None:
        return
    if repositorio_contas.buscar_por_documento(documento) is not None:
        raise DocumentoDuplicadoError(
            f"Já existe uma conta com o documento {documento.strip()}."
        )


class Autocadastro:
    """Autocadastro do usuário: define (ou corrige) o cadastro do
    proprietário da propriedade, com nome, CPF e senha.

    A senha chega em texto digitado e é guardada como credencial
    (hash PBKDF2 com salt) — nunca em texto plano.

    No sistema multiusuário o CPF é a chave de login: quando o cadastro
    muda de nome ou de CPF, o índice de contas (opcional) é atualizado
    para que a próxima entrada continue encontrando o usuário."""

    def __init__(
        self,
        proprietario: Proprietario,
        repositorio: RepositorioProprietario,
        repositorio_contas: Optional[RepositorioContas] = None,
    ) -> None:
        self.__proprietario = proprietario
        self.__repositorio = repositorio
        self.__repositorio_contas = repositorio_contas

    def executar(self, nome: str, cpf: str, senha: str) -> Proprietario:
        if not senha.strip():
            raise RegraNegocioViolation("A senha é obrigatória no autocadastro.")
        documento_novo = cpf.strip()
        documento_antigo = self.__proprietario.cpf
        mudou_documento = (
            normalizar_documento(documento_novo) != normalizar_documento(documento_antigo)
        )
        if mudou_documento:
            _garantir_documento_livre(self.__repositorio_contas, documento_novo)
        credencial = gerar_credencial(senha.strip())
        self.__proprietario.atualizar_cadastro(nome, cpf, credencial)
        self.__repositorio.salvar(self.__proprietario)
        _sincronizar_indice(
            self.__repositorio_contas, documento_antigo, self.__proprietario.nome,
            documento_novo, credencial,
        )
        return self.__proprietario


class CadastrarConta:
    """Autocadastro multiusuário: cria a conta de um novo usuário do
    sistema, com nome, documento (CPF ou CNPJ), papel e senha.

    O papel acompanha a conta — o criador é sempre o ator que vai usar
    o sistema. A conta nasce isolada: ganha um arquivo de dados próprio
    (dados_<documento>.json) já com o cadastro do papel semeado nele,
    e o índice de contas guarda o nome, o documento, o papel, o arquivo
    e a credencial da senha. O documento é a chave de login e não pode
    se repetir, nem mesmo digitado com pontuação diferente."""

    def __init__(
        self,
        repositorio_contas: RepositorioContas,
        criador_de_arquivos,
    ) -> None:
        """Recebe o índice de contas e o criador que semeia o arquivo de
        dados da conta nova (implementado na infraestrutura)."""
        self.__repositorio_contas = repositorio_contas
        self.__criador = criador_de_arquivos

    def executar(
        self, nome: str, documento: str, papel: str, senha: str
    ) -> Conta:
        if not nome.strip() or not documento.strip():
            raise RegraNegocioViolation(
                "Nome e documento são obrigatórios no cadastro da conta."
            )
        if not senha.strip():
            raise RegraNegocioViolation("A senha é obrigatória no cadastro da conta.")
        if papel not in PAPEIS:
            raise RegraNegocioViolation(f"Papel desconhecido: {papel}.")
        conta_existente = self.__repositorio_contas.buscar_por_documento(documento.strip())
        if conta_existente is not None:
            return self.__adotar_ou_rejeitar(conta_existente, nome.strip(), senha.strip())
        credencial = gerar_credencial(senha.strip())
        arquivo = self.__criador.criar(papel, nome.strip(), documento.strip())
        conta = Conta(nome.strip(), documento.strip(), papel, arquivo, credencial)
        self.__repositorio_contas.adicionar(conta)
        self.__repositorio_contas.salvar()
        return conta

    def __adotar_ou_rejeitar(self, conta: Conta, nome: str, senha: str) -> Conta:
        """Contas legadas sem senha são adotadas: o dono do documento
        define o nome e a senha de acesso, e o arquivo de dados — com o
        trabalho que já existe nele — continua o mesmo. Contas que já
        têm senha não podem ser recriadas: o documento é único."""
        if conta.senha:
            raise DocumentoDuplicadoError(
                f"Já existe uma conta com o documento {conta.documento}."
            )
        credencial = gerar_credencial(senha)
        adotada = Conta(nome, conta.documento, conta.papel, conta.arquivo, credencial)
        self.__repositorio_contas.remover(conta.documento)
        self.__repositorio_contas.adicionar(adotada)
        self.__repositorio_contas.salvar()
        return adotada


class AutenticarConta:
    """Login multiusuário: identifica a conta pelo documento e confere a
    senha contra a credencial guardada no índice de contas.

    Devolve a Conta autenticada — nome, documento, papel e arquivo —;
    a composição de raiz usa o papel para abrir a área certa e o
    arquivo para montar o sistema só com os dados desse usuário."""

    def __init__(self, repositorio_contas: RepositorioContas) -> None:
        self.__repositorio_contas = repositorio_contas

    def executar(self, documento: str, senha: Optional[str]) -> Conta:
        conta = self.__repositorio_contas.buscar_por_documento(documento.strip())
        if conta is None:
            raise CredencialInvalidaError("Documento ou senha inválidos.")
        if not conta.senha:
            raise CadastroNaoPreenchidoError(
                "A conta ainda não tem senha: use 'Criar conta' com o mesmo "
                "documento para definir o acesso (os dados dela são mantidos)."
            )
        if senha is None or not conferir(senha, conta.senha):
            raise CredencialInvalidaError("Documento ou senha inválidos.")
        return conta


class CadastrarFornecedor:
    """Correção do cadastro do fornecedor pela área dele.

    No sistema multiusuário o CNPJ é a chave de login: quando muda, o
    índice de contas (opcional) é atualizado para que a próxima entrada
    continue encontrando o usuário."""

    def __init__(
        self,
        fornecedor: Fornecedor,
        repositorio: RepositorioFornecedor,
        repositorio_contas: Optional[RepositorioContas] = None,
    ) -> None:
        self.__fornecedor = fornecedor
        self.__repositorio = repositorio
        self.__repositorio_contas = repositorio_contas

    def executar(self, nome: str, cnpj: str) -> Fornecedor:
        documento_antigo = self.__fornecedor.cnpj
        if normalizar_documento(cnpj.strip()) != normalizar_documento(documento_antigo):
            _garantir_documento_livre(self.__repositorio_contas, cnpj)
        self.__fornecedor.atualizar_cadastro(nome, cnpj)
        self.__repositorio.salvar(self.__fornecedor)
        _sincronizar_indice(
            self.__repositorio_contas, documento_antigo, self.__fornecedor.nome,
            self.__fornecedor.cnpj,
        )
        return self.__fornecedor


class CadastrarFrigorifico:
    """Correção do cadastro do frigorífico pela área dele.

    No sistema multiusuário o CNPJ é a chave de login: quando muda, o
    índice de contas (opcional) é atualizado para que a próxima entrada
    continue encontrando o usuário."""

    def __init__(
        self,
        frigorifico: Frigorifico,
        repositorio: RepositorioFrigorifico,
        repositorio_contas: Optional[RepositorioContas] = None,
    ) -> None:
        self.__frigorifico = frigorifico
        self.__repositorio = repositorio
        self.__repositorio_contas = repositorio_contas

    def executar(self, nome: str, cnpj: str) -> Frigorifico:
        documento_antigo = self.__frigorifico.cnpj
        if normalizar_documento(cnpj.strip()) != normalizar_documento(documento_antigo):
            _garantir_documento_livre(self.__repositorio_contas, cnpj)
        self.__frigorifico.atualizar_cadastro(nome, cnpj)
        self.__repositorio.salvar(self.__frigorifico)
        _sincronizar_indice(
            self.__repositorio_contas, documento_antigo, self.__frigorifico.nome,
            self.__frigorifico.cnpj,
        )
        return self.__frigorifico
