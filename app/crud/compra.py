from datetime import date

from sqlalchemy.orm import joinedload, selectinload
from sqlmodel import Session, select

from app.crud.base import obter_ou_404, paginar
from app.crud.sessao import fim_do_dia_exclusivo, inicio_do_dia
from app.models import Compra, Ingresso, Sessao


def opcoes_ingresso_detalhe():
    """Eager loading dos dados exibidos em IngressoDetalhe (evita N+1)."""
    return (
        joinedload(Ingresso.assento),
        joinedload(Ingresso.sessao).joinedload(Sessao.filme),
        joinedload(Ingresso.sessao).joinedload(Sessao.sala),
    )


def obter(session: Session, compra_id: int) -> Compra:
    compra = obter_ou_404(session, Compra, compra_id, "Compra")
    return compra


def obter_detalhada(session: Session, compra_id: int) -> Compra:
    stmt = (
        select(Compra)
        .where(Compra.id == compra_id)
        .options(selectinload(Compra.ingressos).options(*opcoes_ingresso_detalhe()))
    )
    compra = session.exec(stmt).first()
    if compra is None:
        obter_ou_404(session, Compra, compra_id, "Compra")  # lança 404
    return compra


def listar(
    session: Session,
    *,
    cliente_id: int | None = None,
    status: str | None = None,
    data_inicial: date | None = None,
    data_final: date | None = None,
    offset: int = 0,
    limit: int = 10,
) -> dict:
    stmt = (
        select(Compra)
        .options(selectinload(Compra.ingressos).options(*opcoes_ingresso_detalhe()))
        .order_by(Compra.data_compra.desc(), Compra.id.desc())
    )
    if cliente_id is not None:
        stmt = stmt.where(Compra.cliente_id == cliente_id)
    if status:
        stmt = stmt.where(Compra.status == status)
    if data_inicial:
        stmt = stmt.where(Compra.data_compra >= inicio_do_dia(data_inicial))
    if data_final:
        stmt = stmt.where(Compra.data_compra < fim_do_dia_exclusivo(data_final))
    return paginar(session, stmt, offset, limit)
