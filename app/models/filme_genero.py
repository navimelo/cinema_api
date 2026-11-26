from sqlmodel import Field, SQLModel


class FilmeGenero(SQLModel, table=True):
    """Tabela associativa do relacionamento N:N Filme <-> Gênero."""
    __tablename__ = "filme_genero"

    filme_id: int = Field(foreign_key="filme.id", primary_key=True)
    genero_id: int = Field(foreign_key="genero.id", primary_key=True)
