from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy.orm import joinedload
from sqlmodel import Session, select

from app.crud.base import obter_ou_404, paginar
from app.exceptions import ConflitoError
from app.models import Ingresso, Sessao


def obter(session: Session, sessao_id: int) -> Sessao:
    return obter_ou_404(session, Sessao, sessao_id, "Sessão")


def inicio_do_dia(d: date) -> datetime:
    return datetime.combine(
        d,
        time.min,
        tzinfo=timezone.utc
    )

def fim_do_dia_exclusivo(d: date) -> datetime:
    return datetime.combine(
        d + timedelta(days=1),
        time.min,
        tzinfo=timezone.utc
    )

def listar(
    session: Session,
    *,
    filme_id: int | None = None,
    sala_id: int | None = None,
    status: str | None = None,
    data_inicial: date | None = None,
    data_final: date | None = None,
    offset: int = 0,
    limit: int = 10,
) -> dict:
    stmt = (
        select(Sessao)
        .options(joinedload(Sessao.filme), joinedload(Sessao.sala))
        .order_by(Sessao.inicio, Sessao.id)
    )
    if filme_id is not None:
        stmt = stmt.where(Sessao.filme_id == filme_id)
    if sala_id is not None:
        stmt = stmt.where(Sessao.sala_id == sala_id)
    if status:
        stmt = stmt.where(Sessao.status == status)
    if data_inicial:
        stmt = stmt.where(Sessao.inicio >= inicio_do_dia(data_inicial))
    if data_final:
        stmt = stmt.where(Sessao.inicio < fim_do_dia_exclusivo(data_final))
    return paginar(session, stmt, offset, limit)


def excluir(session: Session, sessao_id: int) -> None:
    sessao = obter(session, sessao_id)
    tem_ingressos = session.exec(select(Ingresso.id).where(Ingresso.sessao_id == sessao_id).limit(1)).first()
    if tem_ingressos is not None:
        raise ConflitoError("A sessão possui ingressos registrados; use o cancelamento da sessão.")
    session.delete(sessao)
    session.commit()
