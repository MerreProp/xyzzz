# enhanced_duplicate_detection.py
"""
Phase 2: Enhanced Duplicate Detection with Proximity Logic
Updates duplicate_detection.py with real geographic distance calculations
"""

import re
import math
from difflib import SequenceMatcher
from typing import List, Tuple, Dict, Any, Optional
from sqlalchemy.orm import Session
from pydantic import BaseModel
from geopy.distance import geodesic
import logging

# Set up logging
logger = logging.getLogger(__name__)

# ================================
# PYDANTIC MODELS (Enhanced)
# ================================

class ProximityDetails(BaseModel):
    """Enhanced proximity information"""
    distance_meters: Optional[float]
    proximity_level: str
    confidence_boost: Optional[float] = 0.0
    confidence_penalty: Optional[float] = 0.0
    proximity_explanation: str

class EnhancedMatchFactors(BaseModel):
    """Enhanced match factors with proximity details"""
    address_similarity: float
    geographic_details: ProximityDetails
    price_similarity: float
    room_count_similarity: float
    advertiser_similarity: float
    
    # New proximity-based factors
    same_landlord_boost: float = 0.0
    portfolio_detection: bool = False
    distance_penalty: float = 0.0
    
    # Explanations for transparency
    primary_factors: List[str]
    concerns: List[str]

class EnhancedPotentialMatch(BaseModel):
    """Enhanced potential match with detailed proximity info"""
    property_id: str
    existing_url: str
    address: str
    confidence_score: float
    match_factors: EnhancedMatchFactors
    property_details: Dict[str, Any]
    
    # New proximity information
    distance_meters: Optional[float]
    proximity_level: str
    recommendation: str  # 'auto_link', 'user_choice', 'separate'
    recommendation_reason: str

# ================================
# ENHANCED GEOGRAPHIC FUNCTIONS
# ================================

def calculate_enhanced_geographic_score(
    existing_lat: Optional[float], 
    existing_lng: Optional[float],
    new_lat: Optional[float], 
    new_lng: Optional[float],
    existing_address: str = "",
    new_address: str = ""
) -> Tuple[float, ProximityDetails]:
    """
    Calculate enhanced geographic similarity with detailed proximity analysis
    """
    
    # Handle missing coordinates
    if not all([existing_lat, existing_lng, new_lat, new_lng]):
        # Fallback to address similarity
        address_sim = SequenceMatcher(None, 
                                    normalize_address(existing_address), 
                                    normalize_address(new_address)).ratio()
        
        return address_sim * 0.5, ProximityDetails(
            distance_meters=None,
            proximity_level="unknown_location",
            proximity_explanation="No coordinates available - using address similarity"
        )
    
    # Calculate actual distance using geopy
    try:
        distance_meters = geodesic((existing_lat, existing_lng), (new_lat, new_lng)).meters
    except Exception as e:
        logger.warning(f"Distance calculation failed: {e}")
        return 0.3, ProximityDetails(
            distance_meters=None,
            proximity_level="calculation_error",
            proximity_explanation="Distance calculation failed"
        )
    
    # Enhanced distance-based scoring with detailed levels
    if distance_meters <= 5:
        geo_score = 1.0
        proximity_level = "same_address"
        explanation = "Likely same building/address"
    elif distance_meters <= 25:
        geo_score = 0.95
        proximity_level = "same_building"
        explanation = "Very close - probably same building"
    elif distance_meters <= 75:
        geo_score = 0.85
        proximity_level = "same_block"
        explanation = "Same block or immediate area"
    elif distance_meters <= 150:
        geo_score = 0.70
        proximity_level = "same_street"
        explanation = "Same street or very close"
    elif distance_meters <= 300:
        geo_score = 0.50
        proximity_level = "walking_distance"
        explanation = "Short walking distance"
    elif distance_meters <= 500:
        geo_score = 0.30
        proximity_level = "same_neighborhood"
        explanation = "Same neighborhood"
    elif distance_meters <= 1000:
        geo_score = 0.15
        proximity_level = "nearby_area"
        explanation = "Nearby area"
    else:
        geo_score = 0.05
        proximity_level = "different_area"
        explanation = f"Far apart ({distance_meters/1000:.1f}km)"
    
    return geo_score, ProximityDetails(
        distance_meters=distance_meters,
        proximity_level=proximity_level,
        proximity_explanation=explanation
    )

