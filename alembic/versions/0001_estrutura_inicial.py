from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_estrutura_inicial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "genero",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_genero_nome", "genero", ["nome"], unique=True)

    op.create_table(
        "filme",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("titulo", sa.String(length=150), nullable=False),
        sa.Column("duracao_minutos", sa.Integer(), nullable=False),
        sa.Column("classificacao_indicativa", sa.String(length=2), nullable=False),
        sa.Column("data_estreia", sa.Date(), nullable=True),
        sa.Column("em_cartaz", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("duracao_minutos > 0", name="ck_filme_duracao_positiva"),
    )
    op.create_index("ix_filme_titulo", "filme", ["titulo"], unique=True)

    op.create_table(
        "filme_genero",
        sa.Column("filme_id", sa.Integer(), nullable=False),
        sa.Column("genero_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["filme_id"], ["filme.id"]),
        sa.ForeignKeyConstraint(["genero_id"], ["genero.id"]),
        sa.PrimaryKeyConstraint("filme_id", "genero_id"),
    )

    op.create_table(
        "sala",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=50), nullable=False),
        sa.Column("tipo", sa.String(length=20), nullable=False),
        sa.Column("capacidade", sa.Integer(), nullable=False),
        sa.Column("ativa", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("capacidade > 0", name="ck_sala_capacidade_positiva"),
    )
    op.create_index("ix_sala_nome", "sala", ["nome"], unique=True)

    op.create_table(
        "assento",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sala_id", sa.Integer(), nullable=False),
        sa.Column("fileira", sa.String(length=2), nullable=False),
        sa.Column("numero", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["sala_id"], ["sala.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sala_id", "fileira", "numero", name="uq_assento_sala_fileira_numero"),
        sa.CheckConstraint("numero > 0", name="ck_assento_numero_positivo"),
    )

    op.create_table(
        "sessao",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("filme_id", sa.Integer(), nullable=False),
        sa.Column("sala_id", sa.Integer(), nullable=False),
        sa.Column("inicio", sa.DateTime(), nullable=False),
        sa.Column("fim", sa.DateTime(), nullable=False),
        sa.Column("preco", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=15), nullable=False),
        sa.ForeignKeyConstraint(["filme_id"], ["filme.id"]),
        sa.ForeignKeyConstraint(["sala_id"], ["sala.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("fim > inicio", name="ck_sessao_fim_apos_inicio"),
        sa.CheckConstraint("preco >= 0", name="ck_sessao_preco_nao_negativo"),
    )

    op.create_table(
        "cliente",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=150), nullable=False),
        sa.Column("cpf", sa.String(length=11), nullable=True),
        sa.Column("telefone", sa.String(length=20), nullable=True),
        sa.Column("data_nascimento", sa.Date(), nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_cliente_email", "cliente", ["email"], unique=True)
    op.create_index("ix_cliente_cpf", "cliente", ["cpf"], unique=True)

    op.create_table(
        "compra",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cliente_id", sa.Integer(), nullable=False),
        sa.Column("data_compra", sa.DateTime(), nullable=False),
        sa.Column("valor_total", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=15), nullable=False),
        sa.ForeignKeyConstraint(["cliente_id"], ["cliente.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "ingresso",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("compra_id", sa.Integer(), nullable=False),
        sa.Column("sessao_id", sa.Integer(), nullable=False),
        sa.Column("assento_id", sa.Integer(), nullable=False),
        sa.Column("valor", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=15), nullable=False),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.Column("cancelado_em", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["compra_id"], ["compra.id"]),
        sa.ForeignKeyConstraint(["sessao_id"], ["sessao.id"]),
        sa.ForeignKeyConstraint(["assento_id"], ["assento.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("valor >= 0", name="ck_ingresso_valor_nao_negativo"),
    )
    # Índice único parcial: um assento só pode ter um ingresso NÃO cancelado por sessão.
    op.create_index(
        "uq_ingresso_sessao_assento_ativo",
        "ingresso",
        ["sessao_id", "assento_id"],
        unique=True,
        sqlite_where=sa.text("status <> 'cancelado'"),
        postgresql_where=sa.text("status <> 'cancelado'"),
    )

    op.create_table(
        "validacao",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ingresso_id", sa.Integer(), nullable=False),
        sa.Column("validado_em", sa.DateTime(), nullable=False),
        sa.Column("operador", sa.String(length=80), nullable=False),
        sa.ForeignKeyConstraint(["ingresso_id"], ["ingresso.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_validacao_ingresso_id", "validacao", ["ingresso_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_validacao_ingresso_id", table_name="validacao")
    op.drop_table("validacao")
    op.drop_index("uq_ingresso_sessao_assento_ativo", table_name="ingresso")
    op.drop_table("ingresso")
    op.drop_table("compra")
    op.drop_index("ix_cliente_cpf", table_name="cliente")
    op.drop_index("ix_cliente_email", table_name="cliente")
    op.drop_table("cliente")
    op.drop_table("sessao")
    op.drop_table("assento")
    op.drop_index("ix_sala_nome", table_name="sala")
    op.drop_table("sala")
    op.drop_table("filme_genero")
    op.drop_index("ix_filme_titulo", table_name="filme")
    op.drop_table("filme")
    op.drop_index("ix_genero_nome", table_name="genero")
    op.drop_table("genero")
