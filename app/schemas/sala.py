from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field

TipoSala = Literal["2D", "3D", "IMAX", "VIP"]


class SalaCreate(BaseModel):
    nome: str = Field(min_length=1, max_length=50)
    tipo: TipoSala = "2D"
    fileiras: int = Field(ge=1, le=26, description="Nº de fileiras (A, B, C...)")
    assentos_por_fileira: int = Field(ge=1, le=50)


class SalaUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=1, max_length=50)
    tipo: TipoSala | None = None
    ativa: bool | None = None


class SalaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nome: str
    tipo: str
    capacidade: int
    ativa: bool


class AssentoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    sala_id: int
    fileira: str
    numero: int

    @computed_field
    @property
    def codigo(self) -> str:
        return f"{self.fileira}{self.numero}"
