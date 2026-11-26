from datetime import date

from fastapi import APIRouter, Query, status

from app.crud import compra as compra_crud
from app.dependencies import IdPath, PaginacaoDep, SessionDep
from app.schemas.common import Pagina
from app.schemas.compra import CompraCreate, CompraRead
from app.services import venda_service

router = APIRouter(prefix="/compras", tags=["Compras (venda de ingressos)"])


@router.post("", response_model=CompraRead, status_code=status.HTTP_201_CREATED,
             summary="Comprar ingressos (vários assentos de uma sessão)")
def comprar(dados: CompraCreate, session: SessionDep):
    compra = venda_service.comprar_ingressos(session, dados)
    return compra_crud.obter_detalhada(session, compra.id)


@router.get("", response_model=Pagina[CompraRead])
def listar_compras(
    session: SessionDep,
    pag: PaginacaoDep,
    cliente_id: int | None = Query(None, gt=0),
    status_compra: str | None = Query(None, alias="status", description="concluida ou cancelada"),
    data_inicial: date | None = None,
    data_final: date | None = None,
):
    return compra_crud.listar(
        session, cliente_id=cliente_id, status=status_compra,
        data_inicial=data_inicial, data_final=data_final, offset=pag.offset, limit=pag.limit,
    )


@router.get("/{compra_id}", response_model=CompraRead)
def obter_compra(compra_id: IdPath, session: SessionDep):
    return compra_crud.obter_detalhada(session, compra_id)


@router.post("/{compra_id}/cancelar", response_model=CompraRead, summary="Cancelar compra inteira")
def cancelar_compra(compra_id: IdPath, session: SessionDep):
    venda_service.cancelar_compra(session, compra_id)
    return compra_crud.obter_detalhada(session, compra_id)
