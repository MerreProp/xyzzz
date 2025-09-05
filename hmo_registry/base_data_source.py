# hmo_registry/base_data_source.py
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
    
    def __init__(self, city_name: str = None, cache_duration: int = 3600):
        self.city_name = city_name.lower() if city_name else 'unknown'
        self.cache_duration = cache_duration
        self._cached_data = None
        self._cache_timestamp = None
        self.display_name = city_name or 'Unknown City'
    
    def _is_cache_valid(self) -> bool:
        """Check if cached data is still valid"""
        if not self._cached_data or not self._cache_timestamp:
            return False
        
        cache_age = datetime.now() - self._cache_timestamp
        return cache_age.total_seconds() < self.cache_duration
    
    def load_raw_data(self) -> List[Dict]:
        """Load raw data from data source - to be implemented by subclasses"""
        return []
    
    def transform_data(self, raw_data: List[Dict]) -> List[Dict]:
        """Transform raw data to standard format - to be implemented by subclasses"""
        return raw_data
    
    def get_hmo_data(self, force_refresh: bool = False, enable_geocoding: bool = True) -> List[Dict]:
        """Get processed HMO data with caching"""
        
        # Check cache first
        if not force_refresh and self._is_cache_valid():
            logger.info(f"Using cached {self.city_name} HMO data ({len(self._cached_data)} records)")
            return self._cached_data
        
        try:
            logger.info(f"Loading fresh {self.city_name} HMO data...")
            
            # Load raw data
            raw_data = self.load_raw_data()
            
            if not raw_data:
                logger.warning(f"No raw data loaded for {self.city_name}")
                return []
            
            # Transform data
            processed_data = self.transform_data(raw_data)
            
            # Cache the results
            self._cached_data = processed_data
            self._cache_timestamp = datetime.now()
            
            geocoded_count = sum(1 for record in processed_data if record.get('geocoded', False))
            logger.info(f"Processed {len(processed_data)} {self.city_name} records ({geocoded_count} geocoded)")
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Error loading {self.city_name} HMO data: {e}")
            return self._cached_data if self._cached_data else []
    
    def get_statistics(self) -> Dict:
        """Get statistics about the HMO data"""
        try:
            data = self.get_hmo_data(enable_geocoding=False)  # Don't geocode for stats
            
            if not data:
                return self._empty_stats()
            
            # Calculate statistics
            total_records = len(data)
            geocoded_records = sum(1 for record in data if record.get('geocoded', False))
            active_licences = sum(1 for record in data if record.get('licence_status') == 'active')
            expired_licences = sum(1 for record in data if record.get('licence_status') == 'expired')
            unknown_status = total_records - active_licences - expired_licences
            
            # Calculate average data quality
            quality_scores = [record.get('data_quality_score', 0.0) for record in data if record.get('data_quality_score')]
            avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
            
            return {
                'total_records': total_records,
                'geocoded_records': geocoded_records,
                'geocoding_success_rate': round((geocoded_records / total_records * 100), 1) if total_records > 0 else 0.0,
                'active_licences': active_licences,
                'expired_licences': expired_licences,
                'unknown_status': unknown_status,
                'average_data_quality': round(avg_quality, 2),
                'last_updated': self._cache_timestamp.isoformat() if self._cache_timestamp else datetime.now().isoformat(),
                'data_source': self.display_name,
                'city': self.city_name
            }
            
        except Exception as e:
            logger.error(f"Error getting statistics for {self.city_name}: {e}")
            return self._empty_stats()
    
    def _empty_stats(self) -> Dict:
        """Return empty statistics structure"""
        return {
            'total_records': 0,
            'geocoded_records': 0,
            'geocoding_success_rate': 0.0,
            'active_licences': 0,
            'expired_licences': 0,
            'unknown_status': 0,
            'average_data_quality': 0.0,
            'last_updated': datetime.now().isoformat(),
            'data_source': self.display_name,
            'city': self.city_name,
            'error': 'No data available'
        }
    
    def _safe_int(self, value, default: int = 0) -> int:
        """Safely convert value to integer"""
        if value is None or str(value).strip() in ['', 'nan', 'None']:
            return default
        try:
            return int(float(str(value)))
        except (ValueError, TypeError):
            return default
    
    def _safe_float(self, value, default: float = 0.0) -> float:
        """Safely convert value to float"""
        if value is None or str(value).strip() in ['', 'nan', 'None']:
            return default
        try:
            return float(str(value))
        except (ValueError, TypeError):
            return default
    
    def _safe_str(self, value, default: str = '') -> str:
        """Safely convert value to string"""
        if value is None:
            return default
        return str(value).strip()
    
    def _determine_licence_status(self, expiry_date_str: str) -> str:
        """Determine licence status from expiry date string"""
        if not expiry_date_str or str(expiry_date_str).strip() in ['', 'nan', 'None']:
            return 'unknown'
        
        try:
            # Try different date formats
            from dateutil import parser
            expiry_date = parser.parse(str(expiry_date_str))
            return 'active' if expiry_date >= datetime.now() else 'expired'
        except Exception:
            return 'unknown'
    
    def _calculate_data_quality_score(self, record: Dict) -> float:
        """Calculate data quality score (0.0 to 1.0)"""
        score = 0.0
        checks = 0
        
        # Check address
        if record.get('address') or record.get('raw_address'):
            score += 0.2
        checks += 1
        
        # Check postcode
        if record.get('postcode'):
            score += 0.2
        checks += 1
        
        # Check geocoding
        if record.get('geocoded') and record.get('latitude') and record.get('longitude'):
            score += 0.2
        checks += 1
        
        # Check licence info
        if record.get('licence_status') and record.get('licence_status') != 'unknown':
            score += 0.2
        checks += 1
        
        # Check occupancy info
        if record.get('total_occupants') or record.get('total_units'):
            score += 0.2
        checks += 1
        
        return round(score, 2)