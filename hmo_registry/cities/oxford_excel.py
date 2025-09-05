# hmo_registry/cities/oxford_excel.py
"""
Oxford HMO Registry - Excel File Integration (FIXED VERSION)
===========================================================

Updated Oxford HMO system that properly handles repeated headers
in the Excel file and processes ALL 9,185+ records.
"""

import pandas as pd
import re
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import requests

logger = logging.getLogger(__name__)

class OxfordExcelHMOData:
    """Oxford HMO registry data handler using Excel file with header skipping"""
    
    def __init__(self):
        self.city = 'oxford'
        self.source_type = 'excel'
        self.data_source_name = 'Oxford City Council HMO Register (Excel)'
        self.update_frequency = 'monthly'
        self._cached_data = None
        self._cache_timestamp = None
        
    def excel_date_to_datetime(self, excel_date):
        """Convert Excel serial date to Python datetime"""
        if pd.isna(excel_date) or excel_date == '':
            return None
        try:
            base_date = datetime(1900, 1, 1)
            return base_date + timedelta(days=float(excel_date) - 2)
        except (ValueError, TypeError):
            return None
    
    def clean_address_text(self, address: str) -> str:
        """Clean address text"""
        if not address or pd.isna(address):
            return ""
        
        cleaned = str(address).strip()
        cleaned = re.sub(r'\s+', ' ', cleaned)
        return cleaned
    
    def extract_postcode(self, address: str) -> Optional[str]:
        """Extract UK postcode from address"""
        if not address:
            return None
        
        postcode_pattern = r'([A-Z]{1,2}[0-9]{1,2}[A-Z]?\s?[0-9][A-Z]{2})'
        match = re.search(postcode_pattern, address.upper())
        
        if match:
            postcode = match.group(1)
            if len(postcode) >= 5 and ' ' not in postcode:
                postcode = postcode[:-3] + ' ' + postcode[-3:]
            return postcode.upper()
        
        return None
    
    def geocode_postcode_io(self, postcode: str) -> Tuple[Optional[float], Optional[float]]:
        """Geocode using postcodes.io API"""
        if not postcode:
            return None, None
            
        try:
            url = f"https://api.postcodes.io/postcodes/{postcode.replace(' ', '')}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 200 and data.get('result'):
                    result = data['result']
                    lat = result.get('latitude')
                    lon = result.get('longitude')
                    if lat and lon:
                        return float(lat), float(lon)
            
            return None, None
            
        except Exception as e:
            logger.debug(f"Postcodes.io error for {postcode}: {e}")
            return None, None
    
    def find_header_rows(self, df) -> List[int]:
        """Find all rows that contain headers (Case Number)"""
        header_rows = []
        
        for index, row in df.iterrows():
            if any(str(cell).strip() == "Case Number" for cell in row if pd.notna(cell)):
                header_rows.append(index)
        
        return header_rows
    
    def process_excel_with_header_skipping(self, excel_path: str = 'HMO Register Copy.xlsx', 
                                         enable_geocoding: bool = True, max_geocode: int = 1000) -> List[Dict]:
        """Process the Oxford Excel file with header skipping"""
        logger.info(f"Processing Oxford Excel file with header skipping: {excel_path}")
        
        try:
            # Read the entire Excel file as raw data
            df = pd.read_excel(excel_path, sheet_name=0, header=None)
            
            # Find all header rows
            header_rows = self.find_header_rows(df)
            logger.info(f"Found {len(header_rows)} header rows in Excel file")
            
            if not header_rows:
                raise ValueError("No header rows found in Excel file")
            
            # Use the first header as column names
            first_header_row = header_rows[0]
            column_names = df.iloc[first_header_row].tolist()
            
            # Find key column indices
            case_col_index = None
            location_col_index = None
            occupants_col_index = None
            units_col_index = None
            commenced_col_index = None
            expires_col_index = None
            
            for i, col_name in enumerate(column_names):
                if pd.notna(col_name):
                    col_lower = str(col_name).lower()
                    if 'case' in col_lower and 'number' in col_lower:
                        case_col_index = i
                    elif 'location' in col_lower:
                        location_col_index = i
                    elif 'occupants' in col_lower:
                        occupants_col_index = i
                    elif 'units' in col_lower:
                        units_col_index = i
                    elif 'commenced' in col_lower:
                        commenced_col_index = i
                    elif 'expires' in col_lower:
                        expires_col_index = i
            
            logger.info(f"Column indices: Case={case_col_index}, Location={location_col_index}, Expires={expires_col_index}")
            
            if case_col_index is None or location_col_index is None:
                raise ValueError("Could not find required columns (Case Number, Location)")
            
            # Collect all data rows (skip headers)
            all_data_rows = []
            
            for i, header_start in enumerate(header_rows):
                # Determine end of this block
                if i < len(header_rows) - 1:
                    block_end = header_rows[i + 1]
                else:
                    block_end = len(df)
                
                # Get data rows for this block (skip the header row itself)
                block_data = df.iloc[header_start + 1:block_end]
                
                # Filter out any remaining header-like rows
                for _, row in block_data.iterrows():
                    # Skip if first cell looks like a header or is empty
                    first_cell = str(row.iloc[case_col_index]).strip() if pd.notna(row.iloc[case_col_index]) else ""
                    if first_cell and first_cell != "Case Number" and first_cell != "nan":
                        all_data_rows.append(row.tolist())
            
            logger.info(f"Collected {len(all_data_rows)} total data rows from all blocks")
            
            # Create DataFrame with proper columns
            processed_df = pd.DataFrame(all_data_rows, columns=column_names)
            
            # Filter out rows where Case Number is empty
            processed_df = processed_df.dropna(subset=[column_names[case_col_index]])
            
            logger.info(f"Processing {len(processed_df)} valid HMO records...")
            
            # Process each record
            processed_records = []
            geocoding_count = 0
            current_date = datetime.now().date()
            
            for index, row in processed_df.iterrows():
                try:
                    case_number = str(row.iloc[case_col_index]).strip()
                    location = str(row.iloc[location_col_index]).strip()
                    
                    if not case_number or not location or case_number == 'nan':
                        continue
                    
                    # Clean address and extract postcode
                    cleaned_address = self.clean_address_text(location)
                    postcode = self.extract_postcode(cleaned_address)
                    
                    # Parse dates
                    licence_start = None
                    licence_expiry = None
                    
                    if commenced_col_index is not None and pd.notna(row.iloc[commenced_col_index]):
                        licence_start = self.excel_date_to_datetime(row.iloc[commenced_col_index])
                    
                    if expires_col_index is not None and pd.notna(row.iloc[expires_col_index]):
                        licence_expiry = self.excel_date_to_datetime(row.iloc[expires_col_index])
                    
                    # Determine licence status
                    licence_status = 'unknown'
                    if licence_expiry:
                        if licence_expiry.date() >= current_date:
                            licence_status = 'active'
                        else:
                            licence_status = 'expired'
                    
                    # Parse occupants and units
                    total_occupants = None
                    total_units = None
                    
                    if occupants_col_index is not None and pd.notna(row.iloc[occupants_col_index]):
                        try:
                            total_occupants = int(float(row.iloc[occupants_col_index]))
                        except (ValueError, TypeError):
                            pass
                    
                    if units_col_index is not None and pd.notna(row.iloc[units_col_index]):
                        try:
                            total_units = int(float(row.iloc[units_col_index]))
                        except (ValueError, TypeError):
                            pass
                    
                    # Geocode if enabled and within limit
                    lat, lon = None, None
                    geocoded = False
                    
                    if enable_geocoding and geocoding_count < max_geocode and postcode:
                        lat, lon = self.geocode_postcode_io(postcode)
                        if lat and lon:
                            geocoded = True
                            geocoding_count += 1
                            
                            if geocoding_count % 100 == 0:
                                logger.info(f"Geocoded {geocoding_count} addresses...")
                            
                            time.sleep(0.2)  # Rate limiting
                    
                    # Calculate data quality score
                    quality_score = 0.0
                    if cleaned_address and len(cleaned_address) > 10:
                        quality_score += 0.2
                    if postcode:
                        quality_score += 0.2
                    if geocoded:
                        quality_score += 0.3
                    if licence_expiry:
                        quality_score += 0.2
                    if total_occupants:
                        quality_score += 0.1
                    
                    record = {
                        'id': case_number,
                        'case_number': case_number,
                        'source': 'oxford_excel',
                        'city': 'oxford',
                        'address': cleaned_address,
                        'postcode': postcode,
                        'latitude': lat,
                        'longitude': lon,
                        'geocoded': geocoded,
                        'total_occupants': total_occupants,
                        'total_units': total_units,
                        'licence_status': licence_status,
                        'licence_start_date': licence_start.isoformat() if licence_start else None,
                        'licence_expiry_date': licence_expiry.isoformat() if licence_expiry else None,
                        'data_quality_score': min(quality_score, 1.0),
                        'processing_notes': f'Imported from Oxford Excel on {datetime.now().strftime("%Y-%m-%d")}',
                        'last_updated': datetime.now().isoformat(),
                        'data_source_url': None
                    }
                    
                    processed_records.append(record)
                    
                    # Progress update
                    if (len(processed_records)) % 1000 == 0:
                        logger.info(f"Processed {len(processed_records)} records...")
                    
                except Exception as e:
                    logger.error(f"Error processing row {index}: {e}")
                    continue
            
            logger.info(f"Successfully processed {len(processed_records)} Oxford records, geocoded {geocoding_count}")
            return processed_records
            
        except Exception as e:
            logger.error(f"Error processing Excel file: {e}")
            raise
    
    def get_hmo_data(self, force_refresh: bool = False, enable_geocoding: bool = True) -> List[Dict]:
        """Get Oxford HMO data in the unified format"""
        
        # Use cached data if available and not forcing refresh
        if not force_refresh and self._cached_data and self._cache_timestamp:
            cache_age = datetime.now() - self._cache_timestamp
            if cache_age.total_seconds() < 7200:  # 2 hour cache
                logger.info(f"Using cached Oxford data ({len(self._cached_data)} records)")
                return self._cached_data
        
        try:
            # Process the Excel file with header skipping
            data = self.process_excel_with_header_skipping('HMO Register Copy.xlsx', enable_geocoding, max_geocode=500)
            
            # Cache the results
            self._cached_data = data
            self._cache_timestamp = datetime.now()
            
            return data
            
        except FileNotFoundError:
            logger.error("Oxford Excel file (HMO Register Copy.xlsx) not found")
            return []
        except Exception as e:
            logger.error(f"Error reading Oxford Excel data: {e}")
            return []
    
    def get_statistics(self) -> Dict:
        """Get Oxford HMO statistics"""
        try:
            data = self.get_hmo_data(enable_geocoding=False)  # Don't geocode for stats
            
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
            geocoded_records = sum(1 for r in data if r['geocoded'])
            active_licences = sum(1 for r in data if r['licence_status'] == 'active')
            expired_licences = sum(1 for r in data if r['licence_status'] == 'expired')
            unknown_status = sum(1 for r in data if r['licence_status'] == 'unknown')
            
            avg_quality = sum(r['data_quality_score'] for r in data) / total_records
            
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
            logger.error(f"Error getting Oxford statistics: {e}")
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
    
    def compare_with_old_data(self, old_csv_path: str = None) -> Dict:
        """Compare current Excel data with old CSV data to find renewed licenses"""
        try:
            current_data = self.get_hmo_data(enable_geocoding=False)
            
            # Create lookup by case number
            current_lookup = {record['case_number']: record for record in current_data}
            
            # Load old data if available
            old_data = []
            if old_csv_path:
                try:
                    df = pd.read_csv(old_csv_path)
                    old_data = df.to_dict('records')
                except Exception as e:
                    logger.warning(f"Could not load old data: {e}")
            
            # Analyze renewal status
            renewed_licenses = []
            still_expired = []
            new_properties = []
            
            for record in current_data:
                case_number = record['case_number']
                status = record['licence_status']
                
                # Find matching old record
                old_record = None
                for old in old_data:
                    if old.get('Case Number') == case_number:
                        old_record = old
                        break
                
                if old_record:
                    # Property existed in old data
                    if status == 'active':
                        renewed_licenses.append(record)
                    elif status == 'expired':
                        still_expired.append(record)
                else:
                    # New property not in old data
                    new_properties.append(record)
            
            return {
                'total_current': len(current_data),
                'total_old': len(old_data),
                'renewed_count': len(renewed_licenses),
                'still_expired_count': len(still_expired),
                'new_properties_count': len(new_properties),
                'renewed_licenses': renewed_licenses[:10],  # Sample
                'still_expired': still_expired[:10],  # Sample
                'new_properties': new_properties[:10],  # Sample
                'analysis_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error comparing data: {e}")
            return {'error': str(e)}
    
    def export_processed_csv(self, output_file: str = None) -> str:
        """Export current data to CSV for backup/analysis"""
        try:
            data = self.get_hmo_data(enable_geocoding=False)
            
            if not output_file:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f'oxford_hmo_excel_export_{timestamp}.csv'
            
            df = pd.DataFrame(data)
            df.to_csv(output_file, index=False)
            
            logger.info(f"Exported {len(data)} records to {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Error exporting CSV: {e}")
            raise