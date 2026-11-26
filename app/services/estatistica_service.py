"""F12 — Estatísticas e agregações calculadas pelo banco (COUNT, SUM, AVG, GROUP BY)."""
from sqlalchemy import and_, desc, func
from sqlmodel import Session, select

from app.models import Cliente, Compra, Filme, FilmeGenero, Genero, Ingresso, Sala, Sessao
from app.models.constantes import StatusSessao
from app.services.consulta_service import ATIVO, filmes_mais_vistos


def _contar(session: Session, coluna) -> int:
    return int(session.exec(select(func.count(coluna))).one())


def calcular(session: Session) -> dict:
    por_status = {
        status: int(qtd)
        for status, qtd in session.exec(
            select(Ingresso.status, func.count(Ingresso.id)).group_by(Ingresso.status)
        ).all()
    }
    receita, ticket = session.exec(
        select(func.coalesce(func.sum(Ingresso.valor), 0), func.coalesce(func.avg(Ingresso.valor), 0)).where(ATIVO)
    ).one()

    # Ocupação média = ingressos ativos / capacidade total das sessões não canceladas.
    capacidade_total = session.exec(
        select(func.coalesce(func.sum(Sala.capacidade), 0))
        .select_from(Sessao)
        .join(Sala, Sala.id == Sessao.sala_id)
        .where(Sessao.status != StatusSessao.CANCELADA)
    ).one()
    vendidos = session.exec(
        select(func.count(Ingresso.id))
        .select_from(Ingresso)
        .join(Sessao, Sessao.id == Ingresso.sessao_id)
        .where(ATIVO, Sessao.status != StatusSessao.CANCELADA)
    ).one()

    qtd_ingressos = func.count(Ingresso.id)
    por_sala = session.exec(
        select(Sala.nome, qtd_ingressos)
        .select_from(Sala)
        .outerjoin(Sessao, Sessao.sala_id == Sala.id)
        .outerjoin(Ingresso, and_(Ingresso.sessao_id == Sessao.id, ATIVO))
        .group_by(Sala.id, Sala.nome)
        .order_by(desc(qtd_ingressos), Sala.nome)
    ).all()
    por_classificacao = session.exec(
        select(Filme.classificacao_indicativa, qtd_ingressos)
        .select_from(Filme)
        .join(Sessao, Sessao.filme_id == Filme.id)
        .join(Ingresso, and_(Ingresso.sessao_id == Sessao.id, ATIVO))
        .group_by(Filme.classificacao_indicativa)
        .order_by(Filme.classificacao_indicativa)
    ).all()
    qtd_filmes = func.count(FilmeGenero.filme_id)
    por_genero = session.exec(
        select(Genero.nome, qtd_filmes)
        .select_from(Genero)
        .outerjoin(FilmeGenero, FilmeGenero.genero_id == Genero.id)
        .group_by(Genero.id, Genero.nome)
        .order_by(desc(qtd_filmes), Genero.nome)
    ).all()

    return {
        "total_filmes": _contar(session, Filme.id),
        "total_salas": _contar(session, Sala.id),
        "total_sessoes": _contar(session, Sessao.id),
        "total_clientes": _contar(session, Cliente.id),
        "total_compras": _contar(session, Compra.id),
        "ingressos_por_status": por_status,
        "receita_total": round(float(receita), 2),
        "ticket_medio": round(float(ticket), 2),
        "ocupacao_media_percentual": round(int(vendidos) * 100 / capacidade_total, 1) if capacidade_total else 0.0,
        "ingressos_por_sala": [{"rotulo": n, "quantidade": int(q)} for n, q in por_sala],
        "ingressos_por_classificacao": [{"rotulo": c, "quantidade": int(q)} for c, q in por_classificacao],
        "filmes_por_genero": [{"rotulo": n, "quantidade": int(q)} for n, q in por_genero],
        "filmes_mais_vistos": filmes_mais_vistos(session, None, None, 5),
    }
