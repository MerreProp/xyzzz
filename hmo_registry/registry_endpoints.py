# File: hmo_registry/registry_endpoints.py
"""
Corrected HMO Registry API Endpoints with Cherwell District Support
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Optional
import logging
import asyncio
from datetime import datetime

from .registry_models import (
    HMORegistryCity, HMOProperty, HMORegistryResponse, 
    HMORegistryStats, HMOCityInfo, CITY_METADATA
)

# Import existing data sources
try:
    from .cities.oxford_with_database import OxfordHMOMapData
except ImportError:
    from .cities.oxford import OxfordHMOMapData

try:
    from .cities.swindon import SwindonHMOMapData
except ImportError:
    SwindonHMOMapData = None

# Import new Cherwell data sources
from .cities.cherwell_banbury import CherwellBanburyHMOMapData
from .cities.cherwell_bicester import CherwellBicesterHMOMapData  
from .cities.cherwell_kidlington import CherwellKidlingtonHMOMapData
from .cities.vale_of_white_horse import ValeOfWhiteHorseHMOData
from .cities.south_oxfordshire import SouthOxfordshireHMOData

logger = logging.getLogger(__name__)

class HMORegistryManager:
    """Updated manager for multiple HMO registry data sources including Cherwell"""
    
    def __init__(self):
        self.data_sources = {
            # Existing sources
            HMORegistryCity.OXFORD: OxfordHMOMapData(),
        }
        
        # Add Swindon if available
        if SwindonHMOMapData:
            self.data_sources[HMORegistryCity.SWINDON] = SwindonHMOMapData()
            
        # Add Cherwell sources
        self.data_sources.update({
            HMORegistryCity.CHERWELL_BANBURY: CherwellBanburyHMOMapData(),
            HMORegistryCity.CHERWELL_BICESTER: CherwellBicesterHMOMapData(),
            HMORegistryCity.CHERWELL_KIDLINGTON: CherwellKidlingtonHMOMapData(),
            HMORegistryCity.VALE_OF_WHITE_HORSE: ValeOfWhiteHorseHMOData(),
            HMORegistryCity.SOUTH_OXFORDSHIRE: SouthOxfordshireHMOData(),
        })
        
        self.city_metadata = CITY_METADATA
        
        # Simple memory cache
        self.cache = {}
        self.cache_timeout = 3600  # 1 hour
    
    async def get_available_cities(self) -> List[HMOCityInfo]:
        """Get list of available HMO registry cities"""
        cities = []
        for city_code, metadata in self.city_metadata.items():
            if city_code not in self.data_sources:
                continue
                
            try:
                # Get basic stats for each city
                data_source = self.data_sources[city_code]
                stats = data_source.get_statistics()
                
                cities.append(HMOCityInfo(
                    code=city_code.value,
                    name=metadata["name"],
                    full_name=metadata["full_name"],
                    region=metadata["region"],
                    data_source=metadata["data_source"],
                    update_frequency=metadata["update_frequency"],
                    available=True,
                    total_records=stats.get("total_records", 0),
                    geocoded_records=stats.get("geocoded_records", 0),
                    last_updated=stats.get("last_updated")
                ))
            except Exception as e:
                logger.warning(f"Error getting stats for {city_code.value}: {e}")
                cities.append(HMOCityInfo(
                    code=city_code.value,
                    name=metadata["name"],
                    full_name=metadata["full_name"],
                    region=metadata["region"],
                    data_source=metadata["data_source"],
                    update_frequency=metadata["update_frequency"],
                    available=False,
                    error=str(e)
                ))
        
        return cities
    
    def _get_cache_key(self, city: str, enable_geocoding: bool) -> str:
        """Generate cache key"""
        return f"{city}_geocoding_{enable_geocoding}"
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache is valid"""
        if cache_key not in self.cache:
            return False
        
        cache_entry = self.cache[cache_key]
        age = datetime.now().timestamp() - cache_entry['timestamp']
        return age < self.cache_timeout
    
    async def get_city_data(self, city: HMORegistryCity, 
                           enable_geocoding: bool = True,
                           force_refresh: bool = False) -> Dict:
        """Get HMO data for a specific city"""
        
        cache_key = self._get_cache_key(city.value, enable_geocoding)
        
        # Check cache first
        if not force_refresh and self._is_cache_valid(cache_key):
            logger.info(f"📦 Returning cached data for {city.value}")
            return self.cache[cache_key]['data']
        
        if city not in self.data_sources:
            return {
                "success": False,
                "city": city.value,
                "error": f"HMO registry data not available for {city.value}",
                "data": [],
                "total_count": 0,
                "geocoded_count": 0
            }
        
        start_time = datetime.now()
        
        try:
            data_source = self.data_sources[city]
            
            # Handle both sync and async data sources
            if hasattr(data_source, 'get_hmo_data') and callable(data_source.get_hmo_data):
                try:
                    # Try async first
                    raw_data = await data_source.get_hmo_data(enable_geocoding=enable_geocoding, force_refresh=force_refresh)
                except TypeError:
                    # Fallback to sync
                    raw_data = data_source.get_hmo_data(force_refresh, enable_geocoding)
            else:
                raw_data = []
            
            # Process data
            geocoded_count = sum(1 for item in raw_data if item.get('geocoded', False))
            
            # Get statistics
            try:
                stats = data_source.get_statistics()
            except Exception as e:
                logger.warning(f"Error getting stats for {city.value}: {e}")
                stats = {}
            
            result = {
                "success": True,
                "city": city.value,
                "data": raw_data,
                "total_count": len(raw_data),
                "geocoded_count": geocoded_count,
                "statistics": stats,
                "processing_time": (datetime.now() - start_time).total_seconds(),
                "cached": False,
                "timestamp": datetime.now().isoformat()
            }
            
            # Cache the result
            self.cache[cache_key] = {
                'data': result,
                'timestamp': datetime.now().timestamp()
            }
            
            logger.info(f"✅ Loaded {len(raw_data)} properties for {city.value} in {result['processing_time']:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error loading data for {city.value}: {e}")
            return {
                "success": False,
                "city": city.value,
                "error": str(e),
                "data": [],
                "total_count": 0,
                "geocoded_count": 0,
                "processing_time": (datetime.now() - start_time).total_seconds()
            }
    
    async def get_multiple_cities_data(self, cities: List[HMORegistryCity],
                                     enable_geocoding: bool = True) -> Dict[str, Dict]:
        """Get HMO data for multiple cities"""
        results = {}
        
        for city in cities:
            try:
                results[city.value] = await self.get_city_data(city, enable_geocoding)
            except Exception as e:
                results[city.value] = {
                    "success": False,
                    "city": city.value,
                    "error": str(e),
                    "data": [],
                    "total_count": 0,
                    "geocoded_count": 0
                }
        
        return results
    
    def clear_cache(self):
        """Clear the memory cache"""
        self.cache.clear()
        logger.info("🗑️ Memory cache cleared")

