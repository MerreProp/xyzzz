"""
Database models for HMO Analyser
Compatible with both SQLite (development) and PostgreSQL (production)
"""

from typing import List, Optional
from pytest import Session
from sqlalchemy import( Column, 
                       String, 
                       Integer, 
                       Float, 
                       DateTime, 
                       Text, 
                       JSON, 
                       DECIMAL, 
                       ForeignKey, 
                       Boolean,
                       Index,
                       Enum,
                       UniqueConstraint,)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.sqlite import TEXT
from sqlalchemy.orm import relationship
from database import Base, DATABASE_URL
import uuid
from datetime import datetime
import enum

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

    # EXISTING Location information
    address = Column(Text)
    postcode = Column(String(20), index=True)
    latitude = Column(Float)
    longitude = Column(Float)

    # ADD THIS - Relationship to additional URLs
    urls = relationship("PropertyURL", back_populates="property", cascade="all, delete-orphan")

    duplicate_decisions = relationship("DuplicateDecision", back_populates="property")
    
    # NEW: Enhanced UK location fields
    city = Column(String(100), index=True)          # Actual city/town (e.g., "Bicester", "Banbury")
    area = Column(String(100), index=True)          # Local area/ward (e.g., "Kings End", "Grimsbury")
    district = Column(String(100), index=True)      # Administrative district (e.g., "Cherwell")
    county = Column(String(100), index=True)        # County (e.g., "Oxfordshire")
    country = Column(String(50), index=True)        # Country (e.g., "England")
    constituency = Column(String(100))              # Parliamentary constituency
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships - one property can have multiple analyses and tasks
    analyses = relationship("PropertyAnalysis", back_populates="property", cascade="all, delete-orphan")
    changes = relationship("PropertyChange", back_populates="property", cascade="all, delete-orphan", order_by="desc(PropertyChange.detected_at)")
    tasks = relationship("AnalysisTask", back_populates="property", cascade="all, delete-orphan")
    rooms = relationship("Room", back_populates="property", cascade="all, delete-orphan")


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
    
    # ✅ NEW: Room uncertainty tracking fields
    uncertain_rooms = Column(Integer, default=0)
    uncertain_rooms_details = Column(JSON)
    confirmed_available_rooms = Column(Integer, default=0)
    confirmed_taken_rooms = Column(Integer, default=0)
    
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

# models.py - Updated AnalysisTask model to support bulk updates

class AnalysisTask(Base):
    """Tracks the status and progress of property analysis tasks"""
    __tablename__ = "analysis_tasks"
    
    # Primary key and foreign key to property
    id = get_uuid_column()
    task_id = Column(String(100), unique=True, nullable=False, index=True)
    # CHANGE: Make property_id nullable to support bulk updates
    property_id = get_uuid_foreign_key("properties", nullable=True)  # Allow NULL for bulk updates
    
    # Task status and progress
    status = Column(String(50), default="pending", index=True)  # pending, running, completed, failed
    progress = Column(JSON)  # Stores progress of each analysis step
    error_message = Column(Text)
    
    # Add task type to distinguish between individual and bulk updates
    task_type = Column(String(50), default="individual", index=True)  # 'individual', 'bulk_update'
    
    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Relationship back to property (optional for bulk tasks)
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

# ADD THIS NEW MODEL to models.py:
class RoomPriceHistory(Base):
    """Track price changes over time for individual rooms"""
    __tablename__ = "room_price_history"
    
    # Primary key and foreign keys
    id = get_uuid_column()
    room_id = get_uuid_foreign_key("rooms", nullable=False)
    property_id = get_uuid_foreign_key("properties", nullable=False)
    analysis_id = get_uuid_foreign_key("property_analyses", nullable=True)
    
    # Price tracking
    previous_price = Column(DECIMAL(8, 2))
    new_price = Column(DECIMAL(8, 2))
    previous_price_text = Column(String(200))
    new_price_text = Column(String(200))
    
    # Change metadata
    price_change_amount = Column(DECIMAL(8, 2))
    price_change_percentage = Column(DECIMAL(5, 2))
    change_reason = Column(String(100))
    
    # Context
    room_status_at_change = Column(String(50))
    market_context = Column(JSON)
    
    # Timestamps
    detected_at = Column(DateTime, default=datetime.utcnow, index=True)
    effective_date = Column(DateTime, nullable=False, index=True)
    
    # FIXED RELATIONSHIPS - No conflicts
    room = relationship("Room", foreign_keys=[room_id])
    property = relationship("Property", foreign_keys=[property_id])
    analysis = relationship("PropertyAnalysis", foreign_keys=[analysis_id])

