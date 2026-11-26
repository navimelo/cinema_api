from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from app.models.filme_genero import FilmeGenero

if TYPE_CHECKING:
    from app.models.filme import Filme


class Genero(SQLModel, table=True):
    __tablename__ = "genero"

    id: int | None = Field(default=None, primary_key=True)
    nome: str = Field(max_length=50, unique=True, index=True)

    filmes: list["Filme"] = Relationship(back_populates="generos", link_model=FilmeGenero)
