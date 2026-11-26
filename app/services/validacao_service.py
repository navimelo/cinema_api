"""Validação (leitura) do ingresso na entrada da sala."""
from datetime import datetime, timedelta

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from app.config import settings
from app.crud.base import obter_ou_404
from app.exceptions import ConflitoError, RegraNegocioError
from app.models import Ingresso, Validacao
from app.models.constantes import StatusIngresso, StatusSessao
from app.schemas.validacao import ValidacaoCreate


def validar_ingresso(session: Session, dados: ValidacaoCreate) -> Validacao:
    ingresso = obter_ou_404(session, Ingresso, dados.ingresso_id, "Ingresso")
    if ingresso.status == StatusIngresso.CANCELADO:
        raise ConflitoError("Ingresso cancelado não pode ser validado.")
    if ingresso.status == StatusIngresso.UTILIZADO or ingresso.validacao is not None:
        raise ConflitoError("Este ingresso já foi validado anteriormente.")

    sessao = ingresso.sessao
    if sessao.status != StatusSessao.AGENDADA:
        raise ConflitoError("A sessão deste ingresso foi cancelada.")
    agora = datetime.now()
    abertura = sessao.inicio - timedelta(minutes=settings.VALIDACAO_ANTECEDENCIA_MIN)
    if agora < abertura:
        raise RegraNegocioError(
            f"A entrada abre {settings.VALIDACAO_ANTECEDENCIA_MIN} minutos antes da sessão ({abertura:%d/%m %H:%M})."
        )
    if agora > sessao.fim:
        raise RegraNegocioError("A sessão deste ingresso já terminou.")

    validacao = Validacao(ingresso_id=ingresso.id, operador=dados.operador, validado_em=agora)
    ingresso.status = StatusIngresso.UTILIZADO
    session.add(validacao)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise ConflitoError("Este ingresso já foi validado anteriormente.")
    session.refresh(validacao)
    return validacao
