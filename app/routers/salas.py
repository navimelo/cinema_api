from fastapi import APIRouter, Query, Response, status

from app.crud import sala as sala_crud
from app.crud import sessao as sessao_crud
from app.dependencies import IdPath, PaginacaoDep, SessionDep
from app.schemas.common import Pagina
from app.schemas.sala import AssentoRead, SalaCreate, SalaRead, SalaUpdate
from app.schemas.sessao import SessaoDetalhe

router = APIRouter(prefix="/salas", tags=["Salas e Assentos"])


@router.post("", response_model=SalaRead, status_code=status.HTTP_201_CREATED,
             summary="Criar sala (gera os assentos automaticamente)")
def criar_sala(dados: SalaCreate, session: SessionDep):
    return sala_crud.criar(session, dados)


@router.get("", response_model=Pagina[SalaRead])
def listar_salas(
    session: SessionDep,
    pag: PaginacaoDep,
    nome: str | None = None,
    tipo: str | None = Query(None, description="2D, 3D, IMAX ou VIP"),
    ativa: bool | None = None,
    capacidade_minima: int | None = Query(None, gt=0),
):
    return sala_crud.listar(
        session, nome=nome, tipo=tipo, ativa=ativa, capacidade_minima=capacidade_minima,
        offset=pag.offset, limit=pag.limit,
    )


@router.get("/{sala_id}", response_model=SalaRead)
def obter_sala(sala_id: IdPath, session: SessionDep):
    return sala_crud.obter(session, sala_id)


@router.patch("/{sala_id}", response_model=SalaRead)
def atualizar_sala(sala_id: IdPath, dados: SalaUpdate, session: SessionDep):
    return sala_crud.atualizar(session, sala_id, dados)


@router.delete("/{sala_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_sala(sala_id: IdPath, session: SessionDep):
    sala_crud.excluir(session, sala_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{sala_id}/assentos", response_model=list[AssentoRead], summary="Assentos de uma sala (1:N)")
def assentos_da_sala(sala_id: IdPath, session: SessionDep):
    return sala_crud.listar_assentos(session, sala_id)


@router.get("/{sala_id}/sessoes", response_model=Pagina[SessaoDetalhe], summary="Sessões de uma sala (1:N)")
def sessoes_da_sala(sala_id: IdPath, session: SessionDep, pag: PaginacaoDep):
    sala_crud.obter(session, sala_id)
    return sessao_crud.listar(session, sala_id=sala_id, offset=pag.offset, limit=pag.limit)
