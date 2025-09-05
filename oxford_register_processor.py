#!/usr/bin/env python3
"""
Oxford HMO Register Copy Processor
==================================

This script processes the "HMO Register Copy.xlsx" file and updates the database
to ensure that HMOs shown as active in the register are not marked as expired
in the map system.

Key features:
1. Reads the Excel file correctly handling the header format
2. Processes license expiry dates from Excel date format
3. Updates existing database records with correct status
4. Uses enhanced address matching to link records properly
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import re
import sys
import os
from typing import Dict, List, Optional, Tuple, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class OxfordRegisterProcessor:
    """Process Oxford HMO Register Copy Excel file"""
    
    def __init__(self, excel_file_path: str = "HMO Register Copy.xlsx"):
        self.excel_file_path = excel_file_path
        self.processed_records = []
        
    def read_excel_file(self) -> pd.DataFrame:
        """Read and parse the Oxford HMO Register Excel file with proper section handling"""
        print("📊 Reading Oxford HMO Register Copy Excel file...")
        
        try:
            # Read the Excel file as raw data to handle sections properly
            df_raw = pd.read_excel(
                self.excel_file_path, 
                sheet_name='Table 1',
                header=None  # Don't use any row as header initially
            )
            
            print(f"   Raw data shape: {df_raw.shape}")
            
            # Find all header rows that contain "Case Number"
            header_rows = []
            for idx, row in df_raw.iterrows():
                if pd.notna(row.iloc[0]) and 'case number' in str(row.iloc[0]).lower():
                    header_rows.append(idx)
            
            print(f"   Found {len(header_rows)} section headers at rows: {header_rows[:10]}...")
            
            # Extract all valid data rows from all sections
            all_data_rows = []
            valid_case_pattern = re.compile(r'\d+/\d+/[A-Z]+')
            
            for i, header_row in enumerate(header_rows):
                # Data starts after header row
                section_start = header_row + 1
                # Section ends at next header or end of file
                section_end = header_rows[i + 1] if i + 1 < len(header_rows) else len(df_raw)
                
                # Process this section
                section_data_count = 0
                for row_idx in range(section_start, section_end):
                    if row_idx < len(df_raw):
                        row = df_raw.iloc[row_idx]
                        case_number = str(row.iloc[0]) if pd.notna(row.iloc[0]) else ''
                        location = str(row.iloc[3]) if pd.notna(row.iloc[3]) else ''
                        
                        # Check if this is a valid HMO record
                        if (valid_case_pattern.match(case_number) and 
                            location and location.strip() and 
                            location.lower() not in ['location', 'nan']):
                            
                            # Create standardized record
                            standardized_row = {
                                'case_number': case_number,
                                'location': location,
                                'total_occupants': row.iloc[10] if len(row) > 10 and pd.notna(row.iloc[10]) else None,
                                'total_units': row.iloc[16] if len(row) > 16 and pd.notna(row.iloc[16]) else None,
                                'licence_commenced': row.iloc[19] if len(row) > 19 and pd.notna(row.iloc[19]) else None,
                                'licence_expires': row.iloc[22] if len(row) > 22 and pd.notna(row.iloc[22]) else None
                            }
                            all_data_rows.append(standardized_row)
                            section_data_count += 1
                
                if section_data_count > 0:
                    print(f"   Section {i+1}: {section_data_count} valid records")
            
            # Convert to DataFrame
            df = pd.DataFrame(all_data_rows)
            
            print(f"   Total valid HMO records extracted: {len(df)}")
            print(f"   Sample records:")
            for i in range(min(3, len(df))):
                case = df.iloc[i]['case_number']
                location = df.iloc[i]['location']
                expires = df.iloc[i]['licence_expires']
                print(f"     {case}: {location} (expires: {expires})")
            
            return df
            
        except Exception as e:
            logger.error(f"Error reading Excel file: {e}")
            raise
    
    def process_expiry_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process and convert Excel date formats to proper dates"""
        print("📅 Processing licence expiry dates...")
        
        if 'licence_expires' not in df.columns:
            logger.warning("No licence_expires column found")
            df['licence_expires_date'] = None
            df['is_active'] = False
            return df
        
        df['licence_expires_date'] = None
        df['is_active'] = False
        
        today = datetime.now().date()
        processed_count = 0
        active_count = 0
        
        for idx, row in df.iterrows():
            expiry_raw = row['licence_expires']
            
            try:
                if pd.isna(expiry_raw):
                    continue
                    
                # Handle Excel date serial numbers
                if isinstance(expiry_raw, (int, float)):
                    # Convert Excel date serial number to datetime
                    # Excel uses 1900-01-01 as day 1, but treats 1900 as a leap year
                    excel_date = datetime(1899, 12, 30) + timedelta(days=int(expiry_raw))
                    expiry_date = excel_date.date()
                elif isinstance(expiry_raw, datetime):
                    expiry_date = expiry_raw.date()
                elif isinstance(expiry_raw, str):
                    # Try to parse string dates
                    for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']:
                        try:
                            expiry_date = datetime.strptime(expiry_raw, fmt).date()
                            break
                        except ValueError:
                            continue
                    else:
                        logger.warning(f"Could not parse date: {expiry_raw}")
                        continue
                else:
                    continue
                
                df.at[idx, 'licence_expires_date'] = expiry_date
                df.at[idx, 'is_active'] = expiry_date >= today
                processed_count += 1
                
                if expiry_date >= today:
                    active_count += 1
                    
            except Exception as e:
                logger.warning(f"Error processing expiry date {expiry_raw}: {e}")
                continue
        
        print(f"   Processed {processed_count} expiry dates")
        print(f"   Found {active_count} active licences")
        print(f"   Found {processed_count - active_count} expired licences")
        
        return df
    
    def normalize_addresses(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize addresses for better matching"""
        print("🏠 Normalizing addresses...")
        
        from enhanced_oxford_matcher import EnhancedOxfordAddressMatcher
        matcher = EnhancedOxfordAddressMatcher()
        
        df['normalized_address'] = ''
        df['postcode'] = ''
        df['house_number'] = ''
        df['street_name'] = ''
        
        for idx, row in df.iterrows():
            location = row.get('location', '')
            if not location:
                continue
                
            normalized = matcher.normalize_oxford_address(str(location))
            df.at[idx, 'normalized_address'] = normalized['full']
            df.at[idx, 'postcode'] = normalized['postcode']
            df.at[idx, 'house_number'] = normalized['number']
            df.at[idx, 'street_name'] = normalized['street']
        
        print(f"   Normalized {len(df)} addresses")
        return df
    
    def update_database_records(self, df: pd.DataFrame) -> Dict[str, int]:
        """Update database with correct licence status"""
        print("💾 Updating database records...")
        
        try:
            # Import database modules (adjust paths as needed) - FIXED IMPORT
            from database import SessionLocal
            from hmo_registry.database_models import HMORegistry  # Changed from HMORegister to HMORegistry
            from enhanced_oxford_matcher import EnhancedOxfordAddressMatcher
            
            db = SessionLocal()
            matcher = EnhancedOxfordAddressMatcher()
            
            stats = {
                'total_processed': 0,
                'found_matches': 0,
                'updated_active': 0,
                'updated_expired': 0,
                'new_records': 0,
                'errors': 0
            }
            
            # Get existing Oxford HMO records
            existing_hmos = db.query(HMORegistry).filter(
                HMORegistry.city == 'oxford'
            ).all()
            
            print(f"   Found {len(existing_hmos)} existing Oxford HMO records in database")
            
            # Create lookup by case number and address
            existing_by_case = {hmo.case_number: hmo for hmo in existing_hmos if hmo.case_number}
            existing_by_address = {hmo.raw_address: hmo for hmo in existing_hmos if hmo.raw_address}
            
            for idx, row in df.iterrows():
                stats['total_processed'] += 1
                
                case_number = str(row['case_number']).strip()
                location = str(row.get('location', '')).strip()
                is_active = row.get('is_active', False)
                expiry_date = row.get('licence_expires_date')
                
                if not case_number or not location:
                    continue
                
                try:
                    # Strategy 1: Find by case number
                    existing_hmo = existing_by_case.get(case_number)
                    
                    # Strategy 2: Find by address matching if no case number match
                    if not existing_hmo:
                        best_match = None
                        best_confidence = 0.0
                        
                        for db_hmo in existing_hmos:
                            if not db_hmo.raw_address:
                                continue
                                
                            confidence = matcher.calculate_address_match_confidence(
                                location, db_hmo.raw_address
                            )
                            
                            if confidence > best_confidence and confidence >= 0.8:  # High confidence threshold
                                best_match = db_hmo
                                best_confidence = confidence
                        
                        existing_hmo = best_match
                    
                    if existing_hmo:
                        stats['found_matches'] += 1
                        
                        # Update the record
                        updated = False
                        
                        # Update case number if missing
                        if not existing_hmo.case_number and case_number:
                            existing_hmo.case_number = case_number
                            updated = True
                        
                        # Update expiry date
                        if expiry_date and existing_hmo.licence_expiry_date != expiry_date:
                            existing_hmo.licence_expiry_date = expiry_date
                            updated = True
                        
                        # Update address if the register version is better
                        if location and (not existing_hmo.raw_address or len(location) > len(existing_hmo.raw_address)):
                            existing_hmo.raw_address = location
                            updated = True
                        
                        if updated:
                            existing_hmo.updated_at = datetime.utcnow()
                            if is_active:
                                stats['updated_active'] += 1
                            else:
                                stats['updated_expired'] += 1
                    
                    else:
                        # Create new record
                        new_hmo = HMORegistry(
                            city='oxford',
                            source='oxford_council_register',
                            case_number=case_number,
                            raw_address=location,
                            licence_expiry_date=expiry_date,
                            total_occupants=row.get('total_occupants'),
                            total_units=row.get('total_units'),
                            licence_status='active' if is_active else 'expired',
                            created_at=datetime.utcnow(),
                            updated_at=datetime.utcnow()
                        )
                        
                        db.add(new_hmo)
                        stats['new_records'] += 1
                        
                        if is_active:
                            stats['updated_active'] += 1
                        else:
                            stats['updated_expired'] += 1
                
                except Exception as e:
                    logger.error(f"Error processing record {case_number}: {e}")
                    stats['errors'] += 1
                    continue
                
                # Progress update
                if stats['total_processed'] % 500 == 0:
                    print(f"   Processed {stats['total_processed']}/{len(df)} records...")
            
            # Commit changes
            db.commit()
            
            print("   Database update completed!")
            for key, value in stats.items():
                print(f"     {key.replace('_', ' ').title()}: {value}")
            
            return stats
            
        except Exception as e:
            logger.error(f"Database update error: {e}")
            if 'db' in locals():
                db.rollback()
            raise
        
        finally:
            if 'db' in locals():
                db.close()
    
    def process_register_file(self) -> Dict[str, Any]:
        """Main processing function"""
        print("🏛️ Processing Oxford HMO Register Copy")
        print("=" * 50)
        
        try:
            # Step 1: Read Excel file
            df = self.read_excel_file()
            
            # Step 2: Process expiry dates
            df = self.process_expiry_dates(df)
            
            # Step 3: Normalize addresses
            df = self.normalize_addresses(df)
            
            # Step 4: Update database
            update_stats = self.update_database_records(df)
            
            # Save processed data to CSV for verification
            output_file = 'oxford_hmo_register_processed.csv'
            df.to_csv(output_file, index=False)
            print(f"💾 Processed data saved to {output_file}")
            
            return {
                'success': True,
                'total_records': len(df),
                'active_records': df['is_active'].sum() if 'is_active' in df else 0,
                'update_stats': update_stats,
                'output_file': output_file
            }
            
        except Exception as e:
            logger.error(f"Error processing register file: {e}")
            return {
                'success': False,
                'error': str(e)
            }


def fix_oxford_hmo_status():
    """Main function to fix Oxford HMO active/expired status"""
    print("🔧 Fixing Oxford HMO Active/Expired Status")
    print("=" * 60)
    
    # Check if Excel file exists
    excel_file = "HMO Register Copy.xlsx"
    if not os.path.exists(excel_file):
        print(f"❌ Error: {excel_file} not found in current directory")
        print("   Please ensure the file is in the same directory as this script")
        return False
    
    # Process the register file
    processor = OxfordRegisterProcessor(excel_file)
    result = processor.process_register_file()
    
    if result['success']:
        print("\n✅ Oxford HMO status update completed successfully!")
        print(f"   Total records processed: {result['total_records']}")
        print(f"   Active licences found: {result['active_records']}")
        print(f"   Database records updated: {result['update_stats']['found_matches']}")
        print(f"   New records created: {result['update_stats']['new_records']}")
        
        print("\n📋 Next steps:")
        print("   1. Restart your web application to see updated data")
        print("   2. Check the map to verify HMOs now show correct active/expired status")
        print("   3. Review the output CSV file for verification")
        
        return True
    else:
        print(f"\n❌ Error occurred: {result['error']}")
        return False


if __name__ == "__main__":
    fix_oxford_hmo_status()