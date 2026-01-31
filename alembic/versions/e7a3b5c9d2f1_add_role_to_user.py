"""Add role to user

Revision ID: e7a3b5c9d2f1
Revises: d4f8e2a1b3c5
Create Date: 2026-01-31 10:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e7a3b5c9d2f1'
down_revision: Union[str, None] = 'd4f8e2a1b3c5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('role', sa.String(length=20), nullable=True, server_default='user'))
    # 기존 superuser는 admin 역할로 설정
    op.execute("UPDATE users SET role = 'admin' WHERE is_superuser = true")
    op.execute("UPDATE users SET role = 'user' WHERE role IS NULL")


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'role')
