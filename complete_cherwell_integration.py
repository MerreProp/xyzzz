#!/usr/bin/env python3
"""
Complete Cherwell HMO Integration - Capture ALL Records
Processes records with missing case numbers by generating them
"""

import sys
import os
from datetime import datetime
import pandas as pd
import numpy as np
import hashlib

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, test_connection_with_retry
from hmo_registry.database_models import HMORegistry, check_hmo_table_exists

def safe_int_convert(value, default=None):
    """Safely convert value to integer, handling NaN and None"""
    if pd.isna(value) or value is None or str(value).strip() in ['', 'nan', 'None']:
        return default
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default

def safe_str_convert(value, default=''):
    """Safely convert value to string, handling NaN"""
    if pd.isna(value) or value is None:
        return default
    return str(value).strip()

def safe_date_convert(value):
    """Safely convert value to date, handling various formats"""
    if pd.isna(value) or value is None or str(value).strip() in ['', 'nan', 'None']:
        return None
    try:
        if isinstance(value, str):
            # Try different date formats
            for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']:
                try:
                    return datetime.strptime(value, fmt).date()
                except ValueError:
                    continue
        return None
    except Exception:
        return None

def generate_case_number(address, location, row_index):
    """Generate a case number for records missing one"""
    if not address:
        return f"CHERWELL_{location.upper()}_{row_index:03d}"
    
    # Create hash from address for consistency
    hash_object = hashlib.md5(address.encode())
    hash_hex = hash_object.hexdigest()[:6].upper()
    
    return f"CHERWELL_{location.upper()}_{hash_hex}"

