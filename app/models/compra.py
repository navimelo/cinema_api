from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

from app.models.constantes import StatusCompra

if TYPE_CHECKING:
    from app.models.cliente import Cliente
    from app.models.ingresso import Ingresso


class Compra(SQLModel, table=True):
    """Operação de venda: um cliente pode comprar vários ingressos de uma só vez."""
    __tablename__ = "compra"

    id: int | None = Field(default=None, primary_key=True)
    cliente_id: int = Field(foreign_key="cliente.id")
    data_compra: datetime = Field(
      default_factory=lambda: datetime.now(timezone.utc)
)
    valor_total: float = Field(default=0)
    status: str = Field(default=StatusCompra.CONCLUIDA, max_length=15)

    cliente: Optional["Cliente"] = Relationship(back_populates="compras")
    ingressos: list["Ingresso"] = Relationship(back_populates="compra")  # 1:N
