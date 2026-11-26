from sqlmodel import Session, select

from app.crud.base import obter_ou_404, paginar
from app.models import Ingresso, Validacao


def obter(session: Session, validacao_id: int) -> Validacao:
    return obter_ou_404(session, Validacao, validacao_id, "Validação")


def listar(
    session: Session,
    *,
    ingresso_id: int | None = None,
    sessao_id: int | None = None,
    operador: str | None = None,
    offset: int = 0,
    limit: int = 10,
) -> dict:
    stmt = select(Validacao).order_by(Validacao.validado_em.desc(), Validacao.id.desc())
    if ingresso_id is not None:
        stmt = stmt.where(Validacao.ingresso_id == ingresso_id)
    if sessao_id is not None:
        stmt = stmt.join(Ingresso, Ingresso.id == Validacao.ingresso_id).where(Ingresso.sessao_id == sessao_id)
    if operador:
        stmt = stmt.where(Validacao.operador.ilike(f"%{operador}%"))
    return paginar(session, stmt, offset, limit)
