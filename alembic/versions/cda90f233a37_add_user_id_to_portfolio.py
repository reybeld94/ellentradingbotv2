"""add user_id to portfolio

Revision ID: cda90f233a37
Revises: 2152693dfc7b
Create Date: 2025-07-02 00:00:00
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'cda90f233a37'
down_revision: Union[str, Sequence[str], None] = '2152693dfc7b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column('portfolios', sa.Column('user_id', sa.Integer(), nullable=False, server_default='1'))
    op.create_foreign_key(None, 'portfolios', 'users', ['user_id'], ['id'])
    op.alter_column('portfolios', 'user_id', server_default=None)


def downgrade() -> None:
    op.drop_constraint(None, 'portfolios', type_='foreignkey')
    op.drop_column('portfolios', 'user_id')
