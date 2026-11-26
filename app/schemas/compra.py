from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.sala import AssentoRead
from app.schemas.sessao import SessaoDetalhe


class CompraCreate(BaseModel):
    cliente_id: int = Field(gt=0)
    sessao_id: int = Field(gt=0)
    assentos_ids: list[int] = Field(min_length=1, description="IDs dos assentos (ver GET /sessoes/{id}/assentos)")


class TrocaAssento(BaseModel):
    assento_id: int = Field(gt=0)


class IngressoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    compra_id: int
    sessao_id: int
    assento_id: int
    valor: float
    status: Literal["valido", "utilizado", "cancelado"]
    criado_em: datetime
    cancelado_em: datetime | None


class IngressoDetalhe(IngressoRead):
    assento: AssentoRead
    sessao: SessaoDetalhe


class CompraRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    cliente_id: int
    data_compra: datetime
    valor_total: float
    status: str
    ingressos: list[IngressoDetalhe] = []
