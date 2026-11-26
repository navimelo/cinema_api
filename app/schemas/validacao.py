from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ValidacaoCreate(BaseModel):
    ingresso_id: int = Field(gt=0)
    operador: str = Field(min_length=2, max_length=80, description="Funcionário que leu o ingresso")


class ValidacaoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    ingresso_id: int
    validado_em: datetime
    operador: str
