# hmo_registry/performance_config.py
"""
Simplified performance configuration - integrated into registry_endpoints.py
This file is kept for compatibility but functionality moved to main endpoints
"""

import asyncio
from typing import Dict
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class HMOAPIOptimization:
    """
    Simplified performance optimization
    Note: Most functionality has been moved to HMORegistryManager in registry_endpoints.py
    """
    
    def __init__(self):
        self.cache_duration = timedelta(hours=1)
        self.memory_cache = {}
        self.last_cache_clear = datetime.now()
        logger.info("🚀 HMO API Optimization initialized (simplified mode)")
        
    async def get_optimized_hmo_data(self, city: str, enable_geocoding: bool = False) -> Dict:
        """
        Get optimized HMO data - delegates to main manager
        This method is deprecated - use HMORegistryManager directly
        """
        logger.warning("⚠️ Using deprecated optimization method - consider using HMORegistryManager directly")
        
        # Import here to avoid circular imports
        from .registry_endpoints import hmo_manager, HMORegistryCity
        
        try:
            # Convert string to enum
            city_enum = None
            for city_option in HMORegistryCity:
                if city_option.value == city:
                    city_enum = city_option
                    break
            
            if not city_enum:
                return {"error": f"Unknown city: {city}", "success": False}
            
            return await hmo_manager.get_city_data(city_enum, enable_geocoding)
            
        except Exception as e:
            logger.error(f"❌ Error in deprecated optimization method: {e}")
            return {"error": str(e), "success": False}
    
    def clear_cache(self):
        """Clear cache - delegates to main manager"""
        from .registry_endpoints import hmo_manager
        hmo_manager.clear_cache()
        self.last_cache_clear = datetime.now()
        logger.info("🗑️ Cache cleared via optimization wrapper")
    
    def get_cache_status(self) -> Dict:
        """Get cache status - delegates to main manager"""
        from .registry_endpoints import hmo_manager
        return {
            "cached_cities": list(hmo_manager.cache.keys()),
            "cache_size": len(hmo_manager.cache),
            "last_cleared": self.last_cache_clear.isoformat(),
            "cache_duration_hours": self.cache_duration.total_seconds() / 3600,
            "note": "Using simplified optimization - consider using HMORegistryManager directly"
        }

# Keep for backward compatibility
def create_optimizer():
    """Factory function for creating optimizer"""
    return HMOAPIOptimization()