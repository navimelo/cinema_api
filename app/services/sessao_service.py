"""Programação de sessões: conflito de sala, reagendamento, cancelamento e mapa de assentos."""
from datetime import datetime, timedelta, timezone 

from sqlalchemy import func
from sqlmodel import Session, select

from app.config import settings
from app.crud.base import obter_ou_404
from app.exceptions import ConflitoError, RegraNegocioError
from app.models import Assento, Filme, Ingresso, Sala, Sessao
from app.models.constantes import StatusIngresso, StatusSessao
from app.schemas.sessao import AssentoDisponibilidade, MapaAssentos, SessaoCreate, SessaoUpdate
from app.services.venda_service import recalcular_compra


def calcular_fim(filme: Filme, inicio: datetime) -> datetime:
    """Fim da ocupação da sala = início + duração do filme + intervalo de limpeza."""
    return inicio + timedelta(minutes=filme.duracao_minutos + settings.INTERVALO_LIMPEZA_MIN)


def _sala_para_agendamento(session: Session, sala_id: int) -> Sala:
    # FOR UPDATE serializa programações simultâneas da mesma sala no PostgreSQL
    # (o SQLite ignora a cláusula, pois já serializa as escritas).
    sala = session.exec(select(Sala).where(Sala.id == sala_id).with_for_update()).first()
    if sala is None:
        obter_ou_404(session, Sala, sala_id, "Sala")  # lança 404
    if not sala.ativa:
        raise RegraNegocioError("Sala inativa não pode receber sessões.")
    return sala


def validar_conflito_sala(
    session: Session, sala_id: int, inicio: datetime, fim: datetime, ignorar_sessao_id: int | None = None
) -> None:
    """Regra: não pode haver duas sessões sobrepostas na mesma sala (intervalos [inicio, fim))."""
    stmt = select(Sessao).where(
        Sessao.sala_id == sala_id,
        Sessao.status != StatusSessao.CANCELADA,
        Sessao.inicio < fim,
        Sessao.fim > inicio,
    )
    if ignorar_sessao_id is not None:
        stmt = stmt.where(Sessao.id != ignorar_sessao_id)
    conflito = session.exec(stmt.limit(1)).first()
    if conflito is not None:
        raise ConflitoError(
            f"Conflito de horário na sala: a sessão {conflito.id} ocupa a sala de "
            f"{conflito.inicio:%d/%m %H:%M} até {conflito.fim:%H:%M} (inclui limpeza)."
        )


def _ingressos_ativos(session: Session, sessao_id: int) -> int:
    return session.exec(
        select(func.count(Ingresso.id)).where(
            Ingresso.sessao_id == sessao_id, Ingresso.status != StatusIngresso.CANCELADO
        )
    ).one()


def criar_sessao(session: Session, dados: SessaoCreate) -> Sessao:
    filme = obter_ou_404(session, Filme, dados.filme_id, "Filme")
    if not filme.em_cartaz:
        raise RegraNegocioError("Filme fora de cartaz não pode ser programado.")
    sala = _sala_para_agendamento(session, dados.sala_id)
    if dados.inicio <= datetime.now(timezone.utc):
        raise RegraNegocioError("A sessão deve ser programada para um horário futuro.")
    fim = calcular_fim(filme, dados.inicio)
    validar_conflito_sala(session, sala.id, dados.inicio, fim)
    sessao = Sessao(
        filme_id=filme.id, sala_id=sala.id, inicio=dados.inicio, fim=fim,
        preco=dados.preco, status=StatusSessao.AGENDADA,
    )
    session.add(sessao)
    session.commit()
    session.refresh(sessao)
    return sessao


