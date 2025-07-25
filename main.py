#!/usr/bin/env python3
"""
FastAPI Backend for HMO Analyser - Working Version with All Endpoints
"""

import asyncio

from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any
import uuid
import os
import json

# Your existing imports...
from fastapi import APIRouter, FastAPI, HTTPException, BackgroundTasks, status, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, HttpUrl, EmailStr
from sqlalchemy import desc, and_, func, or_, Column, String, Integer, DateTime, JSON, Text
from sqlalchemy.orm import Session
from collections import defaultdict
from contextlib import asynccontextmanager
from auth import (
    Token, UserRegister, UserLogin, UserResponse,
    create_access_token, authenticate_user, create_user,
    get_current_active_user, ACCESS_TOKEN_EXPIRE_MINUTES,
    check_list_permission, get_password_hash, get_user_accessible_lists, get_user_by_email, get_user_by_username
)
from modules.postcodes_io import geocode_postcode_io, reverse_geocode_postcode_io


# Database imports
from database import get_db, init_db, test_connection, Base
from models import (ContactListPermission, PermissionLevel, Property, 
                    PropertyAnalysis, 
                    AnalysisTask, 
                    AnalyticsLog,
                    PropertyChange, PropertyTrend, 
                    RoomAvailabilityPeriod, 
                    Room,
                    RoomChange,
                    RoomPriceHistory,
                    MapUsageEvent,
                    Contact,
                    ContactList,
                    ContactFavorite, TeamInvitation, User,
                    )
from crud import (PropertyCRUD, 
                  AnalysisCRUD, 
                  RoomCRUD, 
                  TaskCRUD, 
                  AnalyticsCRUD, 
                  PropertyChangeCRUD, 
                  RoomAvailabilityPeriodCRUD, 
                  calculate_property_date_gone, 
                  get_property_availability_summary,
                  RoomPriceHistoryCRUD, 
                  PropertyTrendCRUD,
                  PropertyURLCRUD)
from contacts_crud import ContactCRUD,ContactListCRUD, ContactFavoriteCRUD
from modules.coordinates import extract_coordinates, extract_property_details, reverse_geocode_nominatim
from test_phase3 import router as phase3_router

from duplicate_detection import (
    DuplicateCheckRequest, 
    DuplicateCheckResponse, 
    PotentialMatch,
    find_potential_duplicates,
    extract_property_details_for_duplicate_check
)


# Your existing module imports...
from modules import (
    extract_coordinates,
    extract_property_details,
    reverse_geocode_nominatim,
    extract_price_section,
    save_to_excel,
    get_exports_directory,
    cleanup_old_exports,
    get_export_stats,
)
from config import DATE_FORMAT

class UsageStatsResponse(BaseModel):
    total_map_loads: int
    unique_sessions: int
    avg_session_duration: float
    most_popular_style: str
    daily_breakdown: List[Dict[str, Any]]
    filter_usage: Dict[str, int]
    quota_usage: Dict[str, Any]

# Create router for map usage tracking
usage_router = APIRouter(prefix="/api/map-usage", tags=["Map Usage Analytics"])

# FastAPI app instance
app = FastAPI(
    title="HMO Analyser API",
    description="REST API for analyzing HMO properties from SpareRoom listings with database storage and organized file management",
    version="2.0.0"
)

# Add CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(phase3_router)
app.include_router(usage_router)  # ← ADD THIS LINE

# Initialize database on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    print("✅ Connected to PostgreSQL database")
    # Your database connection code here
    yield
    # Shutdown code (if needed)
    print("Disconnecting from database")

# Pydantic models for request/response validation
class PropertyAnalysisRequest(BaseModel):
    url: HttpUrl
    force_separate: Optional[bool] = False
    
class PropertyAnalysisResponse(BaseModel):
    task_id: str
    status: str
    message: str
    property_metadata: Optional[Dict[str, Any]] = None
    duplicate_detected: Optional[bool] = False
    duplicate_data: Optional[Dict[str, Any]] = None

class AnalysisStatus(BaseModel):
    task_id: str
    status: str
    progress: Dict[str, str]
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# Pydantic models for API
class ContactCreate(BaseModel):
    name: str
    email: EmailStr
    phone: str
    company: str
    category: str = "other"
    address: Optional[str] = None
    notes: Optional[str] = None
    last_contact_date: Optional[str] = None

class ContactResponse(BaseModel):
    id: str
    name: str
    email: str
    phone: str
    company: str
    category: str
    address: Optional[str]
    notes: Optional[str]
    created_at: str
    updated_at: str
    last_contact_date: str
    contact_list_id: str
    created_by: str
    can_edit: bool  # New: Based on user permissions
    can_delete: bool  # New: Based on user permissions

class ContactListCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ContactListResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    created_at: str
    updated_at: str
    is_default: bool
    contact_count: int
    created_by: str
    permission_level: str  # New: User's permission level
    can_edit: bool  # New: Can edit list settings
    can_delete: bool  # New: Can delete list
    can_invite: bool  # New: Can invite others

# Router for contact endpoints (Phase 2)
contacts_router = APIRouter(prefix="/api/contacts", tags=["Contacts"])

@contacts_router.post("/", response_model=ContactResponse)
async def create_contact(
    contact: ContactCreate,
    contact_list_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new contact (requires EDITOR permission)"""
    # Check if user has editor permission for the list
    if not check_list_permission(db, current_user, contact_list_id, PermissionLevel.EDITOR):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to add contacts to this list"
        )
    
    try:
        # Create new contact
        contact_data = contact.dict()
        contact_data['last_contact_date'] = contact_data.get('last_contact_date') or datetime.utcnow().date().isoformat()
        
        new_contact = Contact(
            name=contact_data['name'],
            email=contact_data['email'],
            phone=contact_data['phone'],
            company=contact_data['company'],
            category=contact_data['category'],
            address=contact_data.get('address'),
            notes=contact_data.get('notes'),
            last_contact_date=datetime.fromisoformat(contact_data['last_contact_date']),
            contact_list_id=contact_list_id,
            created_by=current_user.id
        )
        
        db.add(new_contact)
        db.commit()
        db.refresh(new_contact)
        
        # Check user's permissions for response
        user_permission = check_list_permission(db, current_user, contact_list_id, PermissionLevel.EDITOR)
        
        return ContactResponse(
            id=str(new_contact.id),
            name=new_contact.name,
            email=new_contact.email,
            phone=new_contact.phone,
            company=new_contact.company,
            category=new_contact.category.value,
            address=new_contact.address,
            notes=new_contact.notes,
            created_at=new_contact.created_at.isoformat(),
            updated_at=new_contact.updated_at.isoformat(),
            last_contact_date=new_contact.last_contact_date.isoformat(),
            contact_list_id=str(new_contact.contact_list_id),
            created_by=str(new_contact.created_by),
            can_edit=user_permission,
            can_delete=user_permission
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating contact: {str(e)}"
        )

@contacts_router.get("/", response_model=List[ContactResponse])
async def get_contacts(
    contact_list_id: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get contacts (only from lists user has access to)"""
    
    # If specific list requested, check permissions
    if contact_list_id:
        if not check_list_permission(db, current_user, contact_list_id, PermissionLevel.VIEWER):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this contact list"
            )
        accessible_lists = [contact_list_id]
    else:
        # Get all lists user has access to
        user_lists = get_user_accessible_lists(db, current_user.id)
        accessible_lists = [ul["list_id"] for ul in user_lists]
    
    # Build query
    query = db.query(Contact).filter(Contact.contact_list_id.in_(accessible_lists))
    
    # Apply filters
    if category and category != 'all':
        query = query.filter(Contact.category == category)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            Contact.name.ilike(search_term) |
            Contact.email.ilike(search_term) |
            Contact.company.ilike(search_term)
        )
    
    # Apply pagination
    contacts = query.offset(skip).limit(limit).all()
    
    # Build response with permissions
    result = []
    for contact in contacts:
        user_permission = check_list_permission(db, current_user, contact.contact_list_id, PermissionLevel.EDITOR)
        
        result.append(ContactResponse(
            id=str(contact.id),
            name=contact.name,
            email=contact.email,
            phone=contact.phone,
            company=contact.company,
            category=contact.category.value,
            address=contact.address,
            notes=contact.notes,
            created_at=contact.created_at.isoformat(),
            updated_at=contact.updated_at.isoformat(),
            last_contact_date=contact.last_contact_date.isoformat(),
            contact_list_id=str(contact.contact_list_id),
            created_by=str(contact.created_by),
            can_edit=user_permission,
            can_delete=user_permission
        ))
    
    return result

@contacts_router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: str,
    contact_data: ContactCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a contact (requires EDITOR permission)"""
    # Get the contact
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    
    # Check permissions
    if not check_list_permission(db, current_user, contact.contact_list_id, PermissionLevel.EDITOR):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to edit this contact"
        )
    
    # Update contact
    contact.name = contact_data.name
    contact.email = contact_data.email
    contact.phone = contact_data.phone
    contact.company = contact_data.company
    contact.category = contact_data.category
    contact.address = contact_data.address
    contact.notes = contact_data.notes
    if contact_data.last_contact_date:
        contact.last_contact_date = datetime.fromisoformat(contact_data.last_contact_date)
    contact.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(contact)
    
    user_permission = check_list_permission(db, current_user, contact.contact_list_id, PermissionLevel.EDITOR)
    
    return ContactResponse(
        id=str(contact.id),
        name=contact.name,
        email=contact.email,
        phone=contact.phone,
        company=contact.company,
        category=contact.category.value,
        address=contact.address,
        notes=contact.notes,
        created_at=contact.created_at.isoformat(),
        updated_at=contact.updated_at.isoformat(),
        last_contact_date=contact.last_contact_date.isoformat(),
        contact_list_id=str(contact.contact_list_id),
        created_by=str(contact.created_by),
        can_edit=user_permission,
        can_delete=user_permission
    )

@contacts_router.delete("/{contact_id}")
async def delete_contact(
    contact_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a contact (requires EDITOR permission)"""
    # Get the contact
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    
    # Check permissions
    if not check_list_permission(db, current_user, contact.contact_list_id, PermissionLevel.EDITOR):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to delete this contact"
        )
    
    # Delete contact
    db.delete(contact)
    db.commit()
    
    return {"message": "Contact deleted successfully"}

