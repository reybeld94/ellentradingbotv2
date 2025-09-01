"""add notes column to orders

Revision ID: 8a51a7e87355
Revises: fe8c04b7556e
Create Date: 2025-11-13 00:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '8a51a7e87355'
down_revision: Union[str, Sequence[str], None] = 'fe8c04b7556e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('orders', sa.Column('notes', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('orders', 'notes')
