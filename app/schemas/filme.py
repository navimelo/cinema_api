from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.genero import GeneroRead

Classificacao = Literal["L", "10", "12", "14", "16", "18"]


class FilmeBase(BaseModel):
    titulo: str = Field(min_length=1, max_length=150)
    duracao_minutos: int = Field(gt=0, le=600)
    classificacao_indicativa: Classificacao
    data_estreia: date | None = None
    em_cartaz: bool = True
    sinopse: str | None = Field(default=None, max_length=1000)


class FilmeCreate(FilmeBase):
    generos_ids: list[int] = Field(default_factory=list, description="IDs dos gêneros (N:N)")


class FilmeUpdate(BaseModel):
    titulo: str | None = Field(default=None, min_length=1, max_length=150)
    duracao_minutos: int | None = Field(default=None, gt=0, le=600)
    classificacao_indicativa: Classificacao | None = None
    data_estreia: date | None = None
    em_cartaz: bool | None = None
    sinopse: str | None = Field(default=None, max_length=1000)
    generos_ids: list[int] | None = None


class FilmeRead(FilmeBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    generos: list[GeneroRead] = []


class FilmeResumo(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    titulo: str
    duracao_minutos: int
    classificacao_indicativa: str
