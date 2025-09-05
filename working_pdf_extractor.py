#!/usr/bin/env python3
"""
Fixed PDF Extractor - All Pages Working
=======================================

Based on the debug output, this version properly extracts data from ALL pages
by understanding the different structures on page 1 vs pages 2+.
"""

import pandas as pd
import pdfplumber
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import sys
import os
import re

# Add project path for imports
sys.path.insert(0, os.getcwd())

try:
    from database import SessionLocal
    from hmo_registry.database_models import HMORegistry
    from hmo_registry.utils.improved_geocoding import geocode_address, extract_postcode_from_address
    DATABASE_AVAILABLE = True
    print("✅ Database and geocoding imports successful")
except ImportError as e:
    print(f"⚠️  Database imports not available: {e}")
    DATABASE_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FixedHMOPDFExtractor:
    """Fixed PDF extractor that properly handles all pages"""
    
    def __init__(self):
        self.stats = {
            'vale_processed': 0,
            'south_oxon_processed': 0,
            'geocoded_success': 0,
            'total_processed': 0,
            'errors': 0
        }
    
    def extract_all_pages_data(self, pdf_path: str) -> List[Dict]:
        """Extract data from all pages, handling different structures properly"""
        
        print(f"📄 Extracting from {pdf_path}...")
        
        if not os.path.exists(pdf_path):
            print(f"❌ File not found: {pdf_path}")
            return []
        
        all_records = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                print(f"   PDF has {len(pdf.pages)} pages")
                
                for page_num, page in enumerate(pdf.pages):
                    print(f"   Processing page {page_num + 1}...")
                    
                    # Extract tables from this page
                    tables = page.extract_tables()
                    
                    if tables:
                        for table_num, table in enumerate(tables):
                            if not table or len(table) < 1:
                                continue
                            
                            print(f"     Table {table_num + 1}: {len(table)} rows")
                            
                            # Process table based on page type
                            if page_num == 0:
                                # Page 1 has headers in the table
                                records = self.process_page1_table(table)
                            else:
                                # Pages 2+ have raw data rows
                                records = self.process_data_table(table, page_num + 1)
                            
                            all_records.extend(records)
                            print(f"     Extracted {len(records)} valid records")
        
        except Exception as e:
            print(f"❌ Error processing PDF: {e}")
            return []
        
        print(f"   Total extracted: {len(all_records)} records")
        return all_records
    
    def process_page1_table(self, table: List[List]) -> List[Dict]:
        """Process page 1 table which has headers"""
        
        if len(table) < 3:  # Need title row, header row, and at least one data row
            return []
        
        # Find the actual header row (usually row 1)
        header_row = None
        data_start = None
        
        for i, row in enumerate(table):
            row_text = ' '.join([str(cell) if cell else '' for cell in row]).lower()
            if 'address 1' in row_text and 'postcode' in row_text:
                header_row = i
                data_start = i + 1
                break
        
        if header_row is None or data_start >= len(table):
            return []
        
        headers = table[header_row]
        records = []
        
        # Process data rows
        for i in range(data_start, len(table)):
            row = table[i]
            
            # Skip empty rows
            if not any(cell for cell in row if cell):
                continue
            
            # Create record from row data
            record = self.parse_row_with_headers(row, headers)
            if record:
                records.append(record)
        
        return records
    
    def process_data_table(self, table: List[List], page_num: int) -> List[Dict]:
        """Process pages 2+ which have raw data rows (no headers in table)"""
        
        records = []
        
        for row in table:
            # Skip empty rows
            if not any(cell for cell in row if cell):
                continue
            
            # Check if this looks like property data
            if self.looks_like_property_row(row):
                record = self.parse_raw_data_row(row, page_num)
                if record:
                    records.append(record)
        
        return records
    
    def looks_like_property_row(self, row: List) -> bool:
        """Check if a row contains property data"""
        
        if len(row) < 4:  # Need at least address, town, postcode, occupants
            return False
        
        row_text = ' '.join([str(cell) if cell else '' for cell in row])
        
        # Look for UK postcode pattern
        if re.search(r'[A-Z]{1,2}[0-9][0-9A-Z]?\s*[0-9][A-Z]{2}', row_text.upper()):
            return True
        
        # Look for address + numbers combination
        has_address_word = any(word in row_text.lower() for word in ['road', 'street', 'way', 'close', 'avenue', 'drive', 'lane', 'place'])
        has_numbers = any(cell and str(cell).strip().isdigit() and 1 <= int(cell) <= 50 for cell in row if cell)
        
        return has_address_word and has_numbers
    
    def parse_row_with_headers(self, row: List, headers: List) -> Optional[Dict]:
        """Parse a row using headers from page 1"""
        
        try:
            record = {}
            
            for i, cell in enumerate(row):
                if i < len(headers) and headers[i]:
                    header = str(headers[i]).strip()
                    value = str(cell).strip() if cell else ''
                    record[header] = value
            
            # Must have address and postcode
            address1 = record.get('Address 1', '')
            postcode = record.get('Postcode', '')
            
            if not address1 or not postcode:
                return None
            
            return self.standardize_record(record, 'page1')
            
        except Exception as e:
            logger.warning(f"Error parsing row with headers: {e}")
            return None
    
    def parse_raw_data_row(self, row: List, page_num: int) -> Optional[Dict]:
        """Parse a raw data row from pages 2+ (using positional mapping)"""
        
        try:
            # Based on the debug output, the column structure is:
            # 0: Address 1, 1: Address 2, 2: Town, 3: Postcode, 4: Max occupants,
            # 5: Storeys, 6: Sleeping rooms, 7: Living rooms, 8: Shared kitchens,
            # 9: Shared bathrooms, 10: HMO type, 11: Self contained, 12: Not self contained,
            # 13: Date issued, 14: Duration, 15: Tribunal, 16: Description
            
            if len(row) < 4:
                return None
            
            address1 = str(row[0]).strip() if row[0] else ''
            address2 = str(row[1]).strip() if row[1] else ''
            town = str(row[2]).strip() if row[2] else ''
            postcode = str(row[3]).strip() if row[3] else ''
            
            # Must have address and postcode
            if not address1 or not postcode:
                return None
            
            # Build record dict
            record = {
                'Address 1': address1,
                'Address 2': address2,
                'Town': town,
                'Postcode': postcode,
                'Max. occupants': str(row[4]).strip() if len(row) > 4 and row[4] else '',
                'No. of storeys': str(row[5]).strip() if len(row) > 5 and row[5] else '',
                'No. of rooms for sleeping accommodation': str(row[6]).strip() if len(row) > 6 and row[6] else '',
                'No. of rooms for living accommodation': str(row[7]).strip() if len(row) > 7 and row[7] else '',
                'No. of shared kitchens': str(row[8]).strip() if len(row) > 8 and row[8] else '',
                'Shared bathrooms (excludes en-suites)': str(row[9]).strip() if len(row) > 9 and row[9] else '',
                'HMO type (shared house or flats)': str(row[10]).strip() if len(row) > 10 and row[10] else '',
                'Date full licence issued': str(row[13]).strip() if len(row) > 13 and row[13] else '',
                'Brief description of HMO': str(row[16]).strip() if len(row) > 16 and row[16] else ''
            }
            
            return self.standardize_record(record, f'page{page_num}')
            
        except Exception as e:
            logger.warning(f"Error parsing raw data row: {e}")
            return None
    
    def standardize_record(self, record: Dict, source: str) -> Dict:
        """Convert a record to standard HMO format"""
        
        try:
            # Build full address
            address_parts = []
            
            if record.get('Address 1'):
                address_parts.append(record['Address 1'])
            if record.get('Address 2'):
                address_parts.append(record['Address 2'])
            if record.get('Town'):
                address_parts.append(record['Town'])
            
            raw_address = ', '.join(address_parts)
            
            # Extract data
            postcode = record.get('Postcode', '').strip()
            max_occupants = self._safe_int(record.get('Max. occupants', ''))
            storeys = self._safe_int(record.get('No. of storeys', ''))
            sleeping_rooms = self._safe_int(record.get('No. of rooms for sleeping accommodation', ''))
            licence_date_str = record.get('Date full licence issued', '')
            hmo_type = record.get('HMO type (shared house or flats)', '')
            description = record.get('Brief description of HMO', '')
            
            # Parse licence date
            licence_issued = self._parse_date(licence_date_str)
            licence_expiry = None
            if licence_issued:
                licence_expiry = licence_issued + timedelta(days=5*365)
            
            # Determine status
            licence_status = 'active' if licence_expiry and licence_expiry > datetime.now().date() else 'expired'
            
            return {
                'raw_address': raw_address,
                'postcode': postcode,
                'max_occupants': max_occupants,
                'storeys': storeys,
                'sleeping_rooms': sleeping_rooms,
                'licence_issued': licence_issued,
                'licence_expiry': licence_expiry,
                'licence_status': licence_status,
                'hmo_type': hmo_type,
                'description': description,
                'source_info': source
            }
            
        except Exception as e:
            logger.warning(f"Error standardizing record: {e}")
            return None
    
    def _safe_int(self, value) -> Optional[int]:
        """Safely convert value to int"""
        if not value:
            return None
        try:
            # Handle cases like "25 - NJ to check"
            clean_value = str(value).split()[0].strip()
            return int(float(clean_value))
        except (ValueError, TypeError):
            return None
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string from PDF"""
        if not date_str or date_str.strip() == '':
            return None
        
        date_str = str(date_str).strip()
        
        # Try different date formats
        formats = [
            '%d/%m/%Y',
            '%d-%m-%Y',
            '%Y-%m-%d',
            '%d/%m/%y',
            '%d-%m-%y',
            '%d-%b-%Y',
            '%d-%b-%y',
            '%d-%b-%y'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        
        return None
    
    def transform_to_database_format(self, records: List[Dict], council: str) -> List[Dict]:
        """Transform records to database format"""
        
        print(f"🔄 Transforming {len(records)} {council} records...")
        
        transformed_records = []
        
        for record in records:
            try:
                if not record or not record.get('raw_address'):
                    continue
                
                # Generate case number
                postcode_clean = record.get('postcode', '').replace(' ', '') if record.get('postcode') else 'UNKNOWN'
                address_key = re.sub(r'[^a-zA-Z0-9]', '_', record['raw_address'].split(',')[0])[:20]
                case_number = f"{council}_{postcode_clean}_{address_key}"
                
                # Create database record
                db_record = {
                    'city': council,
                    'source': f'{council.replace("_", " ").title()} District Council',
                    'case_number': case_number,
                    'raw_address': record['raw_address'],
                    'postcode': record.get('postcode', ''),
                    'total_occupants': record.get('max_occupants'),
                    'total_units': record.get('sleeping_rooms'),
                    'licence_status': record.get('licence_status', 'unknown'),
                    'licence_start_date': record.get('licence_issued'),
                    'licence_expiry_date': record.get('licence_expiry'),
                    'data_source_url': f'https://www.{council.replace("_", "")}.gov.uk/',
                    'processing_notes': f'Extracted from PDF. {record.get("hmo_type", "")}. {record.get("description", "")}',
                    'geocoded': False,
                    'data_quality_score': 0.9
                }
                
                transformed_records.append(db_record)
                
            except Exception as e:
                logger.warning(f"Error transforming record: {e}")
                self.stats['errors'] += 1
                continue
        
        print(f"   Transformed {len(transformed_records)} records")
        return transformed_records
    
    def geocode_records(self, records: List[Dict]) -> List[Dict]:
        """Geocode the records"""
        
        if not records:
            return records
        
        print(f"🌍 Geocoding {len(records)} addresses...")
        
        for i, record in enumerate(records):
            try:
                if record['raw_address']:
                    coords = geocode_address(record['raw_address'])
                    
                    if coords:
                        record['latitude'] = coords[0]
                        record['longitude'] = coords[1]
                        record['geocoded'] = True
                        record['geocoding_source'] = 'improved_geocoder'
                        self.stats['geocoded_success'] += 1
                    else:
                        record['geocoded'] = False
                        record['processing_notes'] += '; Geocoding failed'
                
                # Progress indicator
                if (i + 1) % 10 == 0:
                    print(f"   Geocoded {i + 1}/{len(records)} addresses...")
                    
            except Exception as e:
                logger.warning(f"Geocoding failed for {record.get('raw_address', 'unknown')}: {e}")
                record['geocoded'] = False
        
        geocoded_count = sum(1 for r in records if r.get('geocoded', False))
        print(f"   Geocoded {geocoded_count}/{len(records)} addresses ({geocoded_count/len(records)*100:.1f}%)")
        
        return records
    
    def save_to_database(self, records: List[Dict], council: str) -> int:
        """Save records to database"""
        
        if not DATABASE_AVAILABLE:
            print(f"⚠️  Database not available, saving {council} to CSV instead...")
            df = pd.DataFrame(records)
            csv_file = f"{council}_extracted_data.csv"
            df.to_csv(csv_file, index=False)
            print(f"💾 Saved to {csv_file}")
            return len(records)
        
        db = SessionLocal()
        saved_count = 0
        
        try:
            for record in records:
                try:
                    # Check if record already exists
                    existing = db.query(HMORegistry).filter(
                        HMORegistry.city == record['city'],
                        HMORegistry.case_number == record['case_number']
                    ).first()
                    
                    if existing:
                        continue
                    
                    # Also check by address
                    existing_by_address = db.query(HMORegistry).filter(
                        HMORegistry.city == record['city'],
                        HMORegistry.raw_address == record['raw_address']
                    ).first()
                    
                    if existing_by_address:
                        continue
                    
                    # Create new record
                    hmo_record = HMORegistry(**record)
                    db.add(hmo_record)
                    saved_count += 1
                    
                    # Commit in batches
                    if saved_count % 20 == 0:
                        db.commit()
                        print(f"   Saved batch for {council}... (Total: {saved_count})")
                
                except Exception as e:
                    logger.error(f"Error saving {council} record: {e}")
                    db.rollback()
            
            # Final commit
            db.commit()
            print(f"   Successfully saved {saved_count} new {council} records")
            
        except Exception as e:
            logger.error(f"Database error for {council}: {e}")
            db.rollback()
            
        finally:
            db.close()
        
        return saved_count
    
    def extract_vale_data(self) -> List[Dict]:
        """Extract Vale of White Horse data"""
        
        pdf_path = "Vale_HMO-licence-register_Jul-25.pdf"
        records = self.extract_all_pages_data(pdf_path)
        return self.transform_to_database_format(records, 'vale_of_white_horse')
    
    def extract_south_oxon_data(self) -> List[Dict]:
        """Extract South Oxfordshire data"""
        
        pdf_path = "South_HMO-licence-register_Jul-25.pdf"
        records = self.extract_all_pages_data(pdf_path)
        return self.transform_to_database_format(records, 'south_oxfordshire')
    
    def run_full_extraction(self) -> Dict:
        """Run the complete extraction process"""
        
        print("🏛️ FIXED HMO PDF EXTRACTION & INTEGRATION")
        print("=" * 45)
        
        results = {}
        
        # Extract Vale of White Horse
        print("\n1️⃣ Extracting Vale of White Horse data...")
        vale_records = self.extract_vale_data()
        if vale_records:
            vale_records = self.geocode_records(vale_records)
            vale_saved = self.save_to_database(vale_records, 'vale_of_white_horse')
            results['vale_of_white_horse'] = {
                'extracted': len(vale_records),
                'saved': vale_saved
            }
            self.stats['vale_processed'] = vale_saved
        else:
            results['vale_of_white_horse'] = {'extracted': 0, 'saved': 0}
        
        # Extract South Oxfordshire
        print("\n2️⃣ Extracting South Oxfordshire data...")
        south_oxon_records = self.extract_south_oxon_data()
        if south_oxon_records:
            south_oxon_records = self.geocode_records(south_oxon_records)
            south_oxon_saved = self.save_to_database(south_oxon_records, 'south_oxfordshire')
            results['south_oxfordshire'] = {
                'extracted': len(south_oxon_records),
                'saved': south_oxon_saved
            }
            self.stats['south_oxon_processed'] = south_oxon_saved
        else:
            results['south_oxfordshire'] = {'extracted': 0, 'saved': 0}
        
        # Summary
        total_extracted = sum(r['extracted'] for r in results.values())
        total_saved = sum(r['saved'] for r in results.values())
        
        print(f"\n📊 FIXED EXTRACTION SUMMARY")
        print(f"=" * 30)
        print(f"Vale of White Horse: {results['vale_of_white_horse']['saved']} properties")
        print(f"South Oxfordshire: {results['south_oxfordshire']['saved']} properties")
        print(f"Total new properties: {total_saved}")
        print(f"Geocoding success: {self.stats['geocoded_success']}/{total_extracted} ({self.stats['geocoded_success']/max(1,total_extracted)*100:.1f}%)")
        
        if total_saved > 0:
            print(f"\n🔗 NEXT STEPS:")
            print(f"1. Update your HMORegistryCity enum to include:")
            print(f"   - vale_of_white_horse")
            print(f"   - south_oxfordshire")
            print(f"2. Update your registry endpoints")
            print(f"3. Restart your API server")
            print(f"4. Test: curl http://localhost:8001/api/hmo-registry/cities/vale_of_white_horse")
        
        return {
            'success': total_saved > 0,
            'total_extracted': total_extracted,
            'total_saved': total_saved,
            'results': results,
            'stats': self.stats
        }

def main():
    """Main execution function"""
    
    extractor = FixedHMOPDFExtractor()
    results = extractor.run_full_extraction()
    
    if results['success']:
        print(f"\n🎉 Fixed extraction completed successfully!")
        print(f"Added {results['total_saved']} new HMO properties from ALL pages")
    else:
        print(f"\n❌ No new records were processed")
        print(f"Check the output above for any errors")
    
    return results['success']

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✨ All pages processed! Ready to update your API configuration!")
    else:
        print("\n🔧 Check the extraction process for issues")