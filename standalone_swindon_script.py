#!/usr/bin/env python3
"""
Standalone Swindon HMO Integration Script
========================================

This script processes the Swindon HMO Excel file and integrates it into your database.
No external dependencies on utils modules - everything is self-contained.
"""

import pandas as pd
import re
import time
import logging
import requests
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class SwindonHMORecord:
    """Data class for processed Swindon HMO records"""
    case_number: str
    raw_address: str
    cleaned_address: str
    licence_holder: str
    postcode: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    geocoded: bool = False
    quality_score: float = 0.0

class SwindonHMOProcessor:
    """Standalone Swindon HMO processor"""
    
    def __init__(self, excel_file_path: str):
        self.excel_file_path = excel_file_path
        self.geocoding_delay = 0.5  # Faster with postcodes.io
        
    def clean_address(self, address: str) -> str:
        """Clean address text by removing formatting issues"""
        if not address:
            return ""
        
        # Replace \r\n with spaces and clean up
        cleaned = re.sub(r'\r\n', ' ', str(address))
        cleaned = re.sub(r'\s+', ' ', cleaned)  # Multiple spaces to single space
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
            # Ensure proper spacing (e.g., SN12AF -> SN1 2AF)
            if len(postcode) >= 5 and ' ' not in postcode:
                postcode = postcode[:-3] + ' ' + postcode[-3:]
            return postcode.upper()
        
        return None
    
    def generate_case_number(self, index: int, address: str) -> str:
        """Generate a unique case number for Swindon records"""
        address_hash = str(abs(hash(address.lower())))[-4:]
        return f"SWD{index:04d}_{address_hash}"
    
    def geocode_postcode_io(self, postcode: str) -> Tuple[Optional[float], Optional[float]]:
        """Geocode using postcodes.io API (same as your existing system)"""
        if not postcode:
            return None, None
            
        try:
            # Use postcodes.io API - same as your existing system
            url = f"https://api.postcodes.io/postcodes/{postcode.replace(' ', '')}"
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 200 and data.get('result'):
                    result = data['result']
                    lat = result.get('latitude')
                    lon = result.get('longitude')
                    
                    if lat and lon:
                        logger.debug(f"📍 Postcodes.io: {postcode} -> ({lat:.6f}, {lon:.6f})")
                        return float(lat), float(lon)
            
            logger.debug(f"🔍 No results from postcodes.io for: {postcode}")
            return None, None
            
        except Exception as e:
            logger.debug(f"⚠️ Postcodes.io error for {postcode}: {e}")
            return None, None

    def geocode_address(self, address: str) -> Tuple[Optional[float], Optional[float]]:
        """Geocode using postcode first (postcodes.io), then fallback to full address"""
        # First try to extract and geocode the postcode
        postcode = self.extract_postcode(address)
        if postcode:
            lat, lon = self.geocode_postcode_io(postcode)
            if lat and lon:
                return lat, lon
        
        # Fallback to full address geocoding with Nominatim (original method)
        try:
            full_address = f"{address}, Swindon, Wiltshire, UK"
            
            url = "https://nominatim.openstreetmap.org/search"
            params = {
                'q': full_address,
                'format': 'json',
                'limit': 1,
                'countrycodes': 'gb'
            }
            
            headers = {
                'User-Agent': 'SwindonHMORegistry/1.0 (your-email@example.com)'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            
            results = response.json()
            
            if results:
                lat = float(results[0]['lat'])
                lon = float(results[0]['lon'])
                logger.debug(f"📍 Nominatim fallback: {address[:50]}... -> ({lat:.6f}, {lon:.6f})")
                return lat, lon
            
            return None, None
                
        except Exception as e:
            logger.debug(f"⚠️ Full address geocoding error for {address[:50]}...: {e}")
            return None, None
    
    def calculate_quality_score(self, record_data: Dict) -> float:
        """Calculate data quality score based on completeness"""
        score = 0.0
        
        # Address quality (30%)
        if record_data.get('cleaned_address') and len(record_data['cleaned_address']) > 10:
            score += 0.3
        
        # Postcode present (30%)
        if record_data.get('postcode'):
            score += 0.3
        
        # Geocoding success (30%)
        if record_data.get('geocoded'):
            score += 0.3
        
        # Licence holder information (10%)
        if record_data.get('licence_holder') and len(record_data['licence_holder']) > 3:
            score += 0.1
        
        return min(score, 1.0)
    
    def load_and_process_excel(self, enable_geocoding: bool = True) -> List[SwindonHMORecord]:
        """Load Excel file and process all records"""
        logger.info(f"📊 Loading Swindon data from {self.excel_file_path}")
        
        try:
            # Read the Excel file
            df = pd.read_excel(self.excel_file_path, sheet_name='List of HMOs')
            
            # Clean column names
            df.columns = df.columns.str.strip()
            
            logger.info(f"✅ Loaded {len(df)} records from Excel file")
            logger.info(f"📋 Columns: {list(df.columns)}")
            
            # Process records
            processed_records = []
            geocoding_count = 0
            
            for index, row in df.iterrows():
                try:
                    raw_address = str(row['HMO Address']).strip()
                    licence_holder = str(row['Licence Holder']).strip()  # Removed trailing space
                    
                    # Skip empty rows
                    if not raw_address or raw_address.lower() in ['nan', 'none', '']:
                        logger.warning(f"⚠️ Skipping row {index} - empty address")
                        continue
                    
                    # Clean the address
                    cleaned_address = self.clean_address(raw_address)
                    
                    # Extract postcode
                    postcode = self.extract_postcode(cleaned_address)
                    
                    # Generate case number
                    case_number = self.generate_case_number(index + 1, cleaned_address)
                    
                    # Geocode the address if enabled
                    lat, lon = None, None
                    geocoded = False
                    
                    if enable_geocoding:
                        lat, lon = self.geocode_address(cleaned_address)
                        if lat and lon:
                            geocoded = True
                            geocoding_count += 1
                        
                        # Progress updates
                        if geocoding_count % 10 == 0:
                            logger.info(f"📍 Geocoded {geocoding_count} addresses so far...")
                        
                        # Respect rate limits
                        time.sleep(self.geocoding_delay)
                    
                    # Calculate quality score
                    record_data = {
                        'cleaned_address': cleaned_address,
                        'postcode': postcode,
                        'geocoded': geocoded,
                        'licence_holder': licence_holder
                    }
                    quality_score = self.calculate_quality_score(record_data)
                    
                    # Create record
                    record = SwindonHMORecord(
                        case_number=case_number,
                        raw_address=raw_address,
                        cleaned_address=cleaned_address,
                        licence_holder=licence_holder,
                        postcode=postcode,
                        latitude=lat,
                        longitude=lon,
                        geocoded=geocoded,
                        quality_score=quality_score
                    )
                    
                    processed_records.append(record)
                    
                except Exception as e:
                    logger.error(f"❌ Error processing row {index}: {e}")
                    continue
            
            logger.info(f"✅ Processed {len(processed_records)} Swindon HMO records")
            logger.info(f"📍 Successfully geocoded {geocoding_count} addresses")
            
            return processed_records
            
        except Exception as e:
            logger.error(f"❌ Error loading Excel file: {e}")
            raise
    
    def export_to_csv(self, records: List[SwindonHMORecord], output_file: str = "swindon_hmo_processed.csv"):
        """Export processed records to CSV"""
        logger.info(f"💾 Exporting {len(records)} records to {output_file}")
        
        data = []
        for record in records:
            data.append({
                'case_number': record.case_number,
                'raw_address': record.raw_address,
                'cleaned_address': record.cleaned_address,
                'licence_holder': record.licence_holder,
                'postcode': record.postcode,
                'latitude': record.latitude,
                'longitude': record.longitude,
                'geocoded': record.geocoded,
                'quality_score': record.quality_score
            })
        
        df = pd.DataFrame(data)
        df.to_csv(output_file, index=False)
        
        logger.info(f"✅ Exported to {output_file}")
        return output_file
    
    def get_summary_stats(self, records: List[SwindonHMORecord]) -> Dict:
        """Get summary statistics for processed records"""
        total_records = len(records)
        
        if total_records == 0:
            return {'error': 'No records to analyze'}
        
        geocoded_count = sum(1 for r in records if r.geocoded)
        postcode_count = sum(1 for r in records if r.postcode)
        avg_quality = sum(r.quality_score for r in records) / total_records
        
        return {
            'total_records': total_records,
            'geocoded_records': geocoded_count,
            'geocoding_success_rate': round((geocoded_count / total_records * 100), 1),
            'records_with_postcodes': postcode_count,
            'postcode_coverage': round((postcode_count / total_records * 100), 1),
            'average_quality_score': round(avg_quality, 3),
            'high_quality_records': sum(1 for r in records if r.quality_score >= 0.8),
            'processing_timestamp': datetime.now().isoformat()
        }

def main():
    """Main execution function"""
    print("🏠 Swindon HMO Registry Processing")
    print("=" * 40)
    
    # Configuration
    excel_file = "List_of_houses_in_multiple_occupation__HMOs__in_Swindon-2.xlsx"
    
    # Check if file exists
    import os
    if not os.path.exists(excel_file):
        print(f"❌ Excel file not found: {excel_file}")
        print("   Please ensure the Swindon Excel file is in the current directory")
        return
    
    try:
        # Initialize processor
        processor = SwindonHMOProcessor(excel_file)
        
        # Ask user about geocoding
        geocoding_choice = input("🌍 Enable geocoding? This will take longer but provides coordinates (y/N): ").lower().strip()
        enable_geocoding = geocoding_choice == 'y'
        
        if enable_geocoding:
            print("⚠️  Geocoding enabled - this will take several minutes and respect rate limits")
        else:
            print("⚠️  Geocoding disabled - coordinates will not be available")
        
        # Process records
        print(f"\n🔄 Processing records...")
        records = processor.load_and_process_excel(enable_geocoding=enable_geocoding)
        
        if not records:
            print("❌ No records were processed successfully")
            return
        
        # Show sample records
        print(f"\n📋 Sample processed records:")
        for i, record in enumerate(records[:3]):
            print(f"\n{i+1}. Case: {record.case_number}")
            print(f"   Address: {record.cleaned_address}")
            print(f"   Postcode: {record.postcode}")
            print(f"   Licence Holder: {record.licence_holder}")
            print(f"   Geocoded: {record.geocoded}")
            if record.geocoded:
                print(f"   Coordinates: ({record.latitude:.6f}, {record.longitude:.6f})")
            print(f"   Quality Score: {record.quality_score:.2f}")
        
        # Get and display statistics
        print(f"\n📈 Processing Statistics:")
        stats = processor.get_summary_stats(records)
        for key, value in stats.items():
            if key != 'processing_timestamp':
                print(f"   {key.replace('_', ' ').title()}: {value}")
        
        # Export to CSV
        csv_file = processor.export_to_csv(records)
        print(f"\n💾 Data exported to: {csv_file}")
        
        # Instructions for database integration
        print(f"\n🔗 Next Steps:")
        print(f"   1. Review the exported CSV file: {csv_file}")
        print(f"   2. Use the processed data to update your database")
        print(f"   3. Integrate with your existing HMO registry API")
        print(f"   4. Add Swindon to your map visualization")
        
        print(f"\n✅ Swindon HMO processing complete!")
        
    except Exception as e:
        logger.error(f"❌ Error in main execution: {e}")
        raise

if __name__ == "__main__":
    main()