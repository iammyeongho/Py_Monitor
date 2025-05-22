"""initial migration

Revision ID: 001
Revises: 
Create Date: 2024-03-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # users 테이블 생성
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('status', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
        sa.Column('last_login_ip', sa.String(length=45), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )

    # projects 테이블 생성
    op.create_table(
        'projects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('host_name', sa.String(length=50), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('url', sa.String(length=255), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('open_date', sa.DateTime(), nullable=True),
        sa.Column('snapshot_path', sa.String(length=255), nullable=True),
        sa.Column('last_snapshot_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('status_interval', sa.Integer(), nullable=True),
        sa.Column('expiry_d_day', sa.Integer(), nullable=True),
        sa.Column('expiry_interval', sa.Integer(), nullable=True),
        sa.Column('time_limit', sa.Integer(), nullable=True),
        sa.Column('time_limit_interval', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('projects')
    op.drop_table('users') 