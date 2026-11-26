from sqlalchemy import func
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from app.crud.base import obter_ou_404, paginar
from app.exceptions import ConflitoError, NaoEncontradoError
from app.models import Filme, Genero, Sessao
from app.schemas.filme import FilmeCreate, FilmeUpdate


def _buscar_generos(session: Session, ids: list[int]) -> list[Genero]:
    ids = list(set(ids))
    if not ids:
        return []
    generos = session.exec(select(Genero).where(Genero.id.in_(ids))).all()
    faltando = set(ids) - {g.id for g in generos}
    if faltando:
        raise NaoEncontradoError(f"Gênero(s) inexistente(s): {sorted(faltando)}.")
    return list(generos)


def _titulo_existe(session: Session, titulo: str, ignorar_id: int | None = None) -> bool:
    stmt = select(Filme.id).where(func.lower(Filme.titulo) == titulo.lower())
    if ignorar_id is not None:
        stmt = stmt.where(Filme.id != ignorar_id)
    return session.exec(stmt.limit(1)).first() is not None


def obter(session: Session, filme_id: int) -> Filme:
    return obter_ou_404(session, Filme, filme_id, "Filme")


def listar(
    session: Session,
    *,
    titulo: str | None = None,
    genero_id: int | None = None,
    classificacao: str | None = None,
    em_cartaz: bool | None = None,
    offset: int = 0,
    limit: int = 10,
) -> dict:
    stmt = select(Filme).options(selectinload(Filme.generos)).order_by(Filme.titulo)
    if titulo:
        stmt = stmt.where(Filme.titulo.ilike(f"%{titulo}%"))
    if genero_id is not None:
        stmt = stmt.where(Filme.generos.any(Genero.id == genero_id))
    if classificacao:
        stmt = stmt.where(Filme.classificacao_indicativa == classificacao)
    if em_cartaz is not None:
        stmt = stmt.where(Filme.em_cartaz == em_cartaz)
    return paginar(session, stmt, offset, limit)


def listar_por_genero(session: Session, genero_id: int, offset: int, limit: int) -> dict:
    """F10 (N:N): filmes de um gênero, navegando pelo relacionamento."""
    stmt = (
        select(Filme)
        .options(selectinload(Filme.generos))
        .where(Filme.generos.any(Genero.id == genero_id))
        .order_by(Filme.titulo)
    )
    return paginar(session, stmt, offset, limit)


def criar(session: Session, dados: FilmeCreate) -> Filme:
    if _titulo_existe(session, dados.titulo):
        raise ConflitoError(f"Já existe um filme com o título '{dados.titulo}'.")
    campos = dados.model_dump(exclude={"generos_ids"})
    filme = Filme(**campos)
    filme.generos = _buscar_generos(session, dados.generos_ids)
    session.add(filme)
    session.commit()
    session.refresh(filme)
    return filme


def atualizar(session: Session, filme_id: int, dados: FilmeUpdate) -> Filme:
    filme = obter(session, filme_id)
    campos = {k: v for k, v in dados.model_dump(exclude_unset=True).items() if v is not None}
    generos_ids = campos.pop("generos_ids", None)
    if "titulo" in campos and _titulo_existe(session, campos["titulo"], ignorar_id=filme_id):
        raise ConflitoError(f"Já existe um filme com o título '{campos['titulo']}'.")
    for campo, valor in campos.items():
        setattr(filme, campo, valor)
    if generos_ids is not None:
        filme.generos = _buscar_generos(session, generos_ids)
    session.commit()
    session.refresh(filme)
    return filme


def excluir(session: Session, filme_id: int) -> None:
    filme = obter(session, filme_id)
    tem_sessoes = session.exec(select(Sessao.id).where(Sessao.filme_id == filme_id).limit(1)).first()
    if tem_sessoes is not None:
        raise ConflitoError("O filme possui sessões; desative-o (em_cartaz=false) em vez de excluir.")
    session.delete(filme)
    session.commit()
