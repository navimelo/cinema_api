from fastapi import APIRouter, Query, Response, status

from app.crud import filme as filme_crud
from app.crud import sessao as sessao_crud
from app.dependencies import IdPath, PaginacaoDep, SessionDep
from app.schemas.common import Pagina
from app.schemas.filme import Classificacao, FilmeCreate, FilmeRead, FilmeUpdate
from app.schemas.sessao import SessaoDetalhe

router = APIRouter(prefix="/filmes", tags=["Filmes"])


@router.post("", response_model=FilmeRead, status_code=status.HTTP_201_CREATED)
def criar_filme(dados: FilmeCreate, session: SessionDep):
    return filme_crud.criar(session, dados)


@router.get("", response_model=Pagina[FilmeRead], summary="Listar filmes (paginado e filtrável)")
def listar_filmes(
    session: SessionDep,
    pag: PaginacaoDep,
    titulo: str | None = Query(None, description="Busca parcial no título"),
    genero_id: int | None = Query(None, gt=0),
    classificacao: Classificacao | None = None,
    em_cartaz: bool | None = None,
):
    return filme_crud.listar(
        session, titulo=titulo, genero_id=genero_id, classificacao=classificacao,
        em_cartaz=em_cartaz, offset=pag.offset, limit=pag.limit,
    )


@router.get("/{filme_id}", response_model=FilmeRead)
def obter_filme(filme_id: IdPath, session: SessionDep):
    return filme_crud.obter(session, filme_id)


@router.patch("/{filme_id}", response_model=FilmeRead)
def atualizar_filme(filme_id: IdPath, dados: FilmeUpdate, session: SessionDep):
    return filme_crud.atualizar(session, filme_id, dados)


@router.delete("/{filme_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_filme(filme_id: IdPath, session: SessionDep):
    filme_crud.excluir(session, filme_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{filme_id}/sessoes", response_model=Pagina[SessaoDetalhe], summary="Sessões de um filme (1:N)")
def sessoes_do_filme(filme_id: IdPath, session: SessionDep, pag: PaginacaoDep, status_sessao: str | None = Query(None, alias="status")):
    filme_crud.obter(session, filme_id)
    return sessao_crud.listar(session, filme_id=filme_id, status=status_sessao, offset=pag.offset, limit=pag.limit)
