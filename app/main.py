import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError

from app.dependencies import SessionDep
from app.exceptions import AppError
from app.routers import (
    clientes, compras, consultas, estatisticas, filmes, generos, ingressos, salas, sessoes, validacoes,
)

logger = logging.getLogger("cinema")

app = FastAPI(
    title="Sistema de Cinema",
    description="Venda de ingressos e controle de assentos por sessão (FastAPI + SQLModel + Alembic).",
    version="1.0.0",
)

for modulo in (generos, filmes, salas, sessoes, clientes, compras, ingressos, validacoes, consultas, estatisticas):
    app.include_router(modulo.router)


# ----------------------------- Tratamento de erros (F18) -----------------------------
@app.exception_handler(AppError)
async def tratar_erro_de_dominio(_: Request, exc: AppError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(IntegrityError)
async def tratar_integridade(_: Request, exc: IntegrityError):
    logger.warning("Violação de integridade: %s", exc.orig)
    return JSONResponse(
        status_code=409,
        content={"detail": "A operação viola uma restrição de integridade (registro duplicado, "
                           "assento já vendido ou referência a registro inexistente/dependente)."},
    )


@app.exception_handler(OperationalError)
async def tratar_conexao(_: Request, exc: OperationalError):
    logger.error("Erro operacional no banco: %s", exc.orig)
    return JSONResponse(status_code=503, content={"detail": "Banco de dados indisponível no momento. Tente novamente."})


@app.exception_handler(SQLAlchemyError)
async def tratar_erro_persistencia(_: Request, exc: SQLAlchemyError):
    logger.exception("Falha de persistência")
    return JSONResponse(status_code=500, content={"detail": "Falha ao persistir os dados. A operação foi desfeita."})


@app.exception_handler(Exception)
async def tratar_erro_inesperado(_: Request, exc: Exception):
    logger.exception("Erro inesperado")
    return JSONResponse(status_code=500, content={"detail": "Erro interno inesperado."})


# ----------------------------------- Utilidades --------------------------------------
@app.get("/", tags=["Sistema"])
def raiz():
    return {"sistema": "Cinema API", "documentacao": "/docs"}


@app.get("/saude", tags=["Sistema"], summary="Verifica a conexão com o banco")
def saude(session: SessionDep): # pyright: ignore[reportInvalidTypeForm]
    session.connection().execute(text("SELECT 1"))
    return {"status": "ok"}