# ADD THIS NEW MODEL to models.py:
class PropertyTrend(Base):
    """Store calculated trends and analytics for properties"""
    __tablename__ = "property_trends"
    
    # Primary key and foreign key
    id = get_uuid_column()
    property_id = get_uuid_foreign_key("properties", nullable=False)
    
    # Time period for this trend calculation
    trend_period = Column(String(50), nullable=False, index=True)
    period_start = Column(DateTime, nullable=False, index=True)
    period_end = Column(DateTime, nullable=False)
    
    # Availability trends
    avg_availability_duration = Column(DECIMAL(5, 2))
    total_availability_periods = Column(Integer)
    availability_turnover_rate = Column(DECIMAL(5, 2))
    
    # Price trends
    avg_room_price = Column(DECIMAL(8, 2))
    price_volatility = Column(DECIMAL(5, 2))
    price_trend_direction = Column(String(20))
    price_change_percentage = Column(DECIMAL(5, 2))
    
    # Income trends
    estimated_monthly_income = Column(DECIMAL(10, 2))
    income_stability_score = Column(DECIMAL(3, 2))
    vacancy_impact = Column(DECIMAL(8, 2))
    
    # Market position
    market_competitiveness = Column(String(20))
    demand_indicator = Column(DECIMAL(3, 2))
    
    # Metadata
    calculation_date = Column(DateTime, default=datetime.utcnow)
    data_points_used = Column(Integer)
    confidence_score = Column(DECIMAL(3, 2))
    
    # FIXED RELATIONSHIP - No conflicts
    property = relationship("Property", foreign_keys=[property_id])

class PropertyChange(Base):
    """Tracks changes to properties over time"""
    __tablename__ = "property_changes"
    
    # Primary key and foreign key to property
    id = get_uuid_column()
    property_id = get_uuid_foreign_key("properties", nullable=False)
    
    # Change tracking
    change_type = Column(String(50), nullable=False, index=True)  # 'status', 'price', 'availability', 'rooms', 'offline'
    field_name = Column(String(100))  # Specific field that changed
    old_value = Column(Text)  # Previous value
    new_value = Column(Text)  # New value
    
    # Additional context
    room_details = Column(JSON)  # For room-specific changes
    change_summary = Column(Text)  # Human-readable description
    
    # Detection metadata
    detected_at = Column(DateTime, default=datetime.utcnow, index=True)
    analysis_id = get_uuid_foreign_key("property_analyses", nullable=True)  # Link to analysis that detected the change
    
    # Relationship back to property
    property = relationship("Property", back_populates="changes")

