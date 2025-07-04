"""Add Trade model

Revision ID: 2f1f8a38381d
Revises: f9db15bb6dbc
Create Date: 2025-07-03 22:00:34.237054

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2f1f8a38381d'
down_revision: Union[str, Sequence[str], None] = 'f9db15bb6dbc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('trades',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('strategy_id', sa.String(length=50), nullable=True),
    sa.Column('symbol', sa.String(length=10), nullable=True),
    sa.Column('action', sa.String(length=10), nullable=True),
    sa.Column('quantity', sa.Float(), nullable=True),
    sa.Column('entry_price', sa.Float(), nullable=True),
    sa.Column('exit_price', sa.Float(), nullable=True),
    sa.Column('status', sa.String(length=10), nullable=True),
    sa.Column('opened_at', sa.DateTime(), nullable=True),
    sa.Column('closed_at', sa.DateTime(), nullable=True),
    sa.Column('pnl', sa.Float(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_trades_id'), 'trades', ['id'], unique=False)
    op.create_index(op.f('ix_trades_strategy_id'), 'trades', ['strategy_id'], unique=False)
    op.create_index(op.f('ix_trades_symbol'), 'trades', ['symbol'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_trades_symbol'), table_name='trades')
    op.drop_index(op.f('ix_trades_strategy_id'), table_name='trades')
    op.drop_index(op.f('ix_trades_id'), table_name='trades')
    op.drop_table('trades')
    # ### end Alembic commands ###