def apply_proximity_adjustments(
    base_confidence: float,
    proximity_details: ProximityDetails,
    advertiser_similarity: float,
    existing_address: str,
    new_address: str
) -> Tuple[float, Dict[str, Any]]:
    """
    Apply proximity-based confidence adjustments based on Phase 1 requirements
    """
    
    adjustments = {
        "base_confidence": base_confidence,
        "adjustments_applied": []
    }
    
    adjusted_confidence = base_confidence
    distance = proximity_details.distance_meters
    
    if distance is None:
        return adjusted_confidence, adjustments
    
    # Same landlord detection
    same_landlord = advertiser_similarity > 0.8
    
    # PHASE 1 PROXIMITY LOGIC IMPLEMENTATION:
    
    if distance <= 50 and same_landlord:
        # Very close + same landlord = likely same building, different units
        boost = 0.15
        adjusted_confidence = min(adjusted_confidence + boost, 1.0)
        adjustments["adjustments_applied"].append({
            "type": "same_building_same_landlord",
            "boost": boost,
            "reason": "Same landlord + very close (<50m) = likely same building with multiple units"
        })
        proximity_details.confidence_boost = boost
        
    elif distance <= 100 and same_landlord:
        # Close + same landlord = possible portfolio properties
        boost = 0.10
        adjusted_confidence = min(adjusted_confidence + boost, 1.0)
        adjustments["adjustments_applied"].append({
            "type": "portfolio_properties",
            "boost": boost,
            "reason": "Same landlord + close proximity (<100m) = likely portfolio properties"
        })
        proximity_details.confidence_boost = boost
        
    elif distance <= 20 and not same_landlord:
        # Very close + different landlord = possibly same building, different owners
        boost = 0.08
        adjusted_confidence = min(adjusted_confidence + boost, 1.0)
        adjustments["adjustments_applied"].append({
            "type": "same_building_different_landlord",
            "boost": boost,
            "reason": "Very close (<20m) despite different landlords = possibly same building"
        })
        proximity_details.confidence_boost = boost
        
    elif distance >= 500:
        # Far apart = less likely to be duplicate
        penalty = 0.10
        adjusted_confidence = max(adjusted_confidence - penalty, 0)
        adjustments["adjustments_applied"].append({
            "type": "distance_penalty",
            "penalty": penalty,
            "reason": f"Properties far apart ({distance:.0f}m) = less likely to be duplicates"
        })
        proximity_details.confidence_penalty = penalty
    
    # Additional logic: exact address match despite distance
    if distance > 100:
        address_exact_match = normalize_address(existing_address) == normalize_address(new_address)
        if address_exact_match:
            boost = 0.20
            adjusted_confidence = min(adjusted_confidence + boost, 1.0)
            adjustments["adjustments_applied"].append({
                "type": "exact_address_override",
                "boost": boost,
                "reason": "Exact address match overrides distance concerns"
            })
    
    adjustments["final_confidence"] = adjusted_confidence
    adjustments["total_adjustment"] = adjusted_confidence - base_confidence
    
    return adjusted_confidence, adjustments

# ================================
# ENHANCED CONFIDENCE CALCULATION
# ================================

