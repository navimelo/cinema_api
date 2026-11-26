from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, Index, text
from sqlmodel import Field, Relationship, SQLModel

from app.models.constantes import StatusIngresso

if TYPE_CHECKING:
    from app.models.assento import Assento
    from app.models.compra import Compra
    from app.models.sessao import Sessao
    from app.models.validacao import Validacao


class Ingresso(SQLModel, table=True):
    __tablename__ = "ingresso"
    __table_args__ = (
        CheckConstraint("valor >= 0", name="ck_ingresso_valor_nao_negativo"),
        Index(
            "uq_ingresso_sessao_assento_ativo",
            "sessao_id",
            "assento_id",
            unique=True,
            sqlite_where=text("status <> 'cancelado'"),
            postgresql_where=text("status <> 'cancelado'"),
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    compra_id: int = Field(foreign_key="compra.id")
    sessao_id: int = Field(foreign_key="sessao.id")
    assento_id: int = Field(foreign_key="assento.id")
    valor: float
    status: str = Field(default=StatusIngresso.VALIDO, max_length=15)
    criado_em: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
)
    cancelado_em: datetime | None = Field(default=None)

    compra: Optional["Compra"] = Relationship(back_populates="ingressos")
    sessao: Optional["Sessao"] = Relationship(back_populates="ingressos")
    assento: Optional["Assento"] = Relationship(back_populates="ingressos")
    validacao: Optional["Validacao"] = Relationship(  # 1:1
        back_populates="ingresso", sa_relationship_kwargs={"uselist": False}
    )
