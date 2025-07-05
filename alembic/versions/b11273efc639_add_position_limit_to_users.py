"""add position_limit column to users

Revision ID: b11273efc639
Revises: a74e112ad3e8
Create Date: 2025-07-05 15:00:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'b11273efc639'
down_revision: Union[str, Sequence[str], None] = 'a74e112ad3e8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('position_limit', sa.Integer(), nullable=False, server_default='7'))
    op.alter_column('users', 'position_limit', server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'position_limit')
