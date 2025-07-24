"""Add UK location fields to properties table

Revision ID: e834342db481
Revises: fb57e57021a7
Create Date: 2025-07-13 20:07:26.986699

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = 'e834342db481'
down_revision = None  # You may need to update this
branch_labels = None
depends_on = None

def upgrade():
    """Add UK location fields to properties table"""
    print("🔄 Adding UK location fields to properties table...")
    
    # Add new columns to properties table
    op.add_column('properties', sa.Column('city', sa.String(100)))
    op.add_column('properties', sa.Column('area', sa.String(100)))
    op.add_column('properties', sa.Column('district', sa.String(100)))
    op.add_column('properties', sa.Column('county', sa.String(100)))
    op.add_column('properties', sa.Column('country', sa.String(50)))
    op.add_column('properties', sa.Column('constituency', sa.String(100)))
    
    # Create indexes for better query performance
    op.create_index('ix_properties_city', 'properties', ['city'])
    op.create_index('ix_properties_area', 'properties', ['area'])
    op.create_index('ix_properties_district', 'properties', ['district'])
    op.create_index('ix_properties_county', 'properties', ['county'])
    op.create_index('ix_properties_country', 'properties', ['country'])
    
    print("✅ UK location fields added successfully")

def downgrade():
    """Remove UK location fields from properties table"""
    print("🔄 Removing UK location fields from properties table...")
    
    # Drop indexes first
    op.drop_index('ix_properties_country', 'properties')
    op.drop_index('ix_properties_county', 'properties')
    op.drop_index('ix_properties_district', 'properties')
    op.drop_index('ix_properties_area', 'properties')
    op.drop_index('ix_properties_city', 'properties')
    
    # Drop columns
    op.drop_column('properties', 'constituency')
    op.drop_column('properties', 'country')
    op.drop_column('properties', 'county')
    op.drop_column('properties', 'district')
    op.drop_column('properties', 'area')
    op.drop_column('properties', 'city')
    
    print("✅ UK location fields removed successfully")