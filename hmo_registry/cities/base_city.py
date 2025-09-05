# hmo_registry/cities/base_city.py
"""
Base class for HMO registry data sources
Defines the interface that all city implementations must follow
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class BaseHMODataSource(ABC):
    """Abstract base class for HMO registry data sources"""
    
    def __init__(self, city_name: str, cache_duration: int = 3600):
        self.city_name = city_name.lower()
        self.cache_duration = cache_duration
        self._cached_data = None
        self._cache_timestamp = None
    
    @abstractmethod
    def fetch_raw_data(self) -> List[Dict]:
        """Fetch raw data from the city's data source"""
        pass
    
    @abstractmethod
    def process_record(self, record: Dict, enable_geocoding: bool = True) -> Optional[Dict]:
        """Process a single record into standard format"""
        pass
    
    def get_hmo_data(self, force_refresh: bool = False, enable_geocoding: bool = True) -> List[Dict]:
        """Get processed HMO data with caching"""
        
        # Check cache first
        if (not force_refresh and self._cached_data and self._cache_timestamp and 
            (datetime.now() - self._cache_timestamp).seconds < self.cache_duration):
            logger.info(f"Using cached {self.city_name} HMO data")
            return self._cached_data
        
        try:
            logger.info(f"Fetching fresh {self.city_name} HMO data...")
            
            # Fetch raw data
            raw_data = self.fetch_raw_data()
            
            # Process each record
            processed_data = []
            geocoded_count = 0
            
            for record in raw_data:
                processed_record = self.process_record(record, enable_geocoding)
                if processed_record:
                    processed_data.append(processed_record)
                    if processed_record.get('geocoded'):
                        geocoded_count += 1
            
            logger.info(f"Processed {len(processed_data)} {self.city_name} records ({geocoded_count} geocoded)")
            
            # Cache the results
            self._cached_data = processed_data
            self._cache_timestamp = datetime.now()
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Error fetching {self.city_name} HMO data: {e}")
            return self._cached_data if self._cached_data else []
    
    def get_statistics(self) -> Dict:
        """Get statistics about the HMO data"""
        data = self.get_hmo_data()
        
        if not data:
            return {'error': 'No data available'}
        
        # Calculate statistics
        total_records = len(data)
        geocoded_records = sum(1 for record in data if record.get('geocoded'))
        active_licences = sum(1 for record in data if record.get('licence_status') == 'active')
        expired_licences = sum(1 for record in data if record.get('licence_status') == 'expired')
        
        # Calculate average data quality
        quality_scores = [record.get('data_quality_score', 0) for record in data]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        return {
            'total_records': total_records,
            'geocoded_records': geocoded_records,
            'geocoding_success_rate': round((geocoded_records / total_records * 100), 1) if total_records > 0 else 0,
            'active_licences': active_licences,
            'expired_licences': expired_licences,
            'unknown_status': len(data) - active_licences - expired_licences,
            'average_data_quality': round(avg_quality, 2),
            'last_updated': self._cache_timestamp.isoformat() if self._cache_timestamp else None
        }
    
    def _safe_int(self, value) -> Optional[int]:
        """Safely convert value to int"""
        if not value or str(value).strip() == '' or str(value).lower() == 'nan':
            return None
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return None
    
    def _safe_date(self, value, dayfirst: bool = True):
        """Safely convert value to date"""
        if not value or str(value).strip() == '' or str(value).lower() == 'nan':
            return None
        try:
            import pandas as pd
            return pd.to_datetime(value, dayfirst=dayfirst).date()
        except (ValueError, TypeError):
            return None
    
    def _calculate_confidence(self, record: Dict, coords: Optional[Tuple], postcode: Optional[str]) -> float:
        """Calculate confidence score for a record"""
        score = 0.0
        
        # Has coordinates
        if coords:
            score += 0.4
        
        # Has postcode
        if postcode:
            score += 0.3
        
        # Has occupancy info
        if self._safe_int(record.get('Total Number Occupants')):
            score += 0.2
        
        # Has unit info
        if self._safe_int(record.get('Total Number Units')):
            score += 0.1
        
        # Has valid dates
        if self._safe_date(record.get('Licence Expires')):
            score += 0.1
        
        return min(score, 1.0)
    
    def _generate_processing_notes(self, record: Dict, coords: Optional[Tuple], postcode: Optional[str]) -> str:
        """Generate processing notes"""
        notes = []
        
        if not coords:
            notes.append("No coordinates found")
        if not postcode:
            notes.append("No postcode extracted")
        if not self._safe_int(record.get('Total Number Occupants')):
            notes.append("Missing occupant count")
        
        return "; ".join(notes) if notes else "Processed successfully"