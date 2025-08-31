"""Add is_bracket_parent column to orders

Revision ID: fe8c04b7556e
Revises: 5f00e55d2fc1
Create Date: 2025-08-31 23:27:52.086231

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fe8c04b7556e'
down_revision: Union[str, Sequence[str], None] = '5f00e55d2fc1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add is_bracket_parent column
    op.add_column('orders', sa.Column('is_bracket_parent', sa.Boolean(), nullable=True))

    # Create index for performance
    op.create_index(op.f('ix_orders_is_bracket_parent'), 'orders', ['is_bracket_parent'], unique=False)

    # Set default value for existing records
    op.execute("UPDATE orders SET is_bracket_parent = false WHERE is_bracket_parent IS NULL")

    # Make column non-nullable
    op.alter_column('orders', 'is_bracket_parent', nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop index first
    op.drop_index(op.f('ix_orders_is_bracket_parent'), table_name='orders')

    # Drop column
    op.drop_column('orders', 'is_bracket_parent')
