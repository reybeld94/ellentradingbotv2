"""Add strategy JSON configuration columns

Revision ID: f630fdef4c30
Revises: bbeb948ead61
Create Date: 2025-09-12 00:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'f630fdef4c30'
down_revision: Union[str, Sequence[str], None] = 'bbeb948ead61'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add JSON columns for strategy configuration.

    Columns are added as nullable with an empty JSON object default so that
    existing rows receive a valid value. Afterwards the columns are marked as
    non-nullable and the default is dropped.
    """
    empty_json = sa.text("'{}'::json")

    op.add_column(
        'strategies',
        sa.Column('entry_rules', sa.JSON(), nullable=True, server_default=empty_json),
    )
    op.add_column(
        'strategies',
        sa.Column('exit_rules', sa.JSON(), nullable=True, server_default=empty_json),
    )
    op.add_column(
        'strategies',
        sa.Column('risk_parameters', sa.JSON(), nullable=True, server_default=empty_json),
    )
    op.add_column(
        'strategies',
        sa.Column('position_sizing', sa.JSON(), nullable=True, server_default=empty_json),
    )

    # Ensure all existing records have an empty JSON object
    op.execute("UPDATE strategies SET entry_rules = '{}'::json WHERE entry_rules IS NULL")
    op.execute("UPDATE strategies SET exit_rules = '{}'::json WHERE exit_rules IS NULL")
    op.execute("UPDATE strategies SET risk_parameters = '{}'::json WHERE risk_parameters IS NULL")
    op.execute(
        "UPDATE strategies SET position_sizing = '{}'::json WHERE position_sizing IS NULL"
    )

    # Remove defaults and enforce non-null constraint
    op.alter_column(
        'strategies',
        'entry_rules',
        existing_type=sa.JSON(),
        nullable=False,
        server_default=None,
    )
    op.alter_column(
        'strategies',
        'exit_rules',
        existing_type=sa.JSON(),
        nullable=False,
        server_default=None,
    )
    op.alter_column(
        'strategies',
        'risk_parameters',
        existing_type=sa.JSON(),
        nullable=False,
        server_default=None,
    )
    op.alter_column(
        'strategies',
        'position_sizing',
        existing_type=sa.JSON(),
        nullable=False,
        server_default=None,
    )


def downgrade() -> None:
    """Remove strategy configuration columns."""
    op.drop_column('strategies', 'position_sizing')
    op.drop_column('strategies', 'risk_parameters')
    op.drop_column('strategies', 'exit_rules')
    op.drop_column('strategies', 'entry_rules')
