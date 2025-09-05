# oxford_map_only.py
"""
Simple Oxford HMO data fetcher for map display only
No database integration, no address matching - just pure map data
"""

import requests
import pandas as pd
from io import StringIO
from typing import List, Dict, Optional, Tuple
import logging
import re
from datetime import datetime

# Try to import the new geocoding functions
try:
    from modules.coordinates import geocode_address, extract_postcode_from_address
    GEOCODING_AVAILABLE = True
    print("✅ Geocoding functions imported successfully")
except ImportError:
    try:
        from coordinates import geocode_address, extract_postcode_from_address
        GEOCODING_AVAILABLE = True
        print("✅ Geocoding functions imported from coordinates module")
    except ImportError:
        print("⚠️ Geocoding functions not found - will use fallback methods")
        GEOCODING_AVAILABLE = False
        
        def geocode_address(address):
            return None
        
        def extract_postcode_from_address(address):
            # Simple regex-based postcode extraction as fallback
            import re
            postcode_pattern = r'([A-Z]{1,2}[0-9R][0-9A-Z]? ?[0-9][A-Z]{2})'
            match = re.search(postcode_pattern, address.upper())
            return match.group(1) if match else None

logger = logging.getLogger(__name__)

class OxfordHMOMapData:
    """Fetch Oxford HMO data for map display only"""
    
    CSV_URL = "https://oxopendata.github.io/register-of-houses-in-multiple-occupation/data/hmo-simplified-register.csv"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'HMO-Analyser/1.0 (Property Analysis Tool)'
        })
        self._cached_data = None
        self._cache_timestamp = None
        self._cache_duration = 3600  # 1 hour cache
    
    def get_oxford_hmo_data(self, force_refresh: bool = False, enable_geocoding: bool = True) -> List[Dict]:
        """Get processed Oxford HMO data for map display"""
        
        # Check cache first
        if (not force_refresh and self._cached_data and self._cache_timestamp and 
            (datetime.now() - self._cache_timestamp).seconds < self._cache_duration):
            logger.info("Using cached Oxford HMO data")
            return self._cached_data
        
        try:
            logger.info("Fetching fresh Oxford HMO data...")
            
            # Fetch CSV data
            response = self.session.get(self.CSV_URL, timeout=30)
            response.raise_for_status()
            
            # Parse CSV
            df = pd.read_csv(StringIO(response.text))
            
            # Clean data
            df = df.dropna(subset=['Location'])  # Must have address
            df = df.drop_duplicates(subset=['Case Number'])  # Remove duplicates
            
            logger.info(f"Fetched {len(df)} Oxford HMO records")
            
            # Process each record for map display
            processed_data = []
            geocoded_count = 0
            
            for _, record in df.iterrows():
                processed_record = self._process_record_for_map(record.to_dict(), enable_geocoding)
                if processed_record:
                    processed_data.append(processed_record)
                    if processed_record.get('geocoded'):
                        geocoded_count += 1
            
            logger.info(f"Processed {len(processed_data)} records ({geocoded_count} geocoded)")
            
            # Cache the results
            self._cached_data = processed_data
            self._cache_timestamp = datetime.now()
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Error fetching Oxford HMO data: {e}")
            return self._cached_data if self._cached_data else []
    
    def _process_record_for_map(self, record: Dict, enable_geocoding: bool = True) -> Optional[Dict]:
        """Process a single Oxford HMO record for map display"""
        try:
            # Extract basic information
            case_number = str(record.get('Case Number', '')).strip()
            location = str(record.get('Location', '')).strip()
            
            if not case_number or not location:
                return None
            
            # Parse numeric fields safely
            total_occupants = self._safe_int(record.get('Total Number Occupants'))
            total_units = self._safe_int(record.get('Total Number Units'))
            
            # Parse dates safely
            licence_start = self._safe_date(record.get('Licence Commenced'))
            licence_expires = self._safe_date(record.get('Licence Expires'))
            
            # Determine licence status
            licence_status = 'active'
            if licence_expires and licence_expires < datetime.now().date():
                licence_status = 'expired'
            elif not licence_expires:
                licence_status = 'unknown'
            
            # Try to geocode the address using the new separate function
            coords = None
            if enable_geocoding and GEOCODING_AVAILABLE:
                try:
                    coords = geocode_address(location)
                    if coords:
                        print(f"📍 Geocoded: {location} -> {coords}")
                except Exception as e:
                    print(f"🔍 Geocoding error for {location}: {e}")
                    coords = None
            
            # Extract postcode
            postcode = extract_postcode_from_address(location)
            
            # Create map-ready record
            map_record = {
                # Identification
                'id': f"oxford_hmo_{case_number}",
                'case_number': case_number,
                'source': 'oxford_council',
                
                # Location
                'address': location,
                'postcode': postcode,
                'latitude': coords[0] if coords else None,
                'longitude': coords[1] if coords else None,
                'geocoded': coords is not None,
                
                # Property details
                'total_occupants': total_occupants,
                'total_units': total_units,
                
                # Licence information
                'licence_status': licence_status,
                'licence_start_date': licence_start.isoformat() if licence_start else None,
                'licence_expiry_date': licence_expires.isoformat() if licence_expires else None,
                
                # Data quality
                'data_quality_score': self._calculate_confidence(record, coords, postcode),
                'processing_notes': self._generate_processing_notes(record, coords, postcode),
                
                # Metadata
                'last_updated': datetime.now().isoformat(),
                'data_source_url': self.CSV_URL
            }
            
            return map_record
            
        except Exception as e:
            logger.error(f"Error processing Oxford record {record}: {e}")
            return None
    
    def _safe_int(self, value) -> Optional[int]:
        """Safely convert value to int"""
        if pd.isna(value) or value == '':
            return None
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return None
    
    def _safe_date(self, value):
        """Safely convert value to date"""
        if pd.isna(value) or value == '':
            return None
        try:
            return pd.to_datetime(value, dayfirst=True).date()
        except (ValueError, TypeError):
            return None
    
    def _calculate_confidence(self, record: Dict, coords: Optional[Tuple], postcode: Optional[str]) -> float:
        """Calculate confidence score for Oxford record"""
        score = 0.0
        
        # Has coordinates
        if coords:
            score += 0.4
        
        # Has postcode
        if postcode:
            score += 0.3
        
        # Has occupancy info
        if self._safe_int(record.get('Total Number Occupants')):
            score += 0.2
        
        # Has unit info
        if self._safe_int(record.get('Total Number Units')):
            score += 0.1
        
        # Has valid dates
        if self._safe_date(record.get('Licence Expires')):
            score += 0.1
        
        return min(score, 1.0)
    
    def _generate_processing_notes(self, record: Dict, coords: Optional[Tuple], postcode: Optional[str]) -> str:
        """Generate processing notes"""
        notes = []
        
        if not coords:
            notes.append("No coordinates found")
        if not postcode:
            notes.append("No postcode extracted")
        if not self._safe_int(record.get('Total Number Occupants')):
            notes.append("Missing occupant count")
        
        return "; ".join(notes) if notes else "Processed successfully"
    
    def get_statistics(self) -> Dict:
        """Get statistics about the Oxford HMO data"""
        data = self.get_oxford_hmo_data()
        
        if not data:
            return {'error': 'No data available'}
        
        # Calculate statistics
        total_records = len(data)
        geocoded_records = sum(1 for record in data if record.get('geocoded'))
        active_licences = sum(1 for record in data if record.get('licence_status') == 'active')
        expired_licences = sum(1 for record in data if record.get('licence_status') == 'expired')
        
        # Calculate average data quality
        quality_scores = [record.get('data_quality_score', 0) for record in data]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        return {
            'total_records': total_records,
            'geocoded_records': geocoded_records,
            'geocoding_success_rate': round((geocoded_records / total_records * 100), 1) if total_records > 0 else 0,
            'active_licences': active_licences,
            'expired_licences': expired_licences,
            'unknown_status': len(data) - active_licences - expired_licences,
            'average_data_quality': round(avg_quality, 2),
            'last_updated': self._cache_timestamp.isoformat() if self._cache_timestamp else None
        }


