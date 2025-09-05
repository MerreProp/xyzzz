"""
Async Background Tasks for HMO Analyser - Phase 1 Implementation
High-performance async task system with real-time WebSocket updates
"""

import asyncio
import aiohttp
from datetime import datetime
from typing import List, Dict, Optional
import uuid
import traceback
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database_async import AsyncSessionLocal
from crud import TaskCRUD, PropertyCRUD, AnalysisCRUD, RoomCRUD, AnalyticsCRUD
from models import Property
from modules.async_scraper import extract_price_section_async, batch_extract_multiple_properties
from modules.coordinates import extract_coordinates, extract_property_details, reverse_geocode_nominatim
from websocket_manager import notify_progress, notify_stage_complete, notify_task_complete, notify_task_error
from modules.excel_handler import save_to_excel
from modules.async_scraper import cleanup_async_scraper


class AsyncTaskManager:
    """Manages async background tasks with WebSocket notifications"""
    
    def __init__(self):
        self.active_tasks: Dict[str, asyncio.Task] = {}
    
    async def start_property_analysis_task(self, task_id: str, url: str, existing_property_id: str = None):
        """Start an async property analysis task"""
        task = asyncio.create_task(
            self._analyze_property_async(task_id, url, existing_property_id)
        )
        self.active_tasks[task_id] = task
        
        # Clean up completed tasks
        task.add_done_callback(lambda t: self.active_tasks.pop(task_id, None))
        
        return task
    
    async def start_bulk_update_task(self, task_id: str, property_ids: List[str]):
        """Start an async bulk update task"""
        task = asyncio.create_task(
            self._bulk_update_properties_async(task_id, property_ids)
        )
        self.active_tasks[task_id] = task
        
        # Clean up completed tasks
        task.add_done_callback(lambda t: self.active_tasks.pop(task_id, None))
        
        return task
    
    async def _analyze_property_async(self, task_id: str, url: str, existing_property_id: str = None):
        """Async property analysis with real-time updates"""
        async with AsyncSessionLocal() as db:
            try:
                # Notify start
                await notify_progress(task_id, "starting", 0, "Initializing property analysis...")
                
                # Update task status in database
                await self._update_task_status_async(db, task_id, "running", {"stage": "starting"})
                
                # Step 1: Extract coordinates (25% progress)
                await notify_progress(task_id, "coordinates", 25, "Extracting location coordinates...")
                
                analysis_data = {'url': url, 'timestamp': datetime.now().isoformat()}
                
                # Note: extract_coordinates is still synchronous - we'd need to make it async too
                # For now, run it in a thread pool
                coords = await asyncio.get_event_loop().run_in_executor(
                    None, extract_coordinates, url, analysis_data
                )
                
                if coords.get('found'):
                    await notify_stage_complete(task_id, "coordinates", {"coordinates": coords})
                    
                    # Step 2: Reverse geocoding (40% progress)
                    await notify_progress(task_id, "geocoding", 40, "Getting address information...")
                    
                    lat, lon = coords['latitude'], coords['longitude']
                    await asyncio.get_event_loop().run_in_executor(
                        None, reverse_geocode_nominatim, lat, lon, analysis_data
                    )
                    
                    await notify_stage_complete(task_id, "geocoding", {"address": analysis_data.get('Address')})
                else:
                    await notify_progress(task_id, "coordinates", 25, "⚠️ Coordinates not found, continuing...")
                
                # Step 3: Property details extraction (60% progress)  
                await notify_progress(task_id, "property_details", 60, "Extracting property details...")
                
                # This would also need to be made async
                details = await asyncio.get_event_loop().run_in_executor(
                    None, extract_property_details, url, analysis_data
                )
                
                await notify_stage_complete(task_id, "property_details", details)
                
                # Step 4: Price section scraping (80% progress)
                await notify_progress(task_id, "scraping", 80, "Analyzing room availability and pricing...")
                
                # This is our new async scraper!
                analysis_data = await extract_price_section_async(url, analysis_data)
                
                # ✅ NEW: Early exit if listing is expired
                if analysis_data.get('_EXPIRED_LISTING'):
                    print(f"[{task_id}] ⚠️ LISTING EXPIRED - Stopping async analysis early")
                    print(f"[{task_id}] 🚫 Property is not currently accepting applications")
                    
                    # Notify about expired listing
                    await notify_stage_complete(task_id, "scraping", {
                        "status": "expired",
                        "listing_status": analysis_data.get('Listing Status', 'Expired'),
                        "message": "Listing is not currently accepting applications"
                    })
                    
                    # Complete task with expired status
                    result_data = {
                        'status': 'expired_listing',
                        'listing_status': analysis_data.get('Listing Status', 'Expired'),
                        'url': url,
                        'message': 'Listing is not currently accepting applications'
                    }
                    
                    await self._update_task_status_async(db, task_id, "completed", result_data)
                    await notify_task_complete(task_id, result_data)
                    
                    # Log analytics for expired listing
                    await self._log_analytics_async(db, "analysis_completed_expired", task_id, result_data)
                    
                    print(f"[{task_id}] ✅ Async analysis completed - Listing expired")
                    return  # Early exit for expired listings
                
                # Continue with normal analysis for active listings
                await notify_stage_complete(task_id, "scraping", {
                    "rooms_found": len(analysis_data.get('All Rooms List', [])),
                    "listing_status": analysis_data.get('Listing Status')
                })
                
                # Step 5: Save to database (90% progress)
                await notify_progress(task_id, "saving", 90, "Saving analysis to database...")
                
                # Get or create property
                if existing_property_id:
                    property_obj = await self._get_property_async(db, existing_property_id)
                else:
                    property_obj = await self._create_property_async(db, analysis_data)
                
                # Save analysis
                analysis_obj = await self._save_analysis_async(db, property_obj, analysis_data)
                
                # Process rooms (only for active listings)
                rooms_list = analysis_data.get('All Rooms List', [])
                if rooms_list:
                    room_results = await self._process_rooms_async(db, property_obj.id, rooms_list, analysis_obj.id)
                    await notify_stage_complete(task_id, "room_processing", room_results)
                
                # Step 6: Excel export (100% progress)
                await notify_progress(task_id, "exporting", 95, "Generating Excel report...")
                
                excel_filename = f"property_{task_id}.xlsx"
                excel_path = await asyncio.get_event_loop().run_in_executor(
                    None, save_to_excel, analysis_data, excel_filename
                )
                
                # Task complete!
                result_data = {
                    'property_id': str(property_obj.id),
                    'analysis_id': str(analysis_obj.id),
                    'excel_file': excel_filename,
                    'excel_path': excel_path,
                    'total_rooms': analysis_data.get('Total Rooms', 0),
                    'monthly_income': analysis_data.get('Monthly Income', 0),
                    'listing_status': analysis_data.get('Listing Status', 'Unknown')
                }
                
                await self._update_task_status_async(db, task_id, "completed", result_data)
                await notify_task_complete(task_id, result_data)
                
                # Log analytics
                await self._log_analytics_async(db, "analysis_completed", task_id, result_data)
                
                print(f"[{task_id}] ✅ Async analysis completed successfully!")
                
                # Clean up async scraper resources
                await cleanup_async_scraper()
                print(f"[{task_id}] 🧹 Async resources cleaned up")
                
            except Exception as e:
                error_msg = f"Analysis failed: {str(e)}"
                print(f"[{task_id}] ❌ {error_msg}")
                traceback.print_exc()
                
                await self._update_task_status_async(db, task_id, "failed", {"error": error_msg})
                await notify_task_error(task_id, error_msg)

    async def _bulk_update_properties_async(self, task_id: str, property_ids: List[str]):
        """Async bulk update with parallel processing"""
        async with AsyncSessionLocal() as db:
            try:
                total_properties = len(property_ids)
                await notify_progress(task_id, "starting", 0, f"Starting bulk update of {total_properties} properties...")
                
                # Update task status
                await self._update_task_status_async(db, task_id, "running", {"stage": "bulk_update"})
                
                # Process properties in batches for optimal performance
                batch_size = 5  # Process 5 properties simultaneously
                updated_count = 0
                changes_detected = 0
                
                for i in range(0, total_properties, batch_size):
                    batch = property_ids[i:i + batch_size]
                    batch_num = (i // batch_size) + 1
                    total_batches = (total_properties + batch_size - 1) // batch_size
                    
                    progress_percent = int((i / total_properties) * 100)
                    await notify_progress(
                        task_id, 
                        "processing", 
                        progress_percent, 
                        f"Processing batch {batch_num}/{total_batches} ({len(batch)} properties)..."
                    )
                    
                    # Process batch in parallel
                    batch_results = await asyncio.gather(
                        *[self._update_single_property_async(db, prop_id) for prop_id in batch],
                        return_exceptions=True
                    )
                    
                    # Count successful updates
                    for result in batch_results:
                        if isinstance(result, Exception):
                            print(f"❌ Batch update error: {result}")
                        else:
                            updated_count += 1
                            if result.get('changes_detected'):
                                changes_detected += 1
                    
                    # Notify batch completion
                    await notify_stage_complete(task_id, f"batch_{batch_num}", {
                        "batch_size": len(batch),
                        "successful_updates": len([r for r in batch_results if not isinstance(r, Exception)]),
                        "total_updated": updated_count
                    })
                
                # Final completion
                result_data = {
                    "total_properties": total_properties,
                    "updated_count": updated_count,
                    "changes_detected": changes_detected,
                    "completion_time": datetime.now().isoformat()
                }
                
                await self._update_task_status_async(db, task_id, "completed", result_data)
                await notify_task_complete(task_id, result_data)
                
                # Log analytics
                await self._log_analytics_async(db, "bulk_update_completed", task_id, result_data)
                
                print(f"[{task_id}] ✅ Bulk update completed: {updated_count} properties, {changes_detected} changes")
                
            except Exception as e:
                error_msg = f"Bulk update failed: {str(e)}"
                print(f"[{task_id}] ❌ {error_msg}")
                traceback.print_exc()
                
                await self._update_task_status_async(db, task_id, "failed", {"error": error_msg})
                await notify_task_error(task_id, error_msg)
    
    async def _update_single_property_async(self, db: AsyncSession, property_id: str) -> Dict:
        """Update a single property asynchronously"""
        try:
            # Get property
            result = await db.execute(
                select(Property).filter(Property.id == property_id)
            )
            property_obj = result.scalar_one_or_none()
            
            if not property_obj:
                return {"error": f"Property {property_id} not found"}
            
            # Get latest analysis for comparison
            latest_analysis = await self._get_latest_analysis_async(db, property_obj.id)
            if not latest_analysis:
                return {"error": f"No previous analysis found for {property_id}"}
            
            # Re-analyze using async scraper
            analysis_data = {'url': property_obj.url, 'timestamp': datetime.now().isoformat()}
            analysis_data = await extract_price_section_async(property_obj.url, analysis_data)
            
            # Compare with previous analysis
            changes_detected = await self._detect_changes_async(db, latest_analysis, analysis_data)
            
            if changes_detected:
                # Save new analysis
                new_analysis = await self._save_analysis_async(db, property_obj, analysis_data)
                
                # Process room changes
                if not analysis_data.get('_EXPIRED_LISTING'):
                    rooms_list = analysis_data.get('All Rooms List', [])
                    if rooms_list:
                        await self._process_rooms_async(db, property_obj.id, rooms_list, new_analysis.id)
                
                return {
                    "success": True,
                    "changes_detected": True,
                    "property_id": property_id,
                    "new_analysis_id": str(new_analysis.id)
                }
            else:
                return {
                    "success": True,
                    "changes_detected": False,
                    "property_id": property_id
                }
                
        except Exception as e:
            return {"error": f"Failed to update {property_id}: {str(e)}"}
    
    # Helper methods for database operations
    async def _update_task_status_async(self, db: AsyncSession, task_id: str, status: str, progress: Dict):
        """Update task status in database asynchronously"""
        # Note: This would need to be implemented with async SQLAlchemy
        # For now, we'll run the sync version in a thread pool
        await asyncio.get_event_loop().run_in_executor(
            None, 
            lambda: self._update_task_status_sync(task_id, status, progress)
        )
    
    def _update_task_status_sync(self, task_id: str, status: str, progress: Dict):
        """Sync version of task status update (temporary)"""
        from database import SessionLocal
        with SessionLocal() as sync_db:
            TaskCRUD.update_task_status(sync_db, task_id, status, progress)
    
    async def _get_property_async(self, db: AsyncSession, property_id: str):
        """Get property by ID asynchronously"""
        result = await db.execute(
            select(Property).filter(Property.id == property_id)
        )
        return result.scalar_one_or_none()
    
    async def _create_property_async(self, db: AsyncSession, analysis_data: Dict):
        """Create new property asynchronously"""
        # This would need to be implemented with async SQLAlchemy
        # For now, run sync version in thread pool
        return await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self._create_property_sync(analysis_data)
        )
    
    def _create_property_sync(self, analysis_data: Dict):
        """Sync version of property creation (temporary)"""
        from database import SessionLocal
        with SessionLocal() as sync_db:
            # Extract the URL from analysis_data and pass it as the second parameter
            url = analysis_data['url']
            
            # Pass any additional property fields from analysis_data as kwargs
            # Filter out fields that don't belong in the Property model
            property_fields = {}
            
            # Add fields that should be stored in the Property model
            if 'Address' in analysis_data:
                property_fields['address'] = analysis_data['Address']
            if 'Postcode' in analysis_data:
                property_fields['postcode'] = analysis_data['Postcode']
            if 'latitude' in analysis_data:
                property_fields['latitude'] = analysis_data['latitude']
            if 'longitude' in analysis_data:
                property_fields['longitude'] = analysis_data['longitude']
            if 'City' in analysis_data:
                property_fields['city'] = analysis_data['City']
            if 'Area' in analysis_data:
                property_fields['area'] = analysis_data['Area']
            if 'District' in analysis_data:
                property_fields['district'] = analysis_data['District']
            if 'County' in analysis_data:
                property_fields['county'] = analysis_data['County']
            if 'Country' in analysis_data:
                property_fields['country'] = analysis_data['Country']
            if 'Constituency' in analysis_data:
                property_fields['constituency'] = analysis_data['Constituency']
            
            return PropertyCRUD.create_property(sync_db, url, **property_fields)
    
    async def _save_analysis_async(self, db: AsyncSession, property_obj, analysis_data: Dict):
        """Save analysis asynchronously"""
        return await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self._save_analysis_sync(property_obj, analysis_data)
        )
    
    def _save_analysis_sync(self, property_obj, analysis_data: Dict):
        """Sync version of analysis saving (temporary)"""
        from database import SessionLocal
        with SessionLocal() as sync_db:
            # Extract property_id from property_obj and pass analysis_data as kwargs
            property_id = property_obj.id
            
            # Filter analysis_data to only include fields that belong in PropertyAnalysis model
            analysis_fields = {}
            
            # Add fields that should be stored in the PropertyAnalysis model
            # Based on your actual PropertyAnalysis model structure
            field_mappings = {
                'Total Rooms': 'total_rooms',
                'Monthly Income': 'monthly_income', 
                'Bills Included': 'bills_included',
                'Listing Status': 'listing_status',
                'Advertiser Name': 'advertiser_name',
                'All Rooms List': 'all_rooms_list',
                'Available Rooms': 'available_rooms',
                'Taken Rooms': 'taken_rooms',
                'Listed Rooms': 'listed_rooms',
                'Landlord Type': 'landlord_type',
                'Household Gender': 'household_gender',
                'Main Photo URL': 'main_photo_url',
                'Analysis Date': 'analysis_date',
                'Title': 'title',
                'Meets Requirements': 'meets_requirements'
            }
            
            for key, db_field in field_mappings.items():
                if key in analysis_data:
                    analysis_fields[db_field] = analysis_data[key]
            
            # Convert 'All Rooms List' to JSON if it's a list (PostgreSQL JSON field)
            if 'all_rooms_list' in analysis_fields and isinstance(analysis_fields['all_rooms_list'], list):
                # PostgreSQL JSON field can accept Python lists directly
                pass  # No conversion needed for PostgreSQL JSON fields
            
            # Calculate annual income if monthly income is provided
            if 'monthly_income' in analysis_fields and analysis_fields['monthly_income']:
                try:
                    monthly = float(analysis_fields['monthly_income'])
                    analysis_fields['annual_income'] = monthly * 12
                except (ValueError, TypeError):
                    pass
            
            return AnalysisCRUD.create_analysis(sync_db, property_id, **analysis_fields)
    
    async def _process_rooms_async(self, db: AsyncSession, property_id, rooms_list: List, analysis_id):
        """Process rooms asynchronously"""
        return await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self._process_rooms_sync(property_id, rooms_list, analysis_id)
        )
    
    def _process_rooms_sync(self, property_id, rooms_list: List, analysis_id):
        """Sync version of room processing (temporary)"""
        from database import SessionLocal
        with SessionLocal() as sync_db:
            return RoomCRUD.process_rooms_list(sync_db, property_id, rooms_list, analysis_id)
    
    async def _get_latest_analysis_async(self, db: AsyncSession, property_id):
        """Get latest analysis asynchronously"""
        return await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self._get_latest_analysis_sync(property_id)
        )
    
    def _get_latest_analysis_sync(self, property_id):
        """Sync version of getting latest analysis (temporary)"""
        from database import SessionLocal
        with SessionLocal() as sync_db:
            return AnalysisCRUD.get_latest_analysis(sync_db, property_id)
    
    async def _detect_changes_async(self, db: AsyncSession, latest_analysis, analysis_data: Dict) -> bool:
        """Detect if there are changes in the analysis"""
        # Simple change detection - compare key fields
        old_status = latest_analysis.listing_status
        new_status = analysis_data.get('Listing Status')
        
        old_rooms = latest_analysis.total_rooms or 0
        new_rooms = analysis_data.get('Total Rooms', 0)
        
        old_income = float(latest_analysis.monthly_income or 0)
        new_income = float(analysis_data.get('Monthly Income', 0))
        
        return (old_status != new_status or 
                old_rooms != new_rooms or 
                abs(old_income - new_income) > 0.01)
    
    async def _log_analytics_async(self, db: AsyncSession, event_type: str, task_id: str, event_data: Dict):
        """Log analytics event asynchronously"""
        await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self._log_analytics_sync(event_type, task_id, event_data)
        )
    
    def _log_analytics_sync(self, event_type: str, task_id: str, event_data: Dict):
        """Sync version of analytics logging (temporary)"""
        from database import SessionLocal
        with SessionLocal() as sync_db:
            AnalyticsCRUD.log_event(sync_db, event_type, task_id=task_id, event_data=event_data)
    
    def get_active_tasks(self) -> Dict[str, str]:
        """Get list of currently active tasks"""
        return {
            task_id: "running" if not task.done() else "completed"
            for task_id, task in self.active_tasks.items()
        }
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task"""
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            if not task.done():
                task.cancel()
                await notify_task_error(task_id, "Task cancelled by user")
                return True
        return False

# Global task manager instance
task_manager = AsyncTaskManager()

# Helper functions for use in FastAPI endpoints
async def start_property_analysis(task_id: str, url: str, existing_property_id: str = None):
    """Start async property analysis task"""
    return await task_manager.start_property_analysis_task(task_id, url, existing_property_id)

async def start_bulk_update(task_id: str, property_ids: List[str]):
    """Start async bulk update task"""
    return await task_manager.start_bulk_update_task(task_id, property_ids)

async def get_active_tasks():
    """Get currently active tasks"""
    return task_manager.get_active_tasks()

async def cancel_task(task_id: str):
    """Cancel a running task"""
    return await task_manager.cancel_task(task_id)