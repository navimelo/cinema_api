from sqlalchemy import func
from sqlmodel import Session, select

from app.crud.base import obter_ou_404, paginar
from app.exceptions import ConflitoError
from app.models import Assento, Sala, Sessao
from app.schemas.sala import SalaCreate, SalaUpdate


def _nome_existe(session: Session, nome: str, ignorar_id: int | None = None) -> bool:
    stmt = select(Sala.id).where(func.lower(Sala.nome) == nome.lower())
    if ignorar_id is not None:
        stmt = stmt.where(Sala.id != ignorar_id)
    return session.exec(stmt.limit(1)).first() is not None


def obter(session: Session, sala_id: int) -> Sala:
    return obter_ou_404(session, Sala, sala_id, "Sala")


def listar(
    session: Session,
    *,
    nome: str | None = None,
    tipo: str | None = None,
    ativa: bool | None = None,
    capacidade_minima: int | None = None,
    offset: int = 0,
    limit: int = 10,
) -> dict:
    stmt = select(Sala).order_by(Sala.nome)
    if nome:
        stmt = stmt.where(Sala.nome.ilike(f"%{nome}%"))
    if tipo:
        stmt = stmt.where(Sala.tipo == tipo)
    if ativa is not None:
        stmt = stmt.where(Sala.ativa == ativa)
    if capacidade_minima is not None:
        stmt = stmt.where(Sala.capacidade >= capacidade_minima)
    return paginar(session, stmt, offset, limit)


def criar(session: Session, dados: SalaCreate) -> Sala:
    """Cria a sala e gera automaticamente o mapa de assentos (A1, A2, ... B1, ...)."""
    if _nome_existe(session, dados.nome):
        raise ConflitoError(f"Já existe uma sala chamada '{dados.nome}'.")
    sala = Sala(nome=dados.nome, tipo=dados.tipo, capacidade=dados.fileiras * dados.assentos_por_fileira)
    sala.assentos = [
        Assento(fileira=chr(ord("A") + f), numero=n)
        for f in range(dados.fileiras)
        for n in range(1, dados.assentos_por_fileira + 1)
    ]
    session.add(sala)
    session.commit()
    session.refresh(sala)
    return sala


def atualizar(session: Session, sala_id: int, dados: SalaUpdate) -> Sala:
    sala = obter(session, sala_id)
    campos = {k: v for k, v in dados.model_dump(exclude_unset=True).items() if v is not None}
    if "nome" in campos and _nome_existe(session, campos["nome"], ignorar_id=sala_id):
        raise ConflitoError(f"Já existe uma sala chamada '{campos['nome']}'.")
    if campos.get("ativa") is False:
        agendada = session.exec(
            select(Sessao.id).where(Sessao.sala_id == sala_id, Sessao.status == "agendada").limit(1)
        ).first()
        if agendada is not None:
            raise ConflitoError("A sala possui sessões agendadas e não pode ser desativada.")
    for campo, valor in campos.items():
        setattr(sala, campo, valor)
    session.commit()
    session.refresh(sala)
    return sala


def excluir(session: Session, sala_id: int) -> None:
    sala = obter(session, sala_id)
    tem_sessoes = session.exec(select(Sessao.id).where(Sessao.sala_id == sala_id).limit(1)).first()
    if tem_sessoes is not None:
        raise ConflitoError("A sala possui sessões (histórico); desative-a em vez de excluir.")
    session.delete(sala)  # cascade remove os assentos
    session.commit()


def listar_assentos(session: Session, sala_id: int) -> list[Assento]:
    obter(session, sala_id)
    return list(
        session.exec(select(Assento).where(Assento.sala_id == sala_id).order_by(Assento.fileira, Assento.numero)).all()
    )
