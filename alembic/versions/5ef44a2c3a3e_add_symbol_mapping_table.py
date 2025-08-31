"""add symbol mapping table

Revision ID: 5ef44a2c3a3e
Revises: 8db7b36ec533
Create Date: 2025-08-31 00:45:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '5ef44a2c3a3e'
down_revision: Union[str, Sequence[str], None] = '8db7b36ec533'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'symbol_mappings',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('raw_symbol', sa.String(length=50), nullable=False, unique=True),
        sa.Column('broker_symbol', sa.String(length=50), nullable=False),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('symbol_mappings')
