"""
Database models for HMO Analyser
Compatible with both SQLite (development) and PostgreSQL (production)
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON, DECIMAL, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.sqlite import TEXT
from sqlalchemy.orm import relationship
from database import Base, DATABASE_URL
import uuid
from datetime import datetime

# Smart UUID handling functions for database compatibility
def get_uuid_column():
    """Create appropriate UUID column type based on database"""
    if DATABASE_URL and DATABASE_URL.startswith("sqlite"):
        # SQLite: Use TEXT with string UUID default
        return Column(TEXT, primary_key=True, default=lambda: str(uuid.uuid4()))
    else:
        # PostgreSQL: Use native UUID type
        return Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

def get_uuid_foreign_key(table_name, column_name="id", nullable=False):
    """Create appropriate foreign key column type based on database"""
    if DATABASE_URL and DATABASE_URL.startswith("sqlite"):
        # SQLite: Use TEXT for foreign keys
        return Column(TEXT, ForeignKey(f"{table_name}.{column_name}", ondelete="CASCADE"), nullable=nullable)
    else:
        # PostgreSQL: Use UUID for foreign keys
        return Column(UUID(as_uuid=True), ForeignKey(f"{table_name}.{column_name}", ondelete="CASCADE"), nullable=nullable)

class Property(Base):
    """Main property table storing basic property information"""
    __tablename__ = "properties"
    
    # Primary key with database-appropriate UUID handling
    id = get_uuid_column()
    
    # Property identification
    url = Column(Text, unique=True, nullable=False, index=True)
    property_id = Column(String(50), index=True)  # SpareRoom property ID
    
    # Location information
    address = Column(Text)
    postcode = Column(String(20), index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships - one property can have multiple analyses and tasks
    analyses = relationship("PropertyAnalysis", back_populates="property", cascade="all, delete-orphan")
    tasks = relationship("AnalysisTask", back_populates="property", cascade="all, delete-orphan")

class PropertyAnalysis(Base):
    """Detailed analysis results for each property"""
    __tablename__ = "property_analyses"
    
    # Primary key and foreign key to property
    id = get_uuid_column()
    property_id = get_uuid_foreign_key("properties", nullable=False)
    
    # Property details extracted from listing
    advertiser_name = Column(String(255))
    landlord_type = Column(String(100))
    bills_included = Column(String(50), index=True)
    household_gender = Column(String(50))
    listing_status = Column(String(100))
    
    # Room information
    total_rooms = Column(Integer, index=True)
    available_rooms = Column(Integer, index=True)
    taken_rooms = Column(Integer)
    listed_rooms = Column(Integer)
    
    # Financial information
    monthly_income = Column(DECIMAL(10, 2), index=True)
    annual_income = Column(DECIMAL(10, 2), index=True)
    
    # Analysis results
    meets_requirements = Column(Text, index=True)
    room_details = Column(JSON)  # Stores detailed room breakdown
    all_rooms_list = Column(JSON)  # Stores formatted room list for display
    available_rooms_details = Column(JSON)  # Stores available rooms details
    
    # Additional metadata
    main_photo_url = Column(Text)
    analysis_date = Column(String(20))
    title = Column(Text)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationship back to property
    property = relationship("Property", back_populates="analyses")

class AnalysisTask(Base):
    """Tracks the status and progress of property analysis tasks"""
    __tablename__ = "analysis_tasks"
    
    # Primary key and foreign key to property
    id = get_uuid_column()
    task_id = Column(String(100), unique=True, nullable=False, index=True)
    property_id = get_uuid_foreign_key("properties")
    
    # Task status and progress
    status = Column(String(50), default="pending", index=True)  # pending, running, completed, failed
    progress = Column(JSON)  # Stores progress of each analysis step
    error_message = Column(Text)
    
    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Relationship back to property
    property = relationship("Property", back_populates="tasks")

class AnalyticsLog(Base):
    """Logs analytics events for monitoring and insights"""
    __tablename__ = "analytics_logs"
    
    # Primary key and optional foreign key to property
    id = get_uuid_column()
    event_type = Column(String(100), nullable=False, index=True)  # 'analysis_started', 'analysis_completed', etc.
    property_id = get_uuid_foreign_key("properties", nullable=True)  # Optional - some events aren't property-specific
    task_id = Column(String(100))  # Optional reference to analysis task
    
    # Event data and metadata
    event_data = Column(JSON)  # Stores additional event information
    user_agent = Column(Text)  # Browser/client information
    ip_address = Column(String(45))  # IPv4 or IPv6 address
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, index=True)