class CompleteCherswellIntegration:
    """Complete Cherwell integration that captures ALL records"""
    
    def __init__(self):
        self.processed_count = 0
        self.error_count = 0
        self.generated_case_numbers = 0
        
    def extract_postcode(self, address):
        """Extract UK postcode from address"""
        import re
        if not address:
            return None
        
        postcode_pattern = r'([A-Z]{1,2}[0-9R][0-9A-Z]? ?[0-9][A-Z]{2})'
        match = re.search(postcode_pattern, address.upper())
        return match.group(1) if match else None
    
    def geocode_address(self, address):
        """Geocode address using available geocoding modules"""
        if not address or str(address).strip() in ['', 'nan', 'None']:
            return None
            
        try:
            # Try improved geocoding first
            try:
                from hmo_registry.utils.improved_geocoding import geocode_address as improved_geocode
                coords = improved_geocode(address)
                if coords and len(coords) == 2:
                    print(f"✅ Geocoded: {address[:50]}...")
                    return coords
            except ImportError:
                pass
            
            # Fallback to basic coordinates module
            try:
                from coordinates import geocode_address as basic_geocode
                coords = basic_geocode(address)
                if coords and len(coords) == 2:
                    print(f"✅ Geocoded: {address[:50]}...")
                    return coords
            except ImportError:
                pass
            
            return None
            
        except Exception as e:
            print(f"❌ Geocoding error for {address[:30]}: {e}")
            return None
    
    def process_csv_location(self, csv_path, location_name):
        """Process ALL records in a location-specific CSV file"""
        try:
            df = pd.read_csv(csv_path)
            print(f"📊 Found {len(df)} records in CSV")
            
            processed_records = []
            
            for idx, row in df.iterrows():
                try:
                    # Extract address - this is our primary requirement
                    raw_address = safe_str_convert(row.get('raw_address', ''))
                    if not raw_address:
                        print(f"⏭️  Skipping row {idx}: No address")
                        continue
                    
                    # Get or generate case number
                    case_number = safe_str_convert(row.get('case_number'))
                    if not case_number:
                        case_number = generate_case_number(raw_address, location_name, idx)
                        self.generated_case_numbers += 1
                        print(f"🔧 Generated case number: {case_number}")
                    
                    # Use correct database field names
                    record_data = {
                        # Core HMORegistry fields
                        'city': f'cherwell_{location_name}',
                        'source': 'cherwell_district_council',
                        'case_number': case_number,
                        'data_source_url': 'https://www.cherwell.gov.uk/',
                        'raw_address': raw_address,
                        'postcode': safe_str_convert(row.get('postcode')),
                        
                        # Geocoding fields (will be set below)
                        'latitude': None,
                        'longitude': None,
                        'geocoded': False,
                        'geocoding_source': None,
                        
                        # Property details
                        'total_occupants': safe_int_convert(row.get('max_occupancy')),
                        'total_units': safe_int_convert(row.get('self_contained_units')),
                        
                        # License information  
                        'licence_status': 'active',  # Default, will be calculated
                        'licence_start_date': safe_date_convert(row.get('start_date')),
                        'licence_expiry_date': safe_date_convert(row.get('expiry_date')),
                        
                        # Data quality and processing
                        'data_quality_score': 0.5,  # Base score
                        'processing_notes': f'Complete integration - case_number {"generated" if not safe_str_convert(row.get("case_number")) else "original"}',
                        'source_last_updated': datetime.utcnow(),
                        'created_at': datetime.utcnow(),
                        'updated_at': datetime.utcnow()
                    }
                    
                    # Determine licence status based on expiry date
                    if record_data['licence_expiry_date']:
                        if record_data['licence_expiry_date'] < datetime.now().date():
                            record_data['licence_status'] = 'expired'
                        else:
                            record_data['licence_status'] = 'active'
                    else:
                        record_data['licence_status'] = 'unknown'
                    
                    # Geocode the address
                    coords = self.geocode_address(raw_address)
                    if coords:
                        record_data['latitude'] = coords[0]
                        record_data['longitude'] = coords[1]
                        record_data['geocoded'] = True
                        record_data['geocoding_source'] = 'improved_geocoding'
                        record_data['data_quality_score'] += 0.3  # Higher score for geocoded
                    
                    # Additional quality score factors
                    if record_data['postcode']:
                        record_data['data_quality_score'] += 0.1
                    if record_data['total_occupants']:
                        record_data['data_quality_score'] += 0.1
                    
                    record_data['data_quality_score'] = min(record_data['data_quality_score'], 1.0)
                    
                    processed_records.append(record_data)
                    self.processed_count += 1
                    
                except Exception as e:
                    print(f"❌ Error processing row {idx}: {e}")
                    self.error_count += 1
                    continue
            
            return processed_records
            
        except Exception as e:
            print(f"❌ Error reading CSV {csv_path}: {e}")
            return []
    
    def get_hmo_data(self, location_name, force_refresh=False):
        """Get HMO data for a specific location"""
        csv_path = f"data/cherwell/processed/cherwell_{location_name}_hmo.csv"
        
        if not os.path.exists(csv_path):
            print(f"⚠️  CSV file not found: {csv_path}")
            return []
        
        return self.process_csv_location(csv_path, location_name)

