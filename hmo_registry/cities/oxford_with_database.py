# hmo_registry/cities/oxford_with_database.py
"""
Oxford HMO Registry with Database Storage
Geocodes once, stores in database, serves from cache
"""

import requests
import pandas as pd
from io import StringIO
from typing import List, Dict, Optional, Tuple
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from .base_city import BaseHMODataSource
from ..database_models import HMORegistry, create_hmo_registry_table, check_hmo_table_exists
from database import SessionLocal

# Try to import geocoding functions
try:
    from ..utils.improved_geocoding import geocode_address, extract_postcode_from_address, get_geocoding_statistics
    GEOCODING_AVAILABLE = True
    print("✅ Improved geocoding functions imported successfully")
except ImportError:
    try:
        from modules.coordinates import geocode_address, extract_postcode_from_address
        GEOCODING_AVAILABLE = True
        print("⚠️ Using fallback geocoding functions")
    except ImportError:
        print("⚠️ Geocoding functions not found - using fallback methods")
        GEOCODING_AVAILABLE = False
        
        def geocode_address(address):
            return None
        
        def extract_postcode_from_address(address):
            import re
            postcode_pattern = r'([A-Z]{1,2}[0-9R][0-9A-Z]? ?[0-9][A-Z]{2})'
            match = re.search(postcode_pattern, address.upper())
            return match.group(1) if match else None

logger = logging.getLogger(__name__)