# =============================================================================
# API ENDPOINTS FOR MAP-ONLY INTEGRATION
# =============================================================================

def add_oxford_map_endpoints(app):
    """Add Oxford HMO map endpoints (no database required)"""
    
    oxford_data = OxfordHMOMapData()
    
    @app.get("/api/oxford-hmo/map-data")
    async def get_oxford_hmo_map_data(force_refresh: bool = False, enable_geocoding: bool = True):
        """Get Oxford HMO data for map display"""
        try:
            data = oxford_data.get_oxford_hmo_data(force_refresh=force_refresh, enable_geocoding=enable_geocoding)
            return {
                'success': True,
                'data': data,
                'count': len(data)
            }
        except Exception as e:
            from fastapi import HTTPException
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/oxford-hmo/statistics")
    async def get_oxford_hmo_statistics():
        """Get Oxford HMO statistics"""
        try:
            stats = oxford_data.get_statistics()
            return stats
        except Exception as e:
            from fastapi import HTTPException
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/oxford-hmo/refresh")
    async def refresh_oxford_hmo_data():
        """Refresh Oxford HMO data cache"""
        try:
            data = oxford_data.get_oxford_hmo_data(force_refresh=True)
            return {
                'success': True,
                'message': f'Refreshed {len(data)} Oxford HMO records',
                'count': len(data)
            }
        except Exception as e:
            from fastapi import HTTPException
            raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# COMMAND LINE INTERFACE
