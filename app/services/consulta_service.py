"""Consultas complexas (F11): JOINs, agrupamento, agregação, intervalos de datas e ordenação."""
from datetime import date

from sqlalchemy import and_, desc, func
from sqlmodel import Session, select

from app.crud.base import executar_paginado, montar_pagina
from app.crud.sessao import fim_do_dia_exclusivo, inicio_do_dia
from app.exceptions import RegraNegocioError
from app.models import Filme, Ingresso, Sala, Sessao
from app.models.constantes import StatusIngresso, StatusSessao

ATIVO = Ingresso.status != StatusIngresso.CANCELADO


def _validar_periodo(inicio: date | None, fim: date | None) -> None:
    if inicio and fim and fim < inicio:
        raise RegraNegocioError("A data final não pode ser anterior à data inicial.")


def filmes_mais_vistos(session: Session, inicio: date | None, fim: date | None, limite: int) -> list[dict]:
    """Ranking de público: JOIN Filme-Sessao-Ingresso, GROUP BY filme, COUNT/SUM, ORDER BY público."""
    _validar_periodo(inicio, fim)
    publico = func.count(Ingresso.id)
    stmt = (
        select(
            Filme.id.label("filme_id"),
            Filme.titulo.label("titulo"),
            publico.label("ingressos"),
            func.coalesce(func.sum(Ingresso.valor), 0).label("receita"),
        )
        .select_from(Filme)
        .join(Sessao, Sessao.filme_id == Filme.id)
        .join(Ingresso, Ingresso.sessao_id == Sessao.id)
        .where(ATIVO)
        .group_by(Filme.id, Filme.titulo)
        .order_by(desc(publico), Filme.titulo)
        .limit(limite)
    )
    if inicio:
        stmt = stmt.where(Sessao.inicio >= inicio_do_dia(inicio))
    if fim:
        stmt = stmt.where(Sessao.inicio < fim_do_dia_exclusivo(fim))
    return [
        {
            "filme_id": r.filme_id,
            "titulo": r.titulo,
            "ingressos_vendidos": int(r.ingressos),
            "receita": round(float(r.receita), 2),
        }
        for r in session.exec(stmt).all()
    ]


def ocupacao_sessoes(
    session: Session,
    *,
    data: date | None,
    sala_id: int | None,
    filme_id: int | None,
    offset: int,
    limit: int,
) -> dict:
    """Ocupação por sessão: LEFT JOIN com ingressos ativos, COUNT por sessão e % sobre a capacidade."""
    vendidos = func.count(Ingresso.id)
    stmt = (
        select(
            Sessao.id.label("sessao_id"),
            Filme.titulo.label("filme"),
            Sala.nome.label("sala"),
            Sessao.inicio.label("inicio"),
            Sala.capacidade.label("capacidade"),
            vendidos.label("vendidos"),
        )
        .select_from(Sessao)
        .join(Filme, Filme.id == Sessao.filme_id)
        .join(Sala, Sala.id == Sessao.sala_id)
        .outerjoin(Ingresso, and_(Ingresso.sessao_id == Sessao.id, ATIVO))
        .where(Sessao.status != StatusSessao.CANCELADA)
        .group_by(Sessao.id, Filme.titulo, Sala.nome, Sessao.inicio, Sala.capacidade)
        .order_by(Sessao.inicio, Sessao.id)
    )
    if data:
        stmt = stmt.where(Sessao.inicio >= inicio_do_dia(data), Sessao.inicio < fim_do_dia_exclusivo(data))
    if sala_id is not None:
        stmt = stmt.where(Sessao.sala_id == sala_id)
    if filme_id is not None:
        stmt = stmt.where(Sessao.filme_id == filme_id)
    total, linhas = executar_paginado(session, stmt, offset, limit)
    itens = [
        {
            "sessao_id": r.sessao_id,
            "filme": r.filme,
            "sala": r.sala,
            "inicio": r.inicio,
            "capacidade": r.capacidade,
            "vendidos": int(r.vendidos),
            "disponiveis": r.capacidade - int(r.vendidos),
            "ocupacao_percentual": round(int(r.vendidos) * 100 / r.capacidade, 1),
        }
        for r in linhas
    ]
    return montar_pagina(total, itens, offset, limit)


def vendas_por_dia(session: Session, inicio: date, fim: date) -> list[dict]:
    """Vendas em um período: agrupamento por dia da venda com COUNT e SUM."""
    _validar_periodo(inicio, fim)
    dia = func.date(Ingresso.criado_em)
    stmt = (
        select(dia.label("dia"), func.count(Ingresso.id).label("ingressos"), func.sum(Ingresso.valor).label("receita"))
        .where(
            ATIVO,
            Ingresso.criado_em >= inicio_do_dia(inicio),
            Ingresso.criado_em < fim_do_dia_exclusivo(fim),
        )
        .group_by(dia)
        .order_by(dia)
    )
    return [
        {"dia": str(r.dia), "ingressos": int(r.ingressos), "receita": round(float(r.receita or 0), 2)}
        for r in session.exec(stmt).all()
    ]


def sessoes_sem_vendas(session: Session, offset: int, limit: int) -> dict:
    """Entidades SEM determinado relacionamento: sessões agendadas sem nenhum ingresso ativo (NOT EXISTS)."""
    from sqlalchemy.orm import joinedload

    stmt = (
        select(Sessao)
        .options(joinedload(Sessao.filme), joinedload(Sessao.sala))
        .where(Sessao.status == StatusSessao.AGENDADA, ~Sessao.ingressos.any(ATIVO))
        .order_by(Sessao.inicio, Sessao.id)
    )
    total, itens = executar_paginado(session, stmt, offset, limit)
    return montar_pagina(total, itens, offset, limit)
