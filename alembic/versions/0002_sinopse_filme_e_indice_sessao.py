from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_sinopse_e_indice"
down_revision: Union[str, None] = "0001_estrutura_inicial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # batch_alter_table: no SQLite recria a tabela mantendo os dados; no PostgreSQL vira ALTER TABLE.
    with op.batch_alter_table("filme") as batch:
        batch.add_column(sa.Column("sinopse", sa.String(length=1000), nullable=True))
    op.create_index("ix_sessao_inicio", "sessao", ["inicio"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_sessao_inicio", table_name="sessao")
    with op.batch_alter_table("filme") as batch:
        batch.drop_column("sinopse")
