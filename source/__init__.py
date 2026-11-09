"""Camada fonte do sistema de gestão de rebanho.

Estrutura em camadas influenciada pelo Domain-Driven Design (DDD):

- domain/: camada de domínio, o coração do sistema. Não importa nada das
  outras camadas — todas as dependências apontam para dentro.
- usecases/: camada de aplicação com os casos de uso, que orquestram as
  entidades do domínio sem conter regras de negócio.
- infra/: camada de infraestrutura. Implementa os contratos (repositórios)
  que o resto do sistema consome, sem que o domínio saiba como os dados
  são persistidos.
- interfaces/: camada de apresentação (console e Tkinter). Só chama métodos
  das classes — nenhuma regra de negócio vive aqui.
"""
