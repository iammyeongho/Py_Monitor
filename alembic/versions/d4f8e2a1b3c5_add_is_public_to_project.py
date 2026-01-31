"""Add is_public to project

Revision ID: d4f8e2a1b3c5
Revises: ac27af5c1e9b
Create Date: 2026-01-31 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4f8e2a1b3c5'
down_revision: Union[str, None] = 'ac27af5c1e9b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('projects', sa.Column('is_public', sa.Boolean(), nullable=True, server_default=sa.text('false')))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('projects', 'is_public')
