"""Add portfolio model"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '50c3e5bad110'
down_revision: Union[str, Sequence[str], None] = 'f9db15bb6dbc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'portfolios',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=100), nullable=False, unique=True),
        sa.Column('api_key_encrypted', sa.String(length=255), nullable=False),
        sa.Column('secret_key_encrypted', sa.String(length=255), nullable=False),
        sa.Column('base_url', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='0'),
    )
    op.create_index(op.f('ix_portfolios_id'), 'portfolios', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_portfolios_id'), table_name='portfolios')
    op.drop_table('portfolios')
