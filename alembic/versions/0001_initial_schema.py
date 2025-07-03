"""Initial database schema

Revision ID: 0001
Revises: 
Create Date: 2025-06-27 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create enum types
    company_status = postgresql.ENUM(
        'ACTIVE', 'ACQUIRED', 'CLOSED', 'IPO', name='company_status'
    )
    company_status.create(op.get_bind())
    
    funding_round_type = postgresql.ENUM(
        'PRE_SEED', 'SEED', 'SERIES_A', 'SERIES_B', 'SERIES_C', 'SERIES_D', 
        'SERIES_E', 'SERIES_F', 'SERIES_G', 'SERIES_H', 'SERIES_I', 'SERIES_J',
        'GRANT', 'ANGEL', 'PRIVATE_EQUITY', 'DEBT_FINANCING', 'POST_IPO_DEBT',
        'POST_IPO_EQUITY', 'NON_EQUITY_ASSISTANCE', 'SECONDARY_MARKET',
        'CONVERTIBLE_NOTE', 'CORPORATE_ROUND', 'UNDISCLOSED', name='funding_round_type'
    )
    funding_round_type.create(op.get_bind())
    
    # Create tables
    op.create_table(
        'companies',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('website', sa.String(), nullable=True),
        sa.Column('founded_date', sa.Date(), nullable=True),
        sa.Column('status', sa.Enum('ACTIVE', 'ACQUIRED', 'CLOSED', 'IPO', name='company_status'), nullable=True),
        sa.Column('total_funding', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('last_funding_date', sa.Date(), nullable=True),
        sa.Column('employee_count', sa.Integer(), nullable=True),
        sa.Column('country', sa.String(), nullable=True),
        sa.Column('city', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table(
        'founders',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('linkedin_url', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table(
        'investors',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('type', sa.String(), nullable=True),
        sa.Column('website', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table(
        'company_founders',
        sa.Column('company_id', sa.String(), nullable=False),
        sa.Column('founder_id', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('is_current', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.ForeignKeyConstraint(['founder_id'], ['founders.id'], ),
        sa.PrimaryKeyConstraint('company_id', 'founder_id')
    )
    
    op.create_table(
        'funding_rounds',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('company_id', sa.String(), nullable=False),
        sa.Column('round_type', sa.Enum(
            'PRE_SEED', 'SEED', 'SERIES_A', 'SERIES_B', 'SERIES_C', 'SERIES_D', 
            'SERIES_E', 'SERIES_F', 'SERIES_G', 'SERIES_H', 'SERIES_I', 'SERIES_J',
            'GRANT', 'ANGEL', 'PRIVATE_EQUITY', 'DEBT_FINANCING', 'POST_IPO_DEBT',
            'POST_IPO_EQUITY', 'NON_EQUITY_ASSISTANCE', 'SECONDARY_MARKET',
            'CONVERTIBLE_NOTE', 'CORPORATE_ROUND', 'UNDISCLOSED', name='funding_round_type'
        ), nullable=True),
        sa.Column('announced_date', sa.Date(), nullable=True),
        sa.Column('raised_amount', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table(
        'investment_participants',
        sa.Column('round_id', sa.String(), nullable=False),
        sa.Column('investor_id', sa.String(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('is_lead', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['investor_id'], ['investors.id'], ),
        sa.ForeignKeyConstraint(['round_id'], ['funding_rounds.id'], ),
        sa.PrimaryKeyConstraint('round_id', 'investor_id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_companies_name'), 'companies', ['name'], unique=False)
    op.create_index(op.f('ix_companies_status'), 'companies', ['status'], unique=False)
    op.create_index(op.f('ix_founders_name'), 'founders', ['name'], unique=False)
    op.create_index(op.f('ix_investors_name'), 'investors', ['name'], unique=False)
    op.create_index(op.f('ix_funding_rounds_company_id'), 'funding_rounds', ['company_id'], unique=False)
    op.create_index(op.f('ix_funding_rounds_round_type'), 'funding_rounds', ['round_type'], unique=False)
    op.create_index(op.f('ix_funding_rounds_announced_date'), 'funding_rounds', ['announced_date'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_funding_rounds_announced_date'), table_name='funding_rounds')
    op.drop_index(op.f('ix_funding_rounds_round_type'), table_name='funding_rounds')
    op.drop_index(op.f('ix_funding_rounds_company_id'), table_name='funding_rounds')
    op.drop_index(op.f('ix_investors_name'), table_name='investors')
    op.drop_index(op.f('ix_founders_name'), table_name='founders')
    op.drop_index(op.f('ix_companies_status'), table_name='companies')
    op.drop_index(op.f('ix_companies_name'), table_name='companies')
    
    # Drop tables
    op.drop_table('investment_participants')
    op.drop_table('funding_rounds')
    op.drop_table('company_founders')
    op.drop_table('investors')
    op.drop_table('founders')
    op.drop_table('companies')
    
    # Drop enum types
    funding_round_type = postgresql.ENUM(
        'PRE_SEED', 'SEED', 'SERIES_A', 'SERIES_B', 'SERIES_C', 'SERIES_D', 
        'SERIES_E', 'SERIES_F', 'SERIES_G', 'SERIES_H', 'SERIES_I', 'SERIES_J',
        'GRANT', 'ANGEL', 'PRIVATE_EQUITY', 'DEBT_FINANCING', 'POST_IPO_DEBT',
        'POST_IPO_EQUITY', 'NON_EQUITY_ASSISTANCE', 'SECONDARY_MARKET',
        'CONVERTIBLE_NOTE', 'CORPORATE_ROUND', 'UNDISCLOSED', name='funding_round_type'
    )
    funding_round_type.drop(op.get_bind())
    
    company_status = postgresql.ENUM(
        'ACTIVE', 'ACQUIRED', 'CLOSED', 'IPO', name='company_status'
    )
    company_status.drop(op.get_bind())
