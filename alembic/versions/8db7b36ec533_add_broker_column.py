"""add broker column

Revision ID: 8db7b36ec533
Revises: b11273efc639
Create Date: 2025-07-20 19:09:05.905403

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8db7b36ec533'
down_revision: Union[str, Sequence[str], None] = 'b11273efc639'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "portfolios",
        sa.Column("broker", sa.String(length=20), nullable=False, server_default="kraken"),
    )
    op.alter_column("portfolios", "broker", server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("portfolios", "broker")
