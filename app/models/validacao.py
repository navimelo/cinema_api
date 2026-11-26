from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.ingresso import Ingresso


class Validacao(SQLModel, table=True):
    """Registro da entrada do cliente na sala (leitura do ingresso). Relação 1:1 com Ingresso."""
    __tablename__ = "validacao"

    id: int | None = Field(default=None, primary_key=True)
    ingresso_id: int = Field(foreign_key="ingresso.id", unique=True, index=True)
    validado_em: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    operador: str = Field(max_length=80)

    ingresso: Optional["Ingresso"] = Relationship(back_populates="validacao")
