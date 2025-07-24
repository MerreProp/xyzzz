# duplicate_detection.py
# Multi-Factor Duplicate Detection System for Property Analysis

import re
import math
from difflib import SequenceMatcher
from typing import List, Tuple, Dict, Any, Optional
from sqlalchemy.orm import Session
from pydantic import BaseModel


# ================================
# PYDANTIC MODELS
# ================================

class PotentialMatch(BaseModel):
    property_id: str
    existing_url: str
    address: str
    confidence_score: float
    match_factors: Dict[str, Any]
    property_details: Dict[str, Any]

class DuplicateCheckRequest(BaseModel):
    url: str

class DuplicateCheckResponse(BaseModel):
    has_potential_duplicates: bool
    potential_matches: List[PotentialMatch]
    extracted_address: Optional[str]
    extraction_successful: bool

# ================================
# ADDRESS NORMALIZATION FUNCTIONS
# ================================

def normalize_address(address: str) -> str:
    """Normalize address for comparison"""
    if not address:
        return ""
    
    # Convert to lowercase
    normalized = address.lower().strip()
    
    # Remove common prefixes/suffixes
    prefixes_to_remove = [
        r'^(flat|apartment|apt|unit|room)\s*\d*[a-z]?\s*,?\s*',
        r'^(floor|fl)\s*\d+\s*,?\s*',
        r'^\d+[a-z]?\s*-\s*'
    ]
    
    for prefix in prefixes_to_remove:
        normalized = re.sub(prefix, '', normalized)
    
    # Standardize street types
    street_replacements = {
        r'\bst\b': 'street',
        r'\brd\b': 'road',
        r'\bave\b': 'avenue',
        r'\bdr\b': 'drive',
        r'\bln\b': 'lane',
        r'\bcl\b': 'close',
        r'\bpl\b': 'place',
        r'\bcrt\b': 'court',
        r'\bgrv\b': 'grove'
    }
    
    for pattern, replacement in street_replacements.items():
        normalized = re.sub(pattern, replacement, normalized)
    
    # Remove extra spaces and punctuation
    normalized = re.sub(r'[,\.\-]+', ' ', normalized)
    normalized = re.sub(r'\s+', ' ', normalized)
    
    return normalized.strip()

def extract_postcode(address: str) -> str:
    """Extract UK postcode from address"""
    if not address:
        return ""
    
    # UK postcode pattern
    postcode_pattern = r'[A-Z]{1,2}\d{1,2}[A-Z]?\s?\d[A-Z]{2}'
    match = re.search(postcode_pattern, address.upper())
    
    return match.group(0).replace(' ', '') if match else ""

def extract_house_number(address: str) -> str:
    """Extract house number from address"""
    if not address:
        return ""
    
    # Look for number at start of address or after common prefixes
    number_patterns = [
        r'^\d+[a-z]?',  # Start with number
        r'(?:flat|apartment|apt|unit)\s*\d*[a-z]?\s*,?\s*(\d+)',  # After prefix
    ]
    
    for pattern in number_patterns:
        match = re.search(pattern, address.lower())
        if match:
            return match.group(1) if match.lastindex else match.group(0)
    
    return ""

# ================================
# SIMILARITY CALCULATION FUNCTIONS
# ================================

def calculate_address_similarity(addr1: str, addr2: str) -> float:
    """Calculate similarity between two addresses with strict street matching"""
    if not addr1 or not addr2:
        return 0.0
    
    norm1 = normalize_address(addr1)
    norm2 = normalize_address(addr2)
    
    # FIXED: Extract street names for strict comparison
    street1 = extract_street_name(addr1)
    street2 = extract_street_name(addr2)
    
    # If we have different street names, heavily penalize the match
    if street1 and street2 and street1.lower() != street2.lower():
        # Different streets should get very low scores
        # Only allow matches if streets are very similar (typos, abbreviations)
        street_sim = SequenceMatcher(None, street1.lower(), street2.lower()).ratio()
        if street_sim < 0.8:  # Less than 80% similarity between street names
            return max(0.0, street_sim * 0.3)  # Cap at 30% for different streets
    
    # Use SequenceMatcher for overall similarity
    similarity = SequenceMatcher(None, norm1, norm2).ratio()
    
    # Boost score if postcodes match
    postcode1 = extract_postcode(addr1)
    postcode2 = extract_postcode(addr2)
    
    if postcode1 and postcode2 and postcode1 == postcode2:
        similarity = min(1.0, similarity + 0.15)  # Reduced from 0.2 to 0.15
    
    # Boost score if house numbers match
    house1 = extract_house_number(addr1)
    house2 = extract_house_number(addr2)
    
    if house1 and house2 and house1 == house2 and street1 and street2 and street1.lower() == street2.lower():
        similarity = min(1.0, similarity + 0.2)  # Only boost if same street AND same house number
    
    return similarity