class Room(Base):
    """Individual room tracking table - UPDATED for phase 1"""  # ✅ Correct docstring format
    __tablename__ = "rooms"
    
    # Primary key and foreign key to property
    id = get_uuid_column()
    property_id = get_uuid_foreign_key("properties", nullable=False)
    
    # Room identification
    room_identifier = Column(String(500), nullable=False)  # e.g., "Room 1 - £500/month (En-suite)"
    room_number = Column(String(50))  # e.g., "Room 1", "Room A"
    price_text = Column(String(200))  # e.g., "£500/month"
    room_type = Column(String(200))   # e.g., "En-suite", "Shared bathroom"
    
    # Room status tracking
    current_status = Column(String(50), default="available")  # available, taken, offline
    is_currently_listed = Column(Boolean, default=True)
    
    # Discovery tracking
    first_seen_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_seen_date = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Price tracking
    current_price = Column(DECIMAL(8, 2))  # Extracted numeric price
    original_price = Column(DECIMAL(8, 2))  # Price when first discovered
    
    # Metadata
    times_seen = Column(Integer, default=1)
    times_changed = Column(Integer, default=0)
    room_metadata = Column(JSON)  # Store additional room details
    
    # Relationship back to property
    property = relationship("Property", back_populates="rooms")

        # PHASE 1 ADDITIONS:
    
    # Date tracking for "Date Gone" functionality
    date_gone = Column(DateTime, nullable=True, index=True)      # When room became unavailable
    date_returned = Column(DateTime, nullable=True)             # When room became available again
    
    # Availability period tracking
    current_availability_period_id = get_uuid_foreign_key("room_availability_periods", nullable=True)
    total_availability_periods = Column(Integer, default=0)     # How many times room has been available
    average_availability_duration = Column(DECIMAL(5, 2))       # Average days per availability period
    
    # RELATIONSHIPS - ADD THESE:
    # FIXED RELATIONSHIPS - Replace your existing relationship definitions with these:
    availability_periods = relationship(
        "RoomAvailabilityPeriod", 
        back_populates="room", 
        cascade="all, delete-orphan", 
        order_by="desc(RoomAvailabilityPeriod.period_start_date)",
        foreign_keys="[RoomAvailabilityPeriod.room_id]",  # EXPLICIT foreign key
        overlaps="current_period"  # Avoid relationship conflicts
    )
    current_period = relationship(
        "RoomAvailabilityPeriod", 
        foreign_keys="[Room.current_availability_period_id]",  # Use the correct foreign key
        post_update=True,
        uselist=False,
        overlaps="availability_periods"  # Avoid relationship conflicts
    )

    # 🆕 PHASE 5 additions:
    source_url = Column(Text, nullable=True)
    url_confidence = Column(Float, default=1.0)
    linked_room_id = Column(String(50), nullable=True)
    is_primary_instance = Column(Boolean, default=True)
    # Update the Property model to include the rooms relationship
# Add this line to your existing Property class:
# rooms = relationship("Room", back_populates="property", cascade="all, delete-orphan")

class RoomChange(Base):
    """Track changes to individual rooms"""
    __tablename__ = "room_changes"
    
    # Primary key and foreign keys
    id = get_uuid_column()
    room_id = get_uuid_foreign_key("rooms", nullable=False)
    property_id = get_uuid_foreign_key("properties", nullable=False)
    analysis_id = get_uuid_foreign_key("property_analyses", nullable=True)
    
    # Change tracking
    change_type = Column(String(50), nullable=False)  # 'price_change', 'status_change', 'disappeared', 'reappeared'
    old_value = Column(Text)
    new_value = Column(Text)
    change_summary = Column(Text)
    
    # Detection metadata
    detected_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    room = relationship("Room")
    property = relationship("Property")
    analysis = relationship("PropertyAnalysis")

    # ADD THIS NEW MODEL to your existing models.py:

