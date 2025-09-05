"""add is_active column to strategies"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '2b49c1f3e8b3'
down_revision: Union[str, Sequence[str], None] = ('a518a2a016b9', '5ef44a2c3a3e')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'strategies',
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1')
    )
    op.alter_column('strategies', 'is_active', server_default=None)


def downgrade() -> None:
    op.drop_column('strategies', 'is_active')
