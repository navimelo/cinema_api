from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Path, Query
from sqlmodel import Session

from app.database import get_session

SessionDep = Annotated[Session, Depends(get_session)]
IdPath = Annotated[int, Path(gt=0, description="Identificador do recurso (inteiro positivo)")]


@dataclass
class Paginacao:
    offset: int
    limit: int


def _paginacao(
    offset: int = Query(0, ge=0, description="Quantos registros pular"),
    limit: int = Query(10, ge=1, le=100, description="Máximo de registros retornados"),
) -> Paginacao:
    return Paginacao(offset=offset, limit=limit)


PaginacaoDep = Annotated[Paginacao, Depends(_paginacao)]
