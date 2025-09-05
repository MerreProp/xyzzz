# hmo_registry/cities/vale_of_white_horse.py
"""
Vale of White Horse District Council HMO Data Source
Serves data from the database (already loaded by PDF extraction)
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from ..base_data_source import BaseHMODataSource
from database import SessionLocal
from ..database_models import HMORegistry

logger = logging.getLogger(__name__)

class ValeOfWhiteHorseHMOData(BaseHMODataSource):
    """Vale of White Horse HMO registry data source"""
    
    def __init__(self):
        super().__init__('vale_of_white_horse')
        self.display_name = 'Vale of White Horse District Council'
        self.source_url = 'https://www.whitehorsedc.gov.uk/'
    
    def load_raw_data(self) -> List[Dict]:
        """Load Vale of White Horse HMO data from database"""
        
        logger.info(f"Loading {self.city_name} HMO data from database...")
        
        db = SessionLocal()
        try:
            # Query database for Vale of White Horse records
            records = db.query(HMORegistry).filter(
                HMORegistry.city == self.city_name
            ).all()
            
            logger.info(f"Found {len(records)} {self.city_name} records in database")
            
            # Convert to list of dicts
            raw_data = []
            for record in records:
                data = {
                    'case_number': record.case_number,
                    'raw_address': record.raw_address,
                    'postcode': record.postcode,
                    'latitude': float(record.latitude) if record.latitude else None,
                    'longitude': float(record.longitude) if record.longitude else None,
                    'geocoded': record.geocoded,
                    'total_occupants': record.total_occupants,
                    'total_units': record.total_units,
                    'licence_status': record.licence_status,
                    'licence_start_date': record.licence_start_date,
                    'licence_expiry_date': record.licence_expiry_date,
                    'processing_notes': record.processing_notes,
                    'data_quality_score': float(record.data_quality_score) if record.data_quality_score else 0.9,
                    'created_at': record.created_at,
                    'updated_at': record.updated_at
                }
                raw_data.append(data)
            
            return raw_data
            
        except Exception as e:
            logger.error(f"Error loading {self.city_name} data from database: {e}")
            return []
        finally:
            db.close()
    
    def transform_data(self, raw_data: List[Dict]) -> List[Dict]:
        """Transform database data to API format"""
        
        logger.info(f"Transforming {len(raw_data)} {self.city_name} records...")
        
        transformed_records = []
        
        for record in raw_data:
            try:
                # Data is already in good format from database, just standardize
                transformed_record = {
                    'case_number': record['case_number'],
                    'address': record['raw_address'],
                    'postcode': record['postcode'],
                    'latitude': record['latitude'],
                    'longitude': record['longitude'],
                    'geocoded': record['geocoded'],
                    'total_occupants': record['total_occupants'],
                    'licence_status': record['licence_status'],
                    'licence_start_date': record['licence_start_date'].isoformat() if record['licence_start_date'] else None,
                    'licence_expiry_date': record['licence_expiry_date'].isoformat() if record['licence_expiry_date'] else None,
                    'data_quality_score': record['data_quality_score'],
                    'council': 'Vale of White Horse',
                    'source': self.display_name,
                    'last_updated': record['updated_at'].isoformat() if record['updated_at'] else None
                }
                
                transformed_records.append(transformed_record)
                
            except Exception as e:
                logger.warning(f"Error transforming {self.city_name} record: {e}")
                continue
        
        logger.info(f"Transformed {len(transformed_records)} {self.city_name} records")
        return transformed_records