def main():
    """Main integration function - process ALL records"""
    print("🏠 COMPLETE CHERWELL HMO INTEGRATION")
    print("=" * 50)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test database connection first
    print("\n🔌 Testing database connection...")
    success, engine = test_connection_with_retry(max_retries=2, delay=5)
    
    if not success:
        print("❌ Cannot proceed without database connection")
        return False
    
    print("✅ Database connection successful")
    
    # Check if HMO registries table exists
    table_exists = check_hmo_table_exists()
    print(f"✅ HMO registries table exists: {table_exists}")
    
    if not table_exists:
        print("❌ HMO registries table not found. Please create it first.")
        return False
    
    # Initialize integration
    integration = CompleteCherswellIntegration()
    
    # Process each location
    locations = ['banbury', 'bicester', 'kidlington']
    total_processed = 0
    total_geocoded = 0
    
    db = SessionLocal()
    try:
        # Check existing records
        existing_count = db.query(HMORegistry).filter(
            HMORegistry.city.like('cherwell_%')
        ).count()
        print(f"📊 Existing Cherwell records: {existing_count}")
        
        for location in locations:
            print(f"\n📍 Processing {location} (ALL RECORDS)...")
            
            # Get HMO data for this location
            hmo_data = integration.get_hmo_data(location, force_refresh=True)
            
            if not hmo_data:
                print(f"⚠️  No data found for {location}")
                continue
            
            # Process each record
            location_processed = 0
            location_geocoded = 0
            location_skipped = 0
            
            for record_data in hmo_data:
                try:
                    # Check if record already exists (by case_number AND address to handle generated case numbers)
                    existing = db.query(HMORegistry).filter(
                        HMORegistry.city == record_data['city'],
                        HMORegistry.case_number == record_data['case_number']
                    ).first()
                    
                    if existing:
                        # Also check by address in case we have a generated case number collision
                        existing_by_address = db.query(HMORegistry).filter(
                            HMORegistry.city == record_data['city'],
                            HMORegistry.raw_address == record_data['raw_address']
                        ).first()
                        
                        if existing_by_address:
                            print(f"⏭️  Skipping existing address: {record_data['raw_address'][:30]}...")
                            location_skipped += 1
                            continue
                    
                    # Create new HMO record
                    hmo_record = HMORegistry(**record_data)
                    db.add(hmo_record)
                    
                    location_processed += 1
                    if record_data.get('geocoded'):
                        location_geocoded += 1
                    
                    # Commit in batches
                    if location_processed % 20 == 0:
                        db.commit()
                        print(f"💾 Saved progress: {location_processed} records")
                
                except Exception as e:
                    print(f"❌ Error saving record: {e}")
                    db.rollback()
                    continue
            
            # Final commit for this location
            try:
                db.commit()
                print(f"✅ {location} complete: {location_processed} new records, {location_geocoded} geocoded, {location_skipped} skipped")
                total_processed += location_processed
                total_geocoded += location_geocoded
            except Exception as e:
                print(f"❌ Error committing {location} data: {e}")
                db.rollback()
    
    finally:
        db.close()
    
    # Final summary
    final_count = SessionLocal().query(HMORegistry).filter(
        HMORegistry.city.like('cherwell_%')
    ).count()
    
    print("\n" + "=" * 50)
    print("🎉 COMPLETE INTEGRATION FINISHED!")
    print("=" * 50)
    print(f"Total new records processed: {total_processed}")
    print(f"Total geocoded: {total_geocoded}")
    print(f"Generated case numbers: {integration.generated_case_numbers}")
    print(f"Processing errors: {integration.error_count}")
    
    # Get final database summary
    db = SessionLocal()
    try:
        banbury_count = db.query(HMORegistry).filter(HMORegistry.city == 'cherwell_banbury').count()
        bicester_count = db.query(HMORegistry).filter(HMORegistry.city == 'cherwell_bicester').count()
        kidlington_count = db.query(HMORegistry).filter(HMORegistry.city == 'cherwell_kidlington').count()
        total_hmo_count = db.query(HMORegistry).count()
        
        print(f"\n📊 Final Database Summary:")
        print(f"   Banbury: {banbury_count} records")
        print(f"   Bicester: {bicester_count} records") 
        print(f"   Kidlington: {kidlington_count} records")
        print(f"   Total Cherwell: {banbury_count + bicester_count + kidlington_count} records")
        print(f"   Total All HMOs: {total_hmo_count} records")
        
        # Calculate completion percentages
        print(f"\n📈 Completion Rates:")
        print(f"   Banbury: {banbury_count}/114 = {(banbury_count/114*100):.1f}%")
        print(f"   Bicester: {bicester_count}/77 = {(bicester_count/77*100):.1f}%")
        print(f"   Kidlington: {kidlington_count}/32 = {(kidlington_count/32*100):.1f}%")
        
    finally:
        db.close()
    
    print(f"\n🎯 Your Cherwell integration is now complete!")
    print("All properties should appear on your map with full geocoding.")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)