def extract_street_name(address: str) -> str:
    """Extract the street name from an address"""
    if not address:
        return ""
    
    # Remove common prefixes (flat numbers, etc.)
    cleaned = re.sub(r'^(flat|apartment|apt|unit|room)\s*\d*[a-z]?\s*,?\s*', '', address.lower())
    cleaned = re.sub(r'^(floor|fl)\s*\d+\s*,?\s*', '', cleaned)
    cleaned = re.sub(r'^\d+[a-z]?\s*,?\s*', '', cleaned)  # Remove house numbers
    
    # Split by comma and take the first part (should be street name)
    parts = cleaned.split(',')
    if parts:
        street = parts[0].strip()
        # Remove any remaining numbers at the start
        street = re.sub(r'^\d+\s*', '', street)
        return street.strip()
    
    return ""

def calculate_price_similarity(price1: Optional[float], price2: Optional[float], tolerance: float = 0.15) -> float:
    """Calculate price similarity within tolerance range"""
    if price1 is None or price2 is None or price1 <= 0 or price2 <= 0:
        return 0.5  # Neutral score when price unavailable
    
    # Calculate percentage difference
    diff = abs(price1 - price2) / max(price1, price2)
    
    if diff <= tolerance:
        # Closer prices get higher scores
        return 1.0 - (diff / tolerance) * 0.3  # Scale from 1.0 to 0.7
    else:
        return 0.3  # Low score for prices outside tolerance

def calculate_geographic_distance(lat1: Optional[float], lon1: Optional[float], 
                                lat2: Optional[float], lon2: Optional[float]) -> float:
    """Calculate distance between two coordinates in meters using haversine formula"""
    if not all([lat1, lon1, lat2, lon2]):
        return float('inf')
    
    try:
        # Convert latitude and longitude from degrees to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Radius of earth in meters
        r = 6371000
        
        # Calculate the result
        distance = c * r
        return distance
    except:
        return float('inf')

def calculate_room_count_similarity(rooms1: Optional[int], rooms2: Optional[int]) -> float:
    """Calculate room count similarity"""
    if rooms1 is None or rooms2 is None:
        return 0.5  # Neutral score when room count unavailable
    
    if rooms1 == rooms2:
        return 1.0
    elif abs(rooms1 - rooms2) == 1:
        return 0.7  # Close room counts
    elif abs(rooms1 - rooms2) == 2:
        return 0.4  # Somewhat different
    else:
        return 0.1  # Very different

# ================================
# MULTI-FACTOR DETECTION FUNCTION
# ================================

