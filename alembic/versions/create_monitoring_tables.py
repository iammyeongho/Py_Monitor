"""create monitoring tables

Revision ID: create_monitoring_tables
Revises: create_project_tables
Create Date: 2025-03-21 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'create_monitoring_tables'
down_revision = 'create_project_tables'
branch_labels = None
depends_on = None

def upgrade():
    # monitoring_logs 테이블 생성
    op.create_table(
        'monitoring_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('status_code', sa.Integer(), nullable=True),
        sa.Column('response_time', sa.Float(), nullable=True),
        sa.Column('is_available', sa.Boolean(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_monitoring_logs_id'), 'monitoring_logs', ['id'], unique=False)

    # monitoring_alerts 테이블 생성
    op.create_table(
        'monitoring_alerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('alert_type', sa.String(length=50), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('is_resolved', sa.Boolean(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_monitoring_alerts_id'), 'monitoring_alerts', ['id'], unique=False)

    # monitoring_settings 테이블 생성
    op.create_table(
        'monitoring_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('check_interval', sa.Integer(), nullable=True),
        sa.Column('timeout', sa.Integer(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=True),
        sa.Column('alert_threshold', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_monitoring_settings_id'), 'monitoring_settings', ['id'], unique=False)

def downgrade():
    op.drop_index(op.f('ix_monitoring_settings_id'), table_name='monitoring_settings')
    op.drop_table('monitoring_settings')
    op.drop_index(op.f('ix_monitoring_alerts_id'), table_name='monitoring_alerts')
    op.drop_table('monitoring_alerts')
    op.drop_index(op.f('ix_monitoring_logs_id'), table_name='monitoring_logs')
    op.drop_table('monitoring_logs') 