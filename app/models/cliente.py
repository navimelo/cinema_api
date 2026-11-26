from datetime import date, datetime, timezone
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.compra import Compra


class Cliente(SQLModel, table=True):
    __tablename__ = "cliente"

    id: int | None = Field(default=None, primary_key=True)
    nome: str = Field(max_length=120)
    email: str = Field(max_length=150, unique=True, index=True)
    cpf: str | None = Field(default=None, max_length=11, unique=True, index=True)
    telefone: str | None = Field(default=None, max_length=20)
    data_nascimento: date
    ativo: bool = Field(default=True)
    criado_em: datetime = Field(
    default_factory=lambda: datetime.now(timezone.utc)
)

    compras: list["Compra"] = Relationship(back_populates="cliente")  # 1:N