def calculate_duplicate_confidence(
    existing_property: Dict[str, Any],
    new_address: str,
    new_latitude: Optional[float] = None,
    new_longitude: Optional[float] = None,
    new_price: Optional[float] = None,
    new_room_count: Optional[int] = None,
    new_advertiser: Optional[str] = None
) -> Tuple[float, Dict[str, Any]]:
    """
    Calculate confidence score for potential duplicate using multi-factor analysis
    Returns (confidence_score, match_factors)
    """
    
    factors = {}
    
    # 1. Address Similarity (Primary Factor - INCREASED to 50% weight)
    address_sim = calculate_address_similarity(existing_property.get('address', ''), new_address)
    factors['address_similarity'] = address_sim
    
    # FIXED: If address similarity is very low, don't bother with other factors
    if address_sim < 0.3:
        factors['geographic_distance_m'] = None
        factors['geographic_similarity'] = 0.0
        factors['price_similarity'] = 0.5
        factors['room_count_similarity'] = 0.5
        factors['advertiser_similarity'] = 0.5
        
        # Return very low confidence for different addresses
        return address_sim * 0.5, factors
    
    # 2. Geographic Distance (Reduced to 20% weight)  
    distance = calculate_geographic_distance(
        existing_property.get('latitude'), existing_property.get('longitude'),
        new_latitude, new_longitude
    )
    
    if distance == float('inf'):
        geo_score = 0.5  # Neutral when coordinates unavailable
    else:
        # FIXED: More strict distance requirements
        # Within 50m = 1.0, beyond 200m = 0.0 (reduced from 500m)
        geo_score = max(0.0, 1.0 - (distance / 200))
    
    factors['geographic_distance_m'] = distance if distance != float('inf') else None
    factors['geographic_similarity'] = geo_score
    
    # 3. Price Similarity (15% weight - unchanged)
    existing_price = None
    if existing_property.get('latest_analysis'):
        existing_price = existing_property['latest_analysis'].get('monthly_income')
    
    price_sim = calculate_price_similarity(existing_price, new_price)
    factors['price_similarity'] = price_sim
    factors['existing_price'] = existing_price
    factors['new_price'] = new_price
    
    # 4. Room Count Similarity (10% weight - reduced from 15%)
    existing_rooms = None
    if existing_property.get('latest_analysis'):
        existing_rooms = existing_property['latest_analysis'].get('total_rooms')
    
    room_sim = calculate_room_count_similarity(existing_rooms, new_room_count)
    factors['room_count_similarity'] = room_sim
    factors['existing_rooms'] = existing_rooms
    factors['new_rooms'] = new_room_count
    
    # 5. Advertiser/Landlord Similarity (5% weight - unchanged)
    advertiser_sim = 0.5  # Default neutral score
    if new_advertiser and existing_property.get('latest_analysis', {}).get('advertiser_name'):
        existing_advertiser = existing_property['latest_analysis']['advertiser_name']
        if new_advertiser.lower() == existing_advertiser.lower():
            advertiser_sim = 1.0
        else:
            # Check for partial matches
            advertiser_sim = SequenceMatcher(None, 
                                           new_advertiser.lower(), 
                                           existing_advertiser.lower()).ratio()
    
    factors['advertiser_similarity'] = advertiser_sim
    
    # FIXED: Updated weighted confidence score with new weights
    confidence = (
        address_sim * 0.50 +      # INCREASED: Address similarity (primary)
        geo_score * 0.20 +        # REDUCED: Geographic proximity  
        price_sim * 0.15 +        # UNCHANGED: Price similarity
        room_sim * 0.10 +         # REDUCED: Room count similarity
        advertiser_sim * 0.05     # UNCHANGED: Advertiser similarity
    )
    
    return confidence, factors

# ================================
# MAIN DUPLICATE DETECTION FUNCTION
# ================================

