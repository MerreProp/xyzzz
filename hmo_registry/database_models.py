# hmo_registry/database_models.py
"""
Database models for HMO Registry data
Stores geocoded HMO data to avoid re-geocoding on every server startup
"""

from sqlalchemy import Column, String, Integer, Date, DateTime, Text, Boolean, DECIMAL, Index
from sqlalchemy.dialects.postgresql import UUID
from database import Base
from models import get_uuid_column
from datetime import datetime

class HMORegistry(Base):
    """
    Stores HMO registry data from different cities
    Includes geocoded coordinates to avoid repeated API calls
    """
    __tablename__ = "hmo_registries"
    
    id = get_uuid_column()
    
    # Source information
    city = Column(String(50), nullable=False, index=True)
    source = Column(String(100), nullable=False)  # e.g., 'oxford_council'
    case_number = Column(String(100), nullable=False, index=True)
    data_source_url = Column(Text)
    
    # Address information
    raw_address = Column(Text, nullable=False)
    postcode = Column(String(20), index=True)
    
    # Geocoded coordinates (the expensive part we want to cache!)
    latitude = Column(DECIMAL(10, 8), index=True)
    longitude = Column(DECIMAL(11, 8), index=True)
    geocoded = Column(Boolean, default=False, index=True)
    geocoding_source = Column(String(50))  # 'nominatim', 'google', etc.
    
    # Property details
    total_occupants = Column(Integer)
    total_units = Column(Integer)
    
    # License information
    licence_status = Column(String(30), index=True)  # 'active', 'expired', 'unknown'
    licence_start_date = Column(Date)
    licence_expiry_date = Column(Date, index=True)
    
    # Data quality and processing
    data_quality_score = Column(DECIMAL(3, 2))  # 0-1.0 score
    processing_notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    source_last_updated = Column(DateTime)  # When the source data was last updated
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_hmo_city_status', 'city', 'licence_status'),
        Index('idx_hmo_coords', 'latitude', 'longitude'),
        Index('idx_hmo_postcode_city', 'postcode', 'city'),
        Index('idx_hmo_case_city', 'case_number', 'city'),
    )
    
    def __repr__(self):
        return f"<HMORegistry(city='{self.city}', case='{self.case_number}', address='{self.raw_address[:50]}...')>"


# Create the table
def create_hmo_registry_table():
    """Create the HMO registry table"""
    from database import engine
    
    print("🏗️ Creating HMO registry table...")
    try:
        HMORegistry.__table__.create(engine, checkfirst=True)
        print("✅ HMO registry table created successfully")
        return True
    except Exception as e:
        print(f"❌ Error creating HMO registry table: {e}")
        return False


def check_hmo_table_exists():
    """Check if HMO registry table exists"""
    from database import engine
    from sqlalchemy import inspect
    
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    return 'hmo_registries' in tables