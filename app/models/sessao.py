from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint
from sqlmodel import Field, Relationship, SQLModel

from app.models.constantes import StatusSessao

if TYPE_CHECKING:
    from app.models.filme import Filme
    from app.models.ingresso import Ingresso
    from app.models.sala import Sala


class Sessao(SQLModel, table=True):
    __tablename__ = "sessao"
    __table_args__ = (
        CheckConstraint("fim > inicio", name="ck_sessao_fim_apos_inicio"),
        CheckConstraint("preco >= 0", name="ck_sessao_preco_nao_negativo"),
    )

    id: int | None = Field(default=None, primary_key=True)
    filme_id: int = Field(foreign_key="filme.id")
    sala_id: int = Field(foreign_key="sala.id")
    inicio: datetime = Field(index=True)  # índice criado pela migração 0002
    fim: datetime  # inicio + duração do filme + intervalo de limpeza
    preco: float
    status: str = Field(default=StatusSessao.AGENDADA, max_length=15)

    filme: Optional["Filme"] = Relationship(back_populates="sessoes")
    sala: Optional["Sala"] = Relationship(back_populates="sessoes")
    ingressos: list["Ingresso"] = Relationship(back_populates="sessao")
