#!/usr/bin/env python3
"""
FastAPI Backend for HMO Analyser with Database Integration and Organized Excel Storage
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
from models import Property, PropertyAnalysis, AnalysisTask
from crud import PropertyCRUD, AnalysisCRUD, TaskCRUD, AnalyticsCRUD

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
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # React dev servers
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
    status: str  # "pending", "running", "completed", "failed"
    progress: Dict[str, str]  # {"coordinates": "completed", "scraping": "running", etc.}
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class PropertySummary(BaseModel):
    property_id: str
    url: str
    address: Optional[str]
    monthly_income: Optional[float]
    annual_income: Optional[float]
    total_rooms: Optional[int]
    available_rooms: Optional[int]
    bills_included: Optional[str]
    meets_requirements: Optional[str]
    analysis_date: str
    latitude: Optional[float]
    longitude: Optional[float]

class AnalyticsResponse(BaseModel):
    total_properties: int
    total_analyses: int
    viable_properties: int
    average_monthly_income: float
    total_monthly_income: float

class ExportStatsResponse(BaseModel):
    total_files: int
    total_size_mb: float
    exports_directory: str
    oldest_file: Optional[str]
    newest_file: Optional[str]

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
        # New fields for updated history page
        "advertiser_name": latest_analysis.advertiser_name if latest_analysis else None,
        "landlord_type": latest_analysis.landlord_type if latest_analysis else None,
        "listing_status": latest_analysis.listing_status if latest_analysis else None,
        "date_gone": None  # To be implemented later when properties are marked as gone
    }

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
                # Update the property_id field (SpareRoom property ID, not the database primary key)
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
    
    # Start background analysis task
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
    
    # Handle both UUID string formats and direct IDs
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

@app.get("/api/analytics", response_model=AnalyticsResponse)
async def get_analytics(db: Session = Depends(get_db)):
    """Get analytics and statistics"""
    stats = AnalysisCRUD.get_analysis_stats(db)
    
    return AnalyticsResponse(
        total_properties=stats["total_properties"],
        total_analyses=stats["total_analyses"],
        viable_properties=stats["viable_properties"],
        average_monthly_income=stats["average_monthly_income"],
        total_monthly_income=stats["total_monthly_income"]
    )

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

# Admin endpoints for file management
@app.get("/api/admin/export-stats", response_model=ExportStatsResponse)
async def get_export_statistics():
    """Get statistics about exported Excel files"""
    stats = get_export_stats()
    
    return ExportStatsResponse(
        total_files=stats["total_files"],
        total_size_mb=stats["total_size_mb"],
        exports_directory=stats["exports_directory"],
        oldest_file=stats.get("oldest_file"),
        newest_file=stats.get("newest_file")
    )

@app.post("/api/admin/cleanup-exports")
async def cleanup_old_export_files(days_old: int = 30):
    """Clean up Excel files older than specified days"""
    
    if days_old < 1:
        raise HTTPException(
            status_code=400,
            detail="days_old must be at least 1"
        )
    
    deleted_count = cleanup_old_exports(days_old)
    
    return {
        "message": f"Cleanup completed successfully",
        "deleted_files": deleted_count,
        "cutoff_days": days_old
    }

@app.get("/api/admin/exports")
async def list_export_files():
    """List all export files with details"""
    import glob
    
    exports_dir = get_exports_directory()
    excel_files = glob.glob(os.path.join(exports_dir, "*.xlsx"))
    
    file_list = []
    for file_path in excel_files:
        file_stat = os.stat(file_path)
        file_info = {
            "filename": os.path.basename(file_path),
            "size_bytes": file_stat.st_size,
            "size_mb": round(file_stat.st_size / (1024 * 1024), 2),
            "created": datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(file_stat.st_mtime).isoformat()
        }
        file_list.append(file_info)
    
    # Sort by creation date (newest first)
    file_list.sort(key=lambda x: x["created"], reverse=True)
    
    return {
        "total_files": len(file_list),
        "exports_directory": exports_dir,
        "files": file_list
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)