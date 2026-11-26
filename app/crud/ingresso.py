from sqlmodel import Session, select

from app.crud.base import obter_ou_404, paginar
from app.crud.compra import opcoes_ingresso_detalhe
from app.exceptions import NaoEncontradoError
from app.models import Compra, Ingresso


def obter(session: Session, ingresso_id: int) -> Ingresso:
    return obter_ou_404(session, Ingresso, ingresso_id, "Ingresso")


def obter_detalhado(session: Session, ingresso_id: int) -> Ingresso:
    stmt = select(Ingresso).where(Ingresso.id == ingresso_id).options(*opcoes_ingresso_detalhe())
    ingresso = session.exec(stmt).first()
    if ingresso is None:
        raise NaoEncontradoError(f"Ingresso {ingresso_id} não encontrado(a).")
    return ingresso


def listar(
    session: Session,
    *,
    sessao_id: int | None = None,
    cliente_id: int | None = None,
    compra_id: int | None = None,
    status: str | None = None,
    offset: int = 0,
    limit: int = 10,
) -> dict:
    """Filtros combináveis; o filtro por cliente usa JOIN com Compra (F9/F10)."""
    stmt = (
        select(Ingresso)
        .join(Compra, Compra.id == Ingresso.compra_id)
        .options(*opcoes_ingresso_detalhe())
        .order_by(Ingresso.criado_em.desc(), Ingresso.id.desc())
    )
    if sessao_id is not None:
        stmt = stmt.where(Ingresso.sessao_id == sessao_id)
    if cliente_id is not None:
        stmt = stmt.where(Compra.cliente_id == cliente_id)
    if compra_id is not None:
        stmt = stmt.where(Ingresso.compra_id == compra_id)
    if status:
        stmt = stmt.where(Ingresso.status == status)
    return paginar(session, stmt, offset, limit)
