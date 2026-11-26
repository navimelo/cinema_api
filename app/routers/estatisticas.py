from fastapi import APIRouter

from app.dependencies import SessionDep
from app.schemas.consultas import Estatisticas
from app.services import estatistica_service

router = APIRouter(prefix="/estatisticas", tags=["Estatísticas"])


@router.get("", response_model=Estatisticas, summary="Totais, receita, ticket médio, ocupação e rankings")
def estatisticas(session: SessionDep):
    return estatistica_service.calcular(session)
