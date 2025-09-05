# Update hmo_registry/cities/__init__.py to include the new data sources

"""
HMO Registry City Data Sources - Updated with new councils
"""

from .oxford import OxfordHMOMapData
from .vale_of_white_horse import ValeOfWhiteHorseHMOData
from .south_oxfordshire import SouthOxfordshireHMOData

# Import existing data sources
try:
    from .cherwell_banbury import CherswellBanburyHMOData
    from .cherwell_bicester import CherswellBicesterHMOData  
    from .cherwell_kidlington import CherswellKidlingtonHMOData
    CHERWELL_AVAILABLE = True
except ImportError:
    CHERWELL_AVAILABLE = False

try:
    from .swindon import SwindonHMOData
    SWINDON_AVAILABLE = True
except ImportError:
    SWINDON_AVAILABLE = False

__all__ = [
    'OxfordHMOMapData',
    'ValeOfWhiteHorseHMOData',
    'SouthOxfordshireHMOData'
]

if CHERWELL_AVAILABLE:
    __all__.extend([
        'CherswellBanburyHMOData',
        'CherswellBicesterHMOData', 
        'CherswellKidlingtonHMOData'
    ])

if SWINDON_AVAILABLE:
    __all__.append('SwindonHMOData')