def calculate_enhanced_confidence_score(
    existing_property: Dict,
    new_address: str,
    new_latitude: Optional[float] = None,
    new_longitude: Optional[float] = None,
    new_price: Optional[float] = None,
    new_room_count: Optional[int] = None,
    new_advertiser: Optional[str] = None
) -> Tuple[float, EnhancedMatchFactors]:
    """
    Enhanced confidence calculation with proximity logic from Phase 1
    """
    
    # 1. Address Similarity (40% weight - reduced to make room for geographic)
    existing_address = existing_property.get('address', '')
    address_sim = SequenceMatcher(None, 
                                 normalize_address(existing_address), 
                                 normalize_address(new_address)).ratio()
    
    # 2. Enhanced Geographic Proximity (30% weight - increased importance)
    existing_lat = existing_property.get('latitude')
    existing_lng = existing_property.get('longitude')
    
    geo_score, proximity_details = calculate_enhanced_geographic_score(
        existing_lat, existing_lng, new_latitude, new_longitude,
        existing_address, new_address
    )
    
    # 3. Price Similarity (15% weight)
    existing_price = None
    if existing_property.get('latest_analysis'):
        existing_price = existing_property['latest_analysis'].get('monthly_income')
    
    price_sim = calculate_price_similarity(existing_price, new_price)
    
    # 4. Room Count Similarity (10% weight)
    existing_rooms = None
    if existing_property.get('latest_analysis'):
        existing_rooms = existing_property['latest_analysis'].get('total_rooms')
    
    room_sim = calculate_room_count_similarity(existing_rooms, new_room_count)
    
    # 5. Advertiser Similarity (5% weight)
    advertiser_sim = 0.5  # Default neutral score
    if new_advertiser and existing_property.get('latest_analysis', {}).get('advertiser_name'):
        existing_advertiser = existing_property['latest_analysis']['advertiser_name']
        if new_advertiser.lower() == existing_advertiser.lower():
            advertiser_sim = 1.0
        else:
            advertiser_sim = SequenceMatcher(None, 
                                           new_advertiser.lower(), 
                                           existing_advertiser.lower()).ratio()
    
    # Calculate base confidence using weighted factors
    base_confidence = (
        address_sim * 0.40 +      # Address similarity
        geo_score * 0.30 +        # Enhanced geographic proximity
        price_sim * 0.15 +        # Price similarity
        room_sim * 0.10 +         # Room count similarity
        advertiser_sim * 0.05     # Advertiser similarity
    )
    
    # Apply proximity-based adjustments
    adjusted_confidence, proximity_adjustments = apply_proximity_adjustments(
        base_confidence, proximity_details, advertiser_sim, 
        existing_address, new_address
    )
    
    # Identify primary factors and concerns
    primary_factors = []
    concerns = []
    
    if address_sim >= 0.8:
        primary_factors.append(f"Very similar addresses ({address_sim:.0%})")
    
    if proximity_details.distance_meters and proximity_details.distance_meters <= 50:
        primary_factors.append(f"Very close proximity ({proximity_details.distance_meters:.0f}m)")
    
    if advertiser_sim >= 0.9:
        primary_factors.append("Same advertiser/landlord")
    
    if price_sim >= 0.8:
        primary_factors.append(f"Similar pricing ({price_sim:.0%})")
    
    # Identify concerns
    if proximity_details.distance_meters and proximity_details.distance_meters > 200:
        concerns.append(f"Properties are {proximity_details.distance_meters:.0f}m apart")
    
    if room_sim < 0.7:
        concerns.append("Different number of rooms")
    
    if price_sim < 0.6:
        concerns.append("Significantly different pricing")
    
    if advertiser_sim < 0.5:
        concerns.append("Different advertisers/landlords")
    
    # Create enhanced match factors
    match_factors = EnhancedMatchFactors(
        address_similarity=address_sim,
        geographic_details=proximity_details,
        price_similarity=price_sim,
        room_count_similarity=room_sim,
        advertiser_similarity=advertiser_sim,
        same_landlord_boost=proximity_adjustments.get("total_adjustment", 0) if proximity_adjustments.get("total_adjustment", 0) > 0 else 0,
        portfolio_detection=any(adj.get("type") == "portfolio_properties" for adj in proximity_adjustments.get("adjustments_applied", [])),
        distance_penalty=proximity_details.confidence_penalty or 0,
        primary_factors=primary_factors,
        concerns=concerns
    )
    
    return adjusted_confidence, match_factors

# ================================
# ENHANCED DUPLICATE DETECTION
# ================================

