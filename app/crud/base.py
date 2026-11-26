from math import ceil

from sqlalchemy import func
from sqlmodel import Session, select

from app.exceptions import NaoEncontradoError


def obter_ou_404(session: Session, modelo, id_: int, rotulo: str):
    obj = session.get(modelo, id_)
    if obj is None:
        raise NaoEncontradoError(f"{rotulo} {id_} não encontrado(a).")
    return obj


def executar_paginado(session: Session, stmt, offset: int, limit: int):
    """COUNT(*) + OFFSET/LIMIT executados pelo banco. retorna (total, itens)."""
    total = session.exec(select(func.count()).select_from(stmt.order_by(None).subquery())).one()
    itens = session.exec(stmt.offset(offset).limit(limit)).all()
    return total, itens


def montar_pagina(total: int, itens, offset: int, limit: int) -> dict:
    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "pagina_atual": offset // limit + 1,
        "total_paginas": ceil(total / limit) if total else 0,
        "itens": itens,
    }


def paginar(session: Session, stmt, offset: int, limit: int) -> dict:
    total, itens = executar_paginado(session, stmt, offset, limit)
    return montar_pagina(total, itens, offset, limit)
