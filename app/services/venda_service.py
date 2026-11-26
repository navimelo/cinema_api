from datetime import date, datetime, timedelta, timezone

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.config import settings
from app.crud.base import obter_ou_404
from app.exceptions import ConflitoError, RegraNegocioError
from app.models import Assento, Cliente, Compra, Ingresso, Sessao
from app.models.constantes import StatusCompra, StatusIngresso, StatusSessao
from app.schemas.compra import CompraCreate


def _idade(nascimento: date, hoje: date) -> int:
    return hoje.year - nascimento.year - ((hoje.month, hoje.day) < (nascimento.month, nascimento.day))


def _idade_minima(classificacao: str) -> int:
    return 0 if classificacao == "L" else int(classificacao)


def recalcular_compra(compra: Compra) -> None:
    """Atualiza valor_total e status da compra conforme os ingressos ainda ativos."""
    ativos = [i for i in compra.ingressos if i.status != StatusIngresso.CANCELADO]
    compra.valor_total = round(sum(i.valor for i in ativos), 2)
    compra.status = StatusCompra.CONCLUIDA if ativos else StatusCompra.CANCELADA


def _ids_ocupados(session: Session, sessao_id: int, assentos_ids: list[int]) -> set[int]:
    stmt = select(Ingresso.assento_id).where(
        Ingresso.sessao_id == sessao_id,
        Ingresso.assento_id.in_(assentos_ids),
        Ingresso.status != StatusIngresso.CANCELADO,
    )
    return set(session.exec(stmt).all())


def _codigos(assentos: list[Assento]) -> str:
    return ", ".join(f"{a.fileira}{a.numero}" for a in sorted(assentos, key=lambda x: (x.fileira, x.numero)))


def comprar_ingressos(session: Session, dados: CompraCreate) -> Compra:
    cliente = obter_ou_404(session, Cliente, dados.cliente_id, "Cliente")
    if not cliente.ativo:
        raise RegraNegocioError("Cliente inativo não pode realizar compras.")

    sessao = obter_ou_404(session, Sessao, dados.sessao_id, "Sessão")
    if sessao.status != StatusSessao.AGENDADA:
        raise RegraNegocioError("A sessão está cancelada e não aceita vendas.")
    agora = datetime.now(timezone.utc)
    if sessao.inicio <= agora:
        raise RegraNegocioError("A sessão já começou; não é possível vender ingressos.")


    minima = _idade_minima(sessao.filme.classificacao_indicativa)
    if _idade(cliente.data_nascimento, agora.date()) < minima:
        raise RegraNegocioError(
            f"Classificação {sessao.filme.classificacao_indicativa}: o cliente não atinge a idade mínima ({minima} anos)."
        )

    ids = dados.assentos_ids
    if len(ids) > settings.MAX_INGRESSOS_POR_COMPRA:
        raise RegraNegocioError(f"Limite de {settings.MAX_INGRESSOS_POR_COMPRA} ingressos por compra excedido.")
    if len(set(ids)) != len(ids):
        raise RegraNegocioError("A lista de assentos contém itens repetidos.")

    assentos = list(session.exec(select(Assento).where(Assento.id.in_(ids))).all())
    inexistentes = set(ids) - {a.id for a in assentos}
    if inexistentes:
        raise RegraNegocioError(f"Assento(s) inexistente(s): {sorted(inexistentes)}.")
   
    de_outra_sala = [a for a in assentos if a.sala_id != sessao.sala_id]
    if de_outra_sala:
        raise RegraNegocioError(f"Assento(s) {_codigos(de_outra_sala)} não pertencem à sala desta sessão.")

    
    ocupados = _ids_ocupados(session, sessao.id, ids)
    if ocupados:
        raise ConflitoError(
            f"Assento(s) já vendido(s) nesta sessão: {_codigos([a for a in assentos if a.id in ocupados])}."
        )

    compra = Compra(cliente_id=cliente.id, valor_total=round(sessao.preco * len(assentos), 2))
    compra.ingressos = [
        Ingresso(sessao_id=sessao.id, assento_id=a.id, valor=sessao.preco) for a in assentos
    ]
    session.add(compra)
    try:
        session.commit()
    except IntegrityError:
        
        session.rollback()
        raise ConflitoError("Um dos assentos acabou de ser vendido para outro cliente. Escolha outros lugares.")
    session.refresh(compra)
    return compra