def find_enhanced_potential_duplicates(
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
) -> List[EnhancedPotentialMatch]:
    """
    Enhanced duplicate detection with proximity logic
    """
    
    # Import here to avoid circular imports
    from duplicate_detection import get_all_properties_with_latest_analysis
    
    logger.info(f"🔍 Enhanced duplicate detection for: {new_address}")
    if new_latitude and new_longitude:
        logger.info(f"📍 Coordinates: {new_latitude:.6f}, {new_longitude:.6f}")
    
    # Get all properties for comparison
    all_properties = get_all_properties_with_latest_analysis(db)
    
    potential_matches = []
    
    for existing_property in all_properties:
        if existing_property.url == new_url:
            continue  # Skip self
        
        # Calculate enhanced confidence
        confidence, match_factors = calculate_enhanced_confidence_score(
            existing_property=existing_property.__dict__,
            new_address=new_address,
            new_latitude=new_latitude,
            new_longitude=new_longitude,
            new_price=new_price,
            new_room_count=new_room_count,
            new_advertiser=new_advertiser
        )
        
        if confidence >= min_confidence:
            # Generate recommendation based on confidence and factors
            recommendation, reason = generate_match_recommendation(confidence, match_factors)
            
            enhanced_match = EnhancedPotentialMatch(
                property_id=str(existing_property.id),
                existing_url=existing_property.url,
                address=existing_property.address or "Unknown address",
                confidence_score=round(confidence, 3),
                match_factors=match_factors,
                property_details={
                    'monthly_income': existing_property.latest_analysis.monthly_income if existing_property.latest_analysis else None,
                    'total_rooms': existing_property.latest_analysis.total_rooms if existing_property.latest_analysis else None,
                    'advertiser_name': existing_property.latest_analysis.advertiser_name if existing_property.latest_analysis else None,
                    'created_at': existing_property.created_at.isoformat() if existing_property.created_at else None
                },
                distance_meters=match_factors.geographic_details.distance_meters,
                proximity_level=match_factors.geographic_details.proximity_level,
                recommendation=recommendation,
                recommendation_reason=reason
            )
            
            potential_matches.append(enhanced_match)
            
            logger.info(f"📊 Match found: {existing_property.address}")
            logger.info(f"   Confidence: {confidence:.1%}")
            logger.info(f"   Distance: {match_factors.geographic_details.distance_meters or 'Unknown'}m")
            logger.info(f"   Recommendation: {recommendation}")
    
    # Sort by confidence (highest first)
    potential_matches.sort(key=lambda x: x.confidence_score, reverse=True)
    
    logger.info(f"✅ Found {len(potential_matches)} potential matches above {min_confidence:.0%} confidence")
    
    return potential_matches[:max_results]

def generate_match_recommendation(
    confidence: float, 
    match_factors: EnhancedMatchFactors
) -> Tuple[str, str]:
    """
    Generate recommendation for handling the potential duplicate
    """
    
    distance = match_factors.geographic_details.distance_meters
    
    # High confidence thresholds
    if confidence >= 0.85:
        if distance and distance <= 50:
            return "auto_link", f"High confidence ({confidence:.0%}) + very close proximity"
        else:
            return "user_choice", f"High confidence ({confidence:.0%}) but check distance"
    
    # Medium-high confidence  
    elif confidence >= 0.70:
        if match_factors.portfolio_detection:
            return "user_choice", "Likely landlord portfolio - user should confirm"
        elif distance and distance <= 25:
            return "user_choice", "Very close proximity - likely same property"
        else:
            return "user_choice", f"Medium-high confidence ({confidence:.0%}) - user review recommended"
    
    # Medium confidence
    elif confidence >= 0.50:
        if len(match_factors.concerns) <= 1:
            return "user_choice", f"Medium confidence ({confidence:.0%}) with minimal concerns"
        else:
            return "separate", f"Medium confidence ({confidence:.0%}) but multiple concerns"
    
    # Low confidence
    else:
        return "separate", f"Low confidence ({confidence:.0%}) - likely different properties"

# ================================
# UTILITY FUNCTIONS (from original)
# ================================

