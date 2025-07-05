"""merge heads

Revision ID: 2152693dfc7b
Revises: 50c3e5bad110, 50ec6c6fbe36
Create Date: 2025-07-05 00:04:32.498475

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2152693dfc7b'
down_revision: Union[str, Sequence[str], None] = ('50c3e5bad110', '50ec6c6fbe36')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