def find_potential_duplicates(
    db: Session,
    new_url: str,
    new_address: str,
    new_latitude: Optional[float] = None,
    new_longitude: Optional[float] = None,
    new_price: Optional[float] = None,
    new_room_count: Optional[int] = None,
    new_advertiser: Optional[str] = None,
    min_confidence: float = 0.3,
    max_results: int = 5
) -> List[PotentialMatch]:
    """
    Find potential duplicate properties in the database
    
    Args:
        db: Database session
        new_url: URL of the new property
        new_address: Address of the new property
        new_latitude: Latitude of the new property (optional)
        new_longitude: Longitude of the new property (optional)
        new_price: Monthly price of the new property (optional)
        new_room_count: Number of rooms in the new property (optional)
        new_advertiser: Advertiser name for the new property (optional)
        min_confidence: Minimum confidence score to include in results
        max_results: Maximum number of matches to return
    
    Returns:
        List of potential matches sorted by confidence score
    """
    
    # Import models and CRUD here to avoid circular imports
    from models import Property
    from crud import AnalysisCRUD
    
    # Get all existing properties for comparison
    # For efficiency in large databases, you could add filtering by postcode/area here
    existing_properties_query = (db.query(Property)
                               .filter(Property.address.isnot(None))
                               .all())
    
    potential_matches = []
    
    for existing_prop in existing_properties_query:
        # Skip if same URL
        if existing_prop.url == new_url:
            continue
        
        # Get latest analysis for this property
        latest_analysis = AnalysisCRUD.get_latest_analysis(db, existing_prop.id)
        
        # Prepare existing property data
        existing_data = {
            'address': existing_prop.address,
            'latitude': existing_prop.latitude,
            'longitude': existing_prop.longitude,
            'latest_analysis': {}
        }
        
        if latest_analysis:
            existing_data['latest_analysis'] = {
                'monthly_income': latest_analysis.monthly_income,
                'total_rooms': latest_analysis.total_rooms,
                'advertiser_name': latest_analysis.advertiser_name
            }
        
        # Calculate confidence score
        confidence, factors = calculate_duplicate_confidence(
            existing_data,
            new_address,
            new_latitude,
            new_longitude, 
            new_price,
            new_room_count,
            new_advertiser
        )
        
        # Only include matches above minimum threshold
        if confidence >= min_confidence:
            potential_matches.append(PotentialMatch(
                property_id=str(existing_prop.id),
                existing_url=existing_prop.url,
                address=existing_prop.address,
                confidence_score=round(confidence, 3),
                match_factors=factors,
                property_details={
                    'monthly_income': existing_data['latest_analysis'].get('monthly_income'),
                    'total_rooms': existing_data['latest_analysis'].get('total_rooms'),
                    'advertiser_name': existing_data['latest_analysis'].get('advertiser_name'),
                    'created_at': existing_prop.created_at.isoformat() if existing_prop.created_at else None
                }
            ))
    
    # Sort by confidence score (highest first)
    potential_matches.sort(key=lambda x: x.confidence_score, reverse=True)
    
    # Limit results
    return potential_matches[:max_results]

# ================================
# UTILITY FUNCTIONS
# ================================

def extract_property_details_for_duplicate_check(url: str) -> Dict[str, Any]:
    """
    Extract property details from URL for duplicate checking
    This function should use your existing property extraction logic
    """
    try:
        # Import your existing extraction functions
        from modules.coordinates import extract_property_details, extract_coordinates, reverse_geocode_nominatim
        
        # Create an empty analysis_data dictionary for the extraction
        analysis_data = {}
        
        # Step 1: Get coordinates first
        coords_result = extract_coordinates(url, analysis_data)
        
        # Step 2: Get property details
        extracted_data = extract_property_details(url, analysis_data)
        
        # Step 3: If we have coordinates but no address, try reverse geocoding (like main analysis does)
        if coords_result.get('found') and not analysis_data.get('Full Address'):
            lat, lon = coords_result['latitude'], coords_result['longitude']
            print(f"🔍 Reverse geocoding coordinates for duplicate check: {lat}, {lon}")
            reverse_geocode_nominatim(lat, lon, analysis_data)
        
        # Combine all coordinate sources
        latitude = extracted_data.get('latitude') or coords_result.get('latitude')
        longitude = extracted_data.get('longitude') or coords_result.get('longitude')
        
        # The function should now have populated analysis_data with useful information
        # Let's check both sources for the data we need
        result = {
            'address': analysis_data.get('Full Address') or analysis_data.get('address') or extracted_data.get('address'),
            'latitude': latitude,
            'longitude': longitude,
            'monthly_income': analysis_data.get('Monthly Income') or extracted_data.get('monthly_income'),
            'total_rooms': analysis_data.get('Total Rooms') or extracted_data.get('total_rooms'),
            'advertiser_name': analysis_data.get('Advertiser') or analysis_data.get('advertiser_name') or extracted_data.get('advertiser_name')
        }
        
        # Debug: Print what we extracted for troubleshooting
        if result.get('address') or result.get('latitude'):
            print(f"✅ Extracted for duplicate check: Address={result.get('address')}, Coords=({result.get('latitude')}, {result.get('longitude')})")
        else:
            print(f"⚠️ Limited extraction: analysis_data keys = {list(analysis_data.keys())}")
        
        return result
        
    except Exception as e:
        print(f"Error extracting property details for duplicate check: {str(e)}")
        # Print more detailed error info for debugging
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return {}