# Initialize manager
hmo_manager = HMORegistryManager()

# Create router
hmo_router = APIRouter(prefix="/api/hmo-registry", tags=["HMO Registry"])

@hmo_router.get("/cities")
async def get_available_hmo_cities():
    """Get list of cities with available HMO registry data"""
    return await hmo_manager.get_available_cities()

@hmo_router.get("/cities/{city}")
async def get_city_hmo_data(
    city: HMORegistryCity,
    enable_geocoding: bool = Query(True, description="Enable geocoding for addresses"),
    force_refresh: bool = Query(False, description="Force refresh of cached data")
):
    """Get HMO registry data for a specific city"""
    return await hmo_manager.get_city_data(city, enable_geocoding, force_refresh)

@hmo_router.get("/cities/{city}/fast")
async def get_city_hmo_data_fast(
    city: HMORegistryCity,
    enable_geocoding: bool = Query(False, description="Enable geocoding (slower)")
):
    """Fast endpoint that prioritizes speed over geocoding accuracy"""
    try:
        result = await asyncio.wait_for(
            hmo_manager.get_city_data(city, enable_geocoding=enable_geocoding),
            timeout=30.0
        )
        result['fast_mode'] = True
        return result
    except asyncio.TimeoutError:
        return {
            "success": False,
            "city": city.value,
            "error": "Request timeout - try with geocoding disabled",
            "fast_mode": True,
            "data": [],
            "total_count": 0,
            "geocoded_count": 0
        }

@hmo_router.get("/cities/{city}/statistics")
async def get_city_hmo_statistics(city: HMORegistryCity):
    """Get statistics for a city's HMO registry"""
    if city not in hmo_manager.data_sources:
        raise HTTPException(
            status_code=404,
            detail=f"HMO registry data not available for {city.value}"
        )
    
    try:
        data_source = hmo_manager.data_sources[city]
        stats = data_source.get_statistics()
        
        return {
            "city": city.value,
            "total_records": stats.get("total_records", 0),
            "geocoded_records": stats.get("geocoded_records", 0),
            "geocoding_success_rate": stats.get("geocoding_success_rate", 0.0),
            "active_licences": stats.get("active_licences", 0),
            "expired_licences": stats.get("expired_licences", 0),
            "unknown_status": stats.get("unknown_status", 0),
            "average_data_quality": stats.get("average_data_quality", 0.0),
            "last_updated": stats.get("last_updated")
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting statistics for {city.value}: {str(e)}"
        )

