"""Merge UK location fields with existing migrations

Revision ID: 1df5fc051bca
Revises: e834342db481, fb57e57021a7
Create Date: 2025-07-13 20:21:04.161541

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1df5fc051bca'
down_revision: Union[str, Sequence[str], None] = ('e834342db481', 'fb57e57021a7')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
