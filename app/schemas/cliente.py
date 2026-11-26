from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

EMAIL_REGEX = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


def _nao_futura(valor: date | None) -> date | None:
    if valor is not None and valor > date.today():
        raise ValueError("A data de nascimento não pode estar no futuro.")
    return valor


class ClienteCreate(BaseModel):
    nome: str = Field(min_length=2, max_length=120)
    email: str = Field(max_length=150, pattern=EMAIL_REGEX)
    cpf: str | None = Field(default=None, pattern=r"^\d{11}$", description="11 dígitos, sem pontuação")
    telefone: str | None = Field(default=None, max_length=20)
    data_nascimento: date

    validar_nascimento = field_validator("data_nascimento")(_nao_futura)


class ClienteUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=2, max_length=120)
    email: str | None = Field(default=None, max_length=150, pattern=EMAIL_REGEX)
    cpf: str | None = Field(default=None, pattern=r"^\d{11}$")
    telefone: str | None = Field(default=None, max_length=20)
    data_nascimento: date | None = None
    ativo: bool | None = None

    validar_nascimento = field_validator("data_nascimento")(_nao_futura)


class ClienteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nome: str
    email: str
    cpf: str | None
    telefone: str | None
    data_nascimento: date
    ativo: bool
    criado_em: datetime
