"""create analytics tables

Revision ID: 007
Revises: 006
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create api_metrics table
    op.create_table(
        'api_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('endpoint', sa.String(500), nullable=False),
        sa.Column('method', sa.String(10), nullable=False),
        sa.Column('status_code', sa.Integer(), nullable=False),
        sa.Column('response_time_ms', sa.Float(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_role', sa.String(50), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.CheckConstraint('response_time_ms >= 0', name='check_response_time_positive'),
    )
    op.create_index('idx_api_metrics_endpoint', 'api_metrics', ['endpoint'])
    op.create_index('idx_api_metrics_timestamp', 'api_metrics', ['timestamp'])
    op.create_index('idx_api_metrics_endpoint_timestamp', 'api_metrics', ['endpoint', 'timestamp'])
    op.create_index('idx_api_metrics_slow_requests', 'api_metrics', ['response_time_ms'], 
                    postgresql_where=sa.text('response_time_ms > 1000'))

    # Create scraping_metrics table
    op.create_table(
        'scraping_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('source_platform', sa.String(50), nullable=False),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('success', sa.Integer(), nullable=False),
        sa.Column('jobs_found', sa.Integer(), default=0, nullable=False),
        sa.Column('jobs_created', sa.Integer(), default=0, nullable=False),
        sa.Column('jobs_updated', sa.Integer(), default=0, nullable=False),
        sa.Column('duration_seconds', sa.Float(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.CheckConstraint('success IN (0, 1)', name='check_success_boolean'),
        sa.CheckConstraint('duration_seconds >= 0', name='check_duration_positive'),
        sa.CheckConstraint('jobs_found >= 0', name='check_jobs_found_positive'),
        sa.CheckConstraint('jobs_created >= 0', name='check_jobs_created_positive'),
        sa.CheckConstraint('jobs_updated >= 0', name='check_jobs_updated_positive'),
    )
    op.create_index('idx_scraping_metrics_platform', 'scraping_metrics', ['source_platform'])
    op.create_index('idx_scraping_metrics_timestamp', 'scraping_metrics', ['timestamp'])
    op.create_index('idx_scraping_metrics_platform_timestamp', 'scraping_metrics', ['source_platform', 'timestamp'])
    op.create_index('idx_scraping_metrics_failures', 'scraping_metrics', ['success'], 
                    postgresql_where=sa.text('success = 0'))

    # Create search_analytics table
    op.create_table(
        'search_analytics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('query_text', sa.String(500), nullable=True),
        sa.Column('location', sa.String(200), nullable=True),
        sa.Column('filters_applied', sa.Text(), nullable=True),
        sa.Column('result_count', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.CheckConstraint('result_count >= 0', name='check_result_count_positive'),
    )
    op.create_index('idx_search_analytics_query', 'search_analytics', ['query_text'])
    op.create_index('idx_search_analytics_timestamp', 'search_analytics', ['timestamp'])
    op.create_index('idx_search_analytics_query_timestamp', 'search_analytics', ['query_text', 'timestamp'])

    # Create job_analytics table
    op.create_table(
        'job_analytics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('employer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('referrer', sa.String(500), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
    )
    op.create_index('idx_job_analytics_job', 'job_analytics', ['job_id'])
    op.create_index('idx_job_analytics_employer', 'job_analytics', ['employer_id'])
    op.create_index('idx_job_analytics_timestamp', 'job_analytics', ['timestamp'])
    op.create_index('idx_job_analytics_job_timestamp', 'job_analytics', ['job_id', 'timestamp'])
    op.create_index('idx_job_analytics_employer_timestamp', 'job_analytics', ['employer_id', 'timestamp'])
    op.create_index('idx_job_analytics_event_type', 'job_analytics', ['event_type'])

    # Create system_health_metrics table
    op.create_table(
        'system_health_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('metric_name', sa.String(100), nullable=False),
        sa.Column('metric_value', sa.Float(), nullable=False),
        sa.Column('metric_unit', sa.String(50), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('extra_data', sa.Text(), nullable=True),
    )
    op.create_index('idx_system_health_name', 'system_health_metrics', ['metric_name'])
    op.create_index('idx_system_health_timestamp', 'system_health_metrics', ['timestamp'])
    op.create_index('idx_system_health_name_timestamp', 'system_health_metrics', ['metric_name', 'timestamp'])


def downgrade() -> None:
    op.drop_table('system_health_metrics')
    op.drop_table('job_analytics')
    op.drop_table('search_analytics')
    op.drop_table('scraping_metrics')
    op.drop_table('api_metrics')
