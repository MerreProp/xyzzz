# hmo_registry/cities/oxford_renewal.py
"""
Oxford HMO License Renewal Analysis System - REWRITTEN
=======================================================

Processes Oxford's Excel file with 3 distinct data sections:
1. Section 1 (Blocks 1-78): License information (~39 rows/block)
2. Section 2 (Blocks 79-317): Agent/holder information (~10-20 rows/block) 
3. Section 3 (Blocks 318-387): Property details with postcodes (~44 rows/block)

Uses block size patterns to identify section types and merges by Case Number.
"""

import pandas as pd
import re
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set
import requests

logger = logging.getLogger(__name__)

class OxfordLicenseRenewalAnalyzer:
    """Analyzes Oxford license renewals using 3-section Excel processing"""
    
    def __init__(self):
        self.city = 'oxford'
        self.excel_file = 'HMO Register Copy.xlsx'
        self._cached_data = None
        self._cache_timestamp = None
        
        # Section identification thresholds
        self.SECTION_1_SIZE = 35  # ~39 rows = License data
        self.SECTION_2_SIZE = 25  # ~10-20 rows = Agent data  
        self.SECTION_3_SIZE = 40  # ~44 rows = Property details
        
    def safe_extract_postcode(self, address: str) -> Optional[str]:
        """Extract UK postcode from address - fixed for Oxford format"""
        if not address:
            return None
        
        # Simple approach: UK postcodes are always at the end and follow pattern
        # Like: OX4 3AH, OX1 2AB, etc.
        import re
        
        # Look for UK postcode pattern: 2-4 letters + 1-2 digits + optional letter + space + digit + 2 letters
        postcode_pattern = r'([A-Z]{1,2}[0-9]{1,2}[A-Z]?\s+[0-9][A-Z]{2})\b'
        
        match = re.search(postcode_pattern, address.upper())
        if match:
            return match.group(1).strip()
        
        return None

    def identify_section_type(self, block_size: int) -> str:
        """Identify section type based on block size"""
        if block_size >= self.SECTION_1_SIZE:
            return 'license'  # Section 1: License information
        elif block_size >= self.SECTION_2_SIZE:
            return 'property'  # Section 3: Property details (prefer this over agent)
        else:
            return 'agent'    # Section 2: Agent information

    def excel_date_to_datetime(self, excel_date):
        """Improved Excel date conversion with better error handling"""
        if pd.isna(excel_date) or excel_date == '' or excel_date is None:
            return None
        
        # Handle datetime objects (already parsed by pandas)
        if isinstance(excel_date, datetime):
            return excel_date
        
        # Handle pandas Timestamp
        if hasattr(excel_date, 'to_pydatetime'):
            return excel_date.to_pydatetime()
        
        try:
            # Handle string dates
            if isinstance(excel_date, str):
                excel_date = excel_date.strip()
                if not excel_date:
                    return None
                    
                # Try various date formats
                for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y-%m-%d %H:%M:%S']:
                    try:
                        return datetime.strptime(excel_date, fmt)
                    except ValueError:
                        continue
                return None
            
            # Handle Excel serial dates (numeric)
            if isinstance(excel_date, (int, float)):
                # Excel date serial number (days since 1900-01-01, with leap year bug)
                if excel_date > 59:  # After Excel's fake leap day
                    base_date = datetime(1899, 12, 30)  # Corrected base
                else:
                    base_date = datetime(1899, 12, 31)
                return base_date + timedelta(days=float(excel_date))
                
        except (ValueError, TypeError, OverflowError) as e:
            logger.debug(f"Date conversion error for {excel_date}: {e}")
            return None
        
        return None
            
    def find_all_header_blocks(self) -> List[Dict]:
        """Find all header blocks and classify them by size"""
        try:
            # Read entire Excel file
            df = pd.read_excel(self.excel_file, sheet_name=0, header=None)
            
            # Find all header positions
            header_indices = []
            for index, row in df.iterrows():
                if any(str(cell).strip() == "Case Number" for cell in row if pd.notna(cell)):
                    header_indices.append(index)
            
            if not header_indices:
                raise ValueError("No header rows found in Excel file")
            
            # Calculate block sizes and classify
            blocks = []
            for i, header_idx in enumerate(header_indices):
                # Determine block end
                if i < len(header_indices) - 1:
                    next_header = header_indices[i + 1]
                    block_size = next_header - header_idx - 1
                else:
                    block_size = len(df) - header_idx - 1
                
                # Get column names from this header
                column_names = df.iloc[header_idx].tolist()
                
                # Classify section type
                section_type = self.identify_section_type(block_size)
                
                blocks.append({
                    'block_number': i + 1,
                    'header_row': header_idx,
                    'data_start': header_idx + 1,
                    'block_size': block_size,
                    'section_type': section_type,
                    'columns': column_names
                })
            
            logger.info(f"Found {len(blocks)} blocks in Excel file")
            
            # Log section distribution
            section_counts = {}
            for block in blocks:
                section_type = block['section_type']
                section_counts[section_type] = section_counts.get(section_type, 0) + 1
            
            logger.info(f"Section distribution: {section_counts}")
            
            # Log some example blocks for debugging
            for i, block in enumerate(blocks[:10]):  # Show first 10 blocks
                logger.info(f"Block {block['block_number']}: {block['section_type']}, size: {block['block_size']}")
            
            return blocks
            
        except Exception as e:
            logger.error(f"Error finding header blocks: {e}")
            return []
    
    def process_license_section(self, df: pd.DataFrame, blocks: List[Dict]) -> Dict[str, Dict]:
        """Process Section 1: License information blocks - FIXED VERSION"""
        license_data = {}
        
        license_blocks = [b for b in blocks if b['section_type'] == 'license']
        logger.info(f"Processing {len(license_blocks)} license blocks...")
        
        for block in license_blocks:
            try:
                # Extract data from this block
                start_row = block['data_start']
                end_row = start_row + block['block_size']
                block_data = df.iloc[start_row:end_row]
                
                # FIXED: Use hardcoded column positions based on Excel analysis
                # These positions are consistent across all Oxford license blocks
                case_col = 0          # Column A: Case Number
                location_col = 3      # Column D: Location  
                occupants_col = 7     # Column H: Total Number Occupants
                commenced_col = 19    # Column T: Licence Commenced (0-indexed: 19)
                expires_col = 22      # Column W: Licence Expires (0-indexed: 22)
                
                logger.debug(f"Processing license block {block['block_number']} with {len(block_data)} rows")
                
                # Process each row in the block
                for idx, (_, row) in enumerate(block_data.iterrows()):
                    # Skip empty rows or header repetitions
                    case_number = str(row.iloc[case_col]).strip() if pd.notna(row.iloc[case_col]) else ""
                    
                    # Skip if case number is empty or is a header repetition
                    if (not case_number or 
                        case_number == 'nan' or 
                        case_number.lower() == 'case number' or
                        len(case_number) < 5):  # Oxford case numbers are longer
                        continue
                    
                    location = str(row.iloc[location_col]).strip() if pd.notna(row.iloc[location_col]) else ""
                    if not location or location.lower() == 'location':
                        continue
                    
                    # Parse license dates from FIXED columns
                    licence_start = None
                    licence_expiry = None
                    
                    # Column T (index 19): Licence Commenced
                    if commenced_col < len(row) and pd.notna(row.iloc[commenced_col]):
                        licence_start = self.excel_date_to_datetime(row.iloc[commenced_col])

                    # Column W (index 22): Licence Expires  
                    if expires_col < len(row) and pd.notna(row.iloc[expires_col]):
                        licence_expiry = self.excel_date_to_datetime(row.iloc[expires_col])
                    
                    # Parse occupants
                    total_occupants = None
                    if occupants_col < len(row) and pd.notna(row.iloc[occupants_col]):
                        try:
                            total_occupants = int(float(row.iloc[occupants_col]))
                        except (ValueError, TypeError):
                            pass
                    
                    # Determine licence status
                    licence_status = 'unknown'
                    if licence_expiry:
                        current_date = datetime.now().date()
                        licence_status = 'active' if licence_expiry.date() >= current_date else 'expired'
                    elif licence_start:
                        # If we have start date but no expiry, assume active
                        licence_status = 'active'
                    
                    license_data[case_number] = {
                        'case_number': case_number,
                        'address': location,
                        'licence_status': licence_status,
                        'licence_start_date': licence_start.isoformat() if licence_start else None,
                        'licence_expiry_date': licence_expiry.isoformat() if licence_expiry else None,
                        'total_occupants': total_occupants,
                        'total_units': None  # Not available in license section
                    }
                    
                    # Debug logging for first few records
                    if len(license_data) <= 5:
                        logger.info(f"Sample record {len(license_data)}: {case_number} - Status: {licence_status}, "
                                f"Expires: {licence_expiry.strftime('%Y-%m-%d') if licence_expiry else 'None'}")
                        
            except Exception as e:
                logger.warning(f"Error processing license block {block['block_number']}: {e}")
                continue
        
        # Log final statistics
        total_records = len(license_data)
        active_records = sum(1 for record in license_data.values() if record['licence_status'] == 'active')
        expired_records = sum(1 for record in license_data.values() if record['licence_status'] == 'expired')
        unknown_records = sum(1 for record in license_data.values() if record['licence_status'] == 'unknown')
        
        logger.info(f"Processed {total_records} license records:")
        logger.info(f"  - Active: {active_records}")
        logger.info(f"  - Expired: {expired_records}")
        logger.info(f"  - Unknown: {unknown_records}")
        
        return license_data
    
    def process_agent_section(self, df: pd.DataFrame, blocks: List[Dict]) -> Dict[str, Dict]:
        """Process Section 2: Agent/License holder information"""
        agent_data = {}
        
        agent_blocks = [b for b in blocks if b['section_type'] == 'agent']
        logger.info(f"Processing {len(agent_blocks)} agent blocks...")
        
        for block in agent_blocks:
            try:
                # Extract data from this block
                start_row = block['data_start']
                end_row = start_row + block['block_size']
                block_data = df.iloc[start_row:end_row]
                
                # Get column mapping
                columns = block['columns']
                case_col = next((i for i, col in enumerate(columns) if pd.notna(col) and 'case' in str(col).lower()), 0)
                location_col = next((i for i, col in enumerate(columns) if pd.notna(col) and 'location' in str(col).lower()), 1)
                party_col = next((i for i, col in enumerate(columns) if pd.notna(col) and 'party' in str(col).lower()), 2)
                name_col = next((i for i, col in enumerate(columns) if pd.notna(col) and 'name' in str(col).lower()), 3)
                address_col = next((i for i, col in enumerate(columns) if pd.notna(col) and 'address' in str(col).lower()), 4)
                
                # Process each row in the block
                for _, row in block_data.iterrows():
                    case_number = str(row.iloc[case_col]).strip() if pd.notna(row.iloc[case_col]) else ""
                    
                    if not case_number or case_number == 'nan':
                        continue
                    
                    # Extract agent information
                    party_type = str(row.iloc[party_col]).strip() if party_col < len(row) and pd.notna(row.iloc[party_col]) else ""
                    agent_name = str(row.iloc[name_col]).strip() if name_col < len(row) and pd.notna(row.iloc[name_col]) else ""
                    agent_address = str(row.iloc[address_col]).strip() if address_col < len(row) and pd.notna(row.iloc[address_col]) else ""
                    
                    # Store agent data (combine multiple agents if needed)
                    if case_number not in agent_data:
                        agent_data[case_number] = {
                            'case_number': case_number,
                            'agents': []
                        }
                    
                    if agent_name or agent_address:
                        agent_data[case_number]['agents'].append({
                            'party_type': party_type,
                            'name': agent_name,
                            'address': agent_address
                        })
                        
            except Exception as e:
                logger.warning(f"Error processing agent block {block['block_number']}: {e}")
                continue
        
        logger.info(f"Processed {len(agent_data)} agent records")
        return agent_data
    
    def process_property_section(self, df: pd.DataFrame, blocks: List[Dict]) -> Dict[str, Dict]:
        """Process Section 3: Property details with postcodes"""
        property_data = {}
        
        property_blocks = [b for b in blocks if b['section_type'] == 'property']
        logger.info(f"Processing {len(property_blocks)} property blocks...")
        
        for block in property_blocks:
            try:
                # Extract data from this block
                start_row = block['data_start']
                end_row = start_row + block['block_size']
                block_data = df.iloc[start_row:end_row]
                
                # Get column mapping
                columns = block['columns']
                case_col = next((i for i, col in enumerate(columns) if pd.notna(col) and 'case' in str(col).lower()), 0)
                location_col = next((i for i, col in enumerate(columns) if pd.notna(col) and 'location' in str(col).lower()), 1)
                postcode_col = next((i for i, col in enumerate(columns) if pd.notna(col) and 'postcode' in str(col).lower()), None)
                occupants_col = next((i for i, col in enumerate(columns) if pd.notna(col) and 'occupant' in str(col).lower()), None)
                
                # Process each row in the block
                for _, row in block_data.iterrows():
                    case_number = str(row.iloc[case_col]).strip() if pd.notna(row.iloc[case_col]) else ""
                    location = str(row.iloc[location_col]).strip() if pd.notna(row.iloc[location_col]) else ""
                    
                    if not case_number or case_number == 'nan':
                        continue
                    
                    # Extract postcode (crucial for geocoding)
                    postcode = None
                    if postcode_col is not None and postcode_col < len(row) and pd.notna(row.iloc[postcode_col]):
                        postcode = str(row.iloc[postcode_col]).strip()
                    
                    # If no explicit postcode column, try to extract from location
                    if not postcode and location:
                        postcode = self.safe_extract_postcode(location)
                    
                    # Extract additional property details
                    occupants_detail = None
                    if occupants_col is not None and occupants_col < len(row) and pd.notna(row.iloc[occupants_col]):
                        try:
                            occupants_detail = int(float(row.iloc[occupants_col]))
                        except (ValueError, TypeError):
                            pass
                    
                    property_data[case_number] = {
                        'case_number': case_number,
                        'postcode': postcode,
                        'occupants_detail': occupants_detail,
                        'property_location': location  # Keep for validation
                    }
                    
            except Exception as e:
                logger.warning(f"Error processing property block {block['block_number']}: {e}")
                continue
        
        logger.info(f"Processed {len(property_data)} property records")
        return property_data
    
    def merge_sections_data(self, license_data: Dict, agent_data: Dict, property_data: Dict) -> List[Dict]:
        """Merge all three sections by Case Number"""
        merged_records = []
        
        # Start with license data as primary source
        for case_number, license_record in license_data.items():
            merged_record = license_record.copy()
            
            # Add agent information if available
            if case_number in agent_data:
                agent_info = agent_data[case_number]
                merged_record['agents'] = agent_info['agents']
                
                # Extract primary agent info
                if agent_info['agents']:
                    primary_agent = agent_info['agents'][0]
                    merged_record['licence_holder_name'] = primary_agent['name']
                    merged_record['licence_holder_address'] = primary_agent['address']
                    merged_record['licence_holder_type'] = primary_agent['party_type']
            
            # Add property details if available
            if case_number in property_data:
                property_info = property_data[case_number]
                
                # Use postcode from property section (more reliable)
                if property_info.get('postcode'):
                    merged_record['postcode'] = property_info['postcode']
                else:
                    # Fallback: try to extract from LOCATION address (not agent address)
                    merged_record['postcode'] = self.safe_extract_postcode(merged_record.get('address', ''))
                
                # Use occupants detail if available (might be more accurate)
                if property_info.get('occupants_detail'):
                    merged_record['total_occupants'] = property_info['occupants_detail']
            
            # If still no postcode, try extracting from the main location address
            if not merged_record.get('postcode'):
                merged_record['postcode'] = self.safe_extract_postcode(merged_record.get('address', ''))
            
            # Add metadata
            merged_record.update({
                'id': f"oxford_hmo_{case_number}",
                'source': 'oxford_excel_renewal',
                'city': 'oxford',
                'geocoded': False,  # Will be set during geocoding
                'latitude': None,
                'longitude': None,
                'last_updated': datetime.now().isoformat(),
                'data_source': 'Oxford City Council HMO Register (Excel)'
            })
            
            merged_records.append(merged_record)
        
        logger.info(f"Merged {len(merged_records)} complete records")
        return merged_records
    
    def geocode_properties(self, records: List[Dict], max_geocode: int = 200) -> List[Dict]:
        """Geocode properties using postcode.io API"""
        geocoded_count = 0
        postcodes_found = 0
        
        # Count how many records have postcodes
        for record in records:
            if record.get('postcode'):
                postcodes_found += 1
        
        logger.info(f"Found {postcodes_found} records with postcodes out of {len(records)} total")
        
        for record in records:
            if geocoded_count >= max_geocode:
                logger.info(f"Reached geocoding limit of {max_geocode}")
                break
            
            postcode = record.get('postcode')
            if not postcode:
                continue
            
            try:
                # Use postcode.io API for geocoding
                url = f"https://api.postcodes.io/postcodes/{postcode.replace(' ', '')}"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == 200 and data.get('result'):
                        result = data['result']
                        record['latitude'] = result.get('latitude')
                        record['longitude'] = result.get('longitude')
                        record['geocoded'] = True
                        geocoded_count += 1
                        
                        # Rate limiting
                        time.sleep(0.1)
                        
                        if geocoded_count % 50 == 0:
                            logger.info(f"Geocoded {geocoded_count} properties...")
                else:
                    logger.debug(f"Postcode API failed for {postcode}: {response.status_code}")
                            
            except Exception as e:
                logger.debug(f"Geocoding error for postcode {postcode}: {e}")
        
        logger.info(f"Successfully geocoded {geocoded_count} out of {postcodes_found} properties with postcodes")
        return records
    
    def load_new_excel_data(self) -> List[Dict]:
        """Load and process all three sections of Excel data"""
        try:
            # Read Excel file and find all header blocks
            df = pd.read_excel(self.excel_file, sheet_name=0, header=None)
            blocks = self.find_all_header_blocks()
            
            if not blocks:
                raise ValueError("No data blocks found in Excel file")
            
            # Process each section
            license_data = self.process_license_section(df, blocks)
            agent_data = self.process_agent_section(df, blocks)
            property_data = self.process_property_section(df, blocks)
            
            # Merge all sections
            merged_records = self.merge_sections_data(license_data, agent_data, property_data)
            
            logger.info(f"Successfully processed Excel file: {len(merged_records)} total records")
            return merged_records
            
        except Exception as e:
            logger.error(f"Error loading Excel data: {e}")
            return []
        
    def get_existing_database_data(self) -> List[Dict]:
        """Get existing Oxford HMO data from database"""
        try:
            from ..database_models import HMORegistry
            from database import SessionLocal
            
            db = SessionLocal()
            try:
                existing_records = db.query(HMORegistry).filter(
                    HMORegistry.city == 'oxford'
                ).all()
                
                data = []
                for record in existing_records:
                    data.append({
                        'case_number': getattr(record, 'case_number', ''),
                        'address': getattr(record, 'standardized_address', None) or getattr(record, 'raw_address', ''),
                        'postcode': getattr(record, 'postcode', None),
                        'latitude': getattr(record, 'latitude', None),
                        'longitude': getattr(record, 'longitude', None),
                        'geocoded': getattr(record, 'geocoded', False),
                        'licence_holder': getattr(record, 'licence_holder', None),
                        'licence_status': getattr(record, 'licence_status', None),
                        'licence_start_date': getattr(record, 'licence_start_date', None),
                        'licence_expiry_date': getattr(record, 'licence_expiry_date', None),
                        'last_updated': getattr(record, 'last_updated', None)
                    })
                
                logger.info(f"Retrieved {len(data)} existing records from database")
                return data
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error retrieving existing data: {e}")
            return []
    
    def analyze_license_renewals(self) -> Dict:
        """Main analysis function"""
        logger.info("Starting Oxford license renewal analysis...")
        
        # Load new Excel data using 3-section processing
        new_data = self.load_new_excel_data()
        if not new_data:
            return {'error': 'Could not read Excel data'}
        
        # Geocode the properties
        geocoded_data = self.geocode_properties(new_data, max_geocode=2966)
        
        # Cache the results
        self._cached_data = geocoded_data
        self._cache_timestamp = datetime.now()
        
        # Get existing data for comparison (optional)
        existing_data = self.get_existing_database_data()
        
        # Create analysis summary
        geocoded_count = sum(1 for record in geocoded_data if record.get('geocoded'))
        active_count = sum(1 for record in geocoded_data if record.get('licence_status') == 'active')
        expired_count = sum(1 for record in geocoded_data if record.get('licence_status') == 'expired')
        
        analysis_summary = {
            'analysis_date': datetime.now().isoformat(),
            'existing_records': len(existing_data),
            'new_excel_records': len(new_data),
            'geocoded_new_properties': geocoded_count,
            'active_licenses': active_count,
            'expired_licenses': expired_count,
            'total_final_records': len(geocoded_data),
            'sample_records': geocoded_data[:5]  # Sample of processed records
        }
        
        return analysis_summary
    
    def get_hmo_data(self, force_refresh: bool = False, enable_geocoding: bool = True) -> List[Dict]:
        """Get combined HMO data"""
        
        # Use cached data if available and not forcing refresh
        if not force_refresh and self._cached_data and self._cache_timestamp:
            cache_age = datetime.now() - self._cache_timestamp
            if cache_age.total_seconds() < 7200:  # 2 hour cache
                logger.info(f"Using cached Oxford renewal data ({len(self._cached_data)} records)")
                return self._cached_data
        
        # Run the analysis to get updated data
        analysis = self.analyze_license_renewals()
        
        if 'error' in analysis:
            logger.error(f"Analysis failed: {analysis['error']}")
            return []
        
        return self._cached_data or []
    
    def get_statistics(self) -> Dict:
        """Get statistics about the Oxford HMO data"""
        data = self.get_hmo_data()
        
        if not data:
            return {
                'total_records': 0,
                'geocoded_records': 0,
                'geocoding_percentage': 0,
                'active_licenses': 0,
                'expired_licenses': 0,
                'error': 'No data available'
            }
        
        geocoded_count = sum(1 for record in data if record.get('geocoded'))
        active_count = sum(1 for record in data if record.get('licence_status') == 'active')
        expired_count = len(data) - active_count
        
        return {
            'total_records': len(data),
            'geocoded_records': geocoded_count,
            'geocoding_percentage': round((geocoded_count / len(data)) * 100, 2),
            'active_licenses': active_count,
            'expired_licenses': expired_count,
            'data_source': 'Oxford 3-Section Excel Analysis',
            'last_updated': datetime.now().isoformat()
        }