from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.filme import FilmeResumo
from app.schemas.sala import AssentoRead, SalaRead


from datetime import timezone

def _para_naive(valor: datetime | None) -> datetime | None:
    if valor is not None and valor.tzinfo is None:
        return valor.replace(tzinfo=timezone.utc)
    return valor


class SessaoCreate(BaseModel):
    filme_id: int = Field(gt=0)
    sala_id: int = Field(gt=0)
    inicio: datetime
    preco: float = Field(ge=0, le=1000)

    validar_inicio = field_validator("inicio")(_para_naive)


class SessaoUpdate(BaseModel):
    filme_id: int | None = Field(default=None, gt=0)
    sala_id: int | None = Field(default=None, gt=0)
    inicio: datetime | None = None
    preco: float | None = Field(default=None, ge=0, le=1000)

    validar_inicio = field_validator("inicio")(_para_naive)


class SessaoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    filme_id: int
    sala_id: int
    inicio: datetime
    fim: datetime
    preco: float
    status: str


class SessaoDetalhe(SessaoRead):
    filme: FilmeResumo
    sala: SalaRead


class SessaoCancelada(BaseModel):
    sessao: SessaoDetalhe
    ingressos_cancelados: int


class AssentoDisponibilidade(AssentoRead):
    disponivel: bool


class MapaAssentos(BaseModel):
    sessao_id: int
    capacidade: int
    ocupados: int
    disponiveis: int
    assentos: list[AssentoDisponibilidade]
