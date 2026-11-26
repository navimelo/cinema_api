from datetime import date

from fastapi import APIRouter, Query, Response, status

from app.crud import ingresso as ingresso_crud
from app.crud import sessao as sessao_crud
from app.dependencies import IdPath, PaginacaoDep, SessionDep
from app.schemas.common import Pagina
from app.schemas.compra import IngressoDetalhe
from app.schemas.sessao import (
    MapaAssentos, SessaoCancelada, SessaoCreate, SessaoDetalhe, SessaoUpdate,
)
from app.services import sessao_service

router = APIRouter(prefix="/sessoes", tags=["Sessões"])


@router.post("", response_model=SessaoDetalhe, status_code=status.HTTP_201_CREATED,
             summary="Programar sessão (valida conflito de sala)")
def criar_sessao(dados: SessaoCreate, session: SessionDep):
    return sessao_service.criar_sessao(session, dados)


@router.get("", response_model=Pagina[SessaoDetalhe], summary="Listar sessões (paginado e filtrável)")
def listar_sessoes(
    session: SessionDep,
    pag: PaginacaoDep,
    filme_id: int | None = Query(None, gt=0),
    sala_id: int | None = Query(None, gt=0),
    status_sessao: str | None = Query(None, alias="status", description="agendada ou cancelada"),
    data_inicial: date | None = None,
    data_final: date | None = None,
):
    return sessao_crud.listar(
        session, filme_id=filme_id, sala_id=sala_id, status=status_sessao,
        data_inicial=data_inicial, data_final=data_final, offset=pag.offset, limit=pag.limit,
    )


@router.get("/{sessao_id}", response_model=SessaoDetalhe)
def obter_sessao(sessao_id: IdPath, session: SessionDep):
    return sessao_crud.obter(session, sessao_id)


@router.patch("/{sessao_id}", response_model=SessaoDetalhe, summary="Alterar programação da sessão")
def atualizar_sessao(sessao_id: IdPath, dados: SessaoUpdate, session: SessionDep):
    return sessao_service.atualizar_sessao(session, sessao_id, dados)


@router.post("/{sessao_id}/cancelar", response_model=SessaoCancelada, summary="Cancelar sessão e seus ingressos")
def cancelar_sessao(sessao_id: IdPath, session: SessionDep):
    sessao, qtd = sessao_service.cancelar_sessao(session, sessao_id)
    return {"sessao": sessao, "ingressos_cancelados": qtd}


@router.delete("/{sessao_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_sessao(sessao_id: IdPath, session: SessionDep):
    sessao_crud.excluir(session, sessao_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{sessao_id}/assentos", response_model=MapaAssentos,
            summary="Mapa de assentos da sessão (livres/ocupados)")
def mapa_de_assentos(
    sessao_id: IdPath,
    session: SessionDep,
    disponiveis: bool | None = Query(None, description="true = só livres; false = só ocupados"),
):
    return sessao_service.mapa_assentos(session, sessao_id, disponiveis)


@router.get("/{sessao_id}/ingressos", response_model=Pagina[IngressoDetalhe], summary="Ingressos de uma sessão")
def ingressos_da_sessao(
    sessao_id: IdPath, session: SessionDep, pag: PaginacaoDep, status_ingresso: str | None = Query(None, alias="status"),
):
    sessao_crud.obter(session, sessao_id)
    return ingresso_crud.listar(session, sessao_id=sessao_id, status=status_ingresso, offset=pag.offset, limit=pag.limit)
