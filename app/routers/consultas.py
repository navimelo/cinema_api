from datetime import date

from fastapi import APIRouter, Query

from app.dependencies import PaginacaoDep, SessionDep
from app.schemas.common import Pagina
from app.schemas.consultas import FilmePublico, OcupacaoSessao, VendasDia
from app.schemas.sessao import SessaoDetalhe
from app.services import consulta_service

router = APIRouter(prefix="/consultas", tags=["Consultas complexas"])


@router.get("/filmes-mais-vistos", response_model=list[FilmePublico], summary="Filmes com maior público")
def filmes_mais_vistos(
    session: SessionDep,
    inicio: date | None = Query(None, description="Início do período (data da sessão)"),
    fim: date | None = Query(None, description="Fim do período (inclusive)"),
    limite: int = Query(5, ge=1, le=50),
):
    return consulta_service.filmes_mais_vistos(session, inicio, fim, limite)


@router.get("/ocupacao-sessoes", response_model=Pagina[OcupacaoSessao],
            summary="Ocupação por sessão (vendidos, disponíveis e %)")
def ocupacao_sessoes(
    session: SessionDep,
    pag: PaginacaoDep,
    data: date | None = None,
    sala_id: int | None = Query(None, gt=0),
    filme_id: int | None = Query(None, gt=0),
):
    return consulta_service.ocupacao_sessoes(
        session, data=data, sala_id=sala_id, filme_id=filme_id, offset=pag.offset, limit=pag.limit
    )


@router.get("/vendas-por-dia", response_model=list[VendasDia], summary="Vendas em um período, agrupadas por dia")
def vendas_por_dia(
    session: SessionDep,
    inicio: date = Query(..., description="Data inicial da venda"),
    fim: date = Query(..., description="Data final da venda (inclusive)"),
):
    return consulta_service.vendas_por_dia(session, inicio, fim)


@router.get("/sessoes-sem-vendas", response_model=Pagina[SessaoDetalhe],
            summary="Sessões agendadas sem nenhum ingresso ativo")
def sessoes_sem_vendas(session: SessionDep, pag: PaginacaoDep):
    return consulta_service.sessoes_sem_vendas(session, pag.offset, pag.limit)
