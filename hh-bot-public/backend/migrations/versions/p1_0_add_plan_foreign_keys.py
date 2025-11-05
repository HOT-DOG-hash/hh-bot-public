"""baseline parity placeholder

Revision ID: p1_0
Revises: p0_3
Create Date: 2025-10-24 15:05:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "p1_0"
down_revision: Union[str, Sequence[str], None] = "p0_3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Schema parity already achieved in p0_3."""
    bind = op.get_bind()
    if bind.dialect.name != "sqlite":
        # Reserved for future adjustments on PostgreSQL deployments.
        return


def downgrade() -> None:
    """No-op downgrade."""
    return
