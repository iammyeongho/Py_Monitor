"""add_extended_playwright_metrics

Revision ID: e2e03e4cbc9d
Revises: fb52c0c8a942
Create Date: 2026-01-26 22:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e2e03e4cbc9d'
down_revision: Union[str, None] = 'fb52c0c8a942'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add extended Playwright metrics."""
    # TTFB (Time to First Byte)
    op.add_column('monitoring_logs', sa.Column('time_to_first_byte', sa.Float(), nullable=True))
    # CLS (Cumulative Layout Shift)
    op.add_column('monitoring_logs', sa.Column('cumulative_layout_shift', sa.Float(), nullable=True))
    # TBT (Total Blocking Time)
    op.add_column('monitoring_logs', sa.Column('total_blocking_time', sa.Float(), nullable=True))
    # Failed resources count
    op.add_column('monitoring_logs', sa.Column('failed_resources', sa.Integer(), nullable=True))
    # Redirect count
    op.add_column('monitoring_logs', sa.Column('redirect_count', sa.Integer(), nullable=True))
    # JS heap memory size
    op.add_column('monitoring_logs', sa.Column('js_heap_size', sa.Integer(), nullable=True))


def downgrade() -> None:
    """Downgrade schema - remove extended Playwright metrics."""
    op.drop_column('monitoring_logs', 'js_heap_size')
    op.drop_column('monitoring_logs', 'redirect_count')
    op.drop_column('monitoring_logs', 'failed_resources')
    op.drop_column('monitoring_logs', 'total_blocking_time')
    op.drop_column('monitoring_logs', 'cumulative_layout_shift')
    op.drop_column('monitoring_logs', 'time_to_first_byte')