@hmo_router.post("/cities/{city}/refresh")
async def refresh_city_hmo_data(city: HMORegistryCity):
    """Refresh cached HMO data for a specific city"""
    return await get_city_hmo_data(city, force_refresh=True)

@hmo_router.get("/bulk")
async def get_multiple_cities_hmo_data(
    cities: List[HMORegistryCity] = Query(..., description="List of cities to fetch"),
    enable_geocoding: bool = Query(True, description="Enable geocoding for addresses")
):
    """Get HMO data for multiple cities at once"""
    return await hmo_manager.get_multiple_cities_data(cities, enable_geocoding)

@hmo_router.get("/cherwell/summary")
async def get_cherwell_summary():
    """Get summary of all Cherwell District HMO data"""
    cherwell_cities = [
        HMORegistryCity.CHERWELL_BANBURY,
        HMORegistryCity.CHERWELL_BICESTER,
        HMORegistryCity.CHERWELL_KIDLINGTON
    ]
    
    results = await hmo_manager.get_multiple_cities_data(cherwell_cities, enable_geocoding=False)
    
    total_properties = sum(result.get('total_count', 0) for result in results.values() if result.get('success', False))
    total_geocoded = sum(result.get('geocoded_count', 0) for result in results.values() if result.get('success', False))
    
    return {
        "district": "Cherwell District Council",
        "total_properties": total_properties,
        "total_geocoded": total_geocoded,
        "locations": {
            "banbury": results.get("cherwell_banbury", {}).get('total_count', 0),
            "bicester": results.get("cherwell_bicester", {}).get('total_count', 0),
            "kidlington": results.get("cherwell_kidlington", {}).get('total_count', 0)
        },
        "breakdown_percentage": {
            "banbury": round((results.get("cherwell_banbury", {}).get('total_count', 0) / total_properties * 100), 2) if total_properties > 0 else 0,
            "bicester": round((results.get("cherwell_bicester", {}).get('total_count', 0) / total_properties * 100), 2) if total_properties > 0 else 0,
            "kidlington": round((results.get("cherwell_kidlington", {}).get('total_count', 0) / total_properties * 100), 2) if total_properties > 0 else 0
        }
    }

@hmo_router.post("/cache/clear")
async def clear_hmo_cache():
    """Clear the HMO data cache"""
    hmo_manager.clear_cache()
    return {"message": "Cache cleared successfully"}

@hmo_router.get("/cache/status")
async def get_cache_status():
    """Get cache status information"""
    return {
        "cached_cities": list(hmo_manager.cache.keys()),
        "cache_size": len(hmo_manager.cache),
        "cache_timeout_seconds": hmo_manager.cache_timeout
    }

# Function to add to your main FastAPI app
def add_hmo_registry_endpoints(app):
    """Add HMO registry endpoints to FastAPI app"""
    app.include_router(hmo_router)

# Legacy support - keep old oxford endpoints for backward compatibility
def add_oxford_map_endpoints(app):
    """Legacy function - redirects to new HMO registry endpoints"""
    legacy_router = APIRouter(prefix="/api/oxford-hmo", tags=["Oxford HMO (Legacy)"])
    
    @legacy_router.get("/map-data")
    async def get_oxford_hmo_map_data_legacy(
        force_refresh: bool = False, 
        enable_geocoding: bool = True
    ):
        """Legacy endpoint - use /api/hmo-registry/cities/oxford instead"""
        return await get_city_hmo_data(HMORegistryCity.OXFORD, enable_geocoding, force_refresh)
    
    @legacy_router.get("/statistics")
    async def get_oxford_hmo_statistics_legacy():
        """Legacy endpoint - use /api/hmo-registry/cities/oxford/statistics instead"""
        return await get_city_hmo_statistics(HMORegistryCity.OXFORD)
    
    @legacy_router.post("/refresh")
    async def refresh_oxford_hmo_data_legacy():
        """Legacy endpoint - use /api/hmo-registry/cities/oxford/refresh instead"""
        return await refresh_city_hmo_data(HMORegistryCity.OXFORD)
    
    app.include_router(legacy_router)