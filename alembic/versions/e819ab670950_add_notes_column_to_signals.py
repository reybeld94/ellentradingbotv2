"""add notes column to signals

Revision ID: e819ab670950
Revises: 8a51a7e87355
Create Date: 2025-09-01 01:26:45

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'e819ab670950'
down_revision: Union[str, Sequence[str], None] = '8a51a7e87355'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('signals', sa.Column('notes', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('signals', 'notes')
