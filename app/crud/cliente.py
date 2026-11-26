from sqlalchemy import func
from sqlmodel import Session, select

from app.crud.base import obter_ou_404, paginar
from app.exceptions import ConflitoError
from app.models import Cliente, Compra
from app.schemas.cliente import ClienteCreate, ClienteUpdate


def _duplicado(session: Session, email: str | None, cpf: str | None, ignorar_id: int | None = None) -> None:
    if email:
        stmt = select(Cliente.id).where(func.lower(Cliente.email) == email.lower())
        if ignorar_id is not None:
            stmt = stmt.where(Cliente.id != ignorar_id)
        if session.exec(stmt.limit(1)).first() is not None:
            raise ConflitoError(f"Já existe um cliente com o e-mail '{email}'.")
    if cpf:
        stmt = select(Cliente.id).where(Cliente.cpf == cpf)
        if ignorar_id is not None:
            stmt = stmt.where(Cliente.id != ignorar_id)
        if session.exec(stmt.limit(1)).first() is not None:
            raise ConflitoError("Já existe um cliente com este CPF.")


def obter(session: Session, cliente_id: int) -> Cliente:
    return obter_ou_404(session, Cliente, cliente_id, "Cliente")


def listar(
    session: Session,
    *,
    nome: str | None = None,
    email: str | None = None,
    ativo: bool | None = None,
    offset: int = 0,
    limit: int = 10,
) -> dict:
    stmt = select(Cliente).order_by(Cliente.nome)
    if nome:
        stmt = stmt.where(Cliente.nome.ilike(f"%{nome}%"))
    if email:
        stmt = stmt.where(Cliente.email.ilike(f"%{email}%"))
    if ativo is not None:
        stmt = stmt.where(Cliente.ativo == ativo)
    return paginar(session, stmt, offset, limit)


def criar(session: Session, dados: ClienteCreate) -> Cliente:
    _duplicado(session, dados.email, dados.cpf)
    cliente = Cliente(**dados.model_dump())
    session.add(cliente)
    session.commit()
    session.refresh(cliente)
    return cliente


def atualizar(session: Session, cliente_id: int, dados: ClienteUpdate) -> Cliente:
    cliente = obter(session, cliente_id)
    campos = {k: v for k, v in dados.model_dump(exclude_unset=True).items() if v is not None}
    _duplicado(session, campos.get("email"), campos.get("cpf"), ignorar_id=cliente_id)
    for campo, valor in campos.items():
        setattr(cliente, campo, valor)
    session.commit()
    session.refresh(cliente)
    return cliente


def excluir(session: Session, cliente_id: int) -> None:
    cliente = obter(session, cliente_id)
    tem_compras = session.exec(select(Compra.id).where(Compra.cliente_id == cliente_id).limit(1)).first()
    if tem_compras is not None:
        raise ConflitoError("O cliente possui compras registradas; inative-o (ativo=false) em vez de excluir.")
    session.delete(cliente)
    session.commit()
