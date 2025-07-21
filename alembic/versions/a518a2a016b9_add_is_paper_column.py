"""add is_paper column to portfolio"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'a518a2a016b9'
down_revision: Union[str, Sequence[str], None] = '8db7b36ec533'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "portfolios",
        sa.Column("is_paper", sa.Boolean(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("portfolios", "is_paper")
