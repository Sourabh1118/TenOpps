"""Create employers table with indexes and constraints

Revision ID: 002_create_employers_table
Revises: 001_create_jobs_table
Create Date: 2024-03-18 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_create_employers_table'
down_revision = '001_create_jobs_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create employers table with all fields, constraints, and indexes."""
    
    # Create enum type for subscription tier
    subscription_tier_enum = postgresql.ENUM(
        'free', 'basic', 'premium',
        name='subscriptiontier',
        create_type=True
    )
    
    # Create employers table
    op.create_table(
        'employers',
        # Primary key
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        
        # Authentication
        sa.Column('email', sa.String(length=255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        
        # Company information
        sa.Column('company_name', sa.String(length=100), nullable=False),
        sa.Column('company_website', sa.String(length=500), nullable=True),
        sa.Column('company_logo', sa.String(length=500), nullable=True),
        sa.Column('company_description', sa.Text(), nullable=True),
        
        # Subscription management
        sa.Column('subscription_tier', subscription_tier_enum, nullable=False, server_default='free'),
        sa.Column('subscription_start_date', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('subscription_end_date', sa.DateTime(timezone=True), nullable=False),
        
        # Usage tracking
        sa.Column('monthly_posts_used', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('featured_posts_used', sa.Integer(), nullable=False, server_default='0'),
        
        # Payment integration
        sa.Column('stripe_customer_id', sa.String(length=255), nullable=True, unique=True),
        
        # Account status
        sa.Column('verified', sa.Boolean(), nullable=False, server_default='false'),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        
        # Check constraints for validation
        sa.CheckConstraint(
            "email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'",
            name='check_email_format'
        ),
        sa.CheckConstraint(
            "char_length(company_name) >= 2 AND char_length(company_name) <= 100",
            name='check_company_name_length'
        ),
        sa.CheckConstraint(
            "company_website IS NULL OR company_website ~* '^https?://.+'",
            name='check_company_website_url'
        ),
        sa.CheckConstraint(
            "monthly_posts_used >= 0",
            name='check_monthly_posts_positive'
        ),
        sa.CheckConstraint(
            "featured_posts_used >= 0",
            name='check_featured_posts_positive'
        ),
        sa.CheckConstraint(
            "subscription_end_date > subscription_start_date",
            name='check_subscription_dates'
        ),
    )
    
    # Create indexes for efficient querying
    op.create_index('idx_employers_id', 'employers', ['id'])
    op.create_index('idx_employers_email', 'employers', ['email'], unique=True)
    op.create_index('idx_employers_subscription_tier', 'employers', ['subscription_tier'])
    op.create_index('idx_employers_verified', 'employers', ['verified'])
    
    # Composite index for subscription management queries
    op.create_index(
        'idx_employers_subscription_status',
        'employers',
        ['subscription_tier', 'subscription_end_date']
    )


def downgrade() -> None:
    """Drop employers table and related objects."""
    
    # Drop indexes first
    op.drop_index('idx_employers_subscription_status', table_name='employers')
    op.drop_index('idx_employers_verified', table_name='employers')
    op.drop_index('idx_employers_subscription_tier', table_name='employers')
    op.drop_index('idx_employers_email', table_name='employers')
    op.drop_index('idx_employers_id', table_name='employers')
    
    # Drop table
    op.drop_table('employers')
    
    # Drop enum type
    sa.Enum(name='subscriptiontier').drop(op.get_bind(), checkfirst=True)