def _checar_prazo_cancelamento(sessao: Sessao) -> None:
    limite = sessao.inicio - timedelta(minutes=settings.CANCELAMENTO_ANTECEDENCIA_MIN)
    if datetime.now() > limite:
        raise RegraNegocioError(
            f"Cancelamento permitido somente até {settings.CANCELAMENTO_ANTECEDENCIA_MIN} minutos antes da sessão."
        )


def cancelar_ingresso(session: Session, ingresso_id: int) -> Ingresso:
    """Cancela um ingresso válido; o assento volta a ficar disponível para a sessão."""
    ingresso = obter_ou_404(session, Ingresso, ingresso_id, "Ingresso")
    if ingresso.status == StatusIngresso.CANCELADO:
        raise ConflitoError("O ingresso já está cancelado.")
    if ingresso.status == StatusIngresso.UTILIZADO:
        raise ConflitoError("O ingresso já foi utilizado e não pode ser cancelado.")
    _checar_prazo_cancelamento(ingresso.sessao)
    ingresso.status = StatusIngresso.CANCELADO
    ingresso.cancelado_em = datetime.now(timezone.utc)
    session.flush()
    recalcular_compra(ingresso.compra)
    session.commit()
    session.refresh(ingresso)
    return ingresso


def cancelar_compra(session: Session, compra_id: int) -> Compra:
    """Cancela todos os ingressos válidos de uma compra (tudo ou nada)."""
    compra = obter_ou_404(session, Compra, compra_id, "Compra")
    if compra.status == StatusCompra.CANCELADA:
        raise ConflitoError("A compra já está cancelada.")
    validos = [i for i in compra.ingressos if i.status == StatusIngresso.VALIDO]
    if any(i.status == StatusIngresso.UTILIZADO for i in compra.ingressos):
        raise ConflitoError("A compra possui ingressos já utilizados e não pode ser cancelada por inteiro.")
    for ingresso in validos:
        _checar_prazo_cancelamento(ingresso.sessao)
    agora = datetime.now(timezone.utc)
    for ingresso in validos:
        ingresso.status = StatusIngresso.CANCELADO
        ingresso.cancelado_em = agora
    session.flush()
    recalcular_compra(compra)
    session.commit()
    session.refresh(compra)
    return compra


def trocar_assento(session: Session, ingresso_id: int, novo_assento_id: int) -> Ingresso:
    
    ingresso = obter_ou_404(session, Ingresso, ingresso_id, "Ingresso")
    if ingresso.status != StatusIngresso.VALIDO:
        raise ConflitoError("Somente ingressos válidos podem ter o assento trocado.")
    sessao = ingresso.sessao
    if sessao.status != StatusSessao.AGENDADA or sessao.inicio <= datetime.now(timezone.utc):
        raise RegraNegocioError("A troca só é possível antes do início de uma sessão agendada.")
    assento = obter_ou_404(session, Assento, novo_assento_id, "Assento")
    if assento.sala_id != sessao.sala_id:
        raise RegraNegocioError("O novo assento não pertence à sala desta sessão.")
    if assento.id == ingresso.assento_id:
        raise RegraNegocioError("O ingresso já está neste assento.")
    if _ids_ocupados(session, sessao.id, [assento.id]):
        raise ConflitoError(f"O assento {assento.fileira}{assento.numero} já está vendido nesta sessão.")
    ingresso.assento_id = assento.id
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise ConflitoError("O assento acabou de ser vendido para outro cliente.")
    session.refresh(ingresso)
    return ingresso
