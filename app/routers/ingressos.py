from fastapi import APIRouter, Query

from app.crud import ingresso as ingresso_crud
from app.dependencies import IdPath, PaginacaoDep, SessionDep
from app.schemas.common import Pagina
from app.schemas.compra import IngressoDetalhe, TrocaAssento
from app.services import venda_service

router = APIRouter(prefix="/ingressos", tags=["Ingressos"])


@router.get("", response_model=Pagina[IngressoDetalhe], summary="Listar ingressos (paginado e filtrável)")
def listar_ingressos(
    session: SessionDep,
    pag: PaginacaoDep,
    sessao_id: int | None = Query(None, gt=0),
    cliente_id: int | None = Query(None, gt=0),
    compra_id: int | None = Query(None, gt=0),
    status_ingresso: str | None = Query(None, alias="status", description="valido, utilizado ou cancelado"),
):
    return ingresso_crud.listar(
        session, sessao_id=sessao_id, cliente_id=cliente_id, compra_id=compra_id,
        status=status_ingresso, offset=pag.offset, limit=pag.limit,
    )


@router.get("/{ingresso_id}", response_model=IngressoDetalhe)
def obter_ingresso(ingresso_id: IdPath, session: SessionDep):
    return ingresso_crud.obter_detalhado(session, ingresso_id)


@router.patch("/{ingresso_id}", response_model=IngressoDetalhe, summary="Trocar o assento do ingresso")
def trocar_assento(ingresso_id: IdPath, dados: TrocaAssento, session: SessionDep):
    venda_service.trocar_assento(session, ingresso_id, dados.assento_id)
    return ingresso_crud.obter_detalhado(session, ingresso_id)


@router.post("/{ingresso_id}/cancelar", response_model=IngressoDetalhe,
             summary="Cancelar ingresso (libera o assento na sessão)")
def cancelar_ingresso(ingresso_id: IdPath, session: SessionDep):
    venda_service.cancelar_ingresso(session, ingresso_id)
    return ingresso_crud.obter_detalhado(session, ingresso_id)
