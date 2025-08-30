"""add idempotency_key to signals

Revision ID: 5f00e55d2fc1
Revises: a518a2a016b9
Create Date: 2025-08-30 13:27:41.595299

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5f00e55d2fc1'
down_revision: Union[str, Sequence[str], None] = 'a518a2a016b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "signals", sa.Column("idempotency_key", sa.String(length=32), nullable=True)
    )
    op.create_index(
        op.f("ix_signals_idempotency_key"),
        "signals",
        ["idempotency_key"],
        unique=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_signals_idempotency_key"), table_name="signals")
    op.drop_column("signals", "idempotency_key")
