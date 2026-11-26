from fastapi import APIRouter, Query, status

from app.crud import validacao as validacao_crud
from app.dependencies import IdPath, PaginacaoDep, SessionDep
from app.schemas.common import Pagina
from app.schemas.validacao import ValidacaoCreate, ValidacaoRead
from app.services import validacao_service

router = APIRouter(prefix="/validacoes", tags=["Validações (entrada na sala)"])


@router.post("", response_model=ValidacaoRead, status_code=status.HTTP_201_CREATED,
             summary="Validar ingresso na entrada (1:1 com o ingresso)")
def validar(dados: ValidacaoCreate, session: SessionDep):
    return validacao_service.validar_ingresso(session, dados)


@router.get("", response_model=Pagina[ValidacaoRead])
def listar_validacoes(
    session: SessionDep,
    pag: PaginacaoDep,
    ingresso_id: int | None = Query(None, gt=0),
    sessao_id: int | None = Query(None, gt=0),
    operador: str | None = None,
):
    return validacao_crud.listar(
        session, ingresso_id=ingresso_id, sessao_id=sessao_id, operador=operador,
        offset=pag.offset, limit=pag.limit,
    )


@router.get("/{validacao_id}", response_model=ValidacaoRead)
def obter_validacao(validacao_id: IdPath, session: SessionDep):
    return validacao_crud.obter(session, validacao_id)
