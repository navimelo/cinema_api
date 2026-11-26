from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint
from sqlmodel import Field, Relationship, SQLModel

from app.models.filme_genero import FilmeGenero

if TYPE_CHECKING:
    from app.models.genero import Genero
    from app.models.sessao import Sessao


class Filme(SQLModel, table=True):
    __tablename__ = "filme"
    __table_args__ = (
        CheckConstraint("duracao_minutos > 0", name="ck_filme_duracao_positiva"),
    )

    id: int | None = Field(default=None, primary_key=True)
    titulo: str = Field(max_length=150, unique=True, index=True)
    duracao_minutos: int
    classificacao_indicativa: str = Field(max_length=2)  # L, 10, 12, 14, 16, 18
    data_estreia: date | None = Field(default=None)
    em_cartaz: bool = Field(default=True)
    sinopse: str | None = Field(default=None, max_length=1000)  # adicionada pela migração 0002

    generos: list["Genero"] = Relationship(back_populates="filmes", link_model=FilmeGenero)  # N:N
    sessoes: list["Sessao"] = Relationship(back_populates="filme")  # 1:N
