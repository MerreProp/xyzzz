# cherwell_hmo_processor.py
"""
Cherwell District Council HMO Register Processor - FIXED VERSION
Handles multi-location register data and separates towns/cities for individual mapping
"""

import pandas as pd
import requests
from datetime import datetime, timedelta
import logging
import re
from typing import Dict, List, Optional, Tuple, Set
import json
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CherwellLocation:
    """Represents a location within Cherwell District"""
    name: str
    category: str  # 'town', 'village', 'parish'
    postcode_prefixes: List[str]
    alternative_names: List[str] = None

class CherwellLocationClassifier:
    """Classifies addresses into Cherwell towns/villages"""
    
    def __init__(self):
        self.locations = {
            'banbury': CherwellLocation(
                name='Banbury',
                category='town',
                postcode_prefixes=['OX16', 'OX15'],
                alternative_names=['Banbury Town', 'Central Banbury']
            ),
            'bicester': CherwellLocation(
                name='Bicester',
                category='town', 
                postcode_prefixes=['OX26', 'OX25'],
                alternative_names=['Bicester Town']
            ),
            'kidlington': CherwellLocation(
                name='Kidlington',
                category='village',
                postcode_prefixes=['OX5'],
                alternative_names=['Kidlington Village']
            ),
            # Additional villages and parishes in Cherwell
            'adderbury': CherwellLocation(
                name='Adderbury',
                category='village',
                postcode_prefixes=['OX17'],
                alternative_names=[]
            ),
            'ambrosden': CherwellLocation(
                name='Ambrosden',
                category='village',
                postcode_prefixes=['OX25'],
                alternative_names=[]
            ),
            'bloxham': CherwellLocation(
                name='Bloxham',
                category='village',
                postcode_prefixes=['OX15'],
                alternative_names=[]
            ),
            'deddington': CherwellLocation(
                name='Deddington',
                category='village',
                postcode_prefixes=['OX15'],
                alternative_names=[]
            ),
            'hook_norton': CherwellLocation(
                name='Hook Norton',
                category='village',
                postcode_prefixes=['OX15'],
                alternative_names=['Hook Norton Village']
            ),
            'islip': CherwellLocation(
                name='Islip',
                category='village',
                postcode_prefixes=['OX5'],
                alternative_names=[]
            ),
            'launton': CherwellLocation(
                name='Launton',
                category='village',
                postcode_prefixes=['OX26'],
                alternative_names=[]
            ),
            'merton': CherwellLocation(
                name='Merton',
                category='village',
                postcode_prefixes=['OX25'],
                alternative_names=[]
            ),
            'middleton_cheney': CherwellLocation(
                name='Middleton Cheney',
                category='village',
                postcode_prefixes=['OX17'],
                alternative_names=[]
            ),
            'north_aston': CherwellLocation(
                name='North Aston',
                category='village',
                postcode_prefixes=['OX25'],
                alternative_names=[]
            ),
            'oxford_suburbs': CherwellLocation(
                name='Oxford Suburbs',
                category='parish',
                postcode_prefixes=['OX2', 'OX3'],
                alternative_names=['North Oxford', 'Summertown']
            )
        }
    
    def classify_address(self, address: str, postcode: str = None) -> str:
        """
        Classify an address to determine which Cherwell location it belongs to
        Returns the location key, or 'unknown' if can't be classified
        """
        if not address:
            return 'unknown'
        
        address_upper = address.upper()
        
        # First try postcode matching if available
        if postcode:
            postcode_area = postcode.upper().split()[0]  # Get OX16, OX15, etc.
            for location_key, location in self.locations.items():
                if postcode_area in location.postcode_prefixes:
                    return location_key
        
        # Then try address text matching
        for location_key, location in self.locations.items():
            # Check main name
            if location.name.upper() in address_upper:
                return location_key
            
            # Check alternative names
            if location.alternative_names:
                for alt_name in location.alternative_names:
                    if alt_name.upper() in address_upper:
                        return location_key
        
        # Extract postcode from address if not provided separately
        if not postcode:
            postcode_match = re.search(r'(OX\d{1,2}\s?\d[A-Z]{2})', address_upper)
            if postcode_match:
                extracted_postcode = postcode_match.group(1)
                postcode_area = extracted_postcode.split()[0] if ' ' in extracted_postcode else extracted_postcode[:4]
                for location_key, location in self.locations.items():
                    if postcode_area in location.postcode_prefixes:
                        return location_key
        
        return 'unknown'
    
    def get_location_info(self, location_key: str) -> Optional[CherwellLocation]:
        """Get location information for a given location key"""
        return self.locations.get(location_key)
    
    def get_all_locations(self) -> Dict[str, CherwellLocation]:
        """Get all defined locations"""
        return self.locations.copy()

