from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Pagina(BaseModel, Generic[T]):
    """Envelope padrão das listagens paginadas (F8)."""
    total: int
    offset: int
    limit: int
    pagina_atual: int
    total_paginas: int
    itens: list[T]
