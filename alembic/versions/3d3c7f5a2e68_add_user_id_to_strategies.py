"""Add user_id column to strategies table

Revision ID: 3d3c7f5a2e68
Revises: 2b49c1f3e8b3, f630fdef4c30
Create Date: 2024-05-06 00:00:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '3d3c7f5a2e68'
down_revision: Union[str, Sequence[str], None] = ('2b49c1f3e8b3', 'f630fdef4c30')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('strategies', sa.Column('user_id', sa.Integer(), nullable=True, server_default='1'))
    op.create_index(op.f('ix_strategies_user_id'), 'strategies', ['user_id'], unique=False)
    op.create_foreign_key(None, 'strategies', 'users', ['user_id'], ['id'])
    op.alter_column('strategies', 'user_id', server_default=None, nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(None, 'strategies', type_='foreignkey')
    op.drop_index(op.f('ix_strategies_user_id'), table_name='strategies')
    op.drop_column('strategies', 'user_id')