def atualizar_sessao(session: Session, sessao_id: int, dados: SessaoUpdate) -> Sessao:
    """Alteração na programação. Preço pode mudar sempre; filme/sala/horário só sem ingressos ativos."""
    sessao = obter_ou_404(session, Sessao, sessao_id, "Sessão")
    if sessao.status != StatusSessao.AGENDADA:
        raise ConflitoError("Sessão cancelada não pode ser alterada.")
    campos = {k: v for k, v in dados.model_dump(exclude_unset=True).items() if v is not None}
    estrutura = {"filme_id", "sala_id", "inicio"} & campos.keys()

    if estrutura:
        if _ingressos_ativos(session, sessao_id) > 0:
            raise ConflitoError(
                "Já existem ingressos vendidos: filme, sala e horário não podem mudar. "
                "Cancele a sessão (os ingressos são cancelados) e programe outra."
            )
        filme = obter_ou_404(session, Filme, campos.get("filme_id", sessao.filme_id), "Filme")
        if not filme.em_cartaz:
            raise RegraNegocioError("Filme fora de cartaz não pode ser programado.")
        sala = _sala_para_agendamento(session, campos.get("sala_id", sessao.sala_id))
        inicio = campos.get("inicio", sessao.inicio)
        if inicio <= datetime.now(timezone.utc):
            raise RegraNegocioError("A sessão deve ser programada para um horário futuro.")
        fim = calcular_fim(filme, inicio)
        validar_conflito_sala(session, sala.id, inicio, fim, ignorar_sessao_id=sessao.id)
        sessao.filme_id, sessao.sala_id, sessao.inicio, sessao.fim = filme.id, sala.id, inicio, fim

    if "preco" in campos:
        sessao.preco = campos["preco"]
    session.commit()
    session.refresh(sessao)
    return sessao


def cancelar_sessao(session: Session, sessao_id: int) -> tuple[Sessao, int]:
    """Cancela a sessão e todos os seus ingressos válidos (assentos liberados, compras recalculadas)."""
    sessao = obter_ou_404(session, Sessao, sessao_id, "Sessão")
    if sessao.status == StatusSessao.CANCELADA:
        raise ConflitoError("A sessão já está cancelada.")
    if sessao.inicio <= datetime.now(timezone.utc):
        raise RegraNegocioError("Sessão em andamento ou já realizada não pode ser cancelada.")
    ingressos = session.exec(
        select(Ingresso).where(Ingresso.sessao_id == sessao_id, Ingresso.status == StatusIngresso.VALIDO)
    ).all()
    agora = datetime.now(timezone.utc)
    compras = {}
    for ingresso in ingressos:
        ingresso.status = StatusIngresso.CANCELADO
        ingresso.cancelado_em = agora
        compras[ingresso.compra_id] = ingresso.compra
    session.flush()
    for compra in compras.values():
        recalcular_compra(compra)
    sessao.status = StatusSessao.CANCELADA
    session.commit()
    session.refresh(sessao)
    return sessao, len(ingressos)


def mapa_assentos(session: Session, sessao_id: int, somente_disponiveis: bool | None = None) -> MapaAssentos:
    """F17 — assentos da sala da sessão, indicando quais estão livres/ocupados NAQUELA sessão."""
    sessao = obter_ou_404(session, Sessao, sessao_id, "Sessão")
    ocupados_ids = select(Ingresso.assento_id).where(
        Ingresso.sessao_id == sessao_id, Ingresso.status != StatusIngresso.CANCELADO
    )
    stmt = (
        select(Assento, Assento.id.in_(ocupados_ids).label("ocupado"))
        .where(Assento.sala_id == sessao.sala_id)
        .order_by(Assento.fileira, Assento.numero)
    )
    linhas = session.exec(stmt).all()
    assentos = [
        AssentoDisponibilidade(
            id=a.id, sala_id=a.sala_id, fileira=a.fileira, numero=a.numero, disponivel=not ocupado
        )
        for a, ocupado in linhas
    ]
    total_ocupados = sum(1 for a in assentos if not a.disponivel)
    if somente_disponiveis is True:
        assentos = [a for a in assentos if a.disponivel]
    elif somente_disponiveis is False:
        assentos = [a for a in assentos if not a.disponivel]
    return MapaAssentos(
        sessao_id=sessao_id,
        capacidade=len(linhas),
        ocupados=total_ocupados,
        disponiveis=len(linhas) - total_ocupados,
        assentos=assentos,
    )
