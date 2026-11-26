from sqlalchemy import func
from sqlmodel import Session, select

from app.crud.base import obter_ou_404, paginar
from app.exceptions import ConflitoError
from app.models import FilmeGenero, Genero
from app.schemas.genero import GeneroCreate, GeneroUpdate


def _nome_existe(session: Session, nome: str, ignorar_id: int | None = None) -> bool:
    stmt = select(Genero.id).where(func.lower(Genero.nome) == nome.lower())
    if ignorar_id is not None:
        stmt = stmt.where(Genero.id != ignorar_id)
    return session.exec(stmt.limit(1)).first() is not None


def obter(session: Session, genero_id: int) -> Genero:
    return obter_ou_404(session, Genero, genero_id, "Gênero")


def listar(session: Session, *, nome: str | None, offset: int, limit: int) -> dict:
    stmt = select(Genero).order_by(Genero.nome)
    if nome:
        stmt = stmt.where(Genero.nome.ilike(f"%{nome}%"))
    return paginar(session, stmt, offset, limit)


def criar(session: Session, dados: GeneroCreate) -> Genero:
    if _nome_existe(session, dados.nome):
        raise ConflitoError(f"Já existe um gênero chamado '{dados.nome}'.")
    genero = Genero(nome=dados.nome)
    session.add(genero)
    session.commit()
    session.refresh(genero)
    return genero


def atualizar(session: Session, genero_id: int, dados: GeneroUpdate) -> Genero:
    genero = obter(session, genero_id)
    if dados.nome is not None:
        if _nome_existe(session, dados.nome, ignorar_id=genero_id):
            raise ConflitoError(f"Já existe um gênero chamado '{dados.nome}'.")
        genero.nome = dados.nome
    session.commit()
    session.refresh(genero)
    return genero


def excluir(session: Session, genero_id: int) -> None:
    genero = obter(session, genero_id)
    em_uso = session.exec(select(FilmeGenero.filme_id).where(FilmeGenero.genero_id == genero_id).limit(1)).first()
    if em_uso is not None:
        raise ConflitoError("O gênero está associado a filmes; remova a associação antes de excluir.")
    session.delete(genero)
    session.commit()
