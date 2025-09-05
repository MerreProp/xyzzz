"""
Cherwell District Council - Kidlington HMO Data Source (Database Version)
"""

from typing import Dict, List
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from ..base_data_source import BaseHMODataSource
from ..database_models import HMORegistry
from database import SessionLocal

logger = logging.getLogger(__name__)

class CherwellKidlingtonHMOMapData(BaseHMODataSource):
    """
    Cherwell District Council - Kidlington HMO Data Source
    Reads data from the HMORegistry database table
    """
    
    def __init__(self):
        super().__init__('cherwell_kidlington')  # ✅ CORRECT CITY
        self.display_name = "Kidlington (Cherwell District)"  # ✅ CORRECT NAME
        
    def load_raw_data(self) -> List[Dict]:
        """Load raw HMO data from database"""
        db = SessionLocal()
        try:
            records = db.query(HMORegistry).filter(
                HMORegistry.city == 'cherwell_kidlington'
            ).all()
            
            logger.info(f"Loaded {len(records)} Kidlington records from database")
            return [self._database_record_to_dict(record) for record in records]
            
        except Exception as e:
            logger.error(f"Error loading Kidlington data: {e}")
            return []
        finally:
            db.close()
    
    def transform_data(self, raw_data: List[Dict]) -> List[Dict]:
        """Transform database records to API format"""
        return [self._transform_record(record) for record in raw_data]
    
    def _database_record_to_dict(self, record: HMORegistry) -> Dict:
        """Convert database record to dictionary"""
        return {
            'id': str(record.id),
            'case_number': record.case_number,
            'source': record.source,
            'city': record.city,
            'raw_address': record.raw_address,
            'postcode': record.postcode,
            'latitude': float(record.latitude) if record.latitude else None,
            'longitude': float(record.longitude) if record.longitude else None,
            'geocoded': record.geocoded,
            'geocoding_source': record.geocoding_source,
            'total_occupants': record.total_occupants,
            'total_units': record.total_units,
            'licence_status': record.licence_status,
            'licence_start_date': record.licence_start_date.isoformat() if record.licence_start_date else None,
            'licence_expiry_date': record.licence_expiry_date.isoformat() if record.licence_expiry_date else None,
            'data_quality_score': float(record.data_quality_score) if record.data_quality_score else 0.0,
            'processing_notes': record.processing_notes or '',
            'data_source_url': record.data_source_url,
            'created_at': record.created_at.isoformat() if record.created_at else None,
            'updated_at': record.updated_at.isoformat() if record.updated_at else None
        }
    
    def _transform_record(self, record: Dict) -> Dict:
        """Transform record to API format"""
        return {
            'id': f"cherwell_kidlington_{record.get('case_number', record.get('id', ''))}",
            'case_number': record.get('case_number', ''),
            'source': 'cherwell_district_council',
            'city': 'cherwell_kidlington',
            'address': record.get('raw_address', ''),
            'postcode': record.get('postcode'),
            'latitude': record.get('latitude'),
            'longitude': record.get('longitude'),
            'geocoded': record.get('geocoded', False),
            'total_occupants': record.get('total_occupants'),
            'total_units': record.get('total_units'),
            'licence_status': record.get('licence_status', 'unknown'),
            'licence_start_date': record.get('licence_start_date'),
            'licence_expiry_date': record.get('licence_expiry_date'),
            'data_quality_score': record.get('data_quality_score', 0.0),
            'processing_notes': record.get('processing_notes', ''),
            'last_updated': record.get('updated_at', datetime.now().isoformat()),
            'data_source_url': record.get('data_source_url')
        }
    
    def get_statistics(self) -> Dict:
        """Get statistics from database"""
        db = SessionLocal()
        try:
            total_records = db.query(HMORegistry).filter(
                HMORegistry.city == 'cherwell_kidlington'
            ).count()
            
            if total_records == 0:
                return self._empty_stats()
            
            geocoded_records = db.query(HMORegistry).filter(
                and_(
                    HMORegistry.city == 'cherwell_kidlington',
                    HMORegistry.geocoded == True
                )
            ).count()
            
            active_licences = db.query(HMORegistry).filter(
                and_(
                    HMORegistry.city == 'cherwell_kidlington',
                    HMORegistry.licence_status == 'active'
                )
            ).count()
            
            expired_licences = db.query(HMORegistry).filter(
                and_(
                    HMORegistry.city == 'cherwell_kidlington',
                    HMORegistry.licence_status == 'expired'
                )
            ).count()
            
            unknown_status = total_records - active_licences - expired_licences
            
            # Get average data quality
            avg_quality = db.query(func.avg(HMORegistry.data_quality_score)).filter(
                HMORegistry.city == 'cherwell_kidlington'
            ).scalar() or 0
            
            # Get last updated
            last_updated = db.query(func.max(HMORegistry.updated_at)).filter(
                HMORegistry.city == 'cherwell_kidlington'
            ).scalar()
            
            return {
                'total_records': total_records,
                'geocoded_records': geocoded_records,
                'geocoding_success_rate': round((geocoded_records / total_records * 100), 1) if total_records > 0 else 0.0,
                'active_licences': active_licences,
                'expired_licences': expired_licences,
                'unknown_status': unknown_status,
                'average_data_quality': round(float(avg_quality), 2),
                'last_updated': last_updated.isoformat() if last_updated else datetime.now().isoformat(),
                'data_source': self.display_name,
                'city': self.city_name
            }
            
        except Exception as e:
            logger.error(f"Error getting Kidlington statistics: {e}")
            return self._empty_stats()
        finally:
            db.close()