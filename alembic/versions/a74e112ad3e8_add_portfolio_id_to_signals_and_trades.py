"""add_portfolio_id_to_signals_and_trades

Revision ID: a74e112ad3e8
Revises: cda90f233a37
Create Date: 2025-07-05 14:17:46.535105

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a74e112ad3e8'
down_revision: Union[str, Sequence[str], None] = 'cda90f233a37'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("signals", sa.Column("portfolio_id", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_signals_portfolio_id"), "signals", ["portfolio_id"], unique=False)
    op.create_foreign_key(None, "signals", "portfolios", ["portfolio_id"], ["id"])

    op.add_column("trades", sa.Column("portfolio_id", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_trades_portfolio_id"), "trades", ["portfolio_id"], unique=False)
    op.create_foreign_key(None, "trades", "portfolios", ["portfolio_id"], ["id"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(None, "trades", type_="foreignkey")
    op.drop_index(op.f("ix_trades_portfolio_id"), table_name="trades")
    op.drop_column("trades", "portfolio_id")

    op.drop_constraint(None, "signals", type_="foreignkey")
    op.drop_index(op.f("ix_signals_portfolio_id"), table_name="signals")
    op.drop_column("signals", "portfolio_id")