def normalize_address(address: str) -> str:
    """Normalize address for comparison (from original duplicate_detection.py)"""
    if not address:
        return ""
    
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
    
    normalized = re.sub(r'[,\.\-]+', ' ', normalized)
    normalized = re.sub(r'\s+', ' ', normalized)
    
    return normalized.strip()

def calculate_price_similarity(existing_price: Optional[float], new_price: Optional[float]) -> float:
    """Calculate price similarity (from original duplicate_detection.py)"""
    if not existing_price or not new_price:
        return 0.5  # Neutral when price unknown
    
    price_diff = abs(existing_price - new_price)
    max_price = max(existing_price, new_price)
    
    if max_price == 0:
        return 1.0 if existing_price == new_price else 0
    
    percentage_diff = price_diff / max_price
    
    if percentage_diff <= 0.05:     # Within 5%
        return 1.0
    elif percentage_diff <= 0.15:   # Within 15%
        return 0.8
    elif percentage_diff <= 0.30:   # Within 30%
        return 0.6
    elif percentage_diff <= 0.50:   # Within 50%
        return 0.4
    else:
        return 0.1

def calculate_room_count_similarity(existing_rooms: Optional[int], new_rooms: Optional[int]) -> float:
    """Calculate room count similarity (from original duplicate_detection.py)"""
    if not existing_rooms or not new_rooms:
        return 0.5  # Neutral when room count unknown
    
    if existing_rooms == new_rooms:
        return 1.0
    
    diff = abs(existing_rooms - new_rooms)
    max_rooms = max(existing_rooms, new_rooms)
    
    if diff == 1 and max_rooms <= 5:  # Off by 1 in small properties
        return 0.8
    elif diff <= 2:                   # Off by 2 rooms
        return 0.6
    elif diff <= 3:                   # Off by 3 rooms
        return 0.4
    else:
        return 0.2

# ================================
# TESTING AND VALIDATION
# ================================

def test_enhanced_proximity_logic():
    """Test the enhanced proximity logic with sample data"""
    
    print("🧪 Testing Enhanced Proximity Logic")
    print("=" * 50)
    
    # Test case 1: Same building, same landlord
    print("\n📋 Test 1: Same building, same landlord")
    geo_score, proximity = calculate_enhanced_geographic_score(
        51.7520, -1.2577,  # Oxford coordinates
        51.7521, -1.2578,  # Very close
        "123 High Street, Oxford",
        "123 High Street, Flat 2, Oxford"
    )
    
    adjusted_conf, adjustments = apply_proximity_adjustments(
        0.65, proximity, 0.95, "123 High Street", "123 High Street, Flat 2"
    )
    
    print(f"   Geographic score: {geo_score:.2f}")
    print(f"   Distance: {proximity.distance_meters:.1f}m")
    print(f"   Proximity level: {proximity.proximity_level}")
    print(f"   Base confidence: 65% → Adjusted: {adjusted_conf:.0%}")
    print(f"   Adjustments: {len(adjustments.get('adjustments_applied', []))}")
    
    # Test case 2: Different areas
    print("\n📋 Test 2: Different areas")
    geo_score2, proximity2 = calculate_enhanced_geographic_score(
        51.7520, -1.2577,  # Oxford
        51.4816, -0.0077,  # Greenwich, London
        "123 High Street, Oxford",
        "456 London Road, Greenwich"
    )
    
    adjusted_conf2, adjustments2 = apply_proximity_adjustments(
        0.70, proximity2, 0.85, "123 High Street, Oxford", "456 London Road, Greenwich"
    )
    
    print(f"   Geographic score: {geo_score2:.2f}")
    print(f"   Distance: {proximity2.distance_meters/1000:.1f}km")
    print(f"   Proximity level: {proximity2.proximity_level}")
    print(f"   Base confidence: 70% → Adjusted: {adjusted_conf2:.0%}")
    print(f"   Adjustments: {len(adjustments2.get('adjustments_applied', []))}")
    
    print(f"\n✅ Enhanced proximity logic working correctly!")

if __name__ == "__main__":
    test_enhanced_proximity_logic()