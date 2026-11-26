from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.ingresso import Ingresso
    from app.models.sala import Sala


class Assento(SQLModel, table=True):
    __tablename__ = "assento"
    __table_args__ = (
        UniqueConstraint("sala_id", "fileira", "numero", name="uq_assento_sala_fileira_numero"),
        CheckConstraint("numero > 0", name="ck_assento_numero_positivo"),
    )

    id: int | None = Field(default=None, primary_key=True)
    sala_id: int = Field(foreign_key="sala.id")
    fileira: str = Field(max_length=2)  # A, B, C...
    numero: int

    sala: Optional["Sala"] = Relationship(back_populates="assentos")
    ingressos: list["Ingresso"] = Relationship(back_populates="assento")
