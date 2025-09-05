# hmo_registry/models.py
"""
Pydantic models for HMO Registry API
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from enum import Enum
from datetime import datetime

class HMORegistryCity(str, Enum):
    OXFORD = "oxford"
    SWINDON = "swindon"
    CHERWELL_BANBURY = "cherwell_banbury"     
    CHERWELL_BICESTER = "cherwell_bicester"   
    CHERWELL_KIDLINGTON = "cherwell_kidlington"
    VALE_OF_WHITE_HORSE = "vale_of_white_horse"
    SOUTH_OXFORDSHIRE = "south_oxfordshire"
    # Vale of White Horse towns
    VALE_ABINGDON = "vale_abingdon"
    VALE_BOTLEY = "vale_botley"
    VALE_KENNINGTON = "vale_kennington"
    VALE_WANTAGE = "vale_wantage"
    VALE_OTHER = "vale_other"
    # South Oxfordshire towns
    SOUTH_DIDCOT = "south_didcot"
    SOUTH_HENLEY = "south_henley"     
    SOUTH_THAME = "south_thame"
    SOUTH_WALLINGFORD = "south_wallingford"
    SOUTH_OTHER = "south_other"
    # Future cities can be added here
    # CAMBRIDGE = "cambridge"
    # BIRMINGHAM = "birmingham"

class HMOProperty(BaseModel):
    """HMO Property model for API responses"""
    id: str
    case_number: str
    source: str
    city: str
    address: str
    postcode: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    geocoded: bool
    total_occupants: Optional[int]
    total_units: Optional[int]
    licence_status: str
    licence_start_date: Optional[str]
    licence_expiry_date: Optional[str]
    data_quality_score: float
    processing_notes: str
    last_updated: str
    data_source_url: Optional[str] = None

class HMORegistryResponse(BaseModel):
    """Response model for HMO registry data"""
    success: bool
    city: str
    data: List[HMOProperty]
    count: int
    statistics: Dict
    
class HMORegistryStats(BaseModel):
    """Statistics model for HMO registry"""
    total_records: int
    geocoded_records: int
    geocoding_success_rate: float
    active_licences: int
    expired_licences: int
    unknown_status: int
    average_data_quality: float
    last_updated: Optional[str]

class HMOCityInfo(BaseModel):
    """Information about an available HMO registry city"""
    code: str
    name: str
    full_name: str
    region: str
    data_source: str
    update_frequency: str
    available: bool
    total_records: Optional[int] = 0
    geocoded_records: Optional[int] = 0
    last_updated: Optional[str] = None
    error: Optional[str] = None


CITY_METADATA = {
    HMORegistryCity.OXFORD: {
        "name": "Oxford",
        "full_name": "Oxford City Council",
        "region": "Oxfordshire",
        "data_source": "Oxford Excel Register",
        "update_frequency": "Monthly",
        "total_properties_estimate": 3029,
        "postcode_areas": ["OX1", "OX2", "OX3", "OX4"],
        "description": "Historic university city with comprehensive HMO licensing"
    },
    HMORegistryCity.SWINDON: {
        "name": "Swindon",
        "full_name": "Swindon Borough Council",
        "region": "Wiltshire",
        "data_source": "Swindon Excel Register",
        "update_frequency": "Manual",
        "total_properties_estimate": 384,
        "postcode_areas": ["SN1", "SN2", "SN3", "SN4", "SN5"],
        "description": "Major town in Wiltshire with growing HMO sector"
    },
    HMORegistryCity.CHERWELL_BANBURY: {
        "name": "Banbury",
        "full_name": "Banbury, Cherwell District Council",
        "region": "Oxfordshire",
        "data_source": "Cherwell District Register",
        "update_frequency": "Manual",
        "total_properties_estimate": 114,
        "postcode_areas": ["OX16", "OX15"],
        "description": "Historic market town in north Oxfordshire, council headquarters"
    },
    HMORegistryCity.CHERWELL_BICESTER: {
        "name": "Bicester",
        "full_name": "Bicester, Cherwell District Council", 
        "region": "Oxfordshire",
        "data_source": "Cherwell District Register",
        "update_frequency": "Manual",
        "total_properties_estimate": 77,
        "postcode_areas": ["OX26", "OX25"],
        "description": "Growing town with Garden Town status, excellent transport links"
    },
    HMORegistryCity.CHERWELL_KIDLINGTON: {
        "name": "Kidlington",
        "full_name": "Kidlington, Cherwell District Council",
        "region": "Oxfordshire", 
        "data_source": "Cherwell District Register",
        "update_frequency": "Manual",
        "total_properties_estimate": 32,
        "postcode_areas": ["OX5"],
        "description": "Large village, contender for England's largest village"
    },
    HMORegistryCity.VALE_OF_WHITE_HORSE: {
        "name": "Vale of White Horse",
        "full_name": "Vale of White Horse District Council",
        "region": "Oxfordshire", 
        "data_source": "Council PDF Register",
        "update_frequency": "Manual",
        "total_properties_estimate": 78,
        "postcode_areas": ["OX1", "OX2", "OX12", "OX13", "OX14"],
        "description": "District including Abingdon, Botley, Wantage, Kennington and surrounding areas"
    },
    HMORegistryCity.SOUTH_OXFORDSHIRE: {
        "name": "South Oxfordshire",
        "full_name": "South Oxfordshire District Council", 
        "region": "Oxfordshire",
        "data_source": "Council PDF Register",
        "update_frequency": "Manual",
        "total_properties_estimate": 55,
        "postcode_areas": ["OX4", "OX9", "OX10", "OX11", "OX33", "RG9"],
        "description": "District including Didcot, Henley-on-Thames, Thame, Wallingford and surrounding areas"
    },
}