class RoomAvailabilityPeriod(Base):
    """Track discrete periods when rooms are available"""
    __tablename__ = "room_availability_periods"
    
    # Primary key and foreign key to room
    id = get_uuid_column()
    room_id = get_uuid_foreign_key("rooms", nullable=False)
    
    # Period timing
    period_start_date = Column(DateTime, nullable=False, index=True)
    period_end_date = Column(DateTime, nullable=True, index=True)  # NULL if still available
    
    # Room details at start of period
    price_at_start = Column(DECIMAL(8, 2))
    price_text_at_start = Column(String(200))  # e.g., "£500/month"
    room_type_at_start = Column(String(200))   # e.g., "En-suite"
    room_identifier_at_start = Column(String(500))  # Full room string
    
    # Analysis tracking
    discovery_analysis_id = get_uuid_foreign_key("property_analyses", nullable=True)
    end_analysis_id = get_uuid_foreign_key("property_analyses", nullable=True)
    
    # Calculated fields
    duration_days = Column(Integer)  # Calculated when period ends
    is_current_period = Column(Boolean, default=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Room relationship - FIXED to avoid ambiguous foreign keys
    room = relationship(
        "Room", 
        back_populates="availability_periods",
        foreign_keys="[RoomAvailabilityPeriod.room_id]",  # EXPLICIT foreign key
        overlaps="current_period"  # Avoid relationship conflicts
    )   
    
    # Analysis relationships - FIXED
    discovery_analysis = relationship(
        "PropertyAnalysis", 
        foreign_keys="[RoomAvailabilityPeriod.discovery_analysis_id]",
        uselist=False
    )    
    end_analysis = relationship(
        "PropertyAnalysis", 
        foreign_keys="[RoomAvailabilityPeriod.end_analysis_id]",
        uselist=False
    )

class MapUsageEvent(Base):
    """Track map usage events for Mapbox quota monitoring and analytics"""
    __tablename__ = "map_usage_events"
    
    # Primary key
    id = get_uuid_column()
    
    # Event tracking
    event_type = Column(String(50), nullable=False, index=True)  # 'map_load', 'style_change', 'filter_usage', etc.
    session_id = Column(String(100), nullable=False, index=True)  # Track user sessions
    timestamp = Column(DateTime, nullable=False, index=True)      # When event occurred
    data = Column(JSON)                                           # Event-specific data
    
    # Optional metadata for analysis
    user_agent = Column(String(500))    # Browser/device info
    ip_address = Column(String(45))     # IPv4/IPv6 address
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

# Performance indexes for Phase 2 analytics
Index('ix_price_history_room_date', RoomPriceHistory.room_id, RoomPriceHistory.effective_date)
Index('ix_price_history_property_date', RoomPriceHistory.property_id, RoomPriceHistory.effective_date)
Index('ix_trends_property_period', PropertyTrend.property_id, PropertyTrend.trend_period, PropertyTrend.period_start)
# Also add this performance index after your existing indexes
Index('ix_map_usage_session_timestamp', MapUsageEvent.session_id, MapUsageEvent.timestamp)
Index('ix_map_usage_type_timestamp', MapUsageEvent.event_type, MapUsageEvent.timestamp)

# Contact Categories Enum
class ContactCategory(enum.Enum):
    LANDLORD = "landlord"
    TENANT = "tenant"
    CONTRACTOR = "contractor"
    AGENT = "agent"
    SUPPLIER = "supplier"
    OTHER = "other"

class ContactList(Base):
    """Contact Lists that can be shared among users (Phase 1: No user relationships)"""
    __tablename__ = "contact_lists"
    
    id = get_uuid_column()
    name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # User reference
    created_by = get_uuid_foreign_key("users", nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_default = Column(Boolean, default=False)
    
    # Relationships
    created_by_user = relationship("User", back_populates="created_lists")
    permissions = relationship("ContactListPermission", back_populates="contact_list", cascade="all, delete-orphan")
    contacts = relationship("Contact", back_populates="contact_list", cascade="all, delete-orphan")

class Contact(Base):
    """Individual contacts in the system"""
    __tablename__ = "contacts"
    
    id = get_uuid_column()
    
    # Basic contact information
    name = Column(String(200), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    phone = Column(String(50), nullable=False)
    company = Column(String(200), nullable=False, index=True)
    
    # Categorization
    category = Column(Enum(ContactCategory), nullable=False, default=ContactCategory.OTHER, index=True)
    
    # Additional information
    address = Column(Text)
    notes = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_contact_date = Column(DateTime, default=datetime.utcnow)
    
    # Foreign keys
    contact_list_id = get_uuid_foreign_key("contact_lists", nullable=False)
    
    # User reference
    created_by = get_uuid_foreign_key("users", nullable=False)

    # Relationships
    created_by_user = relationship("User", back_populates="created_contacts")
    contact_list = relationship("ContactList", back_populates="contacts")


class ContactFavorite(Base):
    """Track which contacts are favorited by users"""
    __tablename__ = "contact_favorites"
    
    id = get_uuid_column()
    contact_id = get_uuid_foreign_key("contacts", nullable=False)
    
    # Phase 2: Use user-based approach
    user_id = get_uuid_foreign_key("users", nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="favorites")
    contact = relationship("Contact")
    
    # Ensure unique user-contact combinations
    __table_args__ = (
        UniqueConstraint('user_id', 'contact_id', name='unique_user_contact_favorite'),
    )


# User Authentication Models
class User(Base):
    """User accounts for the contact book system"""
    __tablename__ = "users"
    
    id = get_uuid_column()
    
    # Basic user information
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    full_name = Column(String(200), nullable=False)
    
    # Authentication
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships - Fixed with proper overlaps handling
    created_lists = relationship("ContactList", back_populates="created_by_user")
    created_contacts = relationship("Contact", back_populates="created_by_user")
    
    # Specify which foreign key to use for this relationship
    list_permissions = relationship(
        "ContactListPermission", 
        back_populates="user",
        foreign_keys="ContactListPermission.user_id"
    )
    
    # Separate relationship for permissions granted by this user
    granted_permissions = relationship(
        "ContactListPermission",
        foreign_keys="ContactListPermission.created_by",
        overlaps="granted_by_user"  # This tells SQLAlchemy about the overlap
    )
    
    favorites = relationship("ContactFavorite", back_populates="user")

# Permission System
class PermissionLevel(enum.Enum):
    OWNER = "owner"      # Can delete list, manage permissions
    EDITOR = "editor"    # Can add/edit/delete contacts
    VIEWER = "viewer"    # Can only view contacts

class ContactListPermission(Base):
    """Track user permissions for contact lists"""
    __tablename__ = "contact_list_permissions"
    
    id = get_uuid_column()
    
    # Foreign keys
    user_id = get_uuid_foreign_key("users", nullable=False)
    contact_list_id = get_uuid_foreign_key("contact_lists", nullable=False)
    
    # Permission level
    permission_level = Column(Enum(PermissionLevel), nullable=False, default=PermissionLevel.VIEWER)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = get_uuid_foreign_key("users", nullable=False)  # Who granted this permission
    
    # Relationships - Fixed with proper overlaps handling
    user = relationship(
        "User", 
        back_populates="list_permissions",
        foreign_keys=[user_id]
    )
    
    contact_list = relationship("ContactList", back_populates="permissions")
    
    granted_by_user = relationship(
        "User", 
        foreign_keys=[created_by],
        overlaps="granted_permissions"  # This tells SQLAlchemy about the overlap
    )
    
    # Ensure unique user-list combinations
    __table_args__ = (
        UniqueConstraint('user_id', 'contact_list_id', name='unique_user_list_permission'),
    )

# Team invitation system
class TeamInvitation(Base):
    """Track invitations to join contact lists"""
    __tablename__ = "team_invitations"
    
    id = get_uuid_column()
    
    # Invitation details
    email = Column(String(255), nullable=False, index=True)
    contact_list_id = get_uuid_foreign_key("contact_lists", nullable=False)
    permission_level = Column(Enum(PermissionLevel), nullable=False, default=PermissionLevel.VIEWER)
    
    # Invitation status
    is_accepted = Column(Boolean, default=False)
    is_expired = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)  # Invitations expire after 7 days
    invited_by = get_uuid_foreign_key("users", nullable=False)
    accepted_by = get_uuid_foreign_key("users", nullable=True)  # Set when accepted
    
    # Relationships
    contact_list = relationship("ContactList")
    invited_by_user = relationship("User", foreign_keys=[invited_by])
    accepted_by_user = relationship("User", foreign_keys=[accepted_by])
    
    # Ensure unique email-list combinations for pending invitations
    __table_args__ = (
        UniqueConstraint('email', 'contact_list_id', name='unique_email_list_invitation'),
    )

class PropertyURL(Base):
    """Track multiple URLs for the same property"""
    __tablename__ = "property_urls"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    property_id = Column(String, ForeignKey("properties.id"), nullable=False)
    url = Column(String, nullable=False, unique=True)
    is_primary = Column(Boolean, default=False)  # Mark the main/original URL
    detected_at = Column(DateTime, default=datetime.utcnow)
    confidence_score = Column(Float)  # Confidence when this was linked as duplicate
    
    # Relationship
    property = relationship("Property", back_populates="urls")

    # 🆕 PHASE 5 additions:
    distance_meters = Column(Float, nullable=True)
    proximity_level = Column(String(50), nullable=True)
    linked_by = Column(String(20), default='system')
    user_confirmed = Column(Boolean, default=False)


class DuplicateDecision(Base):
    __tablename__ = "duplicate_decisions"
    
    id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    new_url = Column(Text, nullable=False)
    existing_property_id = Column(String(50), ForeignKey("properties.id"), nullable=False)
    confidence_score = Column(Float, nullable=False)
    distance_meters = Column(Float, nullable=True)
    user_decision = Column(String(20), nullable=False)
    decided_at = Column(DateTime, default=datetime.utcnow)
    match_factors = Column(JSON, nullable=True)
    
    property = relationship("Property", back_populates="duplicate_decisions")



# Add indexes for better performance
from sqlalchemy import Index
Contact.__table_args__ = (
    Index('idx_contact_category_name', Contact.category, Contact.name),
    Index('idx_contact_email_phone', Contact.email, Contact.phone),
)

# User indexes
Index('ix_user_email_active', User.email, User.is_active)
Index('ix_user_username_active', User.username, User.is_active)

# Permission indexes
Index('ix_permission_user_list', ContactListPermission.user_id, ContactListPermission.contact_list_id)
Index('ix_permission_list_level', ContactListPermission.contact_list_id, ContactListPermission.permission_level)

# Invitation indexes
Index('ix_invitation_email_pending', TeamInvitation.email, TeamInvitation.is_accepted, TeamInvitation.is_expired)
Index('ix_invitation_expires', TeamInvitation.expires_at, TeamInvitation.is_expired)


    # HELPER FUNCTIONS - Add these to your models.py:

def calculate_period_duration(start_date: datetime, end_date: datetime = None) -> int:
    """Calculate duration in days for an availability period"""
    if not start_date:
        return 0
    
    end = end_date or datetime.utcnow()
    duration = (end - start_date).days
    return max(0, duration)  # Ensure non-negative

def get_room_current_period(room_id) -> 'RoomAvailabilityPeriod':
    """Get the current availability period for a room"""
    from sqlalchemy.orm import sessionmaker
    from database import engine
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        period = session.query(RoomAvailabilityPeriod).filter(
            RoomAvailabilityPeriod.room_id == room_id,
            RoomAvailabilityPeriod.is_current_period == True
        ).first()
        
        return period
    finally:
        session.close()

# HELPER FUNCTIONS for models.py:
def calculate_price_change_percentage(old_price: float, new_price: float) -> float:
    """Calculate percentage change between two prices"""
    if not old_price or old_price == 0:
        return 0.0
    return round(((new_price - old_price) / old_price) * 100, 2)

def get_price_trend_direction(price_changes: list) -> str:
    """Determine overall price trend direction from a list of changes"""
    if not price_changes:
        return 'stable'
    
    positive_changes = sum(1 for change in price_changes if change > 0)
    negative_changes = sum(1 for change in price_changes if change < 0)
    
    if positive_changes > negative_changes * 1.5:
        return 'increasing'
    elif negative_changes > positive_changes * 1.5:
        return 'decreasing'
    else:
        return 'stable'

# EXAMPLE USAGE AND VALIDATION:
if __name__ == "__main__":
    # This can be used to test the models
    print("Phase 1 Models Updated:")
    print("- Added RoomAvailabilityPeriod model")
    print("- Updated Room model with date_gone, date_returned")
    print("- Added period tracking fields")
    print("- Added relationships between Room and RoomAvailabilityPeriod")
    
    # Test model structure
    try:
        from database import engine
        
        # This will validate that the models are correctly defined
        Room.__table__.create(engine, checkfirst=True)
        RoomAvailabilityPeriod.__table__.create(engine, checkfirst=True)
        print("✅ Models validated successfully")
        
    except Exception as e:
        print(f"❌ Model validation failed: {e}")