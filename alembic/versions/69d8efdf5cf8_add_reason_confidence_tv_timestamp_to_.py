"""Add reason, confidence, tv_timestamp to signals

Revision ID: 69d8efdf5cf8
Revises: 001d29e61ad7
Create Date: 2025-06-29 14:10:44.545984

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '69d8efdf5cf8'
down_revision: Union[str, Sequence[str], None] = '001d29e61ad7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('signals', sa.Column('reason', sa.String(length=50), nullable=True))
    op.add_column('signals', sa.Column('confidence', sa.Integer(), nullable=True))
    op.add_column('signals', sa.Column('tv_timestamp', sa.String(length=50), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('signals', 'tv_timestamp')
    op.drop_column('signals', 'confidence')
    op.drop_column('signals', 'reason')
    # ### end Alembic commands ###