class OxfordHMOWithDatabase(BaseHMODataSource):
    """Oxford HMO Registry with database storage for geocoded data"""
    
    CSV_URL = "https://oxopendata.github.io/register-of-houses-in-multiple-occupation/data/hmo-simplified-register.csv"
    
    def __init__(self):
        super().__init__("oxford", cache_duration=3600)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'HMO-Analyser/1.0 (Property Analysis Tool)'
        })
        
        # IMPORTANT: Don't check database during initialization
        # We'll check it lazily when needed
        self._database_checked = False
        self._database_ready = False

    def _ensure_database_ready(self):
        """Ensure database table exists - called lazily when needed"""
        if self._database_checked:
            return self._database_ready
        
        try:
            # Now we can safely check the database
            if not check_hmo_table_exists():
                logger.info("Creating HMO registry table...")
                create_hmo_registry_table()
                self._database_ready = True
            else:
                self._database_ready = True
                
        except Exception as e:
            logger.error(f"Database setup failed: {e}")
            self._database_ready = False
        
        self._database_checked = True
        return self._database_ready

    def fetch_raw_data(self) -> List[Dict]:
        """Fetch raw data from Oxford's CSV"""
        try:
            response = self.session.get(self.CSV_URL, timeout=30)
            response.raise_for_status()
            
            df = pd.read_csv(StringIO(response.text))
            df = df.dropna(subset=['Location'])
            df = df.drop_duplicates(subset=['Case Number'])
            
            logger.info(f"Fetched {len(df)} Oxford HMO records from CSV")
            return df.to_dict('records')
            
        except Exception as e:
            logger.error(f"Error fetching Oxford raw data: {e}")
            return []
    
    def get_hmo_data(self, force_refresh: bool = False, enable_geocoding: bool = True) -> List[Dict]:
        """Get HMO data from database first, geocode missing ones - WITH LAZY DATABASE CHECK"""
        
        # Ensure database is ready before proceeding
        if not self._ensure_database_ready():
            logger.warning("Database not available, falling back to direct CSV fetch")
            return self._fetch_from_csv_only()
        
        db = SessionLocal()
        try:
            # Check if we have recent data in database
            if not force_refresh:
                recent_data = self._get_database_data(db)
                if recent_data:
                    logger.info(f"Returning {len(recent_data)} Oxford HMO records from database")
                    return recent_data
            
            # Fetch fresh data and update database
            logger.info("Fetching fresh Oxford HMO data and updating database...")
            return self._fetch_and_update_database(db, enable_geocoding)
            
        finally:
            db.close()
    
    def _fetch_from_csv_only(self) -> List[Dict]:
        """Fallback method to fetch directly from CSV when database unavailable"""
        try:
            raw_data = self.fetch_raw_data()
            processed_data = []
            
            for record in raw_data:
                processed_record = self._process_record_without_db(record)
                if processed_record:
                    processed_data.append(processed_record)
            
            logger.info(f"Fetched {len(processed_data)} records directly from CSV (no database)")
            return processed_data
            
        except Exception as e:
            logger.error(f"Failed to fetch from CSV: {e}")
            return []
    
    def _process_record_without_db(self, record: Dict) -> Optional[Dict]:
        """Process a record without database storage"""
        try:
            # Basic processing without geocoding
            return {
                'id': f"oxford_hmo_{record.get('Case Number', '')}",
                'case_number': record.get('Case Number', ''),
                'address': record.get('Location', ''),
                'postcode': extract_postcode_from_address(record.get('Location', '')),
                'licence_status': 'unknown',
                'city': 'oxford',
                'latitude': None,
                'longitude': None,
                'geocoded': False,
                'source': 'oxford_csv_fallback',
                'total_occupants': self._safe_int(record.get('Total Number Occupants')),
                'total_units': self._safe_int(record.get('Total Number Units')),
                'licence_start_date': None,
                'licence_expiry_date': None,
                'data_quality_score': 0.3,
                'processing_notes': 'Fallback mode - no database geocoding',
                'last_updated': datetime.utcnow().isoformat(),
                'data_source_url': self.CSV_URL
            }
        except Exception as e:
            logger.error(f"Error processing record without database: {e}")
            return None
    
    def _get_database_data(self, db: Session) -> Optional[List[Dict]]:
        """Get data from database if recent enough"""
        try:
            # Check if we have any Oxford data less than 24 hours old
            recent_threshold = datetime.utcnow() - timedelta(days=7)
            
            count = db.query(HMORegistry).filter(
                and_(
                    HMORegistry.city == 'oxford',
                    HMORegistry.updated_at > recent_threshold
                )
            ).count()
            
            if count == 0:
                logger.info("No recent Oxford data in database")
                return None
            
            # Get all Oxford records
            records = db.query(HMORegistry).filter(
                HMORegistry.city == 'oxford'
            ).all()
            
            logger.info(f"Found {len(records)} Oxford HMO records in database ({count} recent)")
            
            # Convert to API format
            return [self._database_record_to_api_format(record) for record in records]
            
        except Exception as e:
            logger.error(f"Error getting database data: {e}")
            return None
    
    def _fetch_and_update_database(self, db: Session, enable_geocoding: bool = True) -> List[Dict]:
        """Fetch fresh data and update database"""
        
        # Fetch raw data
        raw_data = self.fetch_raw_data()
        if not raw_data:
            return []
        
        processed_data = []
        new_geocoded = 0
        updated_count = 0
        batch_size = 50  # Commit in batches to avoid long transactions
        
        for i, record in enumerate(raw_data):
            case_number = str(record.get('Case Number', '')).strip()
            if not case_number:
                continue
            
            # Check if record exists in database
            existing = db.query(HMORegistry).filter(
                and_(
                    HMORegistry.city == 'oxford',
                    HMORegistry.case_number == case_number
                )
            ).first()
            
            if existing:
                # Update existing record
                api_record = self._update_existing_record(db, existing, record, enable_geocoding)
                if existing.geocoded and not existing.latitude:  # Was geocoded in this update
                    new_geocoded += 1
            else:
                # Create new record
                api_record = self._create_new_record(db, record, enable_geocoding)
                if api_record and api_record.get('geocoded'):
                    new_geocoded += 1
            
            if api_record:
                processed_data.append(api_record)
                updated_count += 1
            
            # Commit in batches to avoid long transactions
            if (i + 1) % batch_size == 0:
                try:
                    db.commit()
                    logger.info(f"📦 Committed batch {i + 1}/{len(raw_data)} records")
                except Exception as e:
                    logger.error(f"❌ Error committing batch at record {i + 1}: {e}")
                    db.rollback()
                    continue
        
        # Final commit for remaining records
        try:
            db.commit()
            logger.info(f"✅ Final commit completed")
        except Exception as e:
            logger.error(f"❌ Error in final commit: {e}")
            db.rollback()
        
        if new_geocoded > 0:
            logger.info(f"✅ Geocoded {new_geocoded} new Oxford addresses")
        
        logger.info(f"✅ Updated {updated_count} Oxford HMO records in database")
        return processed_data
    
    # Helper methods
    def _safe_int(self, value) -> Optional[int]:
        """Safely convert to int"""
        if value is None or value == '':
            return None
        try:
            return int(float(str(value)))
        except (ValueError, TypeError):
            return None
    
    def _safe_date(self, value) -> Optional[datetime.date]:
        """Safely convert to date"""
        if not value:
            return None
        try:
            if isinstance(value, str):
                return datetime.strptime(value, '%Y-%m-%d').date()
            return value
        except (ValueError, TypeError):
            return None
    
    def _create_new_record(self, db: Session, raw_record: Dict, enable_geocoding: bool) -> Optional[Dict]:
        """Create new HMO record in database"""
        
        case_number = str(raw_record.get('Case Number', '')).strip()
        location = str(raw_record.get('Location', '')).strip()
        
        if not case_number or not location:
            return None
        
        # Extract basic info
        total_occupants = self._safe_int(raw_record.get('Total Number Occupants'))
        total_units = self._safe_int(raw_record.get('Total Number Units'))
        licence_start = self._safe_date(raw_record.get('Licence Commenced'))
        licence_expires = self._safe_date(raw_record.get('Licence Expires'))
        
        # Determine licence status
        licence_status = 'active'
        if licence_expires and licence_expires < datetime.now().date():
            licence_status = 'expired'
        elif not licence_expires:
            licence_status = 'unknown'
        
        # Extract postcode
        postcode = extract_postcode_from_address(location)
        
        # Geocode if enabled (this is the expensive part!)
        coords = None
        geocoded = False
        if enable_geocoding and GEOCODING_AVAILABLE:
            try:
                coords = geocode_address(location)
                if coords:
                    geocoded = True
                    logger.debug(f"📍 Geocoded: {location} -> {coords}")
            except Exception as e:
                logger.debug(f"🔍 Geocoding error for {location}: {e}")
        
        # Create database record
        db_record = HMORegistry(
            city='oxford',
            source='oxford_council',
            case_number=case_number,
            data_source_url=self.CSV_URL,
            raw_address=location,
            postcode=postcode,
            latitude=coords[0] if coords else None,
            longitude=coords[1] if coords else None,
            geocoded=geocoded,
            geocoding_source='nominatim' if geocoded else None,
            total_occupants=total_occupants,
            total_units=total_units,
            licence_status=licence_status,
            licence_start_date=licence_start,
            licence_expiry_date=licence_expires,
            data_quality_score=self._calculate_confidence_db(raw_record, coords, postcode),
            processing_notes=self._generate_processing_notes(raw_record, coords, postcode),
            source_last_updated=datetime.utcnow()
        )
        
        db.add(db_record)
        
        return self._database_record_to_api_format(db_record)
    
    def _update_existing_record(self, db: Session, existing: HMORegistry, raw_record: Dict, enable_geocoding: bool) -> Dict:
        """Update existing HMO record"""
        
        # Update basic fields
        location = str(raw_record.get('Location', '')).strip()
        existing.raw_address = location
        existing.total_occupants = self._safe_int(raw_record.get('Total Number Occupants'))
        existing.total_units = self._safe_int(raw_record.get('Total Number Units'))
        existing.licence_start_date = self._safe_date(raw_record.get('Licence Commenced'))
        existing.licence_expiry_date = self._safe_date(raw_record.get('Licence Expires'))
        
        # Update licence status
        if existing.licence_expiry_date and existing.licence_expiry_date < datetime.now().date():
            existing.licence_status = 'expired'
        elif existing.licence_expiry_date:
            existing.licence_status = 'active'
        else:
            existing.licence_status = 'unknown'
        
        # Geocode if not already geocoded
        if not existing.geocoded and enable_geocoding and GEOCODING_AVAILABLE:
            try:
                coords = geocode_address(location)
                if coords:
                    existing.latitude = coords[0]
                    existing.longitude = coords[1]
                    existing.geocoded = True
                    existing.geocoding_source = 'nominatim'
                    logger.debug(f"📍 Geocoded existing: {location} -> {coords}")
            except Exception as e:
                logger.debug(f"🔍 Geocoding error for {location}: {e}")
        
        # Update postcode if missing
        if not existing.postcode:
            existing.postcode = extract_postcode_from_address(location)
        
        existing.updated_at = datetime.utcnow()
        existing.source_last_updated = datetime.utcnow()
        
        return self._database_record_to_api_format(existing)
    
    def _database_record_to_api_format(self, record: HMORegistry) -> Dict:
        """Convert database record to API format"""
        return {
            'id': f"oxford_hmo_{record.case_number}",
            'case_number': record.case_number,
            'source': record.source,
            'city': record.city,
            'address': record.raw_address,
            'postcode': record.postcode,
            'latitude': float(record.latitude) if record.latitude else None,
            'longitude': float(record.longitude) if record.longitude else None,
            'geocoded': record.geocoded,
            'total_occupants': record.total_occupants,
            'total_units': record.total_units,
            'licence_status': record.licence_status,
            'licence_start_date': record.licence_start_date.isoformat() if record.licence_start_date else None,
            'licence_expiry_date': record.licence_expiry_date.isoformat() if record.licence_expiry_date else None,
            'data_quality_score': float(record.data_quality_score) if record.data_quality_score else 0.0,
            'processing_notes': record.processing_notes or '',
            'last_updated': record.updated_at.isoformat() if record.updated_at else datetime.utcnow().isoformat(),
            'data_source_url': record.data_source_url
        }
    
    def _calculate_confidence_db(self, record: Dict, coords: Optional[Tuple], postcode: Optional[str]) -> float:
        """Calculate confidence score for database record"""
        score = 0.0
        
        if coords:
            score += 0.4
        if postcode:
            score += 0.3
        if self._safe_int(record.get('Total Number Occupants')):
            score += 0.2
        if self._safe_int(record.get('Total Number Units')):
            score += 0.1
        if self._safe_date(record.get('Licence Expires')):
            score += 0.1
        
        return min(score, 1.0)
    
    def _generate_processing_notes(self, record: Dict, coords: Optional[Tuple], postcode: Optional[str]) -> str:
        """Generate processing notes"""
        notes = []
        if coords:
            notes.append("Geocoded successfully")
        if not postcode:
            notes.append("No postcode found")
        if not self._safe_int(record.get('Total Number Occupants')):
            notes.append("Missing occupant count")
        
        return "; ".join(notes) if notes else "Complete record"
    
    def process_record(self, record: Dict, enable_geocoding: bool = True) -> Optional[Dict]:
        """This method is required by base class but not used in database version"""
        # Database version handles processing differently
        return None
    
    def get_statistics(self) -> Dict:
        """Get statistics from database"""
        # Ensure database is ready
        if not self._ensure_database_ready():
            return {'error': 'Database not available'}
            
        db = SessionLocal()
        try:
            total_records = db.query(HMORegistry).filter(HMORegistry.city == 'oxford').count()
            
            if total_records == 0:
                return {'error': 'No Oxford data in database'}
            
            geocoded_records = db.query(HMORegistry).filter(
                and_(HMORegistry.city == 'oxford', HMORegistry.geocoded == True)
            ).count()
            
            active_licences = db.query(HMORegistry).filter(
                and_(HMORegistry.city == 'oxford', HMORegistry.licence_status == 'active')
            ).count()
            
            expired_licences = db.query(HMORegistry).filter(
                and_(HMORegistry.city == 'oxford', HMORegistry.licence_status == 'expired')
            ).count()
            
            # Get average data quality
            avg_quality = db.query(func.avg(HMORegistry.data_quality_score)).filter(
                HMORegistry.city == 'oxford'
            ).scalar() or 0
            
            # Get last updated
            last_updated = db.query(func.max(HMORegistry.updated_at)).filter(
                HMORegistry.city == 'oxford'
            ).scalar()
            
            return {
                'total_records': total_records,
                'geocoded_records': geocoded_records,
                'geocoding_success_rate': round((geocoded_records / total_records * 100), 1) if total_records > 0 else 0,
                'active_licences': active_licences,
                'expired_licences': expired_licences,
                'unknown_status': total_records - active_licences - expired_licences,
                'average_data_quality': round(float(avg_quality), 2),
                'last_updated': last_updated.isoformat() if last_updated else None
            }
            
        finally:
            db.close()


# Create the database-backed version
OxfordHMOMapData = OxfordHMOWithDatabase