# Contact Lists endpoints (Phase 2)
@contacts_router.get("/lists", response_model=List[ContactListResponse])
async def get_contact_lists(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all contact lists accessible by the user"""
    user_lists = get_user_accessible_lists(db, current_user.id)
    
    result = []
    for ul in user_lists:
        contact_list = ul["list"]
        permission_level = ul["permission_level"]
        
        # Count contacts in this list
        contact_count = db.query(Contact).filter(Contact.contact_list_id == contact_list.id).count()
        
        # Determine permissions
        can_edit = permission_level in ["owner", "editor"]
        can_delete = permission_level == "owner"
        can_invite = permission_level == "owner"
        
        result.append(ContactListResponse(
            id=str(contact_list.id),
            name=contact_list.name,
            description=contact_list.description,
            created_at=contact_list.created_at.isoformat(),
            updated_at=contact_list.updated_at.isoformat(),
            is_default=contact_list.is_default,
            contact_count=contact_count,
            created_by=str(contact_list.created_by),
            permission_level=permission_level,
            can_edit=can_edit,
            can_delete=can_delete,
            can_invite=can_invite
        ))
    
    return result

@contacts_router.post("/lists", response_model=ContactListResponse)
async def create_contact_list(
    contact_list: ContactListCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new contact list"""
    # Create new list
    new_list = ContactList(
        name=contact_list.name,
        description=contact_list.description,
        created_by=current_user.id,
        is_default=False
    )
    
    db.add(new_list)
    db.commit()
    db.refresh(new_list)
    
    # Give the creator owner permission
    from models import ContactListPermission
    permission = ContactListPermission(
        user_id=current_user.id,
        contact_list_id=new_list.id,
        permission_level=PermissionLevel.OWNER,
        created_by=current_user.id
    )
    
    db.add(permission)
    db.commit()
    
    return ContactListResponse(
        id=str(new_list.id),
        name=new_list.name,
        description=new_list.description,
        created_at=new_list.created_at.isoformat(),
        updated_at=new_list.updated_at.isoformat(),
        is_default=new_list.is_default,
        contact_count=0,
        created_by=str(new_list.created_by),
        permission_level="owner",
        can_edit=True,
        can_delete=True,
        can_invite=True
    )

# Favorites endpoints (Phase 2 - User-based)
@contacts_router.post("/favorites/{contact_id}")
async def toggle_favorite(
    contact_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Toggle favorite status for a contact"""
    # Check if contact exists and user has access
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    
    # Check if user has access to the contact's list
    if not check_list_permission(db, current_user, contact.contact_list_id, PermissionLevel.VIEWER):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this contact"
        )
    
    # Check if already favorited
    existing_favorite = db.query(ContactFavorite).filter(
        ContactFavorite.user_id == current_user.id,
        ContactFavorite.contact_id == contact_id
    ).first()
    
    if existing_favorite:
        # Remove from favorites
        db.delete(existing_favorite)
        is_favorite = False
        message = "Removed from favorites"
    else:
        # Add to favorites
        favorite = ContactFavorite(
            user_id=current_user.id,
            contact_id=contact_id
        )
        db.add(favorite)
        is_favorite = True
        message = "Added to favorites"
    
    db.commit()
    
    return {
        "contact_id": contact_id,
        "is_favorite": is_favorite,
        "message": message
    }

@contacts_router.get("/favorites/list")
async def get_favorites(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get list of favorite contact IDs for the current user"""
    favorites = db.query(ContactFavorite).filter(
        ContactFavorite.user_id == current_user.id
    ).all()
    
    # Return just the array (remove the wrapper object)
    return [str(fav.contact_id) for fav in favorites]

@contacts_router.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# Import/Export with user context
@contacts_router.get("/export")
async def export_contacts(
    contact_list_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Export contacts (only from accessible lists)"""
    from fastapi.responses import JSONResponse
    
    # Get accessible lists
    if contact_list_id:
        if not check_list_permission(db, current_user, contact_list_id, PermissionLevel.VIEWER):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this contact list"
            )
        accessible_lists = [contact_list_id]
    else:
        user_lists = get_user_accessible_lists(db, current_user.id)
        accessible_lists = [ul["list_id"] for ul in user_lists]
    
    # Get contacts
    contacts = db.query(Contact).filter(Contact.contact_list_id.in_(accessible_lists)).all()
    
    # Format for export
    export_data = {
        "exported_at": datetime.utcnow().isoformat(),
        "exported_by": current_user.email,
        "contact_count": len(contacts),
        "contacts": [
            {
                "name": contact.name,
                "email": contact.email,
                "phone": contact.phone,
                "company": contact.company,
                "category": contact.category.value,
                "address": contact.address,
                "notes": contact.notes,
                "last_contact_date": contact.last_contact_date.isoformat(),
                "contact_list_id": str(contact.contact_list_id)
            }
            for contact in contacts
        ]
    }
    
    return JSONResponse(
        content=export_data,
        headers={
            "Content-Disposition": f"attachment; filename=contacts_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        }
    )

# Statistics with user context
class ContactsStatsResponse(BaseModel):
    total_contacts: int
    categories: dict
    recent_contacts: int
    accessible_lists: int

@contacts_router.get("/stats/summary", response_model=ContactsStatsResponse)
async def get_contacts_stats(
    contact_list_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get contact statistics for accessible lists"""
    from datetime import timedelta
    
    # Get accessible lists
    if contact_list_id:
        if not check_list_permission(db, current_user, contact_list_id, PermissionLevel.VIEWER):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this contact list"
            )
        accessible_lists = [contact_list_id]
    else:
        user_lists = get_user_accessible_lists(db, current_user.id)
        accessible_lists = [ul["list_id"] for ul in user_lists]
    
    # Get contacts in accessible lists
    contacts_query = db.query(Contact).filter(Contact.contact_list_id.in_(accessible_lists))
    
    # Total contacts
    total_contacts = contacts_query.count()
    
    # Category counts
    from sqlalchemy import func
    category_counts = db.query(
        Contact.category,
        func.count(Contact.id)
    ).filter(
        Contact.contact_list_id.in_(accessible_lists)
    ).group_by(Contact.category).all()
    
    categories = {cat.value: count for cat, count in category_counts}
    
    # Recent contacts (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_contacts = contacts_query.filter(Contact.created_at >= thirty_days_ago).count()
    
    return ContactsStatsResponse(
        total_contacts=total_contacts,
        categories=categories,
        recent_contacts=recent_contacts,
        accessible_lists=len(accessible_lists)
    )


auth_router = APIRouter(prefix="/api/auth", tags=["Authentication"])



# Fixed registration endpoint:
@auth_router.post("/register", response_model=UserResponse)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user"""
    try:
        print(f"🔍 DEBUG: Registration attempt for email: {user_data.email}")
        
        # Check if user already exists
        if get_user_by_email(db, user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        if get_user_by_username(db, user_data.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        
        # Create new user
        hashed_password = get_password_hash(user_data.password)
        
        db_user = User(
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            hashed_password=hashed_password,
            is_active=True,
            is_verified=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        print(f"✅ DEBUG: User created with ID: {db_user.id}")
        
        # Create a default contact list for the new user
        default_list = ContactList(
            name="My Contacts",
            description="Default contact list",
            created_by=db_user.id,
            is_default=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(default_list)
        db.commit()
        db.refresh(default_list)
        
        # Give the user owner permission for their default list
        permission = ContactListPermission(
            user_id=db_user.id,
            contact_list_id=default_list.id,
            permission_level=PermissionLevel.OWNER.value,
            created_by=db_user.id,
            created_at=datetime.utcnow()
        )
        db.add(permission)
        db.commit()
        
        return UserResponse(
            id=str(db_user.id),
            email=db_user.email,
            username=db_user.username,
            full_name=db_user.full_name,
            is_active=db_user.is_active,
            is_verified=db_user.is_verified,
            created_at=db_user.created_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ DEBUG: Registration error: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )
    
@auth_router.get("/test")
async def test_endpoint():
    """Simple test endpoint to verify auth router is working"""
    return {"message": "Auth router is working!", "timestamp": datetime.utcnow().isoformat()}
    
@auth_router.post("/login", response_model=Token)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """Login user and return JWT token"""
    user = authenticate_user(db, user_data.email, user_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, 
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@auth_router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information"""
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        username=current_user.username,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at.isoformat()
    )

@auth_router.post("/logout")
async def logout(current_user: User = Depends(get_current_active_user)):
    """Logout user (client-side token removal)"""
    return {"message": "Successfully logged out"}

# Team management routes
team_router = APIRouter(prefix="/api/team", tags=["Team Management"])

from pydantic import BaseModel
from typing import List

class TeamMemberResponse(BaseModel):
    user_id: str
    username: str
    full_name: str
    email: str
    permission_level: str
    added_at: str

class InviteUserRequest(BaseModel):
    email: str
    permission_level: str  # "owner", "editor", "viewer"

class UpdatePermissionRequest(BaseModel):
    user_id: str
    permission_level: str

@team_router.get("/lists/{list_id}/members", response_model=List[TeamMemberResponse])
async def get_list_members(
    list_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all members of a contact list"""
    # Check if user has access to this list
    if not check_list_permission(db, current_user, list_id, PermissionLevel.VIEWER):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this contact list"
        )
    
    # Get all permissions for this list
    permissions = db.query(ContactListPermission).filter(
        ContactListPermission.contact_list_id == list_id
    ).all()
    
    members = []
    for perm in permissions:
        members.append(TeamMemberResponse(
            user_id=str(perm.user.id),
            username=perm.user.username,
            full_name=perm.user.full_name,
            email=perm.user.email,
            permission_level=perm.permission_level.value,
            added_at=perm.created_at.isoformat()
        ))
    
    return members

@team_router.post("/lists/{list_id}/invite")
async def invite_user_to_list(
    list_id: str,
    invite_data: InviteUserRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Invite a user to join a contact list"""
    # Check if user has owner permission
    if not check_list_permission(db, current_user, list_id, PermissionLevel.OWNER):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only list owners can invite users"
        )
    
    # Validate permission level
    try:
        permission_level = PermissionLevel(invite_data.permission_level)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid permission level"
        )
    
    # Check if user is already a member
    existing_user = db.query(User).filter(User.email == invite_data.email).first()
    if existing_user:
        existing_permission = db.query(ContactListPermission).filter(
            ContactListPermission.user_id == existing_user.id,
            ContactListPermission.contact_list_id == list_id
        ).first()
        
        if existing_permission:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a member of this list"
            )
        
        # Add user directly if they exist
        permission = ContactListPermission(
            user_id=existing_user.id,
            contact_list_id=list_id,
            permission_level=permission_level,
            created_by=current_user.id
        )
        db.add(permission)
        db.commit()
        
        return {"message": f"User {invite_data.email} added to list successfully"}
    
    # Create invitation for non-existing users
    # Check if invitation already exists
    existing_invitation = db.query(TeamInvitation).filter(
        TeamInvitation.email == invite_data.email,
        TeamInvitation.contact_list_id == list_id,
        TeamInvitation.is_accepted == False,
        TeamInvitation.is_expired == False
    ).first()
    
    if existing_invitation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitation already sent to this email"
        )
    
    # Create new invitation
    invitation = TeamInvitation(
        email=invite_data.email,
        contact_list_id=list_id,
        permission_level=permission_level,
        invited_by=current_user.id,
        expires_at=datetime.utcnow() + timedelta(days=7)  # 7 days to accept
    )
    db.add(invitation)
    db.commit()
    
    return {"message": f"Invitation sent to {invite_data.email}"}

@team_router.put("/lists/{list_id}/permissions")
async def update_user_permission(
    list_id: str,
    permission_data: UpdatePermissionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a user's permission level for a contact list"""
    # Check if user has owner permission
    if not check_list_permission(db, current_user, list_id, PermissionLevel.OWNER):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only list owners can update permissions"
        )
    
    # Validate permission level
    try:
        new_permission_level = PermissionLevel(permission_data.permission_level)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid permission level"
        )
    
    # Find the permission to update
    permission = db.query(ContactListPermission).filter(
        ContactListPermission.user_id == permission_data.user_id,
        ContactListPermission.contact_list_id == list_id
    ).first()
    
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not a member of this list"
        )
    
    # Prevent user from removing their own owner status if they're the only owner
    if (permission.user_id == current_user.id and 
        permission.permission_level == PermissionLevel.OWNER and 
        new_permission_level != PermissionLevel.OWNER):
        
        owner_count = db.query(ContactListPermission).filter(
            ContactListPermission.contact_list_id == list_id,
            ContactListPermission.permission_level == PermissionLevel.OWNER
        ).count()
        
        if owner_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove owner permission - list must have at least one owner"
            )
    
    # Update permission
    permission.permission_level = new_permission_level
    db.commit()
    
    return {"message": "Permission updated successfully"}

