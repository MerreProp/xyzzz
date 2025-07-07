#!/usr/bin/env python3
"""
FastAPI Backend for HMO Analyser - Working Version with All Endpoints
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, status, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import asyncio
import json
import os
from pathlib import Path
from sqlalchemy.orm import Session

# Import database components
from database import get_db, init_db, test_connection
from models import Property, PropertyAnalysis, AnalysisTask, PropertyChange
from crud import PropertyCRUD, AnalysisCRUD, TaskCRUD, AnalyticsCRUD, PropertyChangeCRUD

# Import your existing modules
from modules import (
    extract_coordinates,
    extract_property_details,
    reverse_geocode_nominatim,
    extract_price_section,
    save_to_excel,
    get_exports_directory,
    cleanup_old_exports,
    get_export_stats
)
from config import DATE_FORMAT

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

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    print("🚀 Starting HMO Analyser API...")
    
    # Test database connection
    if test_connection():
        # Initialize database tables
        init_db()
        print("✅ Database initialized successfully")
    else:
        print("❌ Database connection failed - check your DATABASE_URL")
    
    # Ensure exports directory exists
    exports_dir = get_exports_directory()
    if not os.path.exists(exports_dir):
        os.makedirs(exports_dir)
        print(f"✅ Created {exports_dir} directory")

# Pydantic models for request/response validation
class PropertyAnalysisRequest(BaseModel):
    url: HttpUrl
    
class PropertyAnalysisResponse(BaseModel):
    task_id: str
    status: str
    message: str

class AnalysisStatus(BaseModel):
    task_id: str
    status: str
    progress: Dict[str, str]
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

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

def format_property_summary(property_obj: Property) -> Dict[str, Any]:
    """Format property with latest analysis for API response"""
    latest_analysis = property_obj.analyses[0] if property_obj.analyses else None
    
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
        "date_gone": None
    }

# WORKING background task (your original version)
async def analyze_property_task(task_id: str, url: str, db: Session):
    """Background task to analyze a property with database storage"""
    try:
        # Update task status
        TaskCRUD.update_task_status(db, task_id, "running", {"coordinates": "running"})
        
        # Log analytics event
        AnalyticsCRUD.log_event(db, "analysis_started", task_id=task_id)
        
        # Get or create property
        property_obj = PropertyCRUD.get_property_by_url(db, url)
        if not property_obj:
            property_obj = PropertyCRUD.create_property(db, url)
        
        # Initialize analysis data
        analysis_data = initialize_analysis_data(url)
        
        # Step 1: Extract coordinates
        print(f"[{task_id}] Starting coordinate extraction...")
        coords = extract_coordinates(url, analysis_data)
        
        if coords.get('found'):
            TaskCRUD.update_task_status(db, task_id, "running", {"coordinates": "completed", "geocoding": "running"})
            
            # Update property with coordinates
            PropertyCRUD.update_property(
                db, 
                property_obj.id,
                latitude=coords['latitude'],
                longitude=coords['longitude']
            )
            
            # Get address from coordinates
            lat, lon = coords['latitude'], coords['longitude']
            address_info = reverse_geocode_nominatim(lat, lon, analysis_data)
            
            if address_info:
                # Update property with address info
                PropertyCRUD.update_property(
                    db,
                    property_obj.id,
                    address=analysis_data.get('Full Address'),
                    postcode=analysis_data.get('Postcode')
                )
            
            TaskCRUD.update_task_status(db, task_id, "running", {
                "coordinates": "completed", 
                "geocoding": "completed", 
                "property_details": "running"
            })
            
            # Extract additional property details
            details = extract_property_details(url, analysis_data)
            
            # Update property with additional details if available
            if analysis_data.get('Property ID'):
                property_obj.property_id = analysis_data.get('Property ID')
                db.commit()
                db.refresh(property_obj)
            
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
            "excel_export": "running"
        })
        
        # Step 3: Save analysis to database
        analysis_obj = save_analysis_to_db(db, property_obj, analysis_data)
        
        # Step 4: Save to Excel in organized folder
        excel_filename = f"property_{task_id}.xlsx"
        excel_full_path = save_to_excel(analysis_data, excel_filename)
        analysis_data["excel_file"] = excel_filename
        analysis_data["excel_path"] = excel_full_path
        
        TaskCRUD.update_task_status(db, task_id, "completed", {
            "coordinates": "completed" if coords.get('found') else "failed",
            "geocoding": "completed" if coords.get('found') else "skipped",
            "property_details": "completed" if coords.get('found') else "skipped",
            "scraping": "completed",
            "excel_export": "completed"
        })
        
        # Log completion
        AnalyticsCRUD.log_event(
            db, 
            "analysis_completed", 
            property_id=property_obj.id,
            task_id=task_id,
            event_data={"monthly_income": analysis_data.get('Monthly Income')}
        )
        
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
async def analyze_property(
    request: PropertyAnalysisRequest, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Start analysis of a SpareRoom property"""
    
    # Generate unique task ID
    task_id = str(uuid.uuid4())
    
    # Check if property already exists
    existing_property = PropertyCRUD.get_property_by_url(db, str(request.url))
    
    if existing_property:
        # Use existing property
        property_obj = existing_property
        print(f"Using existing property: {property_obj.id}")
    else:
        # Create new property record
        property_obj = PropertyCRUD.create_property(db, str(request.url))
        print(f"Created new property: {property_obj.id}")
    
    # Create task record
    TaskCRUD.create_task(db, task_id, property_obj.id)
    
    # Start background analysis task with database session
    background_tasks.add_task(analyze_property_task, task_id, str(request.url), db)
    
    return PropertyAnalysisResponse(
        task_id=task_id,
        status="pending",
        message="Analysis started. Use the task_id to check progress."
    )

