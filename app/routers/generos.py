from fastapi import APIRouter, Query, Response, status

from app.crud import filme as filme_crud
from app.crud import genero as genero_crud
from app.dependencies import IdPath, PaginacaoDep, SessionDep
from app.schemas.common import Pagina
from app.schemas.filme import FilmeRead
from app.schemas.genero import GeneroCreate, GeneroRead, GeneroUpdate

router = APIRouter(prefix="/generos", tags=["Gêneros"])


@router.post("", response_model=GeneroRead, status_code=status.HTTP_201_CREATED)
def criar_genero(dados: GeneroCreate, session: SessionDep):
    return genero_crud.criar(session, dados)


@router.get("", response_model=Pagina[GeneroRead])
def listar_generos(session: SessionDep, pag: PaginacaoDep, nome: str | None = Query(None, description="Busca parcial")):
    return genero_crud.listar(session, nome=nome, offset=pag.offset, limit=pag.limit)


@router.get("/{genero_id}", response_model=GeneroRead)
def obter_genero(genero_id: IdPath, session: SessionDep):
    return genero_crud.obter(session, genero_id)


@router.patch("/{genero_id}", response_model=GeneroRead)
def atualizar_genero(genero_id: IdPath, dados: GeneroUpdate, session: SessionDep):
    return genero_crud.atualizar(session, genero_id, dados)


@router.delete("/{genero_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_genero(genero_id: IdPath, session: SessionDep):
    genero_crud.excluir(session, genero_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{genero_id}/filmes", response_model=Pagina[FilmeRead], summary="Filmes de um gênero (N:N)")
def filmes_do_genero(genero_id: IdPath, session: SessionDep, pag: PaginacaoDep):
    genero_crud.obter(session, genero_id)
    return filme_crud.listar_por_genero(session, genero_id, pag.offset, pag.limit)
