# hmo_registry/cities/oxford.py
"""
Oxford HMO Registry Data Source
Fetches and processes Oxford City Council HMO register data with license renewal analysis
"""

import requests
import pandas as pd
from io import StringIO
from typing import List, Dict, Optional, Tuple
import logging
import re
from datetime import datetime

from .base_city import BaseHMODataSource

# Try to import geocoding functions
try:
    from modules.coordinates import geocode_address, extract_postcode_from_address
    GEOCODING_AVAILABLE = True
    print("✅ Geocoding functions imported successfully")
except ImportError:
    print("⚠️ Geocoding functions not found - using fallback methods")
    GEOCODING_AVAILABLE = False
    
    def geocode_address(address):
        return None
    
    def extract_postcode_from_address(address):
        # Simple regex-based postcode extraction as fallback
        import re
        postcode_pattern = r'([A-Z]{1,2}[0-9R][0-9A-Z]?\s?[0-9][A-Z]{2})'  # FIXED - added the missing part
        match = re.search(postcode_pattern, address.upper())
        return match.group(1) if match else None

logger = logging.getLogger(__name__)

class OxfordHMOMapData(BaseHMODataSource):
    """Oxford HMO Registry data source with license renewal analysis"""
    
    CSV_URL = "https://oxopendata.github.io/register-of-houses-in-multiple-occupation/data/hmo-simplified-register.csv"
    
    def __init__(self):
        super().__init__("oxford", cache_duration=3600)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'HMO-Analyser/1.0 (Property Analysis Tool)'
        })
        self._use_renewal_analysis = True  # Flag to use new renewal system
        self._renewal_analyzer = None
    
    def get_renewal_analyzer(self):
        """Get or create the renewal analyzer"""
        if self._renewal_analyzer is None:
            try:
                from .oxford_renewal import OxfordLicenseRenewalAnalyzer
                self._renewal_analyzer = OxfordLicenseRenewalAnalyzer()
                logger.info("✅ Using Oxford License Renewal Analyzer")
            except ImportError:
                logger.warning("⚠️ Renewal analyzer not available, falling back to CSV data")
                self._use_renewal_analysis = False
        
        return self._renewal_analyzer
    
    def get_hmo_data(self, force_refresh: bool = False, enable_geocoding: bool = True) -> List[Dict]:
        """Get Oxford HMO data - uses renewal analysis if available, otherwise falls back to CSV"""
        
        # Try to use the renewal analysis system first
        if self._use_renewal_analysis:
            analyzer = self.get_renewal_analyzer()
            if analyzer:
                try:
                    logger.info("🔄 Using license renewal analysis for Oxford data")
                    data = analyzer.get_hmo_data(force_refresh, enable_geocoding)
                    
                    if data:
                        logger.info(f"✅ Retrieved {len(data)} records via renewal analysis")
                        return data
                    else:
                        logger.warning("⚠️ No data from renewal analysis, falling back to CSV")
                
                except Exception as e:
                    logger.error(f"❌ Renewal analysis failed: {e}")
                    logger.info("📄 Falling back to CSV data source")
        
        # Fallback to original CSV method
        logger.info("📄 Using original CSV data source")
        return self._get_csv_data(force_refresh, enable_geocoding)
    
    def get_statistics(self) -> Dict:
        """Get statistics - uses renewal analysis if available"""
        
        if self._use_renewal_analysis:
            analyzer = self.get_renewal_analyzer()
            if analyzer:
                try:
                    stats = analyzer.get_statistics()
                    if stats.get('total_records', 0) > 0:
                        return stats
                except Exception as e:
                    logger.error(f"Error getting renewal statistics: {e}")
        
        # Fallback to CSV statistics
        return self._get_csv_statistics()
    
    def get_renewal_analysis(self) -> Dict:
        """Get detailed renewal analysis (new method)"""
        analyzer = self.get_renewal_analyzer()
        if not analyzer:
            return {'error': 'Renewal analyzer not available'}
        
        try:
            return analyzer.analyze_license_renewals()
        except Exception as e:
            logger.error(f"Error running renewal analysis: {e}")
            return {'error': str(e)}
    
    def _get_csv_data(self, force_refresh: bool = False, enable_geocoding: bool = True) -> List[Dict]:
        """Original CSV data fetching method (fallback)"""
        try:
            # Check cache first
            if not force_refresh and hasattr(self, '_cached_csv_data') and self._cached_csv_data:
                cache_age = datetime.now() - self._cache_timestamp
                if cache_age.total_seconds() < self.cache_duration:
                    logger.info(f"Using cached CSV data ({len(self._cached_csv_data)} records)")
                    return self._cached_csv_data
            
            # Fetch raw data
            raw_data = self.fetch_raw_data()
            if not raw_data:
                return []
            
            # Process records
            processed_data = []
            for record in raw_data:
                processed_record = self.process_record(record, enable_geocoding)
                if processed_record:
                    processed_data.append(processed_record)
            
            # Cache results
            self._cached_csv_data = processed_data
            self._cache_timestamp = datetime.now()
            
            logger.info(f"Processed {len(processed_data)} Oxford records from CSV")
            return processed_data
            
        except Exception as e:
            logger.error(f"Error getting CSV data: {e}")
            return []
    
    def _get_csv_statistics(self) -> Dict:
        """Get statistics from CSV data (fallback)"""
        try:
            data = self._get_csv_data(enable_geocoding=False)
            
            if not data:
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
            
            total_records = len(data)
            geocoded_records = sum(1 for r in data if r.get('geocoded'))
            active_licences = sum(1 for r in data if r.get('licence_status') == 'active')
            expired_licences = sum(1 for r in data if r.get('licence_status') == 'expired')
            unknown_status = sum(1 for r in data if r.get('licence_status') == 'unknown')
            
            qualities = [r.get('data_quality_score', 0) for r in data if r.get('data_quality_score')]
            avg_quality = sum(qualities) / len(qualities) if qualities else 0
            
            return {
                'total_records': total_records,
                'geocoded_records': geocoded_records,
                'geocoding_success_rate': round((geocoded_records / total_records * 100), 1) if total_records > 0 else 0,
                'active_licences': active_licences,
                'expired_licences': expired_licences,
                'unknown_status': unknown_status,
                'average_data_quality': round(avg_quality, 2),
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting CSV statistics: {e}")
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

    def fetch_raw_data(self) -> List[Dict]:
        """Fetch raw data from Oxford's CSV"""
        try:
            # Fetch CSV data
            response = self.session.get(self.CSV_URL, timeout=30)
            response.raise_for_status()
            
            # Parse CSV
            df = pd.read_csv(StringIO(response.text))
            
            # Clean data
            df = df.dropna(subset=['Location'])  # Must have address
            df = df.drop_duplicates(subset=['Case Number'])  # Remove duplicates
            
            logger.info(f"Fetched {len(df)} Oxford HMO records from CSV")
            
            # Convert to list of dictionaries
            return df.to_dict('records')
            
        except Exception as e:
            logger.error(f"Error fetching Oxford raw data: {e}")
            return []
    
    def process_record(self, record: Dict, enable_geocoding: bool = True) -> Optional[Dict]:
        """Process a single Oxford HMO record"""
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
            
            # Try to geocode the address
            coords = None
            if enable_geocoding and GEOCODING_AVAILABLE:
                try:
                    coords = geocode_address(location)
                    if coords:
                        logger.debug(f"📍 Geocoded: {location} -> {coords}")
                except Exception as e:
                    logger.debug(f"🔍 Geocoding error for {location}: {e}")
                    coords = None
            
            # Extract postcode
            postcode = extract_postcode_from_address(location)
            
            # Create standardized record
            processed_record = {
                # Identification
                'id': f"oxford_hmo_{case_number}",
                'case_number': case_number,
                'source': 'oxford_council_csv',
                'city': 'oxford',
                
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
            
            return processed_record
            
        except Exception as e:
            logger.error(f"Error processing Oxford record {record}: {e}")
            return None


# Backward compatibility - keep the old function names
def get_oxford_hmo_data(force_refresh: bool = False, enable_geocoding: bool = True) -> List[Dict]:
    """Legacy function for backward compatibility"""
    oxford_data = OxfordHMOMapData()
    return oxford_data.get_hmo_data(force_refresh, enable_geocoding)

def get_oxford_statistics() -> Dict:
    """Legacy function for backward compatibility"""
    oxford_data = OxfordHMOMapData()
    return oxford_data.get_statistics()


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
            
            # Test renewal analysis first
            print("\n--- Testing Renewal Analysis ---")
            try:
                analysis = oxford_data.get_renewal_analysis()
                if 'error' not in analysis:
                    print(f"✅ Renewal analysis successful!")
                    print(f"  📊 Existing records: {analysis.get('existing_records', 0)}")
                    print(f"  📄 New Excel records: {analysis.get('new_excel_records', 0)}")
                    print(f"  🔄 Renewed licenses: {analysis.get('renewed_licenses', 0)}")
                    print(f"  ❌ Still expired: {analysis.get('still_expired', 0)}")
                    print(f"  🆕 New properties: {analysis.get('new_properties', 0)}")
                    print(f"  📍 Geocoded new: {analysis.get('geocoded_new_properties', 0)}")
                    print(f"  📈 Total final records: {analysis.get('total_final_records', 0)}")
                else:
                    print(f"❌ Renewal analysis failed: {analysis['error']}")
            except Exception as e:
                print(f"❌ Renewal analysis error: {e}")
            
            # Test data retrieval
            print("\n--- Testing Data Retrieval ---")
            data = oxford_data.get_hmo_data(enable_geocoding=False)
            
            if not data:
                print("❌ No data fetched")
                return
            
            print(f"✅ Fetched {len(data)} records")
            
            # Print statistics
            print("\n--- Testing Statistics ---")
            stats = oxford_data.get_statistics()
            
            print(f"📊 Statistics:")
            for key, value in stats.items():
                if key != 'last_updated':
                    print(f"  {key}: {value}")
            
            # Print sample records
            print("\n--- Sample Records ---")
            geocoded_records = [r for r in data if r.get('geocoded')]
            for i, record in enumerate(geocoded_records[:3], 1):
                print(f"  {i}. {record.get('case_number', 'N/A')}: {record.get('address', 'N/A')[:50]}...")
                print(f"     Status: {record.get('licence_status', 'N/A')}")
                if record.get('geocoded'):
                    print(f"     Coordinates: {record.get('latitude')}, {record.get('longitude')}")
            
            print("\n✅ Oxford HMO data test completed")
            
        elif command == 'analyze':
            # Run detailed renewal analysis
            print("🔍 Running detailed Oxford license renewal analysis...")
            
            oxford_data = OxfordHMOMapData()
            analysis = oxford_data.get_renewal_analysis()
            
            if 'error' in analysis:
                print(f"❌ Analysis failed: {analysis['error']}")
                return
            
            print(f"\n📊 Renewal Analysis Results:")
            print(f"  📄 Existing database records: {analysis.get('existing_records', 0):,}")
            print(f"  📋 New Excel records: {analysis.get('new_excel_records', 0):,}")
            print(f"  ✅ Exact case matches: {analysis.get('exact_case_matches', 0):,}")
            print(f"  🏠 Address matches: {analysis.get('address_matches', 0):,}")
            print(f"  🔄 Renewed licenses: {analysis.get('renewed_licenses', 0):,}")
            print(f"  ❌ Still expired: {analysis.get('still_expired', 0):,}")
            print(f"  🆕 New properties: {analysis.get('new_properties', 0):,}")
            print(f"  📍 Geocoded new properties: {analysis.get('geocoded_new_properties', 0):,}")
            print(f"  📈 Total final records: {analysis.get('total_final_records', 0):,}")
            
            # Show sample renewed licenses
            renewed_sample = analysis.get('sample_renewed', [])
            if renewed_sample:
                print(f"\n🔄 Sample Renewed Licenses:")
                for i, record in enumerate(renewed_sample, 1):
                    print(f"  {i}. {record.get('case_number', 'N/A')}: {record.get('address', 'N/A')[:50]}...")
                    print(f"     Expires: {record.get('licence_expiry_date', 'N/A')}")
            
            # Show sample new properties
            new_sample = analysis.get('sample_new', [])
            if new_sample:
                print(f"\n🆕 Sample New Properties:")
                for i, record in enumerate(new_sample, 1):
                    print(f"  {i}. {record.get('case_number', 'N/A')}: {record.get('address', 'N/A')[:50]}...")
                    print(f"     Geocoded: {record.get('geocoded', False)}")
            
            print(f"\n✅ Renewal analysis completed!")
            
        else:
            print(f"Unknown command: {command}")
            print("Available commands: test, analyze")
    else:
        print("Oxford HMO Map Data with License Renewal Analysis")
        print("Usage: python3 -m hmo_registry.cities.oxford [command]")
        print("Commands:")
        print("  test     - Test data fetching and renewal analysis")
        print("  analyze  - Run detailed license renewal analysis")


if __name__ == "__main__":
    main()