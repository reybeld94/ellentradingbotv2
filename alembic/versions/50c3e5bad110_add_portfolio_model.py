"""Add portfolio model"""

revision = '50c3e5bad110'
revises = 'f9db15bb6dbc'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


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
