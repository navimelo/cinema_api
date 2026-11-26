# Trabalho-de-persist-ncia
nome do projeto: 
Criação de API de cinema

## integrantes: 
Ana Vitória de Melo Silva
Anna Rayca Alves Cardoso
Sophia Muniz de Oliveira

## tema recebido: 
Tema 20 - Sistema de Cinema

## objetivo: 
Armazenar os dados do cinema, organizar as vendas e assentos, além de visualizar os filmes com maior público, períodos com mais clientes, etc.

## Tecnologias utilizadas:
FastAPI, Alembic e PostgreSQL

## Descrição das entidades:

1. Gênero:
- nome (único)

2. Filme:
- Título (único)
- duração
- classificação_indicativa
- em_cartaz
- estreia
- sinopse

3. Filme_Genero:
- id do filme
- id do gênero
(forma uma chave composta)

4. Sala:
- Nome
- Tipo
- Capacidade
- está_ativa

5. Assento:
- sala_id
- número

6. Sessao:
- filme_id
- data
- valor_total
- status

7. Cliente:
- nome
- e-mail
- CPF
- data_nascimento
- cadastro

8. Compra:
- cliente_id
- data
- valor_total
- status
  (obs.: o id de assento se inicia do 21)
  
9. Ingresso:
- compra_id
- sessao_id
- assento_id
- valor
- status (único)
- operador
- data/hora

10. Validação:
- ingresso_id

## Descrição dos relacionamentos
1:1 -> ingresso e validação
1:N -> sala e assento, sala e sessao, filme e sessao, cliente e compra, compra e ingresso, sessao e ingresso, assento e ingresso.
N:N -> filme e gênero 

## Instruções de instalação:
- ambiente virtual 
python -m venv .venv
source .venv/bin/activate
Windows: .venv\Scripts\activate

- dependências 
python -m pip install -r requirements.txt


## Filtros:
GET /filmes: titulo, genero_id classificacao, em_cartaz.
GET /sessoes: filme_id, sala_id, status, data_inicial, data_final.
GET /salas: nome, tipo, ativa, apacidade_minima.
GET /clientes: nome, email, ativo. 
GET /compras: cliente_id, status, data_inicial, data_final.
GET /ingressos: sessao_id, cliente_id, compra_id, status. 
GET /validacoes: ingresso_id, sessao_id, operador. 
GET /sessoes: id assentos disponiveis=true/false

## Principais endpoints

Gêneros - POST/GET /generos, GET/PATCH/DELETE /generos/{id}, GET /generos/{id}/filmes

Filmes - POST/GET /filmes, GET/PATCH/DELETE /filmes/{id}, GET /filmes/{id}/sessoes

Salas - POST/GET /salas, GET/PATCH/DELETE /salas/{id}, GET /salas/{id}/assentos, GET /salas/{id}/sessoes

Sessões - POST/GET /sessoes, GET/PATCH/DELETE /sessoes/{id}, POST /sessoes/{id}/cancelar, GET /sessoes/{id}/assentos, GET /sessoes/{id}/ingressos

Clientes- POST/GET /clientes, GET/PATCH/DELETE /clientes/{id}, GET /clientes/{id}/compras, GET /clientes/{id}/ingressos

Compras - POST/GET /compras, GET /compras/{id}, POST /compras/{id}/cancelar

Ingressos - GET /ingressos, GET/PATCH /ingressos/{id} (troca de assento), POST /ingressos/{id}/cancelar

Validações - POST/GET /validacoes, GET /validacoes/{id}

Consultas- GET /consultas/filmes-mais-vistos, /ocupacao-sessoes, /vendas-por-dia, /sessoes-sem-vendas

Estatísticas - GET /estatisticas

## Configuração do PostgreSQL
PostgreSQL  DATABASE_URL=postgresql+psycopg://usuario:senha@localhost:5432/cinema

## Configuração do SQLite
PostgreSQL  DATABASE_URL=postgresql+psycopg://sqlite:///./database.db

## Configuração do Post
psql -U postgres -c "CREATE DATABASE cinema;"

## Configuração da variável DATABASE_URL
DATABASE_URL=sqlite:///./database.db

## Consultas complexas:
- Filmes mais vistos
- Ocupação de sessões
- Vendas por dia
- Sessoes sem venda

## Consultas específicas:
- Ingressos de um cliente (Cliente→Compra→Ingresso).
- Sessões de um filme.
- Sessões de uma sala.
- Filmes de um gênero (N:N).
- Ingressos de uma sessão.
- Assentos de uma sala.

## Execução da aplicação:
uvicorn app.main:app --reload

## Execução das migrações:
alembic upgrade head 

## Execução do povoamento:
python -m 
Scripts.seed

## Regras de negócio
- Não pode haver dois ingressos com o mesmo assento
- Não pode haver choque de horário entre sessões da mesma sala
- Após cancelar a compra de um ingresso, o assento deve voltar a ficar disnponível

## Descrição da funcionalidade específica do tema:
GET /sessoes/{id}/assentos— mapa de lugares da sala indicando *livres/ocupados naquela sessão*
POST /compras — compra de **vários assentos** de uma sessão numa só operação (tudo ou nada).
Proteção contra concorrência pelo **índice único parcial** do banco + captura da violação (409).
POST /ingressos/{id}/cancelar` e
POST /compras/{id}/cancelar — liberam o assento para nova venda.
PATCH /ingressos/{id} — troca de assento na mesma sessão.
POST /sessoes/{id}/cancelar — alteração na programação: cancela a sessão e todos os seus ingressos.
POST /validacoes — registro da entrada (1:1 com o ingresso).
