from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.assento import Assento
    from app.models.sessao import Sessao


class Sala(SQLModel, table=True):
    __tablename__ = "sala"
    __table_args__ = (
        CheckConstraint("capacidade > 0", name="ck_sala_capacidade_positiva"),
    )

    id: int | None = Field(default=None, primary_key=True)
    nome: str = Field(max_length=50, unique=True, index=True)
    tipo: str = Field(default="2D", max_length=20)  # 2D, 3D, IMAX, VIP
    capacidade: int
    ativa: bool = Field(default=True)

    assentos: list["Assento"] = Relationship(
        back_populates="sala", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )  # 1:N
    sessoes: list["Sessao"] = Relationship(back_populates="sala")  # 1:N