class CherwellHMOProcessor:
    """Main processor for Cherwell HMO register data"""
    
    def __init__(self):
        self.classifier = CherwellLocationClassifier()
        self.register_url = "https://licenseregister.cherwell.gov.uk/registers/index.html?fa=licence_register"
    
    def extract_postcode(self, address: str) -> Optional[str]:
        """Extract UK postcode from address string"""
        if not address:
            return None
        
        # UK postcode pattern
        postcode_pattern = r'([A-Z]{1,2}[0-9R][0-9A-Z]?\s?[0-9][A-Z]{2})'
        match = re.search(postcode_pattern, address.upper())
        return match.group(1) if match else None
    
    def clean_address(self, address: str) -> str:
        """Clean and standardize address format"""
        if not address:
            return ""
        
        # Remove extra whitespace and normalize
        cleaned = ' '.join(address.split())
        
        # Remove common prefixes that might interfere with classification
        prefixes_to_remove = ['FLAT ', 'APARTMENT ', 'UNIT ', 'ROOM ']
        for prefix in prefixes_to_remove:
            if cleaned.upper().startswith(prefix):
                cleaned = cleaned[len(prefix):].strip()
        
        return cleaned
    
    def process_csv_data(self, csv_file_path: str) -> pd.DataFrame: 
        """
        Process Cherwell HMO data from CSV file
        FIXED: Now properly handles the 'HMO Address' column from Cherwell data
        """
        try:
            # Read the CSV data
            df = pd.read_csv(csv_file_path)
            
            logger.info(f"Loaded {len(df)} records from Cherwell CSV")
            logger.info(f"Columns: {list(df.columns)}")
            
            # Process each record
            processed_records = []
            location_stats = {}
            
            for idx, row in df.iterrows():
                try:
                    # FIXED: Extract address from correct column name
                    # First try 'HMO Address' (Cherwell format), then fallback to other common names
                    raw_address = (str(row.get('HMO Address', '')) or 
                                str(row.get('address', '')) or 
                                str(row.get('property_address', '')))
                    
                    if not raw_address or raw_address == 'nan':
                        logger.warning(f"No address found for row {idx}")
                        continue
                    
                    postcode = self.extract_postcode(raw_address)
                    cleaned_address = self.clean_address(raw_address)
                    
                    # Classify location
                    location_key = self.classifier.classify_address(cleaned_address, postcode)
                    location_info = self.classifier.get_location_info(location_key)
                    
                    # Count location stats
                    if location_key not in location_stats:
                        location_stats[location_key] = 0
                    location_stats[location_key] += 1
                    
                    # Create processed record with proper column mapping for Cherwell data
                    processed_record = {
                        'case_number': row.get('Manual Reference Number', f'CHERWELL_{idx}'),
                        'licence_number': row.get('Licence Number', ''),
                        'licence_reference': row.get('Licence Reference', ''),
                        'raw_address': raw_address,
                        'cleaned_address': cleaned_address,
                        'postcode': postcode,
                        'location_key': location_key,
                        'location_name': location_info.name if location_info else 'Unknown',
                        'location_category': location_info.category if location_info else 'unknown',
                        'licensee': row.get('Licensee', ''),
                        'person_managing': row.get('Person Managing', ''),
                        'licence_description': row.get('Licence Description', ''),
                        'licence_type': row.get('Licence Type', ''),
                        'issue_date': row.get('Issue Date', ''),
                        'start_date': row.get('Start Date', ''),
                        'expiry_date': row.get('Expiry Date', ''),
                        'description_of_hmo': row.get('Description Of Licensed Hmo', ''),
                        'licensee_address': row.get('Licensee Address', ''),
                        'property_manager': row.get('Property Manager', ''),
                        'number_of_storeys': row.get('Number Of Storeys', None),
                        'number_of_self_contained_flats': row.get('Number Of Self Contained Flats', None),
                        'number_of_not_self_contained_flats': row.get('Number Of Not Self Contained Flats', None)
                    }
                    
                    processed_records.append(processed_record)
                    
                except Exception as e:
                    logger.warning(f"Error processing row {idx}: {e}")
                    continue
            
            # Create final DataFrame
            processed_df = pd.DataFrame(processed_records)
            
            # Log location statistics
            logger.info("Location Distribution:")
            for location_key, count in sorted(location_stats.items(), key=lambda x: x[1], reverse=True):
                location_info = self.classifier.get_location_info(location_key)
                location_name = location_info.name if location_info else location_key
                logger.info(f"  {location_name}: {count} properties")
            
            return processed_df
            
        except Exception as e:
            logger.error(f"Error processing CSV data: {e}")
            raise

        """
        Process Cherwell HMO data from CSV file
        FIXED: Now properly handles the 'HMO Address' column from Cherwell data
        """
        try:
            # Read the CSV data
            df = pd.read_csv(csv_file_path)
            
            logger.info(f"Loaded {len(df)} records from Cherwell CSV")
            logger.info(f"Columns: {list(df.columns)}")
            
            # Process each record
            processed_records = []
            location_stats = {}
            
            for idx, row in df.iterrows():
                try:
                    # FIXED: Extract address from correct column name
                    # First try 'HMO Address' (Cherwell format), then fallback to other common names
                    raw_address = (str(row.get('HMO Address', '')) or 
                                 str(row.get('address', '')) or 
                                 str(row.get('property_address', '')))
                    
                    if not raw_address or raw_address == 'nan':
                        logger.warning(f"No address found for row {idx}")
                        continue
                    
                    postcode = self.extract_postcode(raw_address)
                    cleaned_address = self.clean_address(raw_address)
                    
                    # Classify location
                    location_key = self.classifier.classify_address(cleaned_address, postcode)
                    location_info = self.classifier.get_location_info(location_key)
                    
                    # Count location stats
                    if location_key not in location_stats:
                        location_stats[location_key] = 0
                    location_stats[location_key] += 1
                    
                    # Create processed record with proper column mapping
                    processed_record = {
                        'case_number': row.get('Manual Reference Number', f'CHERWELL_{idx}'),
                        'licence_number': row.get('Licence Number', ''),
                        'licence_reference': row.get('Licence Reference', ''),
                        'raw_address': raw_address,
                        'cleaned_address': cleaned_address,
                        'postcode': postcode,
                        'location_key': location_key,
                        'location_name': location_info.name if location_info else 'Unknown',
                        'location_category': location_info.category if location_info else 'unknown',
                        'licensee': row.get('Licensee', ''),
                        'person_managing': row.get('Person Managing', ''),
                        'licence_description': row.get('Licence Description', ''),
                        'licence_type': row.get('Licence Type', ''),
                        'issue_date': row.get('Issue Date', ''),
                        'start_date': row.get('Start Date', ''),
                        'expiry_date': row.get('Expiry Date', ''),
                        'description_of_hmo': row.get('Description Of Licensed Hmo', ''),
                        'licensee_address': row.get('Licensee Address', ''),
                        'property_manager': row.get('Property Manager', ''),
                        'number_of_storeys': row.get('Number Of Storeys', None),
                        'number_of_self_contained_flats': row.get('Number Of Self Contained Flats', None),
                        'number_of_not_self_contained_flats': row.get('Number Of Not Self Contained Flats', None)
                    }
                    
                    processed_records.append(processed_record)
                    
                except Exception as e:
                    logger.warning(f"Error processing row {idx}: {e}")
                    continue
            
            # Create final DataFrame
            processed_df = pd.DataFrame(processed_records)
            
            # Log location statistics
            logger.info("Location Distribution:")
            for location_key, count in sorted(location_stats.items(), key=lambda x: x[1], reverse=True):
                location_info = self.classifier.get_location_info(location_key)
                location_name = location_info.name if location_info else location_key
                logger.info(f"  {location_name}: {count} properties")
            
            return processed_df
            
        except Exception as e:
            logger.error(f"Error processing CSV data: {e}")
            raise
    
    def split_by_location(self, df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """Split the processed DataFrame by location"""
        location_dfs = {}
        
        for location_key in df['location_key'].unique():
            if location_key != 'unknown':  # Skip unknown locations for now
                location_df = df[df['location_key'] == location_key].copy()
                location_info = self.classifier.get_location_info(location_key)
                
                if len(location_df) > 0:
                    location_dfs[location_key] = location_df
                    logger.info(f"Created {location_info.name} dataset with {len(location_df)} properties")
        
        # Handle unknown locations separately
        unknown_df = df[df['location_key'] == 'unknown']
        if len(unknown_df) > 0:
            location_dfs['unknown'] = unknown_df
            logger.info(f"Unknown locations: {len(unknown_df)} properties")
        
        return location_dfs
    
    def save_location_datasets(self, location_dfs: Dict[str, pd.DataFrame], output_dir: str = "cherwell_data"):
        """Save individual location datasets as CSV files"""
        import os
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        saved_files = []
        
        for location_key, df in location_dfs.items():
            location_info = self.classifier.get_location_info(location_key)
            location_name = location_info.name if location_info else location_key
            
            filename = f"cherwell_{location_key}_hmo.csv"
            filepath = os.path.join(output_dir, filename)
            
            df.to_csv(filepath, index=False)
            
            saved_files.append({
                'location_key': location_key,
                'location_name': location_name,
                'filename': filename,
                'filepath': filepath,
                'record_count': len(df)
            })
            
            logger.info(f"Saved {location_name} data to {filepath} ({len(df)} records)")
        
        return saved_files
    
    def save_location_summary(self, location_dfs: Dict[str, pd.DataFrame], output_dir: str = "cherwell_data"):
        """Save a summary of all locations"""
        import os
        
        summary = {
            'processing_date': datetime.now().isoformat(),
            'total_records': sum(len(df) for df in location_dfs.values()),
            'locations': {}
        }
        
        for location_key, df in location_dfs.items():
            location_info = self.classifier.get_location_info(location_key)
            summary['locations'][location_key] = {
                'name': location_info.name if location_info else location_key,
                'category': location_info.category if location_info else 'unknown',
                'record_count': len(df),
                'postcode_prefixes': location_info.postcode_prefixes if location_info else [],
                'sample_addresses': df['raw_address'].head(3).tolist() if len(df) > 0 else []
            }
        
        summary_path = os.path.join(output_dir, 'cherwell_locations_summary.json')
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Saved location summary to {summary_path}")
        return summary_path
    
    def generate_processing_report(self, df: pd.DataFrame, location_dfs: Dict[str, pd.DataFrame]) -> Dict:
        """Generate a comprehensive processing report"""
        total_records = len(df)
        
        report = {
            'processing_date': datetime.now().isoformat(),
            'total_records': total_records,
            'locations_found': len(location_dfs),
            'location_breakdown': {}
        }
        
        for location_key, location_df in location_dfs.items():
            location_info = self.classifier.get_location_info(location_key)
            report['location_breakdown'][location_key] = {
                'name': location_info.name if location_info else location_key,
                'category': location_info.category if location_info else 'unknown',
                'record_count': len(location_df),
                'percentage': round((len(location_df) / total_records) * 100, 2)
            }
        
        return report

def main():
    """Main CLI function - FIXED VERSION"""
    import argparse
    import os
    
    parser = argparse.ArgumentParser(description='Process Cherwell HMO Register')
    parser.add_argument('input_file', help='Path to Cherwell HMO register file (CSV or Excel)')
    parser.add_argument('--output-dir', default='cherwell_data', 
                       help='Output directory for processed data (default: cherwell_data)')
    parser.add_argument('--no-geocoding', action='store_true',
                       help='Skip geocoding to speed up processing')
    
    args = parser.parse_args()
    
    # Use absolute path and check if file exists
    input_file_path = os.path.abspath(args.input_file)
    print(f"🔍 Looking for input file: {input_file_path}")
    
    if not os.path.exists(input_file_path):
        print(f"❌ File not found: {input_file_path}")
        print(f"📁 Current directory: {os.getcwd()}")
        print(f"📁 Contents of data/cherwell/raw/:")
        raw_dir = "data/cherwell/raw"
        if os.path.exists(raw_dir):
            for file in os.listdir(raw_dir):
                print(f"   - {file}")
        else:
            print("   Directory doesn't exist!")
        return False
    
    print(f"✅ Found input file: {input_file_path}")
    
    # Run the workflow
    processor = CherwellHMOProcessor()
    
    try:
        # Process the CSV data
        print("Starting Cherwell HMO register processing...")
        processed_df = processor.process_csv_data(input_file_path)
        
        # Split by location
        print("Splitting data by location...")
        location_dfs = processor.split_by_location(processed_df)
        
        # Save individual location datasets
        print("Saving location datasets...")
        saved_files = processor.save_location_datasets(location_dfs, args.output_dir)
        
        # Save location summary
        processor.save_location_summary(location_dfs, args.output_dir)
        
        # Generate processing report
        print("Generating processing report...")
        report = processor.generate_processing_report(processed_df, location_dfs)
        
        # Print summary
        print("\n" + "="*60)
        print("CHERWELL HMO REGISTER PROCESSING COMPLETE")
        print("="*60)
        print(f"Total records processed: {len(processed_df)}")
        print(f"Locations identified: {len(location_dfs)}")
        
        print("\nLocation breakdown:")
        for location_key, stats in report['location_breakdown'].items():
            print(f"  {stats['name']}: {stats['record_count']} properties ({stats['percentage']}%)")
        
        print(f"\nDatasets saved to {args.output_dir}/:")
        for file_info in saved_files:
            print(f"  {file_info['location_name']}: {file_info['filename']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Processing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()