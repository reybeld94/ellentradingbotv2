"""Add Strategy model

Revision ID: bbeb948ead61
Revises: e819ab670950
Create Date: 2025-09-01 16:41:18.595847

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bbeb948ead61'
down_revision: Union[str, Sequence[str], None] = 'e819ab670950'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
