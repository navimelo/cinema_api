print("INÍCIO DO TESTE")

from sqlalchemy.orm import configure_mappers
from sqlmodel import SQLModel, create_engine

from app.models.assento import Assento
from app.models.cliente import Cliente
from app.models.compra import Compra
from app.models.filme import Filme
from app.models.filme_genero import FilmeGenero
from app.models.genero import Genero
from app.models.ingresso import Ingresso
from app.models.sala import Sala
from app.models.sessao import Sessao
from app.models.validacao import Validacao

print("Modelos importados!")

engine = create_engine("sqlite:///teste.db", echo=True)

print("Criando as tabelas...")
SQLModel.metadata.create_all(engine)
print("Tabelas criadas com sucesso!")

print("Tabelas registradas:")
for nome_tabela in SQLModel.metadata.tables:
    print(nome_tabela)

print("Verificando relacionamentos...")
configure_mappers()
print("Relacionamentos configurados!")
print("TESTE CONCLUÍDO!")
