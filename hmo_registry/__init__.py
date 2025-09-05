# Create/update the __init__.py file:
"""
HMO Registry Package
Provides multi-city HMO registry data management and API endpoints
"""

from .registry_endpoints import add_hmo_registry_endpoints, add_oxford_map_endpoints
from .registry_models import HMOProperty, HMORegistryResponse, HMORegistryStats, HMOCityInfo
from .cities.oxford import OxfordHMOMapData

__version__ = "1.0.0"
__all__ = [
    "add_hmo_registry_endpoints",
    "add_oxford_map_endpoints", 
    "HMOProperty", 
    "HMORegistryResponse", 
    "HMORegistryStats",
    "HMOCityInfo",
    "OxfordHMOMapData"
]