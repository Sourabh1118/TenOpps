"""create consents table

Revision ID: 008
Revises: 007
Create Date: 2024-01-16 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create consents table for GDPR compliance."""
    op.create_table(
        'consents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_type', sa.String(20), nullable=False),
        sa.Column('marketing_emails', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('data_processing', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('third_party_sharing', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('consent_date', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    
    # Create indexes
    op.create_index('idx_consents_id', 'consents', ['id'])
    op.create_index('idx_consents_user_id', 'consents', ['user_id'])
    op.create_index('idx_consents_user', 'consents', ['user_id', 'user_type'])


def downgrade() -> None:
    """Drop consents table."""
    op.drop_index('idx_consents_user', table_name='consents')
    op.drop_index('idx_consents_user_id', table_name='consents')
    op.drop_index('idx_consents_id', table_name='consents')
    op.drop_table('consents')
