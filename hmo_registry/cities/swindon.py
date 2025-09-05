
# hmo_registry/cities/swindon.py
"""
Swindon HMO Registry Integration
===============================

Integrates Swindon HMO data into the unified registry system.
Data source: Excel file from Swindon Borough Council
"""

import pandas as pd
import re
import time
import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
import requests
from sqlalchemy import and_, func

# Your existing imports
try:
    from ..registry_models import HMOProperty, HMORegistryResponse, HMORegistryStats
    from database_models import HMORegistry, SessionLocal
except ImportError:
    # Fallback for direct usage
    pass

logger = logging.getLogger(__name__)

class SwindonHMOMapData:
    """Swindon HMO registry data handler"""
    
    def __init__(self):
        self.city = 'swindon'
        self.source_type = 'excel'
        self.data_source_name = 'Swindon Borough Council HMO Register'
        self.update_frequency = 'manual'
        
    def clean_address_text(self, address: str) -> str:
        """Clean address text by removing excessive whitespace and formatting"""
        if not address:
            return ""
        
        # Replace \r\n with spaces and clean up
        cleaned = re.sub(r'\r\n', ' ', str(address))
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = cleaned.strip()
        
        return cleaned
    
    def extract_postcode(self, address: str) -> Optional[str]:
        """Extract UK postcode from address"""
        if not address:
            return None
        
        # UK postcode pattern
        postcode_pattern = r'([A-Z]{1,2}[0-9]{1,2}[A-Z]?\s?[0-9][A-Z]{2})'
        match = re.search(postcode_pattern, address.upper())
        
        if match:
            postcode = match.group(1)
            # Ensure proper spacing
            if len(postcode) >= 5 and ' ' not in postcode:
                postcode = postcode[:-3] + ' ' + postcode[-3:]
            return postcode.upper()
        
        return None
    
    def geocode_address(self, address: str) -> Tuple[Optional[float], Optional[float]]:
        """Geocode an address using Nominatim"""
        try:
            full_address = f"{address}, Swindon, Wiltshire, UK"
            
            url = "https://nominatim.openstreetmap.org/search"
            params = {
                'q': full_address,
                'format': 'json',
                'limit': 1,
                'countrycodes': 'gb'
            }
            
            headers = {'User-Agent': 'SwindonHMORegistry/1.0'}
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            
            results = response.json()
            
            if results:
                return float(results[0]['lat']), float(results[0]['lon'])
            
            return None, None
                
        except Exception as e:
            logger.debug(f"Geocoding error for {address[:50]}...: {e}")
            return None, None
    
    def process_excel_file(self, excel_path: str, enable_geocoding: bool = True) -> List[Dict]:
        """Process the Swindon Excel file and return standardized data"""
        logger.info(f"Processing Swindon Excel file: {excel_path}")
        
        try:
            # Read Excel file
            df = pd.read_excel(excel_path, sheet_name='List of HMOs')
            df.columns = df.columns.str.strip()
            
            processed_records = []
            geocoding_count = 0
            
            for index, row in df.iterrows():
                try:
                    raw_address = str(row['HMO Address']).strip()
                    licence_holder = str(row['Licence Holder']).strip()  # Fixed: removed trailing space
                    
                    if not raw_address or raw_address.lower() in ['nan', 'none', '']:
                        continue
                    
                    # Clean address
                    cleaned_address = self.clean_address_text(raw_address)
                    postcode = self.extract_postcode(cleaned_address)
                    
                    # Generate unique case number
                    case_number = f"SWD{index+1:04d}_{str(hash(cleaned_address.lower()))[-4:]}"
                    
                    # Geocode if enabled
                    lat, lon = None, None
                    geocoded = False
                    
                    if enable_geocoding:
                        lat, lon = self.geocode_address(cleaned_address)
                        if lat and lon:
                            geocoded = True
                            geocoding_count += 1
                        
                        # Rate limiting
                        if geocoding_count % 10 == 0:
                            logger.info(f"Geocoded {geocoding_count} addresses...")
                        time.sleep(1.0)
                    
                    # Calculate data quality score
                    quality_score = 0.0
                    if cleaned_address and len(cleaned_address) > 10:
                        quality_score += 0.3
                    if postcode:
                        quality_score += 0.3
                    if geocoded:
                        quality_score += 0.3
                    if licence_holder and len(licence_holder) > 3:
                        quality_score += 0.1
                    
                    record = {
                        'case_number': case_number,
                        'raw_address': raw_address,
                        'cleaned_address': cleaned_address,
                        'postcode': postcode,
                        'latitude': lat,
                        'longitude': lon,
                        'geocoded': geocoded,
                        'licence_holder': licence_holder,
                        'quality_score': min(quality_score, 1.0)
                    }
                    
                    processed_records.append(record)
                    
                except Exception as e:
                    logger.error(f"Error processing row {index}: {e}")
                    continue
            
            logger.info(f"Processed {len(processed_records)} Swindon records, geocoded {geocoding_count}")
            return processed_records
            
        except Exception as e:
            logger.error(f"Error processing Excel file: {e}")
            raise
    
    def update_database_from_excel(self, excel_path: str, enable_geocoding: bool = True) -> Dict:
        """Update database with data from Excel file"""
        logger.info("Updating Swindon database from Excel file")
        
        # Process Excel file
        records = self.process_excel_file(excel_path, enable_geocoding)
        
        try:
            from database_models import HMORegistry, SessionLocal
            db = SessionLocal()
        except ImportError:
            # Fallback to direct database connection
            import sqlite3
            return self._update_database_sqlite(records)
        
        stats = {'inserted': 0, 'updated': 0, 'errors': 0}
        
        try:
            for record in records:
                try:
                    # Check if record exists
                    existing = db.query(HMORegistry).filter(
                        and_(
                            HMORegistry.city == 'swindon',
                            HMORegistry.case_number == record['case_number']
                        )
                    ).first()
                    
                    if existing:
                        # Update existing record
                        existing.raw_address = record['raw_address']
                        existing.standardized_address = record['cleaned_address']
                        existing.postcode = record['postcode']
                        existing.latitude = record['latitude']
                        existing.longitude = record['longitude']
                        existing.geocoded = record['geocoded']
                        existing.licence_holder_name = record['licence_holder']
                        existing.data_quality_score = record['quality_score']
                        existing.updated_at = datetime.utcnow()
                        existing.source_last_updated = datetime.utcnow()
                        
                        stats['updated'] += 1
                    else:
                        # Create new record
                        hmo_record = HMORegistry(
                            city='swindon',
                            source_type='excel',
                            source_url='manual_upload',
                            last_updated=datetime.utcnow(),
                            data_freshness='manual',
                            
                            case_number=record['case_number'],
                            raw_address=record['raw_address'],
                            standardized_address=record['cleaned_address'],
                            postcode=record['postcode'],
                            latitude=record['latitude'],
                            longitude=record['longitude'],
                            geocoded=record['geocoded'],
                            geocoding_source='nominatim' if record['geocoded'] else None,
                            
                            licence_status='active',  # Assume active (no expiry data)
                            licence_holder_name=record['licence_holder'],
                            
                            data_quality_score=record['quality_score'],
                            processing_notes=f'Imported from Excel on {datetime.now().strftime("%Y-%m-%d")}',
                            
                            created_at=datetime.utcnow(),
                            updated_at=datetime.utcnow(),
                            source_last_updated=datetime.utcnow()
                        )
                        
                        db.add(hmo_record)
                        stats['inserted'] += 1
                
                except Exception as e:
                    logger.error(f"Error saving record {record['case_number']}: {e}")
                    stats['errors'] += 1
                    continue
            
            db.commit()
            logger.info(f"Database update complete: {stats}")
            
        except Exception as e:
            logger.error(f"Database error: {e}")
            db.rollback()
            raise
        
        finally:
            db.close()
        
        return stats
    
    def get_statistics(self) -> Dict:
        """Get Swindon HMO statistics in the unified format"""
        try:
            import pandas as pd
            df = pd.read_csv('swindon_hmo_processed.csv')
            
            total_records = len(df)
            geocoded_records = df['geocoded'].sum()
            geocoding_rate = (geocoded_records / total_records * 100) if total_records > 0 else 0
            avg_quality = df['quality_score'].mean() if 'quality_score' in df.columns else 0
            
            return {
                'total_records': total_records,
                'geocoded_records': int(geocoded_records),
                'geocoding_success_rate': round(geocoding_rate, 1),
                'active_licences': total_records,  # Assume all active for now
                'expired_licences': 0,
                'unknown_status': 0,
                'average_data_quality': round(avg_quality, 2),
                'last_updated': datetime.now().isoformat()
            }
            
        except FileNotFoundError:
            return {
                'total_records': 0,
                'geocoded_records': 0,
                'geocoding_success_rate': 0,
                'active_licences': 0,
                'expired_licences': 0,
                'unknown_status': 0,
                'average_data_quality': 0,
                'last_updated': None
            }
        except Exception as e:
            logger.error(f"Error getting Swindon statistics: {e}")
            return {
                'total_records': 0,
                'geocoded_records': 0,
                'geocoding_success_rate': 0,
                'active_licences': 0,
                'expired_licences': 0,
                'unknown_status': 0,
                'average_data_quality': 0,
                'last_updated': None
            }
    
    def _get_statistics_sqlite(self) -> Dict:
        """Fallback statistics using direct SQLite connection"""
        try:
            import sqlite3
            conn = sqlite3.connect('hmo_analyser.db')
            cursor = conn.cursor()
            
            # Get basic counts
            cursor.execute("SELECT COUNT(*) FROM hmo_registries WHERE city = 'swindon'")
            total_records = cursor.fetchone()[0]
            
            if total_records == 0:
                return {'error': 'No Swindon data in database'}
            
            cursor.execute("SELECT COUNT(*) FROM hmo_registries WHERE city = 'swindon' AND geocoded = 1")
            geocoded_records = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM hmo_registries WHERE city = 'swindon' AND licence_status = 'active'")
            active_licences = cursor.fetchone()[0]
            
            cursor.execute("SELECT AVG(data_quality_score) FROM hmo_registries WHERE city = 'swindon'")
            avg_quality = cursor.fetchone()[0] or 0
            
            conn.close()
            
            geocoding_success_rate = (geocoded_records / total_records * 100) if total_records > 0 else 0
            
            return {
                'total_records': total_records,
                'geocoded_records': geocoded_records,
                'geocoding_success_rate': round(geocoding_success_rate, 1),
                'active_licences': active_licences,
                'expired_licences': 0,
                'unknown_status': 0,
                'average_data_quality': round(avg_quality, 2),
                'last_updated': None
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_hmo_data(self, force_refresh: bool = False, enable_geocoding: bool = True) -> List[Dict]:
        """Get Swindon HMO data in the unified format"""
        try:
            # Read from CSV file for now
            import pandas as pd
            df = pd.read_csv('swindon_hmo_processed.csv')
            
            data = []
            for _, row in df.iterrows():
                if pd.notna(row.get('latitude')) and pd.notna(row.get('longitude')):
                    record = {
                        'id': row['case_number'],
                        'case_number': row['case_number'],
                        'source': 'swindon_excel',
                        'city': 'swindon',
                        'address': row['cleaned_address'],
                        'postcode': row.get('postcode'),
                        'latitude': float(row['latitude']),
                        'longitude': float(row['longitude']),
                        'geocoded': bool(row['geocoded']),
                        'total_occupants': None,  # Not available in Swindon data
                        'total_units': None,      # Not available in Swindon data
                        'licence_status': 'active',  # Default for now
                        'licence_start_date': None,
                        'licence_expiry_date': None,
                        'data_quality_score': float(row.get('quality_score', 0.0)),
                        'processing_notes': f'Imported from Swindon Excel',
                        'last_updated': datetime.now().isoformat(),
                        'data_source_url': None
                    }
                    data.append(record)
            
            return data
            
        except FileNotFoundError:
            logger.error("Swindon HMO data file not found")
            return []
        except Exception as e:
            logger.error(f"Error reading Swindon HMO data: {e}")
            return []
    
        
# Add this function to your hmo_registry/cities/swindon.py file

def add_swindon_hmo_endpoint(app):
    """Add Swindon HMO endpoints to FastAPI app"""
    from fastapi import APIRouter, HTTPException
    
    swindon_router = APIRouter(prefix="/api/swindon-hmo", tags=["Swindon HMO"])
    swindon_data = SwindonHMOMapData()
    
    @swindon_router.get("/map-data")
    async def get_swindon_hmo_map_data(force_refresh: bool = False, enable_geocoding: bool = True):
        """Get Swindon HMO data for map display"""
        try:
            # For now, return data from the CSV file
            # Later you can integrate with database
            import pandas as pd
            
            # Try to read the processed CSV file
            try:
                df = pd.read_csv('swindon_hmo_processed.csv')
                data = []
                
                for _, row in df.iterrows():
                    if pd.notna(row.get('latitude')) and pd.notna(row.get('longitude')):
                        record = {
                            'id': row['case_number'],
                            'case_number': row['case_number'],
                            'address': row['cleaned_address'],
                            'raw_address': row['raw_address'],
                            'postcode': row.get('postcode'),
                            'licence_holder': row['licence_holder'],
                            'latitude': float(row['latitude']),
                            'longitude': float(row['longitude']),
                            'geocoded': bool(row['geocoded']),
                            'city': 'swindon',
                            'licence_status': 'active',  # Default for now
                            'data_quality_score': row.get('quality_score', 0.0)
                        }
                        data.append(record)
                
                return {
                    'success': True,
                    'data': data,
                    'count': len(data),
                    'source': 'swindon_csv'
                }
                
            except FileNotFoundError:
                return {
                    'success': False,
                    'error': 'Swindon HMO data file not found. Please run the Swindon data processing script first.',
                    'data': [],
                    'count': 0
                }
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching Swindon HMO data: {str(e)}")
    
    @swindon_router.get("/statistics")
    async def get_swindon_hmo_statistics():
        """Get Swindon HMO statistics"""
        try:
            import pandas as pd
            
            try:
                df = pd.read_csv('swindon_hmo_processed.csv')
                
                total_records = len(df)
                geocoded_records = df['geocoded'].sum()
                geocoding_rate = (geocoded_records / total_records * 100) if total_records > 0 else 0
                avg_quality = df['quality_score'].mean() if 'quality_score' in df.columns else 0
                
                stats = {
                    'total_records': total_records,
                    'geocoded_records': int(geocoded_records),
                    'geocoding_success_rate': round(geocoding_rate, 1),
                    'average_data_quality': round(avg_quality, 2),
                    'active_licences': total_records,  # Assume all active for now
                    'expired_licences': 0,
                    'data_source': 'Swindon Borough Council Excel',
                    'last_updated': 'Manual upload'
                }
                
                return stats
                
            except FileNotFoundError:
                return {
                    'error': 'Swindon HMO data file not found',
                    'total_records': 0,
                    'geocoded_records': 0,
                    'geocoding_success_rate': 0,
                    'average_data_quality': 0
                }
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error getting Swindon statistics: {str(e)}")
    
    @swindon_router.post("/refresh")
    async def refresh_swindon_hmo_data():
        """Refresh Swindon HMO data (placeholder for future database integration)"""
        try:
            # For now, just return current data count
            import pandas as pd
            
            try:
                df = pd.read_csv('swindon_hmo_processed.csv')
                count = len(df)
                
                return {
                    'success': True,
                    'message': f'Swindon data refreshed - {count} records available',
                    'count': count,
                    'note': 'Currently using CSV data. Database integration coming soon.'
                }
                
            except FileNotFoundError:
                return {
                    'success': False,
                    'message': 'Swindon data file not found',
                    'count': 0
                }
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error refreshing Swindon data: {str(e)}")
    
    # Add the router to the app
    app.include_router(swindon_router)

swindon_hmo_data = SwindonHMOMapData()


