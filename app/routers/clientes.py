from fastapi import APIRouter, Query, Response, status

from app.crud import cliente as cliente_crud
from app.crud import compra as compra_crud
from app.crud import ingresso as ingresso_crud
from app.dependencies import IdPath, PaginacaoDep, SessionDep
from app.schemas.cliente import ClienteCreate, ClienteRead, ClienteUpdate
from app.schemas.common import Pagina
from app.schemas.compra import CompraRead, IngressoDetalhe

router = APIRouter(prefix="/clientes", tags=["Clientes"])


@router.post("", response_model=ClienteRead, status_code=status.HTTP_201_CREATED)
def criar_cliente(dados: ClienteCreate, session: SessionDep):
    return cliente_crud.criar(session, dados)


@router.get("", response_model=Pagina[ClienteRead])
def listar_clientes(
    session: SessionDep,
    pag: PaginacaoDep,
    nome: str | None = Query(None, description="Busca parcial no nome"),
    email: str | None = None,
    ativo: bool | None = None,
):
    return cliente_crud.listar(session, nome=nome, email=email, ativo=ativo, offset=pag.offset, limit=pag.limit)


@router.get("/{cliente_id}", response_model=ClienteRead)
def obter_cliente(cliente_id: IdPath, session: SessionDep):
    return cliente_crud.obter(session, cliente_id)


@router.patch("/{cliente_id}", response_model=ClienteRead)
def atualizar_cliente(cliente_id: IdPath, dados: ClienteUpdate, session: SessionDep):
    return cliente_crud.atualizar(session, cliente_id, dados)


@router.delete("/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_cliente(cliente_id: IdPath, session: SessionDep):
    cliente_crud.excluir(session, cliente_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{cliente_id}/compras", response_model=Pagina[CompraRead], summary="Compras de um cliente (1:N)")
def compras_do_cliente(cliente_id: IdPath, session: SessionDep, pag: PaginacaoDep):
    cliente_crud.obter(session, cliente_id)
    return compra_crud.listar(session, cliente_id=cliente_id, offset=pag.offset, limit=pag.limit)


@router.get("/{cliente_id}/ingressos", response_model=Pagina[IngressoDetalhe],
            summary="Ingressos de um cliente (Cliente → Compra → Ingresso)")
def ingressos_do_cliente(
    cliente_id: IdPath, session: SessionDep, pag: PaginacaoDep, status_ingresso: str | None = Query(None, alias="status"),
):
    cliente_crud.obter(session, cliente_id)
    return ingresso_crud.listar(session, cliente_id=cliente_id, status=status_ingresso, offset=pag.offset, limit=pag.limit)