@team_router.delete("/lists/{list_id}/members/{user_id}")
async def remove_user_from_list(
    list_id: str,
    user_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Remove a user from a contact list"""
    # Check if user has owner permission
    if not check_list_permission(db, current_user, list_id, PermissionLevel.OWNER):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only list owners can remove users"
        )
    
    # Find the permission to remove
    permission = db.query(ContactListPermission).filter(
        ContactListPermission.user_id == user_id,
        ContactListPermission.contact_list_id == list_id
    ).first()
    
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not a member of this list"
        )
    
    # Prevent removing the last owner
    if permission.permission_level == PermissionLevel.OWNER:
        owner_count = db.query(ContactListPermission).filter(
            ContactListPermission.contact_list_id == list_id,
            ContactListPermission.permission_level == PermissionLevel.OWNER
        ).count()
        
        if owner_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the last owner from the list"
            )
    
    # Remove permission
    db.delete(permission)
    db.commit()
    
    return {"message": "User removed from list successfully"}


# Update main.py to include the new routers:
app.include_router(contacts_router)
app.include_router(auth_router)  
app.include_router(team_router)

def initialize_analysis_data(url: str) -> Dict[str, Any]:
    """Initialize the analysis data structure"""
    return {
        'Analysis Date': datetime.now().strftime(DATE_FORMAT),
        'URL': str(url),
        'Latitude': None,
        'Longitude': None,
        'Full Address': None,
        'Postcode': None,
        'Property ID': None,
        'Title': None,
        'Advertiser Name': None,
        'Landlord Type': None,
        'Bills Included': None,
        'Household Gender': None,
        'Listing Status': None,
        'Main Photo URL': None,
        'Total Rooms': None,
        'Listed Rooms': None,
        'Available Rooms': None,
        'Available Rooms Details': [],
        'Taken Rooms': None,
        'Room Details': None,
        'All Rooms List': [],
        'Monthly Income': None,
        'Annual Income': None,
        'Meets Requirements': None
    }

def save_analysis_to_db(db: Session, property_obj: Property, analysis_data: Dict[str, Any]) -> PropertyAnalysis:
    """Save analysis results to database"""
    analysis_kwargs = {
        'advertiser_name': analysis_data.get('Advertiser Name'),
        'landlord_type': analysis_data.get('Landlord Type'),
        'bills_included': analysis_data.get('Bills Included'),
        'household_gender': analysis_data.get('Household Gender'),
        'listing_status': analysis_data.get('Listing Status'),
        'total_rooms': analysis_data.get('Total Rooms'),
        'available_rooms': analysis_data.get('Available Rooms'),
        'taken_rooms': analysis_data.get('Taken Rooms'),
        'listed_rooms': analysis_data.get('Listed Rooms'),
        'monthly_income': analysis_data.get('Monthly Income'),
        'annual_income': analysis_data.get('Annual Income'),
        'meets_requirements': analysis_data.get('Meets Requirements'),
        'room_details': analysis_data.get('Room Details'),
        'all_rooms_list': analysis_data.get('All Rooms List'),
        'available_rooms_details': analysis_data.get('Available Rooms Details'),
        'main_photo_url': analysis_data.get('Main Photo URL'),
        'analysis_date': analysis_data.get('Analysis Date'),
        'title': analysis_data.get('Title')
    }
    
    return AnalysisCRUD.create_analysis(db, property_obj.id, **analysis_kwargs)

def format_property_summary(property_obj: Property, db: Session) -> Dict[str, Any]:
    """Format property with latest analysis for API response"""
    # Get the most recent analysis explicitly
    latest_analysis = AnalysisCRUD.get_latest_analysis(db, property_obj.id)  # ✅ Now db is available
    
    return {
        "property_id": str(property_obj.id),
        "url": property_obj.url,
        "address": property_obj.address,
        "monthly_income": float(latest_analysis.monthly_income) if latest_analysis and latest_analysis.monthly_income else None,
        "annual_income": float(latest_analysis.annual_income) if latest_analysis and latest_analysis.annual_income else None,
        "total_rooms": latest_analysis.total_rooms if latest_analysis else None,
        "available_rooms": latest_analysis.available_rooms if latest_analysis else None,
        "bills_included": latest_analysis.bills_included if latest_analysis else None,
        "meets_requirements": latest_analysis.meets_requirements if latest_analysis else None,
        "analysis_date": latest_analysis.analysis_date if latest_analysis else None,
        "latitude": property_obj.latitude,
        "longitude": property_obj.longitude,
        "advertiser_name": latest_analysis.advertiser_name if latest_analysis else None,
        "landlord_type": latest_analysis.landlord_type if latest_analysis else None,
        "listing_status": latest_analysis.listing_status if latest_analysis else None,
        "date_gone": None,  # To be implemented later
        # Add metadata about analysis history
        "last_updated": latest_analysis.created_at.isoformat() if latest_analysis else None,
        "total_analyses": len(property_obj.analyses) if property_obj.analyses else 0
    }
# Update your analyze_property_task function in main.py to include room tracking:

def replace_city_in_address(address_string, old_city, new_city):
    """
    Replace the old city name with the new city name in an address string
    
    Args:
        address_string (str): Original address like "Middleton Road, Grimsbury, Cherwell, OX16 3WT"
        old_city (str): City to replace like "Cherwell"  
        new_city (str): New city like "Banbury"
    
    Returns:
        str: Updated address like "Middleton Road, Grimsbury, Banbury, OX16 3WT"
    """
    if not address_string or not old_city or not new_city:
        return address_string
    
    # Replace the old city with new city (case insensitive)
    updated_address = address_string.replace(old_city, new_city)
    
    # Also try lowercase replacement in case of case mismatch
    updated_address = updated_address.replace(old_city.lower(), new_city)
    updated_address = updated_address.replace(old_city.upper(), new_city)
    
    return updated_address

async def analyze_property_task(task_id: str, url: str, existing_property_id: str = None):
    """Background task to analyze a property with database storage and room tracking"""
    
    # Create a new database session for this background task
    from database import SessionLocal
    db = SessionLocal()
    
    try:
        # Update task status
        TaskCRUD.update_task_status(db, task_id, "running", {"coordinates": "running"})
        
        # Log analytics event
        AnalyticsCRUD.log_event(db, "analysis_started", task_id=task_id)
        
        # FIXED: Use existing_property_id if provided, otherwise lookup by ANY URL (including linked URLs)
        if existing_property_id:
            print(f"[{task_id}] Analyzing existing property: {existing_property_id}")
            property_obj = PropertyCRUD.get_property_by_id(db, existing_property_id)
            if not property_obj:
                raise Exception(f"Property with ID {existing_property_id} not found")
        else:
            print(f"[{task_id}] Looking up property by URL: {url}")
            
            # FIXED: Use get_property_by_any_url instead of get_property_by_url
            # This function checks BOTH the main properties table AND the property_urls table
            property_obj = PropertyURLCRUD.get_property_by_any_url(db, url)
            
            if not property_obj:
                # Create new property if not found
                print(f"[{task_id}] Creating new property for URL: {url}")
                property_obj = PropertyCRUD.create_property(db, url)
            else:
                print(f"[{task_id}] Found existing property via linked URL: {property_obj.id}")
                
        print(f"[{task_id}] Analyzing property ID: {property_obj.id}")
        
        # Initialize analysis data
        analysis_data = initialize_analysis_data(url)
        
        # Step 1: Extract coordinates
        print(f"[{task_id}] Starting coordinate extraction...")
        coords = extract_coordinates(url, analysis_data)
        
        if coords.get('found'):
            TaskCRUD.update_task_status(db, task_id, "running", {"coordinates": "completed", "geocoding": "running"})            
            # Update property with coordinates - USE ID NOT OBJECT
            PropertyCRUD.update_property(
                db, 
                property_obj.id,  # Use ID instead of object
                latitude=coords['latitude'],
                longitude=coords['longitude']
            )
            
            # Get address from coordinates using Postcodes.io for UK properties
            lat, lon = coords['latitude'], coords['longitude']

            # First try Nominatim for basic address info (STREET LEVEL DATA)
            address_info = reverse_geocode_nominatim(lat, lon, analysis_data)
            
            # Store the ORIGINAL street address from Nominatim before enhancement
            original_street_address = analysis_data.get('Full Address')
            print(f"🏠 Original street address from Nominatim: {original_street_address}")

            # Then enhance with Postcodes.io data for UK properties
            postcode = analysis_data.get('Postcode')

            if postcode:
                # First get raw postcode.io data
                location_data = await geocode_postcode_io(postcode)
                
                if location_data:
                    # Then get enhanced city detection
                    from modules.coordinates import get_location_from_uk_postcode
                    enhanced_data = get_location_from_uk_postcode(postcode, analysis_data)
                    
                    # Use raw postcode.io data for everything EXCEPT city
                    city_to_use = location_data.get('city')  # Default to raw district
                    
                    # Build the corrected address with enhanced city
                    corrected_address = original_street_address
                    
                    if enhanced_data and analysis_data.get('City'):
                        city_to_use = analysis_data.get('City')  # Override with enhanced city
                        
                        # Replace the old city in the address string with the enhanced city
                        old_city = location_data.get('city')  # This would be "Cherwell"
                        corrected_address = replace_city_in_address(original_street_address, old_city, city_to_use)
                        
                        print(f"🎯 Using enhanced city: {city_to_use} (instead of {old_city})")
                        print(f"🏠 Updated address: {original_street_address} → {corrected_address}")
                    
                    PropertyCRUD.update_property(
                        db,
                        property_obj.id,  # Use ID instead of object
                        address=corrected_address,                 # USE CORRECTED ADDRESS WITH ENHANCED CITY
                        postcode=location_data.get('postcode'),     # Raw from postcode.io
                        latitude=location_data.get('latitude'),     # Raw from postcode.io
                        longitude=location_data.get('longitude'),   # Raw from postcode.io
                        city=city_to_use,                          # Enhanced if available, otherwise raw
                        area=location_data.get('area'),            # Raw ward from postcode.io
                        district=location_data.get('district'),    # Raw district from postcode.io
                        county=location_data.get('county'),        # Raw county from postcode.io
                        country=location_data.get('country'),      # Raw country from postcode.io
                        constituency=location_data.get('constituency') # Raw constituency from postcode.io
                    )
                    print(f"✅ Final address: {corrected_address}")
                    print(f"✅ Enhanced city: {city_to_use}, Raw area: {location_data.get('area')}, County: {location_data.get('county')}")
                
                else:
                    # Fallback: postcode lookup failed, try reverse geocoding
                    print("⚠️ Direct postcode lookup failed, trying reverse geocoding...")
                    location_data = await reverse_geocode_postcode_io(lat, lon)
                    
                    if location_data:
                        PropertyCRUD.update_property(
                            db,
                            property_obj.id,  # Use ID instead of object
                            address=original_street_address,       # PRESERVE STREET ADDRESS
                            postcode=location_data.get('postcode'),
                            latitude=location_data.get('latitude'),
                            longitude=location_data.get('longitude'),
                            city=location_data.get('city'),        # No enhancement available, use raw
                            area=location_data.get('area'),
                            district=location_data.get('district'),
                            county=location_data.get('county'),
                            country=location_data.get('country'),
                            constituency=location_data.get('constituency')
                        )
                        print(f"✅ Reverse geocoding - Street: {original_street_address}, City: {location_data.get('city')}")
                    else:
                        # Final fallback: use Nominatim data if all postcode methods fail
                        print("⚠️ All postcode methods failed, using Nominatim data...")
                        if address_info:
                            PropertyCRUD.update_property(
                                db,
                                property_obj.id,  # Use ID instead of object
                                address=original_street_address,   # PRESERVE STREET ADDRESS
                                postcode=analysis_data.get('Postcode'),
                                city=analysis_data.get('City'),
                                area=analysis_data.get('Area'),
                                district=analysis_data.get('District'),
                                county=analysis_data.get('County'),
                                country=analysis_data.get('Country'),
                                constituency=analysis_data.get('Constituency')
                            )
                            print(f"ℹ️ Using Nominatim data - Street: {original_street_address}")
            
            elif address_info:
                # No postcode available, use Nominatim data directly
                PropertyCRUD.update_property(
                    db,
                    property_obj.id,  # Use ID instead of object
                    address=original_street_address,           # PRESERVE STREET ADDRESS
                    postcode=analysis_data.get('Postcode'),
                    city=analysis_data.get('City'),
                    area=analysis_data.get('Area'),
                    district=analysis_data.get('District'),
                    county=analysis_data.get('County'),
                    country=analysis_data.get('Country'),
                    constituency=analysis_data.get('Constituency')
                )
                print(f"ℹ️ Using Nominatim geocoding data (no postcode available) - Street: {original_street_address}")

            TaskCRUD.update_task_status(db, task_id, "running", {
                "coordinates": "completed", 
                "geocoding": "completed", 
                "property_details": "running"
            })
            
            # Extract additional property details
            details = extract_property_details(url, analysis_data)
            
            # Update property with additional details if available
            if analysis_data.get('Property ID'):
                # Get fresh property object for this session
                fresh_property = PropertyCRUD.get_property_by_id(db, property_obj.id)
                if fresh_property:
                    fresh_property.property_id = analysis_data.get('Property ID')
                    db.commit()
            
            TaskCRUD.update_task_status(db, task_id, "running", {
                "coordinates": "completed",
                "geocoding": "completed", 
                "property_details": "completed",
                "scraping": "running"
            })
        else:
            TaskCRUD.update_task_status(db, task_id, "running", {
                "coordinates": "failed",
                "geocoding": "skipped",
                "property_details": "skipped",
                "scraping": "running"
            })
        
        # Step 2: Extract price section and analyze
        print(f"[{task_id}] Starting price section extraction...")
        extract_price_section(url, analysis_data)
        
        TaskCRUD.update_task_status(db, task_id, "running", {
            "coordinates": "completed" if coords.get('found') else "failed",
            "geocoding": "completed" if coords.get('found') else "skipped",
            "property_details": "completed" if coords.get('found') else "skipped",
            "scraping": "completed",
            "room_tracking": "running"
        })
        
        # Step 3: Save analysis to database
        analysis_obj = save_analysis_to_db(db, property_obj, analysis_data)
        
        # Step 4: Process room tracking
        print(f"[{task_id}] Processing room tracking...")
        rooms_list = analysis_data.get('All Rooms List', [])
        
        # Check if listing is expired and handle differently
        if analysis_data.get('_EXPIRED_LISTING'):
            # For expired listings, mark existing rooms as taken
            print(f"[{task_id}] Marking existing rooms as taken for expired listing...")
            room_results = RoomCRUD.mark_all_property_rooms_as_taken(
                db, property_obj.id, analysis_obj.id
            )
            print(f"[{task_id}] Room status update: {len(room_results.get('updated_rooms', []))} rooms marked as taken")
        else:
            # For active listings, use normal room tracking
            if rooms_list:
                room_results = RoomCRUD.process_rooms_list(
                    db, property_obj.id, rooms_list, analysis_obj.id
                )
                print(f"[{task_id}] Room tracking: {len(room_results.get('new_rooms', []))} new, "
                      f"{len(room_results.get('disappeared_rooms', []))} disappeared, "
                      f"{room_results.get('total_changes', 0)} total changes")
        
        TaskCRUD.update_task_status(db, task_id, "running", {
            "coordinates": "completed" if coords.get('found') else "failed",
            "geocoding": "completed" if coords.get('found') else "skipped",
            "property_details": "completed" if coords.get('found') else "skipped",
            "scraping": "completed",
            "room_tracking": "completed",
            "excel_export": "running"
        })
        
        # Step 5: Save to Excel in organized folder
        excel_filename = f"property_{task_id}.xlsx"
        excel_full_path = save_to_excel(analysis_data, excel_filename)
        analysis_data["excel_file"] = excel_filename
        analysis_data["excel_path"] = excel_full_path
        
        TaskCRUD.update_task_status(db, task_id, "completed", {
            "coordinates": "completed" if coords.get('found') else "failed",
            "geocoding": "completed" if coords.get('found') else "skipped",
            "property_details": "completed" if coords.get('found') else "skipped",
            "scraping": "completed",
            "room_tracking": "completed",
            "excel_export": "completed"
        })
        
        # Log completion
        TaskCRUD.update_task_status(db, task_id, "completed", {
            "coordinates": "completed",
            "geocoding": "completed", 
            "property_details": "completed",
            "scraping": "completed",
            "excel_export": "completed"
        })
        
        print(f"[{task_id}] Analysis completed successfully!")
        
    except Exception as e:
        print(f"[{task_id}] Analysis failed: {str(e)}")
        TaskCRUD.update_task_status(db, task_id, "failed", error_message=str(e))
        
        # Log failure
        AnalyticsCRUD.log_event(
            db, 
            "analysis_failed", 
            task_id=task_id,
            event_data={"error": str(e)}
        )
        raise
    finally:
        # CRITICAL: Always close the database session
        db.close()

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "HMO Analyser API with Database and Organized Storage",
        "version": "2.0.0",
        "features": ["Database Storage", "Analytics", "Search", "Historical Data", "Organized File Management"],
        "endpoints": {
            "analyze": "/api/analyze",
            "status": "/api/analysis/{task_id}",
            "properties": "/api/properties",
            "search": "/api/properties/search",
            "analytics": "/api/analytics",
            "export": "/api/export/{property_id}",
            "export_stats": "/api/admin/export-stats"
        }
    }

@app.post("/api/analyze", response_model=PropertyAnalysisResponse)
async def analyze_property(request: PropertyAnalysisRequest, db: Session = Depends(get_db)):
    """Analyze a property from SpareRoom URL with duplicate detection and user confirmation"""
    
    task_id = str(uuid.uuid4())
    
    # Check if property already exists by URL
    existing_property = PropertyCRUD.get_property_by_url(db, str(request.url))
    
    if existing_property:
        # Property URL already exists - update existing property
        existing_analyses = AnalysisCRUD.get_all_analyses(db, existing_property.id)
        
        # FIXED: CREATE TASK BEFORE STARTING BACKGROUND ANALYSIS
        TaskCRUD.create_property_task(db, task_id, existing_property.id)
        
        property_metadata = {
            "property_id": str(existing_property.id),
            "is_existing": True,
            "total_analyses": len(existing_analyses),
            "has_changes_history": len(existing_analyses) > 0,
            "last_analysis_date": existing_analyses[0].created_at.isoformat() if existing_analyses else None
        }
        
        # Queue background task for existing property
        asyncio.create_task(analyze_property_task(task_id, str(request.url), existing_property.id))

        return PropertyAnalysisResponse(
            task_id=task_id,
            status="queued",
            message="🔄 Updating existing property analysis...",
            property_metadata=property_metadata
        )
            
    else:
        # NEW PROPERTY - Check for potential duplicates (unless force_separate is True)
        if not request.force_separate:
            print(f"🔍 New URL detected, checking for potential duplicates...")
            
            try:
                # Extract property details for duplicate checking
                extracted_data = extract_property_details_for_duplicate_check(str(request.url))
                
                if extracted_data and extracted_data.get('address'):
                    # Find potential duplicates
                    potential_matches = find_potential_duplicates(
                        db=db,
                        new_url=str(request.url),
                        new_address=extracted_data['address'],
                        new_latitude=extracted_data.get('latitude'),
                        new_longitude=extracted_data.get('longitude'),
                        new_price=extracted_data.get('monthly_income'),
                        new_room_count=extracted_data.get('total_rooms'),
                        new_advertiser=extracted_data.get('advertiser_name'),
                        min_confidence=0.6,  # Lower threshold for user confirmation
                        max_results=1  # Only check the best match
                    )
                    
                    if potential_matches:
                        best_match = potential_matches[0]
                        print(f"🚨 POTENTIAL DUPLICATE DETECTED!")
                        print(f"   Confidence: {best_match.confidence_score}")
                        print(f"   Existing Property: {best_match.address}")
                        print(f"   Existing URL: {best_match.existing_url}")
                        print(f"   New URL: {str(request.url)}")
                        
                        # AUTO-LINK high confidence matches (70%+)
                        if best_match.confidence_score >= 0.7:
                            print(f"🔗 Auto-linking URL to existing property (confidence: {best_match.confidence_score})")
                            
                            # Link the URL to existing property
                            try:
                                from models import PropertyURL
                                
                                # Check if URL already exists in property_urls table
                                existing_url_record = (db.query(PropertyURL)
                                                    .filter(PropertyURL.url == str(request.url))
                                                    .first())
                                
                                if existing_url_record:
                                    print(f"🔗 URL already linked to property: {existing_url_record.property_id}")
                                    existing_property_id = existing_url_record.property_id
                                else:
                                    # URL doesn't exist yet, create new PropertyURL record
                                    property_url = PropertyURL(
                                        property_id=best_match.property_id,
                                        url=str(request.url),
                                        is_primary=False,
                                        confidence_score=best_match.confidence_score
                                    )
                                    db.add(property_url)
                                    db.commit()
                                    existing_property_id = best_match.property_id
                                    
                                    # Add change record
                                    PropertyChangeCRUD.create_change(
                                        db=db,
                                        property_id=best_match.property_id,
                                        change_type="url_linked",
                                        field_name="additional_url",
                                        old_value="",
                                        new_value=str(request.url),
                                        change_summary=f"Auto-linked duplicate URL (confidence: {best_match.confidence_score:.1%})"
                                    )
                                    
                                    print(f"🔗 Successfully linked new URL to existing property")
                                
                                # FIXED: CREATE TASK BEFORE STARTING BACKGROUND ANALYSIS
                                TaskCRUD.create_property_task(db, task_id, existing_property_id)
                                
                                # Get existing property and analyses for metadata
                                existing_property = PropertyCRUD.get_property_by_id(db, existing_property_id)
                                existing_analyses = AnalysisCRUD.get_all_analyses(db, existing_property.id)
                                
                                property_metadata = {
                                    "property_id": str(existing_property.id),
                                    "is_existing": True,
                                    "was_auto_linked": True,
                                    "confidence_score": best_match.confidence_score,
                                    "total_analyses": len(existing_analyses),
                                    "has_changes_history": len(existing_analyses) > 0
                                }
                                
                                # Queue background task for existing property
                                asyncio.create_task(analyze_property_task(task_id, str(request.url)))
                                
                                return PropertyAnalysisResponse(
                                    task_id=task_id,
                                    status="queued",
                                    message="🔗 Auto-linked to existing property - updating analysis...",
                                    property_metadata=property_metadata
                                )
                                
                            except Exception as e:
                                print(f"❌ Failed to auto-link URL: {str(e)}")
                                # If linking fails, rollback and proceed as separate property
                                db.rollback()
                                
                                # Fall through to creating separate property
                                print(f"⚠️ Proceeding to create separate property due to linking failure")
                        
                        # MEDIUM CONFIDENCE (30-70%) - Ask user for confirmation
                        elif 0.3 <= best_match.confidence_score < 0.7:
                            print(f"❓ Medium confidence match - requesting user confirmation")
                            
                            return PropertyAnalysisResponse(
                                task_id=task_id,
                                status="duplicate_detected",
                                message="Potential duplicate property detected. Please confirm your action.",
                                duplicate_detected=True,
                                duplicate_data={
                                    "potential_matches": [
                                        {
                                            "property_id": best_match.property_id,
                                            "existing_url": best_match.existing_url,
                                            "address": best_match.address,
                                            "confidence_score": best_match.confidence_score,
                                            "match_factors": best_match.match_factors,
                                            "property_details": best_match.property_details
                                        }
                                    ],
                                    "extracted_address": extracted_data['address'],
                                    "extraction_successful": True
                                }
                            )
                    
                    # No matches found or low confidence - proceed as new property
                    print(f"✅ No duplicates detected or confidence too low - creating new property")
                    
                else:
                    print(f"⚠️ Could not extract property details for duplicate checking")
                    
            except Exception as e:
                # Duplicate detection failed - create new property anyway but log the error
                print(f"❌ Duplicate detection failed: {str(e)}")
        
        # CREATE NEW PROPERTY (no duplicates or force_separate=True)
        property_obj = PropertyCRUD.create_property(db, str(request.url))
        
        # FIXED: CREATE TASK BEFORE STARTING BACKGROUND ANALYSIS
        TaskCRUD.create_property_task(db, task_id, property_obj.id)
        
        property_metadata = {
            "property_id": str(property_obj.id),
            "is_existing": False,
            "total_analyses": 0,
            "has_changes_history": False,
            "force_separate": request.force_separate
        }
        
        message = "🔗 Linked to existing property - starting analysis..." if request.force_separate else "✨ New property detected - starting first-time analysis..."
        
        # Queue background task for new property
        asyncio.create_task(analyze_property_task(task_id, str(request.url)))
        
        return PropertyAnalysisResponse(
            task_id=task_id,
            status="queued",
            message=message,
            property_metadata=property_metadata
        )

# FIX FOR main.py - Update the get_analysis_status endpoint around line 445

@app.get("/api/analysis/{task_id}")
async def get_analysis_status(task_id: str, db: Session = Depends(get_db)):
    """Get the status of an analysis task"""
    try:
        task = TaskCRUD.get_task_by_id(db, task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # FIXED: Convert integer values to strings for Pydantic validation
        progress = task.progress or {}
        
        # Convert numeric values to strings to match Pydantic model expectations
        if isinstance(progress.get('updated_count'), int):
            progress['updated_count'] = str(progress['updated_count'])
        
        if isinstance(progress.get('changes_detected'), int):
            progress['changes_detected'] = str(progress['changes_detected'])
        
        # Ensure all progress values are strings
        for key, value in progress.items():
            if isinstance(value, (int, float)):
                progress[key] = str(value)
        
        # FIXED: Get the actual analysis result when task is completed
        result = None
        if task.status == "completed" and task.property_id:
            # This is an individual property analysis task that completed
            # Get the latest analysis for this property
            try:
                property_obj = PropertyCRUD.get_property_by_id(db, task.property_id)
                if property_obj:
                    latest_analysis = AnalysisCRUD.get_latest_analysis(db, property_obj.id)
                    if latest_analysis:
                        # Format the result similar to the existing format_property_summary
                        result = {
                            'Property ID': str(property_obj.id),
                            'URL': property_obj.url,
                            'Full Address': property_obj.address,
                            'Postcode': property_obj.postcode,
                            'Latitude': property_obj.latitude,
                            'Longitude': property_obj.longitude,
                            'Total Rooms': latest_analysis.total_rooms,
                            'Available Rooms': latest_analysis.available_rooms,
                            'Monthly Income': float(latest_analysis.monthly_income) if latest_analysis.monthly_income else None,
                            'Annual Income': float(latest_analysis.annual_income) if latest_analysis.annual_income else None,
                            'Bills Included': latest_analysis.bills_included,
                            'Meets Requirements': latest_analysis.meets_requirements,
                            'Advertiser Name': latest_analysis.advertiser_name,
                            'Landlord Type': latest_analysis.landlord_type,
                            'Listing Status': latest_analysis.listing_status,
                            'Analysis Date': latest_analysis.analysis_date.isoformat() if latest_analysis.analysis_date else None,
                            'Created At': latest_analysis.created_at.isoformat() if latest_analysis.created_at else None
                        }
            except Exception as e:
                print(f"Error fetching analysis result for task {task_id}: {e}")
                # Don't fail the whole request, just leave result as None
        
        return AnalysisStatus(
            task_id=task_id,
            status=task.status,
            progress=progress,
            started_at=task.started_at.isoformat() if task.started_at else None,
            completed_at=task.completed_at.isoformat() if task.completed_at else None,
            error_message=task.error_message,
            result=result  # NOW PROPERLY RETURNS THE ANALYSIS RESULT
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting analysis status: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting analysis status: {str(e)}")


@app.get("/api/properties")
async def get_all_properties(
    limit: int = 100, 
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get all analyzed properties with pagination - shows latest analysis data"""
    properties = PropertyCRUD.get_all_properties(db, limit=limit, offset=offset)
    
    # Format each property with latest analysis data
    formatted_properties = []
    for prop in properties:
        # Pass db session to format function
        summary = format_property_summary_with_db(prop, db)
        formatted_properties.append(summary)
    
    return formatted_properties

def format_property_summary_with_db(property_obj: Property, db: Session) -> Dict[str, Any]:
    """Format property with latest analysis for API response (with db session)"""
    # Get the most recent analysis explicitly using the db session
    latest_analysis = AnalysisCRUD.get_latest_analysis(db, property_obj.id)

    # PHASE 1 ADDITION: Calculate property date gone
    property_date_gone = calculate_property_date_gone(db, property_obj.id)

    # ✅ NEW: Get room history data
    rooms_data = RoomCRUD.get_property_rooms_with_history(db, property_obj.id)
    
    return {
        "property_id": str(property_obj.id),
        "url": property_obj.url,
        "address": property_obj.address,
        "monthly_income": float(latest_analysis.monthly_income) if latest_analysis and latest_analysis.monthly_income else None,
        "annual_income": float(latest_analysis.annual_income) if latest_analysis and latest_analysis.annual_income else None,
        "total_rooms": latest_analysis.total_rooms if latest_analysis else None,
        "available_rooms": latest_analysis.available_rooms if latest_analysis else None,
        "available_rooms_details": latest_analysis.available_rooms_details if latest_analysis else [],
        "bills_included": latest_analysis.bills_included if latest_analysis else None,
        "meets_requirements": latest_analysis.meets_requirements if latest_analysis else None,
        "analysis_date": latest_analysis.analysis_date if latest_analysis else None,
        "latitude": property_obj.latitude,
        "longitude": property_obj.longitude,
        "advertiser_name": latest_analysis.advertiser_name if latest_analysis else None,
        "landlord_type": latest_analysis.landlord_type if latest_analysis else None,
        "listing_status": latest_analysis.listing_status if latest_analysis else None,
        "date_gone": property_date_gone,  # Calculated from room availability
        "last_updated": str(latest_analysis.created_at) if latest_analysis and latest_analysis.created_at else None,
        "total_analyses": len(property_obj.analyses) if property_obj.analyses else 0,
        "has_updates": len(property_obj.analyses) > 1 if property_obj.analyses else False,
        "date_found": property_obj.created_at.strftime('%d/%m/%y') if property_obj.created_at else None,
        # ✅ FIXED: Add room history data for the history table
        "Rooms With History": rooms_data  # This will enable room numbers in the table
    }

@app.get("/api/properties/search")
async def search_properties(
    q: str = None,
    min_income: float = None,
    max_income: float = None,
    min_rooms: int = None,
    bills_included: str = None,
    meets_requirements: str = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Search properties with filters - shows latest analysis data"""
    properties = PropertyCRUD.search_properties(
        db=db,
        search_term=q,
        min_income=min_income,
        max_income=max_income,
        min_rooms=min_rooms,
        bills_included=bills_included,
        meets_requirements=meets_requirements,
        limit=limit
    )
    
    # Format each property with latest analysis data
    formatted_properties = []
    for prop in properties:
        summary = format_property_summary_with_db(prop, db)
        formatted_properties.append(summary)
    
    return formatted_properties

@app.get("/api/properties/search")
async def search_properties(
    q: str = None,
    min_income: float = None,
    max_income: float = None,
    min_rooms: int = None,
    bills_included: str = None,
    meets_requirements: str = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Search properties with filters"""
    properties = PropertyCRUD.search_properties(
        db=db,
        search_term=q,
        min_income=min_income,
        max_income=max_income,
        min_rooms=min_rooms,
        bills_included=bills_included,
        meets_requirements=meets_requirements,
        limit=limit
    )
    return [format_property_summary(prop) for prop in properties]

# Update the get_property_details endpoint to include room data:
@app.get("/api/properties/{property_id}")
async def get_property_details(property_id: str, db: Session = Depends(get_db)):
    """Get detailed information about a specific property including room history - UPDATED for Phase 1"""
    
    property_obj = PropertyCRUD.get_property_by_id(db, property_id)
    
    if not property_obj:
        raise HTTPException(
            status_code=404,
            detail="Property not found"
        )
    
    # Get latest analysis
    latest_analysis = AnalysisCRUD.get_latest_analysis(db, property_obj.id)
    
    if not latest_analysis:
        raise HTTPException(
            status_code=404,
            detail="No analysis found for this property"
        )
    
    # PHASE 1 ADDITION: Get enhanced room data with periods and date gone
    rooms_data = RoomCRUD.get_property_rooms_with_history(db, property_obj.id)
    
    # PHASE 1 ADDITION: Get availability summary - USE THE CRUD FUNCTION (NOT ASYNC)
    availability_summary = get_property_availability_summary(db, property_obj.id)
    
    # Return detailed property data with Phase 1 enhancements
    return {
        'Analysis Date': latest_analysis.analysis_date,
        'Date Found': property_obj.created_at.strftime('%d/%m/%y') if property_obj.created_at else None,
        'URL': property_obj.url,
        'Latitude': property_obj.latitude,
        'Longitude': property_obj.longitude,
        'Full Address': property_obj.address,
        'Postcode': property_obj.postcode,
        'Property ID': property_obj.property_id,
        'Title': latest_analysis.title,
        'Advertiser Name': latest_analysis.advertiser_name,
        'Landlord Type': latest_analysis.landlord_type,
        'Bills Included': latest_analysis.bills_included,
        'Household Gender': latest_analysis.household_gender,
        'Listing Status': latest_analysis.listing_status,
        'Main Photo URL': latest_analysis.main_photo_url,
        'Total Rooms': latest_analysis.total_rooms,
        'Listed Rooms': latest_analysis.listed_rooms,
        'Available Rooms': latest_analysis.available_rooms,
        'Available Rooms Details': latest_analysis.available_rooms_details,
        'Taken Rooms': latest_analysis.taken_rooms,
        'Room Details': latest_analysis.room_details,
        'All Rooms List': latest_analysis.all_rooms_list,
        'Monthly Income': float(latest_analysis.monthly_income) if latest_analysis.monthly_income else None,
        'Annual Income': float(latest_analysis.annual_income) if latest_analysis.annual_income else None,
        'Meets Requirements': latest_analysis.meets_requirements,
        
        # PHASE 1 ADDITIONS:
        'Date Gone': availability_summary.get("property_date_gone"),  # NOW THIS WILL WORK
        'Rooms With History': rooms_data,  # Enhanced room data with periods
        'Availability Summary': {
            'total_rooms': availability_summary["total_rooms"],
            'current_available_rooms': availability_summary["current_available_rooms"],
            'rooms_currently_gone': availability_summary["rooms_currently_gone"],
            'total_availability_periods': availability_summary["total_periods"],
            'rooms_with_period_history': availability_summary["rooms_with_periods"]
        }
    }

@app.post("/api/properties/check-duplicates", response_model=DuplicateCheckResponse)
async def check_potential_duplicates(
    request: DuplicateCheckRequest,
    db: Session = Depends(get_db)
):
    """
    Check for potential duplicate properties before analysis
    """
    try:
        # Extract property details from the new URL
        extracted_data = extract_property_details_for_duplicate_check(request.url)
        
        if not extracted_data or not extracted_data.get('address'):
            return DuplicateCheckResponse(
                has_potential_duplicates=False,
                potential_matches=[],
                extracted_address=None,
                extraction_successful=False
            )
        
        # Find potential duplicates using the dedicated module
        potential_matches = find_potential_duplicates(
            db=db,
            new_url=request.url,
            new_address=extracted_data['address'],
            new_latitude=extracted_data.get('latitude'),
            new_longitude=extracted_data.get('longitude'),
            new_price=extracted_data.get('monthly_income'),
            new_room_count=extracted_data.get('total_rooms'),
            new_advertiser=extracted_data.get('advertiser_name'),
            min_confidence=0.3,  # 30% minimum confidence
            max_results=5
        )
        
        return DuplicateCheckResponse(
            has_potential_duplicates=len(potential_matches) > 0,
            potential_matches=potential_matches,
            extracted_address=extracted_data['address'],
            extraction_successful=True
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error checking for duplicates: {str(e)}"
        )

@app.post("/api/properties/{existing_property_id}/link-url")
async def link_url_to_existing_property(
    existing_property_id: str,
    request: dict,  # {"new_url": "..."}
    db: Session = Depends(get_db)
):
    """
    Link a new URL to an existing property (when user confirms it's the same property)
    """
    try:
        new_url = request.get("new_url")
        if not new_url:
            raise HTTPException(status_code=400, detail="new_url is required")
            
        # Verify existing property exists
        existing_property = PropertyCRUD.get_property_by_id(db, existing_property_id)
        if not existing_property:
            raise HTTPException(status_code=404, detail="Existing property not found")
        
        # Check if URL is already in database
        url_exists = db.query(Property).filter(Property.url == new_url).first()
        if url_exists:
            raise HTTPException(status_code=400, detail="URL already exists in database")
        
        # Add to property_urls table
        from models import PropertyURL
        property_url = PropertyURL(
            property_id=existing_property_id,
            url=new_url,
            is_primary=False,
            confidence_score=1.0  # User confirmed
        )
        db.add(property_url)
        db.commit()
        
        # Add this as a property change record to track the link
        PropertyChangeCRUD.create_change(
            db=db,
            property_id=existing_property_id,
            change_type="url_linked",
            field_name="additional_url",
            old_value="",
            new_value=new_url,
            change_summary=f"User manually linked URL: {new_url}"
        )
        
        return {
            "message": "URL successfully linked to existing property",
            "existing_property_id": existing_property_id,
            "linked_url": new_url
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error linking URL: {str(e)}"
        )

@app.get("/api/properties/{property_id}/rooms")
async def get_property_rooms(property_id: str, db: Session = Depends(get_db)):
    # """Get all rooms for a property with their discovery dates and history"""
    
    property_obj = PropertyCRUD.get_property_by_id(db, property_id)
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    
    rooms_data = RoomCRUD.get_property_rooms_with_history(db, property_id)
    
    return {
        "property_id": property_id,
        "total_rooms": len(rooms_data),
        "rooms": rooms_data
    }

@app.get("/api/rooms/{room_id}/changes")
async def get_room_changes(room_id: str, db: Session = Depends(get_db)):
    """Get change history for a specific room"""
    
    changes = RoomCRUD.get_room_changes(db, room_id=room_id)
    
    return [
        {
            "change_id": str(change.id),
            "change_type": change.change_type,
            "old_value": change.old_value,
            "new_value": change.new_value,
            "change_summary": change.change_summary,
            "detected_at": change.detected_at.isoformat()
        }
        for change in changes
    ]


@app.get("/api/analytics")
async def get_analytics(db: Session = Depends(get_db)):
    """Get analytics and statistics"""
    stats = AnalysisCRUD.get_analysis_stats(db)
    
    return {
        "total_properties": stats["total_properties"],
        "total_analyses": stats["total_analyses"],
        "viable_properties": stats["viable_properties"],
        "average_monthly_income": stats["average_monthly_income"],
        "total_monthly_income": stats["total_monthly_income"]
    }

@app.get("/api/export/{property_id}")
async def export_property_excel(property_id: str, db: Session = Depends(get_db)):
    """Download Excel file for a specific property"""
    
    # Try to find by property ID first
    property_obj = PropertyCRUD.get_property_by_id(db, property_id)
    
    if not property_obj:
        # Try to find by task_id (backward compatibility)
        task = TaskCRUD.get_task_by_id(db, property_id)
        if task and task.property:
            property_obj = task.property
        else:
            raise HTTPException(
                status_code=404,
                detail="Property not found"
            )
    
    # Check for existing Excel file in exports directory
    exports_dir = get_exports_directory()
    excel_filename = f"property_{property_id}.xlsx"
    excel_full_path = os.path.join(exports_dir, excel_filename)
    
    if not os.path.exists(excel_full_path):
        # Generate Excel file from database data
        latest_analysis = AnalysisCRUD.get_latest_analysis(db, property_obj.id)
        
        if not latest_analysis:
            raise HTTPException(
                status_code=404,
                detail="No analysis data found for this property"
            )
        
        # Recreate analysis_data structure
        analysis_data = {
            'Analysis Date': latest_analysis.analysis_date,
            'URL': property_obj.url,
            'Latitude': property_obj.latitude,
            'Longitude': property_obj.longitude,
            'Full Address': property_obj.address,
            'Postcode': property_obj.postcode,
            'Property ID': property_obj.property_id,
            'Title': latest_analysis.title,
            'Advertiser Name': latest_analysis.advertiser_name,
            'Landlord Type': latest_analysis.landlord_type,
            'Bills Included': latest_analysis.bills_included,
            'Household Gender': latest_analysis.household_gender,
            'Listing Status': latest_analysis.listing_status,
            'Main Photo URL': latest_analysis.main_photo_url,
            'Total Rooms': latest_analysis.total_rooms,
            'Listed Rooms': latest_analysis.listed_rooms,
            'Available Rooms': latest_analysis.available_rooms,
            'Available Rooms Details': latest_analysis.available_rooms_details or [],
            'Taken Rooms': latest_analysis.taken_rooms,
            'Room Details': latest_analysis.room_details,
            'All Rooms List': latest_analysis.all_rooms_list or [],
            'Monthly Income': float(latest_analysis.monthly_income) if latest_analysis.monthly_income else None,
            'Annual Income': float(latest_analysis.annual_income) if latest_analysis.annual_income else None,
            'Meets Requirements': latest_analysis.meets_requirements
        }
        
        # Generate Excel file in exports directory
        excel_full_path = save_to_excel(analysis_data, excel_filename)
    
    return FileResponse(
        excel_full_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=f"hmo_analysis_{property_obj.property_id or property_id}.xlsx"
    )

@app.delete("/api/analysis/{task_id}")
async def delete_analysis(task_id: str, db: Session = Depends(get_db)):
    """Delete an analysis task and its associated files"""
    
    # Try to find task first
    task = TaskCRUD.get_task_by_id(db, task_id)
    
    if task:
        # Delete by task
        property_id = task.property_id
        if property_id:
            PropertyCRUD.delete_property(db, property_id)
    else:
        # Try to find by property ID
        property_obj = PropertyCRUD.get_property_by_id(db, task_id)
        if property_obj:
            PropertyCRUD.delete_property(db, property_obj.id)
        else:
            raise HTTPException(
                status_code=404,
                detail="Task or property not found"
            )
    
    # Remove Excel file from exports directory
    exports_dir = get_exports_directory()
    excel_filename = f"property_{task_id}.xlsx"
    excel_full_path = os.path.join(exports_dir, excel_filename)
    if os.path.exists(excel_full_path):
        os.remove(excel_full_path)
    
    return {"message": "Analysis deleted successfully"}

@app.get("/api/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint with database statistics - UPDATED for Phase 1"""
    
    # Get database statistics
    stats = AnalysisCRUD.get_analysis_stats(db)
    
    # Get active tasks
    active_tasks = TaskCRUD.get_active_tasks(db)
    
    # Get export statistics
    export_stats = get_export_stats()
    
    # PHASE 1 ADDITION: Get availability statistics
    total_periods = db.query(RoomAvailabilityPeriod).count()
    current_available = db.query(RoomAvailabilityPeriod).filter(
        RoomAvailabilityPeriod.is_current_period == True
    ).count()
    rooms_with_date_gone = db.query(Room).filter(
        Room.date_gone.isnot(None)
    ).count()
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "database_connected": True,
        "total_properties": stats["total_properties"],
        "total_analyses": stats["total_analyses"],
        "active_tasks": len(active_tasks),
        "viable_properties": stats["viable_properties"],
        "export_files": export_stats["total_files"],
        "export_size_mb": export_stats["total_size_mb"],
        
        # PHASE 1 ADDITIONS:
        "availability_tracking": {
            "total_availability_periods": total_periods,
            "currently_available_rooms": current_available,
            "rooms_currently_gone": rooms_with_date_gone
        }
    }

@app.get("/api/filters/cities")
def get_cities_for_filter(db: Session = Depends(get_db)):
    """Get list of cities that have properties for dropdown filter"""
    try:
        cities = PropertyCRUD.get_cities_with_properties(db)
        return {"cities": cities}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching cities: {str(e)}")

@app.get("/api/filters/areas/{city}")
def get_areas_for_city_filter(city: str, db: Session = Depends(get_db)):
    """Get list of areas for a specific city for dropdown filter"""
    try:
        areas = PropertyCRUD.get_areas_for_city(db, city)
        return {"areas": areas}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching areas for {city}: {str(e)}")


# Add these new functions to your main.py

class PropertyUpdateRequest(BaseModel):
    property_ids: Optional[List[str]] = None  # If None, update all properties

class PropertyUpdateResponse(BaseModel):
    task_id: str
    status: str
    message: str
    properties_queued: int

class PropertyChangeResponse(BaseModel):
    change_id: str
    change_type: str
    field_name: str
    old_value: str
    new_value: str
    change_summary: str
    detected_at: str

# ADD THE MAP USAGE MODELS HERE:
class MapUsageEventRequest(BaseModel):
    type: str
    sessionId: str
    timestamp: int
    data: Dict[str, Any]

class BatchUsageEventsRequest(BaseModel):
    events: List[MapUsageEventRequest]

def detect_changes(old_analysis: Dict[str, Any], new_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Compare two analyses and detect changes"""
    changes = []
    
    # Fields to monitor for changes
    monitored_fields = {
        'Listing Status': 'status',
        'Available Rooms': 'availability',
        'Total Rooms': 'rooms',
        'Monthly Income': 'price',
        'Annual Income': 'price',
        'Bills Included': 'bills',
        'Meets Requirements': 'requirements'
    }
    
    for field, change_type in monitored_fields.items():
        old_val = old_analysis.get(field)
        new_val = new_analysis.get(field)
        
        if old_val != new_val:
            # Create change record
            change = {
                'change_type': change_type,
                'field_name': field,
                'old_value': str(old_val) if old_val is not None else 'None',
                'new_value': str(new_val) if new_val is not None else 'None',
                'change_summary': f"{field} changed from '{old_val}' to '{new_val}'"
            }
            changes.append(change)
    
    # Special handling for room details
    old_rooms = old_analysis.get('All Rooms List', [])
    new_rooms = new_analysis.get('All Rooms List', [])
    
    if old_rooms != new_rooms:
        room_changes = analyze_room_changes(old_rooms, new_rooms)
        if room_changes:
            changes.append({
                'change_type': 'rooms',
                'field_name': 'Room Configuration',
                'old_value': '; '.join(old_rooms) if old_rooms else 'None',
                'new_value': '; '.join(new_rooms) if new_rooms else 'None',
                'change_summary': room_changes,
                'room_details': {
                    'old_rooms': old_rooms,
                    'new_rooms': new_rooms,
                    'analysis': room_changes
                }
            })
    
    return changes

def analyze_room_changes(old_rooms: List[str], new_rooms: List[str]) -> str:
    """Analyze specific room changes"""
    changes = []
    
    # Convert room lists to sets for comparison
    old_set = set(old_rooms)
    new_set = set(new_rooms)
    
    # Rooms that were removed
    removed_rooms = old_set - new_set
    if removed_rooms:
        changes.append(f"Removed: {', '.join(removed_rooms)}")
    
    # Rooms that were added
    added_rooms = new_set - old_set
    if added_rooms:
        changes.append(f"Added: {', '.join(added_rooms)}")
    
    # Analyze availability changes (basic pattern matching)
    old_available = [room for room in old_rooms if 'available' in room.lower() or '(' in room]
    new_available = [room for room in new_rooms if 'available' in room.lower() or '(' in room]
    
    if len(old_available) != len(new_available):
        changes.append(f"Available rooms changed from {len(old_available)} to {len(new_available)}")
    
    return '; '.join(changes) if changes else 'Room configuration modified'

async def update_property_task(task_id: str, property_ids: List[str]):
    """Background task to update multiple properties"""
    
    # Create a new database session for this background task
    from database import SessionLocal
    db = SessionLocal()

    try:
        updated_count = 0
        changes_detected = 0
        
        TaskCRUD.update_task_status(db, task_id, "running", {"progress": "starting"})
        
        for i, property_id in enumerate(property_ids):
            try:
                # Get existing property and latest analysis
                property_obj = PropertyCRUD.get_property_by_id(db, property_id)
                if not property_obj:
                    continue
                
                latest_analysis = AnalysisCRUD.get_latest_analysis(db, property_obj.id)
                if not latest_analysis:
                    continue
                
                # Update progress
                progress = f"Updating property {i+1}/{len(property_ids)}"
                TaskCRUD.update_task_status(db, task_id, "running", {"progress": progress})
                
                # Re-analyze the property
                analysis_data = initialize_analysis_data(property_obj.url)
                
                # Extract new data
                coords = extract_coordinates(property_obj.url, analysis_data)
                if coords.get('found'):
                    lat, lon = coords['latitude'], coords['longitude']
                    reverse_geocode_nominatim(lat, lon, analysis_data)
                    extract_property_details(property_obj.url, analysis_data)
                
                extract_price_section(property_obj.url, analysis_data)
                
                # Compare with previous analysis
                old_analysis_data = {
                    'Listing Status': latest_analysis.listing_status,
                    'Available Rooms': latest_analysis.available_rooms,
                    'Total Rooms': latest_analysis.total_rooms,
                    'Monthly Income': float(latest_analysis.monthly_income) if latest_analysis.monthly_income else None,
                    'Annual Income': float(latest_analysis.annual_income) if latest_analysis.annual_income else None,
                    'Bills Included': latest_analysis.bills_included,
                    'Meets Requirements': latest_analysis.meets_requirements,
                    'All Rooms List': latest_analysis.all_rooms_list or []
                }
                
                # Detect changes
                changes = detect_changes(old_analysis_data, analysis_data)
                
                # ✅ FIXED: Always run room tracking, regardless of whether other changes are detected
                print(f"[{task_id}] Processing room tracking for property {property_obj.id}...")

                # ✅ NEW: Check if listing is expired and handle differently
                if analysis_data.get('_EXPIRED_LISTING'):
                    # For expired listings, mark existing rooms as taken
                    print(f"[{task_id}] Marking existing rooms as taken for expired listing...")
                    room_results = RoomCRUD.mark_all_property_rooms_as_taken(
                        db, property_obj.id, None
                    )
                    print(f"[{task_id}] Room status update: {len(room_results['updated_rooms'])} rooms marked as taken")
                else:
                    # For active listings, use normal room tracking
                    rooms_list = analysis_data.get('All Rooms List', [])
                    if rooms_list:
                        room_results = RoomCRUD.process_rooms_list(
                            db, property_obj.id, rooms_list, None
                        )
                        print(f"[{task_id}] Room tracking: {len(room_results['new_rooms'])} new, "
                            f"{len(room_results['updated_rooms'])} updated, "
                            f"{len(room_results['disappeared_rooms'])} disappeared")
                
                if changes:
                    # Create new analysis record
                    new_analysis = save_analysis_to_db(db, property_obj, analysis_data)
                    
                    # Save change records
                    for change in changes:
                        PropertyChangeCRUD.create_change(
                            db,
                            property_id=property_obj.id,
                            analysis_id=new_analysis.id,
                            **change
                        )
                    
                    changes_detected += len(changes)
                    print(f"[{task_id}] Detected {len(changes)} changes for property {property_obj.id}")
                else:
                    print(f"[{task_id}] No analysis changes detected for property {property_obj.id}")
                    # But room tracking still ran above!
                
                updated_count += 1
                
            except Exception as e:
                print(f"[{task_id}] Failed to update property {property_id}: {e}")
                continue
        
        # Complete the task
        TaskCRUD.update_task_status(db, task_id, "completed", {
            "progress": "completed",
            "updated_count": updated_count,
            "changes_detected": changes_detected
        })
        
        # Log completion
        AnalyticsCRUD.log_event(
            db,
            "bulk_update_completed",
            task_id=task_id,
            event_data={
                "properties_updated": updated_count,
                "changes_detected": changes_detected
            }
        )
        
        print(f"[{task_id}] Update completed: {updated_count} properties, {changes_detected} changes")
        
    except Exception as e:
        print(f"[{task_id}] Update task failed: {e}")
        TaskCRUD.update_task_status(db, task_id, "failed", error_message=str(e))
    finally:
        # CRITICAL: Always close the database session
        db.close()

@app.post("/api/properties/update", response_model=PropertyUpdateResponse)
async def update_properties(
    request: PropertyUpdateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Start bulk update of properties"""
    
    # Get property IDs to update
    if request.property_ids:
        property_ids = request.property_ids
    else:
        # Get all properties
        all_properties = PropertyCRUD.get_all_properties(db, limit=1000)
        property_ids = [str(prop.id) for prop in all_properties]
    
    if not property_ids:
        raise HTTPException(
            status_code=400,
            detail="No properties found to update"
        )
    
    # Generate task ID
    task_id = str(uuid.uuid4())
    
    # Create bulk update task (no specific property)
    TaskCRUD.create_bulk_update_task(db, task_id)
    
    # Start background update task
    background_tasks.add_task(update_property_task, task_id, property_ids)
    
    return PropertyUpdateResponse(
        task_id=task_id,
        status="pending",
        message=f"Update started for {len(property_ids)} properties",
        properties_queued=len(property_ids)
    )

@app.post("/api/properties/{property_id}/update")
async def update_single_property(
    property_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Update a single property"""
    
    property_obj = PropertyCRUD.get_property_by_id(db, property_id)
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    
    # Generate task ID and create individual property task
    task_id = str(uuid.uuid4())
    TaskCRUD.create_property_task(db, task_id, property_obj.id)
    
    background_tasks.add_task(update_property_task, task_id, [property_id], db)
    
    return PropertyUpdateResponse(
        task_id=task_id,
        status="pending",
        message="Property update started",
        properties_queued=1
    )

@app.get("/api/properties/{property_id}/changes")
async def get_property_changes(
    property_id: str,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get change history for a property"""
    
    property_obj = PropertyCRUD.get_property_by_id(db, property_id)
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    
    changes = PropertyChangeCRUD.get_property_changes(db, property_id, limit=limit)
    
    return [
        PropertyChangeResponse(
            change_id=str(change.id),
            change_type=change.change_type,
            field_name=change.field_name,
            old_value=change.old_value,
            new_value=change.new_value,
            change_summary=change.change_summary,
            detected_at=change.detected_at.isoformat()
        )
        for change in changes
    ]

@app.get("/api/changes/recent")
async def get_recent_changes(
    days: int = 7,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get recent changes across all properties"""
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    changes = PropertyChangeCRUD.get_recent_changes(db, cutoff_date, limit=limit)
    
    return [
        {
            "change_id": str(change.id),
            "property_id": str(change.property_id),
            "property_address": change.property.address if change.property else "Unknown",
            "change_type": change.change_type,
            "field_name": change.field_name,
            "old_value": change.old_value,
            "new_value": change.new_value,
            "change_summary": change.change_summary,
            "detected_at": change.detected_at.isoformat()
        }
        for change in changes
    ]

# ADD THESE NEW ENDPOINTS for Phase 1:

@app.get("/api/properties/{property_id}/availability-summary")
def get_property_availability_summary_endpoint(property_id: str, db: Session = Depends(get_db)):
    """Get comprehensive availability summary for a property"""
    
    property_obj = PropertyCRUD.get_property_by_id(db, property_id)
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    
    summary = get_property_availability_summary(db, property_id)
    
    return {
        "property_id": property_id,
        "summary": summary,
        "calculated_at": datetime.utcnow().isoformat()
    }

@app.get("/api/properties/{property_id}/rooms/{room_id}/periods")
async def get_room_availability_periods(
    property_id: str, 
    room_id: str, 
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get all availability periods for a specific room"""
    
    # Verify property exists
    property_obj = PropertyCRUD.get_property_by_id(db, property_id)
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    
    # Verify room exists and belongs to property
    room = db.query(Room).filter(
        Room.id == room_id,
        Room.property_id == property_id
    ).first()
    
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    # Get periods
    periods = RoomAvailabilityPeriodCRUD.get_room_periods(db, room_id, limit=limit)
    
    return {
        "room_id": room_id,
        "room_number": room.room_number,
        "current_status": room.current_status,
        "date_gone": room.date_gone.isoformat() if room.date_gone else None,
        "date_returned": room.date_returned.isoformat() if room.date_returned else None,
        "total_periods": len(periods),
        "periods": [
            {
                "period_id": str(period.id),
                "start_date": period.period_start_date.isoformat(),
                "end_date": period.period_end_date.isoformat() if period.period_end_date else None,
                "duration_days": period.duration_days,
                "price_at_start": float(period.price_at_start) if period.price_at_start else None,
                "price_text_at_start": period.price_text_at_start,
                "room_type_at_start": period.room_type_at_start,
                "is_current_period": period.is_current_period,
                "status": "ongoing" if period.is_current_period else "completed"
            }
            for period in periods
        ]
    }

@app.get("/api/rooms/periods/recent")
async def get_recent_availability_periods(
    days: int = 30,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get recent availability periods across all properties"""
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    periods = (db.query(RoomAvailabilityPeriod)
              .join(Room)
              .join(Property)
              .filter(RoomAvailabilityPeriod.period_start_date >= cutoff_date)
              .order_by(desc(RoomAvailabilityPeriod.period_start_date))
              .limit(limit)
              .all())
    
    return [
        {
            "period_id": str(period.id),
            "room_id": str(period.room_id),
            "property_id": str(period.room.property_id),
            "property_address": period.room.property.address,
            "room_number": period.room.room_number,
            "start_date": period.period_start_date.isoformat(),
            "end_date": period.period_end_date.isoformat() if period.period_end_date else None,
            "duration_days": period.duration_days,
            "price_at_start": float(period.price_at_start) if period.price_at_start else None,
            "price_text_at_start": period.price_text_at_start,
            "is_current_period": period.is_current_period,
            "status": "ongoing" if period.is_current_period else "completed"
        }
        for period in periods
    ]

@app.get("/api/analytics/availability")
async def get_availability_analytics(db: Session = Depends(get_db)):
    """Get analytics about room availability patterns"""
    
    # Get overall statistics
    total_periods = db.query(RoomAvailabilityPeriod).count()
    current_periods = db.query(RoomAvailabilityPeriod).filter(
        RoomAvailabilityPeriod.is_current_period == True
    ).count()
    
    # Get average duration for completed periods
    completed_periods = db.query(RoomAvailabilityPeriod).filter(
        RoomAvailabilityPeriod.duration_days.isnot(None)
    ).all()
    
    avg_duration = 0
    if completed_periods:
        total_duration = sum(p.duration_days for p in completed_periods)
        avg_duration = total_duration / len(completed_periods)
    
    # Get properties with rooms currently gone
    properties_with_gone_rooms = db.query(Property).join(Room).filter(
        Room.date_gone.isnot(None)
    ).distinct().count()
    
    # Get recent activity (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_periods = db.query(RoomAvailabilityPeriod).filter(
        RoomAvailabilityPeriod.period_start_date >= week_ago
    ).count()
    
    recent_gone = db.query(Room).filter(
        Room.date_gone >= week_ago
    ).count()
    
    return {
        "total_availability_periods": total_periods,
        "currently_available_periods": current_periods,
        "average_availability_duration_days": round(avg_duration, 1),
        "properties_with_rooms_gone": properties_with_gone_rooms,
        "recent_activity": {
            "new_availability_periods_last_7_days": recent_periods,
            "rooms_gone_last_7_days": recent_gone
        },
        "calculated_at": datetime.utcnow().isoformat()
    }

async def test_phase1_functionality(db: Session):
    """Test Phase 1 functionality - can be called manually for testing"""
    
    print("🧪 Testing Phase 1 functionality...")
    
    # Test 1: Get properties with date gone
    properties = PropertyCRUD.get_all_properties(db, limit=5)
    print(f"✅ Retrieved {len(properties)} properties")
    
    for prop in properties[:2]:  # Test first 2 properties
        summary = format_property_summary_with_db(prop, db)
        date_gone = summary.get("date_gone")
        print(f"   Property {prop.id}: Date Gone = {date_gone}")
        
        # Test availability summary
        availability = get_property_availability_summary(db, prop.id)
        print(f"   Available rooms: {availability['current_available_rooms']}")
        print(f"   Rooms gone: {availability['rooms_currently_gone']}")
    
    # Test 2: Get recent periods
    recent_periods = (db.query(RoomAvailabilityPeriod)
                     .order_by(desc(RoomAvailabilityPeriod.period_start_date))
                     .limit(5)
                     .all())
    
    print(f"✅ Found {len(recent_periods)} recent availability periods")
    
    # Test 3: Get rooms with date gone
    rooms_gone = db.query(Room).filter(Room.date_gone.isnot(None)).limit(5).all()
    print(f"✅ Found {len(rooms_gone)} rooms currently gone")
    
    print("🎉 Phase 1 testing completed!")


@app.get("/api/properties/{property_id}/price-trends")
async def get_property_price_trends(property_id: str, days: int = 90, db: Session = Depends(get_db)):
    """Get price trends for all rooms in a property"""
    property_obj = PropertyCRUD.get_property_by_id(db, property_id)
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    
    trends = RoomPriceHistoryCRUD.get_property_price_trends(db, property_id, days)
    return trends

@app.get("/api/properties/{property_id}/trends")
async def get_property_trends(property_id: str, trend_period: str = "monthly", db: Session = Depends(get_db)):
    """Get calculated trends for a property"""
    property_obj = PropertyCRUD.get_property_by_id(db, property_id)
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    
    trends = PropertyTrendCRUD.get_property_trends(db, property_id, trend_period)
    return [
        {
            "period_start": trend.period_start.isoformat(),
            "period_end": trend.period_end.isoformat(),
            "avg_availability_duration": float(trend.avg_availability_duration) if trend.avg_availability_duration else None,
            "turnover_rate": float(trend.availability_turnover_rate) if trend.availability_turnover_rate else None,
            "avg_room_price": float(trend.avg_room_price) if trend.avg_room_price else None,
            "price_trend_direction": trend.price_trend_direction,
            "income_stability": float(trend.income_stability_score) if trend.income_stability_score else None,
            "market_position": trend.market_competitiveness
        }
        for trend in trends
    ]

@app.get("/api/properties/{property_id}/analytics")
async def get_property_analytics(property_id: str, db: Session = Depends(get_db)):
    """Get comprehensive analytics for a property"""
    property_obj = PropertyCRUD.get_property_by_id(db, property_id)
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    
    # Calculate fresh trends
    trend = PropertyTrendCRUD.calculate_and_store_trends(db, property_id)
    
    return {
        "avg_availability_duration": float(trend.avg_availability_duration) if trend.avg_availability_duration else None,
        "turnover_rate": float(trend.availability_turnover_rate) if trend.availability_turnover_rate else None,
        "income_stability": float(trend.income_stability_score) if trend.income_stability_score else None,
        "market_position": trend.market_competitiveness,
        "confidence_score": float(trend.confidence_score) if trend.confidence_score else None
    }

@app.get("/api/properties/{property_id}/availability-timeline")
async def get_availability_timeline(property_id: str, days: int = 90, db: Session = Depends(get_db)):
    """Get availability timeline data"""
    property_obj = PropertyCRUD.get_property_by_id(db, property_id)
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    
    # This is a placeholder - timeline implementation would go here
    return {
        "message": "Timeline data coming soon",
        "property_id": property_id,
        "days": days
    }

@app.post("/api/properties/{property_id}/calculate-trends")
async def calculate_property_trends(property_id: str, db: Session = Depends(get_db)):
    """Manually trigger trend calculation for a property"""
    property_obj = PropertyCRUD.get_property_by_id(db, property_id)
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    
    # Calculate trends for different periods
    trends = {}
    for period in ["weekly", "monthly", "quarterly"]:
        trend = PropertyTrendCRUD.calculate_and_store_trends(db, property_id, period)
        trends[period] = {
            "avg_duration": float(trend.avg_availability_duration) if trend.avg_availability_duration else None,
            "turnover_rate": float(trend.availability_turnover_rate) if trend.availability_turnover_rate else None,
            "price_trend": trend.price_trend_direction
        }
    
    return {
        "message": "Trends calculated successfully",
        "trends": trends
    }

@app.get("/api/test/price-history-table")
async def test_price_history_table(db: Session = Depends(get_db)):
    """Test if room_price_history table exists"""
    try:
        # Try to query the table
        count = db.query(RoomPriceHistory).count()
        return {
            "table": "room_price_history",
            "exists": True,
            "records": count,
            "message": f"Table exists with {count} records"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Table test failed: {str(e)}"
        )

@app.get("/api/test/trends-table")
async def test_trends_table(db: Session = Depends(get_db)):
    """Test if property_trends table exists"""
    try:
        # Try to query the table
        count = db.query(PropertyTrend).count()
        return {
            "table": "property_trends",
            "exists": True,
            "records": count,
            "message": f"Table exists with {count} records"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Table test failed: {str(e)}"
        )
    
# Add these endpoints to your main.py for production Phase 3 features

@app.get("/api/properties/{property_id}/availability-calendar")
async def get_property_availability_calendar(
    property_id: str,
    start_date: str,
    end_date: str,
    db: Session = Depends(get_db)
):
    """Get availability calendar data for heatmap visualization"""
    try:
        from crud import PropertyCRUD, RoomAvailabilityPeriodCRUD
        
        # Validate property exists
        property_obj = PropertyCRUD.get_property_by_id(db, property_id)
        if not property_obj:
            raise HTTPException(status_code=404, detail="Property not found")
        
        # Parse dates
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        # Get all rooms for this property
        rooms = db.query(Room).filter(Room.property_id == property_id).all()
        
        if not rooms:
            return {
                "property_id": property_id,
                "start_date": start_date,
                "end_date": end_date,
                "calendar_data": {},
                "room_summary": {
                    "total_rooms": 0,
                    "avg_occupancy_rate": 0
                }
            }
        
        # Generate calendar data for each day in the range
        calendar_data = {}
        current_date = start_dt
        
        while current_date <= end_dt:
            date_str = current_date.strftime('%Y-%m-%d')
            
            # Calculate occupancy for this date
            total_rooms = len(rooms)
            occupied_rooms = 0
            rooms_by_status = {"available": 0, "taken": 0, "offline": 0}
            
            for room in rooms:
                # Check room status on this date
                room_status = get_room_status_on_date(db, room.id, current_date)
                
                if room_status == "taken":
                    occupied_rooms += 1
                    rooms_by_status["taken"] += 1
                elif room_status == "available":
                    rooms_by_status["available"] += 1
                else:
                    rooms_by_status["offline"] += 1
            
            occupancy_rate = (occupied_rooms / total_rooms * 100) if total_rooms > 0 else 0
            available_rooms = total_rooms - occupied_rooms
            
            calendar_data[date_str] = {
                "occupancy_rate": round(occupancy_rate, 1),
                "occupied_rooms": occupied_rooms,
                "available_rooms": available_rooms,
                "total_rooms": total_rooms,
                "rooms_by_status": rooms_by_status
            }
            
            current_date += timedelta(days=1)
        
        # Calculate summary statistics
        if calendar_data:
            occupancy_rates = [day["occupancy_rate"] for day in calendar_data.values()]
            avg_occupancy = sum(occupancy_rates) / len(occupancy_rates)
        else:
            avg_occupancy = 0
        
        return {
            "property_id": property_id,
            "start_date": start_date,
            "end_date": end_date,
            "calendar_data": calendar_data,
            "room_summary": {
                "total_rooms": len(rooms),
                "avg_occupancy_rate": round(avg_occupancy, 1)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating calendar data: {str(e)}")

@app.get("/api/properties/{property_id}/occupancy-stats")
async def get_property_occupancy_stats(
    property_id: str,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get occupancy statistics for a property"""
    try:
        from crud import PropertyCRUD
        
        # Validate property exists
        property_obj = PropertyCRUD.get_property_by_id(db, property_id)
        if not property_obj:
            raise HTTPException(status_code=404, detail="Property not found")
        
        # Get rooms for this property
        rooms = db.query(Room).filter(Room.property_id == property_id).all()
        
        if not rooms:
            return {
                "property_id": property_id,
                "total_rooms": 0,
                "period_days": days,
                "avg_occupancy_rate": 0,
                "total_availability_periods": 0,
                "avg_period_duration": 0
            }
        
        # Get all availability periods for these rooms in the last N days
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        room_ids = [room.id for room in rooms]
        
        periods = db.query(RoomAvailabilityPeriod).filter(
            RoomAvailabilityPeriod.room_id.in_(room_ids),
            RoomAvailabilityPeriod.period_start_date >= cutoff_date
        ).all()
        
        # Calculate statistics
        total_periods = len(periods)
        completed_periods = [p for p in periods if p.duration_days is not None]
        
        if completed_periods:
            avg_duration = sum(p.duration_days for p in completed_periods) / len(completed_periods)
        else:
            avg_duration = 0
        
        # Estimate occupancy rate based on periods
        if total_periods > 0 and len(rooms) > 0:
            # Simple estimation: assume more periods = higher turnover = lower occupancy
            periods_per_room = total_periods / len(rooms)
            estimated_occupancy = max(30, 100 - (periods_per_room * 10))  # Rough estimation
        else:
            estimated_occupancy = 75  # Default assumption
        
        return {
            "property_id": property_id,
            "total_rooms": len(rooms),
            "period_days": days,
            "avg_occupancy_rate": round(estimated_occupancy, 1),
            "total_availability_periods": total_periods,
            "avg_period_duration": round(avg_duration, 1) if avg_duration > 0 else 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating occupancy stats: {str(e)}")

@app.get("/api/portfolio/comparison")
async def get_portfolio_comparison(
    db: Session = Depends(get_db),
    limit: int = 10
):
    """Compare properties in portfolio - Phase 3 Portfolio Comparison"""
    
    # Get all properties with their basic stats
    properties = PropertyCRUD.get_all_properties(db, limit=limit)
    
    portfolio_data = []
    
    for property_obj in properties:
        # Get rooms for this property
        rooms = RoomCRUD.get_rooms_by_property(db, property_obj.id)
        total_rooms = len(rooms)
        
        if total_rooms == 0:
            continue
        
        # Calculate current occupancy
        currently_available = 0
        for room in rooms:
            current_periods = db.query(RoomAvailabilityPeriod).filter(
                RoomAvailabilityPeriod.room_id == room.id,
                RoomAvailabilityPeriod.start_date <= datetime.now(),
                or_(
                    RoomAvailabilityPeriod.end_date >= datetime.now(),
                    RoomAvailabilityPeriod.end_date.is_(None)
                )
            ).count()
            
            if current_periods > 0:
                currently_available += 1
        
        current_occupancy_rate = ((total_rooms - currently_available) / total_rooms * 100)
        
        # Get latest analysis for income data
        latest_analysis = AnalysisCRUD.get_latest_analysis(db, property_obj.id)
        monthly_income = float(latest_analysis.monthly_income) if latest_analysis and latest_analysis.monthly_income else 0
        
        portfolio_data.append({
            'property_id': property_obj.id,
            'property_name': latest_analysis.title if latest_analysis else property_obj.address[:50],
            'address': property_obj.address,
            'postcode': property_obj.postcode,
            'total_rooms': total_rooms,
            'current_occupancy_rate': round(current_occupancy_rate, 1),
            'monthly_income': monthly_income,
            'annual_income': monthly_income * 12,
            'income_per_room': round(monthly_income / total_rooms, 2) if total_rooms > 0 else 0
        })
    
    # Calculate portfolio averages
    if portfolio_data:
        avg_occupancy = sum(p['current_occupancy_rate'] for p in portfolio_data) / len(portfolio_data)
        avg_income_per_room = sum(p['income_per_room'] for p in portfolio_data) / len(portfolio_data)
        total_portfolio_income = sum(p['monthly_income'] for p in portfolio_data)
    else:
        avg_occupancy = 0
        avg_income_per_room = 0
        total_portfolio_income = 0
    
    return {
        'portfolio_summary': {
            'total_properties': len(portfolio_data),
            'total_rooms': sum(p['total_rooms'] for p in portfolio_data),
            'average_occupancy_rate': round(avg_occupancy, 1),
            'average_income_per_room': round(avg_income_per_room, 2),
            'total_monthly_income': round(total_portfolio_income, 2),
            'total_annual_income': round(total_portfolio_income * 12, 2)
        },
        'properties': portfolio_data,
        'generated_at': datetime.now().isoformat()
    }


def get_room_status_on_date(db: Session, room_id: str, check_date: datetime) -> str:
    """Helper function to determine room status on a specific date"""
    try:
        # Get all availability periods for this room that overlap with the check date
        periods = db.query(RoomAvailabilityPeriod).filter(
            RoomAvailabilityPeriod.room_id == room_id,
            RoomAvailabilityPeriod.period_start_date <= check_date
        ).all()
        
        # Find the most relevant period
        current_period = None
        for period in periods:
            # If period has no end date (ongoing) or end date is after check date
            if period.period_end_date is None or period.period_end_date >= check_date:
                if period.period_start_date <= check_date:
                    current_period = period
                    break
        
        if current_period:
            return "available"  # Room was available on this date
        else:
            # Check if room was generally taken/offline
            room = db.query(Room).filter(Room.id == room_id).first()
            if room:
                if room.current_status == "taken":
                    return "taken"
                elif not room.is_currently_listed:
                    return "offline"
            
            return "taken"  # Default assumption
    
    except Exception as e:
        print(f"Error checking room status: {e}")
        return "taken"  # Safe default

@app.get("/api/properties/{property_id}/availability-trends")
async def get_availability_trends(
    property_id: str,
    period: str = "monthly",  # daily, weekly, monthly
    days: int = 90,
    db: Session = Depends(get_db)
):
    """Get availability trends over time for charts and analysis"""
    
    property_obj = PropertyCRUD.get_property_by_id(db, property_id)
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Get availability periods
    periods = db.query(RoomAvailabilityPeriod).filter(
        RoomAvailabilityPeriod.room_id.in_(
            db.query(Room.id).filter(Room.property_id == property_id)
        ),
        RoomAvailabilityPeriod.period_start_date >= cutoff_date
    ).order_by(RoomAvailabilityPeriod.period_start_date).all()
    
    # Group by time period
    if period == "daily":
        grouped_data = group_periods_by_day(periods)
    elif period == "weekly":
        grouped_data = group_periods_by_week(periods)
    else:  # monthly
        grouped_data = group_periods_by_month(periods)
    
    return {
        'property_id': property_id,
        'period': period,
        'days_analyzed': days,
        'trends_data': grouped_data,
        'total_periods': len(periods),
        'generated_at': datetime.utcnow().isoformat()
    }


def group_periods_by_day(periods):
    """Group availability periods by day"""
    grouped = defaultdict(list)
    
    for period in periods:
        date_key = period.period_start_date.strftime('%Y-%m-%d')
        grouped[date_key].append({
            'period_id': str(period.id),
            'room_id': str(period.room_id),
            'start_date': period.period_start_date.isoformat(),
            'end_date': period.period_end_date.isoformat() if period.period_end_date else None,
            'duration_days': period.duration_days,
            'is_current': period.is_current_period
        })
    
    return dict(grouped)


def group_periods_by_week(periods):
    """Group availability periods by week"""
    grouped = defaultdict(list)
    
    for period in periods:
        # Get the Monday of the week containing this date
        start_date = period.period_start_date
        monday = start_date - timedelta(days=start_date.weekday())
        week_key = monday.strftime('%Y-W%U')  # Year-WeekNumber format
        
        grouped[week_key].append({
            'period_id': str(period.id),
            'room_id': str(period.room_id),
            'start_date': period.period_start_date.isoformat(),
            'end_date': period.period_end_date.isoformat() if period.period_end_date else None,
            'duration_days': period.duration_days,
            'is_current': period.is_current_period,
            'week_start': monday.strftime('%Y-%m-%d')
        })
    
    return dict(grouped)


def group_periods_by_month(periods):
    """Group availability periods by month"""
    grouped = defaultdict(list)
    
    for period in periods:
        month_key = period.period_start_date.strftime('%Y-%m')
        
        grouped[month_key].append({
            'period_id': str(period.id),
            'room_id': str(period.room_id),
            'start_date': period.period_start_date.isoformat(),
            'end_date': period.period_end_date.isoformat() if period.period_end_date else None,
            'duration_days': period.duration_days,
            'is_current': period.is_current_period
        })
    
    return dict(grouped)


@app.get("/api/properties/{property_id}/occupancy-stats")
async def get_occupancy_statistics(
    property_id: str,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get detailed occupancy statistics for a property"""
    
    property_obj = PropertyCRUD.get_property_by_id(db, property_id)
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    
    # Get total rooms
    total_rooms = db.query(Room).filter(Room.property_id == property_id).count()
    
    if total_rooms == 0:
        return {
            'property_id': property_id,
            'total_rooms': 0,
            'message': 'No rooms found for this property'
        }
    
    # Get current availability
    currently_available = db.query(RoomAvailabilityPeriod).filter(
        RoomAvailabilityPeriod.room_id.in_(
            db.query(Room.id).filter(Room.property_id == property_id)
        ),
        RoomAvailabilityPeriod.is_current_period == True
    ).count()
    
    currently_taken = total_rooms - currently_available
    current_occupancy_rate = (currently_taken / total_rooms) * 100
    
    # Historical analysis for the past N days
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Get all periods that started or ended within our timeframe
    historical_periods = db.query(RoomAvailabilityPeriod).filter(
        RoomAvailabilityPeriod.room_id.in_(
            db.query(Room.id).filter(Room.property_id == property_id)
        ),
        RoomAvailabilityPeriod.period_start_date >= cutoff_date
    ).all()
    
    # Calculate average availability duration
    completed_periods = [p for p in historical_periods if p.duration_days is not None]
    avg_availability_duration = 0
    if completed_periods:
        total_duration = sum(p.duration_days for p in completed_periods)
        avg_availability_duration = total_duration / len(completed_periods)
    
    # Calculate turnover rate (how often rooms change status)
    turnover_events = len(historical_periods)
    turnover_rate = turnover_events / days if days > 0 else 0
    
    # Occupancy trends
    occupancy_over_time = []
    for i in range(days):
        check_date = datetime.utcnow() - timedelta(days=i)
        # This would require daily snapshots, which we'll simulate for now
        # In a real implementation, you might store daily occupancy snapshots
        occupancy_over_time.append({
            'date': check_date.strftime('%Y-%m-%d'),
            'occupancy_rate': current_occupancy_rate + (i * 0.5)  # Simulated trend
        })
    
    return {
        'property_id': property_id,
        'analysis_period_days': days,
        'room_statistics': {
            'total_rooms': total_rooms,
            'currently_available': currently_available,
            'currently_taken': currently_taken,
            'current_occupancy_rate': round(current_occupancy_rate, 2)
        },
        'historical_analysis': {
            'total_availability_periods': len(historical_periods),
            'completed_periods': len(completed_periods),
            'avg_availability_duration_days': round(avg_availability_duration, 1),
            'turnover_rate_per_day': round(turnover_rate, 3),
            'turnover_events': turnover_events
        },
        'trends': {
            'occupancy_over_time': occupancy_over_time[::-1]  # Reverse to get chronological order
        },
        'generated_at': datetime.utcnow().isoformat()
    }


@app.get("/api/heatmap/test-data/{property_id}")
async def generate_test_heatmap_data(
    property_id: str,
    months: int = 3,
    db: Session = Depends(get_db)
):
    """Generate test data for heatmap development - REMOVE IN PRODUCTION"""
    
    property_obj = PropertyCRUD.get_property_by_id(db, property_id)
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    
    # Generate sample data for the last N months
    start_date = datetime.utcnow() - timedelta(days=months * 30)
    end_date = datetime.utcnow()
    
    calendar_data = {}
    current_date = start_date
    
    # Simulate realistic occupancy patterns
    import random
    base_occupancy = 75  # Base 75% occupancy
    
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        
        # Add some realistic patterns:
        # - Lower occupancy on weekends (people move more)
        # - Seasonal variations
        # - Random fluctuations
        
        day_of_week = current_date.weekday()
        seasonal_factor = 1.0
        
        # Weekend effect (Friday-Sunday have slightly lower occupancy)
        if day_of_week >= 4:  # Friday, Saturday, Sunday
            weekend_factor = 0.9
        else:
            weekend_factor = 1.0
        
        # Seasonal effect (summer months have higher turnover)
        if current_date.month in [6, 7, 8]:  # Summer months
            seasonal_factor = 0.85
        elif current_date.month in [12, 1]:  # Winter months
            seasonal_factor = 1.1
        
        # Random daily variation
        random_factor = random.uniform(0.8, 1.2)
        
        # Calculate occupancy rate
        occupancy_rate = base_occupancy * weekend_factor * seasonal_factor * random_factor
        occupancy_rate = max(0, min(100, occupancy_rate))  # Clamp between 0-100
        
        # Convert to room counts (assume 5 rooms total)
        total_rooms = 5
        taken_rooms = round((occupancy_rate / 100) * total_rooms)
        available_rooms = total_rooms - taken_rooms
        
        calendar_data[date_str] = {
            'available_rooms': available_rooms,
            'total_rooms': total_rooms,
            'occupancy_rate': round(occupancy_rate, 2),
            'rooms_by_status': {
                'available': available_rooms,
                'taken': taken_rooms,
                'maintenance': 0
            }
        }
        
        current_date += timedelta(days=1)
    
    # Calculate summary
    occupancy_rates = [day['occupancy_rate'] for day in calendar_data.values()]
    avg_occupancy = sum(occupancy_rates) / len(occupancy_rates)
    
    peak_date = max(calendar_data.keys(), key=lambda d: calendar_data[d]['occupancy_rate'])
    low_date = min(calendar_data.keys(), key=lambda d: calendar_data[d]['occupancy_rate'])
    
    return {
        'property_id': property_id,
        'calendar_data': calendar_data,
        'room_summary': {
            'total_rooms': 5,
            'avg_occupancy_rate': round(avg_occupancy, 2),
            'peak_occupancy_date': peak_date,
            'peak_occupancy_rate': calendar_data[peak_date]['occupancy_rate'],
            'lowest_occupancy_date': low_date,
            'lowest_occupancy_rate': calendar_data[low_date]['occupancy_rate']
        },
        'test_data': True,
        'generated_at': datetime.utcnow().isoformat()
    }

        # Used for phase 2 -> delete after development has finised
@app.post("/api/properties/{property_id}/generate-sample-data")
async def generate_sample_price_data(property_id: str, db: Session = Depends(get_db)):
    """Generate sample price change data for testing purposes"""
    
    property_obj = PropertyCRUD.get_property_by_id(db, property_id)
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    
    try:
        # Get rooms for this property
        rooms = db.query(Room).filter(Room.property_id == property_id).all()
        
        if not rooms:
            return {
                "message": "No rooms found for sample data generation",
                "property_id": property_id
            }
        
        # Generate sample price changes for testing
        sample_changes = 0
        
        for room in rooms[:2]:  # Only first 2 rooms to avoid too much test data
            if room.current_price:
                # Create a sample price change (slight increase)
                new_price = room.current_price * Decimal('1.05')  # 5% increase
                
                # Track the price change
                RoomPriceHistoryCRUD.track_price_change(
                    db,
                    room_id=room.id,
                    property_id=property_id,
                    previous_price=room.current_price,
                    new_price=new_price,
                    previous_price_text=room.price_text or f"£{room.current_price}",
                    new_price_text=f"£{new_price}",
                    change_reason="sample_data_generation"
                )
                
                # Update room price
                room.current_price = new_price
                sample_changes += 1
        
        db.commit()
        
        return {
            "message": "Sample price data generated",
            "property_id": property_id,
            "sample_changes_created": sample_changes,
            "note": "This is test data for demonstration purposes"
        }
        
    except Exception as e:
        return {
            "message": "Sample data generation failed",
            "error": str(e),
            "property_id": property_id
        }

@usage_router.post("/")
async def track_map_usage(event: MapUsageEventRequest, db: Session = Depends(get_db)):
    """Track individual map usage event"""
    try:
        # Convert timestamp from JS (milliseconds) to Python datetime
        event_datetime = datetime.fromtimestamp(event.timestamp / 1000)
        
        # Create database record
        db_event = MapUsageEvent(
            event_type=event.type,
            session_id=event.sessionId,
            timestamp=event_datetime,
            data=event.data
        )
        
        db.add(db_event)
        db.commit()
        db.refresh(db_event)
        
        # Log for debugging
        print(f"📊 Map Usage Event Stored: {event.type} - Session: {event.sessionId}")
        
        return {"status": "success", "message": "Event tracked", "id": db_event.id}
    except Exception as e:
        db.rollback()
        print(f"Error storing usage event: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@usage_router.post("/batch")
async def track_batch_usage(batch: BatchUsageEventsRequest, db: Session = Depends(get_db)):
    """Track multiple map usage events in batch"""
    try:
        stored_events = []
        
        for event in batch.events:
            event_datetime = datetime.fromtimestamp(event.timestamp / 1000)
            
            db_event = MapUsageEvent(
                event_type=event.type,
                session_id=event.sessionId,
                timestamp=event_datetime,
                data=event.data
            )
            
            db.add(db_event)
            stored_events.append(db_event)
        
        db.commit()
        
        print(f"📊 Batch Events Stored: {len(stored_events)} events")
        
        return {
            "status": "success", 
            "message": f"Tracked {len(stored_events)} events",
            "event_ids": [e.id for e in stored_events]
        }
    except Exception as e:
        db.rollback()
        print(f"Error storing batch events: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@usage_router.get("/stats")
async def get_usage_stats(days: int = 30, db: Session = Depends(get_db)):
    """Get comprehensive map usage statistics"""
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Query for events in date range
        events_query = db.query(MapUsageEvent).filter(
            MapUsageEvent.timestamp >= start_date,
            MapUsageEvent.timestamp <= end_date
        )
        
        # Total map loads (map_load + style_change events)
        total_map_loads = events_query.filter(
            MapUsageEvent.event_type.in_(['map_load', 'style_change'])
        ).count()
        
        # Unique sessions
        unique_sessions = db.query(MapUsageEvent.session_id).filter(
            MapUsageEvent.timestamp >= start_date,
            MapUsageEvent.timestamp <= end_date
        ).distinct().count()
        
        # Average session duration (from session_end events)
        session_durations = db.query(MapUsageEvent.data).filter(
            MapUsageEvent.event_type == 'session_end',
            MapUsageEvent.timestamp >= start_date
        ).all()
        
        avg_duration = 0
        if session_durations:
            durations = []
            for session in session_durations:
                if session.data and 'duration' in session.data:
                    durations.append(session.data['duration'] / 1000)  # Convert to seconds
            avg_duration = sum(durations) / len(durations) if durations else 0
        
        # Most popular map style
        style_counts = {}
        style_events = events_query.filter(
            MapUsageEvent.event_type.in_(['map_load', 'style_change'])
        ).all()
        
        for event in style_events:
            if event.data and 'style' in event.data:
                style = event.data['style']
            elif event.data and 'to' in event.data:
                style = event.data['to']
            else:
                style = 'Unknown'
            style_counts[style] = style_counts.get(style, 0) + 1
        
        most_popular_style = max(style_counts.items(), key=lambda x: x[1])[0] if style_counts else 'Streets'
        
        # Daily breakdown
        daily_breakdown = []
        for i in range(days):
            day_start = start_date + timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            
            day_map_loads = events_query.filter(
                MapUsageEvent.timestamp >= day_start,
                MapUsageEvent.timestamp < day_end,
                MapUsageEvent.event_type.in_(['map_load', 'style_change'])
            ).count()
            
            day_sessions = db.query(MapUsageEvent.session_id).filter(
                MapUsageEvent.timestamp >= day_start,
                MapUsageEvent.timestamp < day_end
            ).distinct().count()
            
            daily_breakdown.append({
                "date": day_start.strftime('%Y-%m-%d'),
                "map_loads": day_map_loads,
                "sessions": day_sessions
            })
        
        # Filter usage analysis
        filter_usage = {}
        filter_events = events_query.filter(
            MapUsageEvent.event_type == 'filter_usage'
        ).all()
        
        for event in filter_events:
            if event.data and 'filterType' in event.data:
                filter_type = event.data['filterType']
                filter_usage[filter_type] = filter_usage.get(filter_type, 0) + 1
        
        # Quota usage calculations
        current_month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        current_month_loads = db.query(MapUsageEvent).filter(
            MapUsageEvent.timestamp >= current_month_start,
            MapUsageEvent.event_type.in_(['map_load', 'style_change'])
        ).count()
        
        quota_limit = 50000  # Mapbox free tier limit
        percentage_used = (current_month_loads / quota_limit) * 100
        
        # Estimate monthly total based on current usage
        days_in_month = (datetime.utcnow() - current_month_start).days + 1
        days_remaining = 30 - days_in_month  # Approximate
        estimated_monthly_total = current_month_loads + (current_month_loads / days_in_month * days_remaining)
        
        quota_usage = {
            "current_month_loads": current_month_loads,
            "quota_limit": quota_limit,
            "percentage_used": round(percentage_used, 2),
            "estimated_monthly_total": round(estimated_monthly_total),
            "days_in_month": days_in_month,
            "daily_average": round(current_month_loads / days_in_month, 1) if days_in_month > 0 else 0
        }
        
        return UsageStatsResponse(
            total_map_loads=total_map_loads,
            unique_sessions=unique_sessions,
            avg_session_duration=round(avg_duration, 1),
            most_popular_style=most_popular_style,
            daily_breakdown=daily_breakdown,
            filter_usage=filter_usage,
            quota_usage=quota_usage
        )
        
    except Exception as e:
        print(f"Error generating usage stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@usage_router.get("/sessions/{session_id}")
async def get_session_details(session_id: str, db: Session = Depends(get_db)):
    """Get detailed information about a specific session"""
    try:
        events = db.query(MapUsageEvent).filter(
            MapUsageEvent.session_id == session_id
        ).order_by(MapUsageEvent.timestamp).all()
        
        if not events:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session_data = {
            "session_id": session_id,
            "start_time": events[0].timestamp.isoformat(),
            "end_time": events[-1].timestamp.isoformat(),
            "total_events": len(events),
            "events": []
        }
        
        for event in events:
            session_data["events"].append({
                "type": event.event_type,
                "timestamp": event.timestamp.isoformat(),
                "data": event.data
            })
        
        return session_data
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching session details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@usage_router.delete("/cleanup")
async def cleanup_old_events(days_to_keep: int = 90, db: Session = Depends(get_db)):
    """Clean up old usage events (admin only - add authentication in production)"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        deleted_count = db.query(MapUsageEvent).filter(
            MapUsageEvent.timestamp < cutoff_date
        ).delete()
        
        db.commit()
        
        return {
            "status": "success",
            "message": f"Deleted {deleted_count} events older than {days_to_keep} days"
        }
        
    except Exception as e:
        db.rollback()
        print(f"Error cleaning up events: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)