@app.get("/api/analysis/{task_id}", response_model=AnalysisStatus)
async def get_analysis_status(task_id: str, db: Session = Depends(get_db)):
    """Get the status of an analysis task"""
    
    task = TaskCRUD.get_task_by_id(db, task_id)
    
    if not task:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )
    
    result = None
    if task.status == "completed" and task.property:
        # Get the latest analysis for this property
        latest_analysis = AnalysisCRUD.get_latest_analysis(db, task.property_id)
        if latest_analysis:
            # Convert analysis to the expected format
            result = {
                'Analysis Date': latest_analysis.analysis_date,
                'URL': task.property.url,
                'Latitude': task.property.latitude,
                'Longitude': task.property.longitude,
                'Full Address': task.property.address,
                'Postcode': task.property.postcode,
                'Property ID': task.property.property_id,
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
                'Meets Requirements': latest_analysis.meets_requirements
            }
    
    return AnalysisStatus(
        task_id=task_id,
        status=task.status,
        progress=task.progress or {},
        result=result,
        error=task.error_message
    )

@app.get("/api/properties")
async def get_all_properties(
    limit: int = 100, 
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get all analyzed properties with pagination"""
    properties = PropertyCRUD.get_all_properties(db, limit=limit, offset=offset)
    return [format_property_summary(prop) for prop in properties]

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

@app.get("/api/properties/{property_id}")
async def get_property_details(property_id: str, db: Session = Depends(get_db)):
    """Get detailed information about a specific property"""
    
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
    
    # Return detailed property data
    return {
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
        'Available Rooms Details': latest_analysis.available_rooms_details,
        'Taken Rooms': latest_analysis.taken_rooms,
        'Room Details': latest_analysis.room_details,
        'All Rooms List': latest_analysis.all_rooms_list,
        'Monthly Income': float(latest_analysis.monthly_income) if latest_analysis.monthly_income else None,
        'Annual Income': float(latest_analysis.annual_income) if latest_analysis.annual_income else None,
        'Meets Requirements': latest_analysis.meets_requirements
    }

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
    """Health check endpoint with database statistics"""
    
    # Get database statistics
    stats = AnalysisCRUD.get_analysis_stats(db)
    
    # Get active tasks
    active_tasks = TaskCRUD.get_active_tasks(db)
    
    # Get export statistics
    export_stats = get_export_stats()
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database_connected": True,
        "total_properties": stats["total_properties"],
        "total_analyses": stats["total_analyses"],
        "active_tasks": len(active_tasks),
        "viable_properties": stats["viable_properties"],
        "export_files": export_stats["total_files"],
        "export_size_mb": export_stats["total_size_mb"]
    }

# Add these new functions to your main.py

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any

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

async def update_property_task(task_id: str, property_ids: List[str], db: Session):
    """Background task to update multiple properties"""
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
                    print(f"[{task_id}] No changes detected for property {property_obj.id}")
                
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
    
    # Create task record
    TaskCRUD.create_task(db, task_id, None)  # No specific property for bulk updates
    
    # Start background update task
    background_tasks.add_task(update_property_task, task_id, property_ids, db)
    
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
    
    # Use the bulk update function for single property
    task_id = str(uuid.uuid4())
    TaskCRUD.create_task(db, task_id, property_obj.id)
    
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)