# =============================================================================

def main():
    """Main function for command line usage"""
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'test':
            # Test the Oxford HMO data fetching
            print("🧪 Testing Oxford HMO map data...")
            
            oxford_data = OxfordHMOMapData()
            
            # Test without geocoding first
            print("\n--- Testing WITHOUT geocoding ---")
            data_no_geocoding = oxford_data.get_oxford_hmo_data(enable_geocoding=False)
            
            if not data_no_geocoding:
                print("❌ No data fetched")
                return
            
            print(f"✅ Fetched {len(data_no_geocoding)} records without geocoding")
            
            # Test with geocoding (just first few records)
            print("\n--- Testing WITH geocoding (first 5 records) ---")
            oxford_data._cached_data = None  # Clear cache
            data_with_geocoding = oxford_data.get_oxford_hmo_data(enable_geocoding=True)
            
            # Print statistics
            print("\n📊 Final Statistics:")
            oxford_data._process_record_for_map = original_process_method  # Restore original method
            stats = {
                'total_records_available': len(data_no_geocoding),
                'test_records_processed': processed_count,
                'test_geocoding_success': sum(1 for r in data_with_geocoding if r.get('geocoded')),
                'estimated_full_geocoding_time': f"{len(data_no_geocoding) * 0.2 / 60:.1f} minutes"
            }
            
            for key, value in stats.items():
                print(f"  {key}: {value}")
            
            # Print sample records
            print("\n📋 Sample geocoded records:")
            geocoded_records = [r for r in data_with_geocoding if r.get('geocoded')]
            for i, record in enumerate(geocoded_records[:3], 1):
                print(f"  {i}. {record['case_number']}: {record['address']}")
                print(f"     Coordinates: {record['latitude']}, {record['longitude']}")
                print(f"     Status: {record['licence_status']}, Quality: {record['data_quality_score']:.2f}")
            
            print("\n✅ Oxford HMO map data test completed")
            print("💡 To process all records with geocoding, use the API endpoints")
            
        elif command == 'sample':
            # Process a small sample with geocoding
            sample_size = int(sys.argv[2]) if len(sys.argv) > 2 else 50
            print(f"🧪 Processing {sample_size} Oxford HMO records with geocoding...")
            
            oxford_data = OxfordHMOMapData()
            
            # Limit processing to sample size
            original_process_method = oxford_data._process_record_for_map
            processed_count = 0
            
            def limited_process_method(record, enable_geocoding=True):
                nonlocal processed_count
                if processed_count >= sample_size:
                    return None
                result = original_process_method(record, enable_geocoding)
                if result:
                    processed_count += 1
                    if processed_count % 10 == 0:
                        print(f"📍 Processed {processed_count}/{sample_size} records...")
                return result
            
            oxford_data._process_record_for_map = limited_process_method
            data = oxford_data.get_oxford_hmo_data(enable_geocoding=True)
            
            geocoded_count = sum(1 for r in data if r.get('geocoded'))
            success_rate = (geocoded_count / len(data) * 100) if data else 0
            
            print(f"\n✅ Sample processing complete:")
            print(f"  - Processed: {len(data)} records")
            print(f"  - Geocoded: {geocoded_count} records")
            print(f"  - Success rate: {success_rate:.1f}%")
            
        elif command == 'generate-frontend':
            print("🎨 Generating frontend integration code...")
            # This would generate JavaScript/React code for frontend integration
            print("Frontend code generation not implemented yet")
            
        else:
            print(f"Unknown command: {command}")
            print("Available commands: test, sample [number], generate-frontend")
    else:
        print("Oxford HMO Map Data Fetcher")
        print("Usage: python3 oxford_map_only.py [command]")
        print("Commands:")
        print("  test              - Test data fetching (10 records with geocoding)")
        print("  sample [number]   - Process a sample with geocoding (default: 50)")
        print("  generate-frontend - Generate frontend integration code")


if __name__ == "__main__":
    main()