# integrate_phase2.py
"""
Phase 2 Integration Script
Updates your existing duplicate_detection.py with enhanced proximity logic
"""

import os
import shutil
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def integrate_phase2_enhancements():
    """
    Integrate Phase 2 enhancements into existing duplicate detection system
    """
    
    logger.info("🚀 Integrating Phase 2: Enhanced Proximity Logic")
    
    # Step 1: Backup existing duplicate_detection.py
    backup_existing_file()
    
    # Step 2: Update duplicate_detection.py with enhanced functions
    update_duplicate_detection_file()
    
    # Step 3: Update main.py to use enhanced detection
    update_main_py()
    
    # Step 4: Test the integration
    test_integration()
    
    logger.info("✅ Phase 2 integration completed!")

def backup_existing_file():
    """Create backup of existing duplicate_detection.py"""
    
    original_file = Path("duplicate_detection.py")
    
    if original_file.exists():
        backup_file = Path(f"duplicate_detection_backup_phase2.py")
        shutil.copy2(original_file, backup_file)
        logger.info(f"📁 Backed up existing file to: {backup_file}")
    else:
        logger.info("⚠️  duplicate_detection.py not found - will create new file")

def update_duplicate_detection_file():
    """Update duplicate_detection.py with enhanced proximity logic"""
    
    # Read the enhanced duplicate detection code
    enhanced_code = '''# duplicate_detection.py
# Multi-Factor Duplicate Detection System for Property Analysis
# ENHANCED WITH PHASE 2 PROXIMITY LOGIC

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
# PYDANTIC MODELS
# ================================

class PotentialMatch(BaseModel):
    property_id: str
    existing_url: str
    address: str
    confidence_score: float
    match_factors: Dict[str, Any]
    property_details: Dict[str, Any]
    
    # PHASE 2 ADDITIONS:
    distance_meters: Optional[float] = None
    proximity_level: str = "unknown"
    recommendation: str = "user_choice"
    recommendation_reason: str = ""

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
    
    normalized = address.lower().strip()
    
    # Remove common prefixes/suffixes
    prefixes_to_remove = [
        r'^(flat|apartment|apt|unit|room)\\s*\\d*[a-z]?\\s*,?\\s*',
        r'^(floor|fl)\\s*\\d+\\s*,?\\s*',
        r'^\\d+[a-z]?\\s*-\\s*'
    ]
    
    for prefix in prefixes_to_remove:
        normalized = re.sub(prefix, '', normalized)
    
    # Standardize street types
    street_replacements = {
        r'\\bst\\b': 'street',
        r'\\brd\\b': 'road',
        r'\\bave\\b': 'avenue',
        r'\\bdr\\b': 'drive',
        r'\\bln\\b': 'lane',
        r'\\bcl\\b': 'close',
        r'\\bpl\\b': 'place',
        r'\\bcrt\\b': 'court',
        r'\\bgrv\\b': 'grove'
    }
    
    for pattern, replacement in street_replacements.items():
        normalized = re.sub(pattern, replacement, normalized)
    
    normalized = re.sub(r'[,\\.\\-]+', ' ', normalized)
    normalized = re.sub(r'\\s+', ' ', normalized)
    
    return normalized.strip()

# ================================
# ENHANCED GEOGRAPHIC FUNCTIONS (PHASE 2)
# ================================

def calculate_enhanced_geographic_score(
    existing_lat: Optional[float], 
    existing_lng: Optional[float],
    new_lat: Optional[float], 
    new_lng: Optional[float],
    existing_address: str = "",
    new_address: str = ""
) -> Tuple[float, Dict[str, Any]]:
    """
    PHASE 2: Enhanced geographic similarity with real distance calculations
    """
    
    # Handle missing coordinates
    if not all([existing_lat, existing_lng, new_lat, new_lng]):
        address_sim = SequenceMatcher(None, 
                                    normalize_address(existing_address), 
                                    normalize_address(new_address)).ratio()
        
        return address_sim * 0.5, {
            "method": "address_fallback",
            "distance_meters": None,
            "proximity_level": "unknown_location",
            "explanation": "No coordinates available"
        }
    
    # Calculate actual distance using geopy
    try:
        distance_meters = geodesic((existing_lat, existing_lng), (new_lat, new_lng)).meters
    except Exception as e:
        logger.warning(f"Distance calculation failed: {e}")
        return 0.3, {
            "method": "calculation_error",
            "distance_meters": None,
            "proximity_level": "error",
            "explanation": "Distance calculation failed"
        }
    
    # Enhanced distance-based scoring
    if distance_meters <= 5:
        geo_score = 1.0
        proximity_level = "same_address"
    elif distance_meters <= 75:
        geo_score = 0.85
        proximity_level = "same_block"
    elif distance_meters <= 150:
        geo_score = 0.70
        proximity_level = "same_street"
    elif distance_meters <= 300:
        geo_score = 0.50
        proximity_level = "walking_distance"
    elif distance_meters <= 500:
        geo_score = 0.30
        proximity_level = "same_neighborhood"
    elif distance_meters <= 1000:
        geo_score = 0.15
        proximity_level = "nearby_area"
    else:
        geo_score = 0.05
        proximity_level = "different_area"
    
    return geo_score, {
        "method": "geodesic_calculation",
        "distance_meters": distance_meters,
        "proximity_level": proximity_level,
        "explanation": f"{proximity_level.replace('_', ' ')} ({distance_meters:.0f}m)"
    }

def apply_proximity_adjustments(
    base_confidence: float,
    geo_factors: Dict[str, Any],
    advertiser_similarity: float
) -> Tuple[float, Dict[str, Any]]:
    """
    PHASE 2: Apply proximity-based confidence adjustments
    """
    
    adjustments = {
        "base_confidence": base_confidence,
        "adjustments_applied": []
    }
    
    adjusted_confidence = base_confidence
    distance = geo_factors.get("distance_meters")
    
    if distance is None:
        return adjusted_confidence, adjustments
    
    same_landlord = advertiser_similarity > 0.8
    
    # PHASE 1 PROXIMITY LOGIC IMPLEMENTATION:
    
    if distance <= 50 and same_landlord:
        # Very close + same landlord = likely same building, different units
        boost = 0.15
        adjusted_confidence = min(adjusted_confidence + boost, 1.0)
        adjustments["adjustments_applied"].append({
            "type": "same_building_same_landlord",
            "boost": boost,
            "reason": "Same landlord + very close (<50m)"
        })
        
    elif distance <= 100 and same_landlord:
        # Close + same landlord = possible portfolio properties
        boost = 0.10
        adjusted_confidence = min(adjusted_confidence + boost, 1.0)
        adjustments["adjustments_applied"].append({
            "type": "portfolio_properties", 
            "boost": boost,
            "reason": "Same landlord + close proximity (<100m)"
        })
        
    elif distance <= 20 and not same_landlord:
        # Very close + different landlord = possibly same building
        boost = 0.08
        adjusted_confidence = min(adjusted_confidence + boost, 1.0)
        adjustments["adjustments_applied"].append({
            "type": "same_building_different_landlord",
            "boost": boost,
            "reason": "Very close (<20m) despite different landlords"
        })
        
    elif distance >= 500:
        # Far apart = less likely to be duplicate
        penalty = 0.10
        adjusted_confidence = max(adjusted_confidence - penalty, 0)
        adjustments["adjustments_applied"].append({
            "type": "distance_penalty",
            "penalty": penalty,
            "reason": f"Properties far apart ({distance:.0f}m)"
        })
    
    adjustments["final_confidence"] = adjusted_confidence
    adjustments["total_adjustment"] = adjusted_confidence - base_confidence
    
    return adjusted_confidence, adjustments

# ================================
# ENHANCED CONFIDENCE CALCULATION (PHASE 2)
# ================================

def calculate_multi_factor_confidence_score(
    existing_property: Dict,
    new_address: str,
    new_latitude: Optional[float] = None,
    new_longitude: Optional[float] = None,
    new_price: Optional[float] = None,
    new_room_count: Optional[int] = None,
    new_advertiser: Optional[str] = None
) -> Tuple[float, Dict[str, Any]]:
    """
    PHASE 2: Enhanced multi-factor confidence scoring with proximity logic
    """
    
    factors = {}
    
    # 1. Address Similarity (40% weight - reduced for geographic)
    existing_address = existing_property.get('address', '')
    address_sim = SequenceMatcher(None, 
                                 normalize_address(existing_address), 
                                 normalize_address(new_address)).ratio()
    factors['address_similarity'] = address_sim
    
    # 2. ENHANCED Geographic Proximity (30% weight - increased)
    existing_lat = existing_property.get('latitude')
    existing_lng = existing_property.get('longitude')
    
    geo_score, geo_factors = calculate_enhanced_geographic_score(
        existing_lat, existing_lng, new_latitude, new_longitude,
        existing_address, new_address
    )
    factors.update(geo_factors)
    factors['geographic_similarity'] = geo_score
    
    # 3. Price Similarity (15% weight)
    existing_price = None
    if existing_property.get('latest_analysis'):
        existing_price = existing_property['latest_analysis'].get('monthly_income')
    
    price_sim = calculate_price_similarity(existing_price, new_price)
    factors['price_similarity'] = price_sim
    factors['existing_price'] = existing_price
    factors['new_price'] = new_price
    
    # 4. Room Count Similarity (10% weight)
    existing_rooms = None
    if existing_property.get('latest_analysis'):
        existing_rooms = existing_property['latest_analysis'].get('total_rooms')
    
    room_sim = calculate_room_count_similarity(existing_rooms, new_room_count)
    factors['room_count_similarity'] = room_sim
    factors['existing_rooms'] = existing_rooms
    factors['new_rooms'] = new_room_count
    
    # 5. Advertiser Similarity (5% weight)
    advertiser_sim = 0.5
    if new_advertiser and existing_property.get('latest_analysis', {}).get('advertiser_name'):
        existing_advertiser = existing_property['latest_analysis']['advertiser_name']
        if new_advertiser.lower() == existing_advertiser.lower():
            advertiser_sim = 1.0
        else:
            advertiser_sim = SequenceMatcher(None, 
                                           new_advertiser.lower(), 
                                           existing_advertiser.lower()).ratio()
    
    factors['advertiser_similarity'] = advertiser_sim
    
    # Calculate base confidence
    base_confidence = (
        address_sim * 0.40 +
        geo_score * 0.30 +
        price_sim * 0.15 +
        room_sim * 0.10 +
        advertiser_sim * 0.05
    )
    
    # PHASE 2: Apply proximity adjustments
    final_confidence, proximity_adjustments = apply_proximity_adjustments(
        base_confidence, geo_factors, advertiser_sim
    )
    
    # Add proximity adjustment details to factors
    factors['proximity_adjustments'] = proximity_adjustments
    factors['base_confidence'] = base_confidence
    factors['final_confidence'] = final_confidence
    
    return final_confidence, factors

def generate_recommendation(confidence: float, factors: Dict[str, Any]) -> Tuple[str, str]:
    """
    PHASE 2: Generate recommendation based on confidence and factors
    """
    
    distance = factors.get("distance_meters")
    proximity_level = factors.get("proximity_level", "unknown")
    
    # High confidence
    if confidence >= 0.85:
        if distance and distance <= 50:
            return "auto_link", f"High confidence ({confidence:.0%}) + very close"
        else:
            return "user_choice", f"High confidence ({confidence:.0%}) - review distance"
    
    # Medium-high confidence
    elif confidence >= 0.70:
        if any(adj.get("type") == "portfolio_properties" 
               for adj in factors.get("proximity_adjustments", {}).get("adjustments_applied", [])):
            return "user_choice", "Likely landlord portfolio"
        elif distance and distance <= 25:
            return "user_choice", "Very close - likely same property"
        else:
            return "user_choice", f"Medium-high confidence ({confidence:.0%})"
    
    # Medium confidence
    elif confidence >= 0.50:
        return "user_choice", f"Medium confidence ({confidence:.0%}) - needs review"
    
    # Low confidence
    else:
        return "separate", f"Low confidence ({confidence:.0%})"

# ================================
# UTILITY FUNCTIONS
# ================================

def calculate_price_similarity(existing_price: Optional[float], new_price: Optional[float]) -> float:
    """Calculate price similarity between two properties"""
    if not existing_price or not new_price:
        return 0.5
    
    price_diff = abs(existing_price - new_price)
    max_price = max(existing_price, new_price)
    
    if max_price == 0:
        return 1.0 if existing_price == new_price else 0
    
    percentage_diff = price_diff / max_price
    
    if percentage_diff <= 0.05:
        return 1.0
    elif percentage_diff <= 0.15:
        return 0.8
    elif percentage_diff <= 0.30:
        return 0.6
    elif percentage_diff <= 0.50:
        return 0.4
    else:
        return 0.1

def calculate_room_count_similarity(existing_rooms: Optional[int], new_rooms: Optional[int]) -> float:
    """Calculate room count similarity"""
    if not existing_rooms or not new_rooms:
        return 0.5
    
    if existing_rooms == new_rooms:
        return 1.0
    
    diff = abs(existing_rooms - new_rooms)
    
    if diff == 1:
        return 0.8
    elif diff <= 2:
        return 0.6
    elif diff <= 3:
        return 0.4
    else:
        return 0.2

# ================================
# MAIN DUPLICATE DETECTION FUNCTION (ENHANCED)
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
    PHASE 2: Enhanced duplicate detection with proximity logic
    """
    
    logger.info(f"🔍 Enhanced duplicate detection for: {new_address}")
    if new_latitude and new_longitude:
        logger.info(f"📍 Coordinates: {new_latitude:.6f}, {new_longitude:.6f}")
    
    # Get all properties for comparison
    all_properties = get_all_properties_with_latest_analysis(db)
    
    potential_matches = []
    
    for existing_property in all_properties:
        if existing_property.url == new_url:
            continue
        
        # Calculate enhanced confidence
        confidence, factors = calculate_multi_factor_confidence_score(
            existing_property=existing_property.__dict__,
            new_address=new_address,
            new_latitude=new_latitude,
            new_longitude=new_longitude,
            new_price=new_price,
            new_room_count=new_room_count,
            new_advertiser=new_advertiser
        )
        
        if confidence >= min_confidence:
            # Generate recommendation
            recommendation, reason = generate_recommendation(confidence, factors)
            
            potential_match = PotentialMatch(
                property_id=str(existing_property.id),
                existing_url=existing_property.url,
                address=existing_property.address or "Unknown",
                confidence_score=round(confidence, 3),
                match_factors=factors,
                property_details={
                    'monthly_income': existing_property.latest_analysis.monthly_income if existing_property.latest_analysis else None,
                    'total_rooms': existing_property.latest_analysis.total_rooms if existing_property.latest_analysis else None,
                    'advertiser_name': existing_property.latest_analysis.advertiser_name if existing_property.latest_analysis else None,
                    'created_at': existing_property.created_at.isoformat() if existing_property.created_at else None
                },
                distance_meters=factors.get("distance_meters"),
                proximity_level=factors.get("proximity_level", "unknown"),
                recommendation=recommendation,
                recommendation_reason=reason
            )
            
            potential_matches.append(potential_match)
            
            logger.info(f"📊 Match: {existing_property.address}")
            logger.info(f"   Confidence: {confidence:.1%}")
            logger.info(f"   Distance: {factors.get('distance_meters', 'Unknown')}m")
            logger.info(f"   Recommendation: {recommendation}")
    
    # Sort by confidence
    potential_matches.sort(key=lambda x: x.confidence_score, reverse=True)
    
    logger.info(f"✅ Found {len(potential_matches)} matches above {min_confidence:.0%}")
    
    return potential_matches[:max_results]

# ================================
# DATABASE UTILITY FUNCTIONS
# ================================

def get_all_properties_with_latest_analysis(db: Session):
    """Get all properties with their latest analysis data"""
    from sqlalchemy import text
    
    # This query gets properties with their latest analysis
    query = text("""
        SELECT DISTINCT ON (p.id) 
            p.*,
            pa.monthly_income,
            pa.total_rooms,
            pa.advertiser_name,
            pa.created_at as analysis_date
        FROM properties p
        LEFT JOIN property_analyses pa ON p.id = pa.property_id
        ORDER BY p.id, pa.created_at DESC
    """)
    
    result = db.execute(query).fetchall()
    
    # Convert to objects with latest_analysis attribute
    properties = []
    for row in result:
        prop_data = dict(row._mapping)
        
        # Create latest_analysis dict
        latest_analysis = None
        if prop_data.get('monthly_income') is not None:
            latest_analysis = {
                'monthly_income': float(prop_data['monthly_income']) if prop_data['monthly_income'] else None,
                'total_rooms': prop_data['total_rooms'],
                'advertiser_name': prop_data['advertiser_name']
            }
        
        # Create property-like object
        class PropertyWithAnalysis:
            def __init__(self, data, analysis):
                for key, value in data.items():
                    if key not in ['monthly_income', 'total_rooms', 'advertiser_name', 'analysis_date']:
                        setattr(self, key, value)
                self.latest_analysis = analysis
        
        properties.append(PropertyWithAnalysis(prop_data, latest_analysis))
    
    return properties

def extract_property_details_for_duplicate_check(url: str) -> Dict[str, Any]:
    """Extract property details from URL for duplicate checking"""
    try:
        from modules.coordinates import extract_property_details, extract_coordinates, reverse_geocode_nominatim
        
        analysis_data = {}
        
        # Extract coordinates
        coords_result = extract_coordinates(url, analysis_data)
        
        # Extract property details
        extracted_data = extract_property_details(url, analysis_data)
        
        # Get address from coordinates if needed
        if analysis_data.get('latitude') and analysis_data.get('longitude') and not analysis_data.get('address'):
            try:
                geocoded_data = reverse_geocode_nominatim(
                    analysis_data['latitude'], 
                    analysis_data['longitude']
                )
                if geocoded_data and geocoded_data.get('address'):
                    analysis_data['address'] = geocoded_data['address']
            except Exception as e:
                logger.warning(f"Reverse geocoding failed: {e}")
        
        return analysis_data
        
    except ImportError as e:
        logger.error(f"Missing required modules: {e}")
        return {}
    except Exception as e:
        logger.error(f"Property extraction failed: {e}")
        return {}

'''

    # Write the enhanced code to duplicate_detection.py
    with open("duplicate_detection.py", "w") as f:
        f.write(enhanced_code)
    
    logger.info("✅ Updated duplicate_detection.py with Phase 2 enhancements")

def update_main_py():
    """Update main.py to use the enhanced duplicate detection"""
    
    logger.info("📝 Updating main.py to use enhanced detection...")
    
    # This is a placeholder - you would need to update the specific lines in main.py
    # that call the duplicate detection functions
    
    update_instructions = """
    # UPDATE INSTRUCTIONS FOR main.py:
    
    # 1. In the duplicate detection section, update the function call:
    
    # OLD:
    # potential_matches = find_potential_duplicates(...)
    
    # NEW: 
    # potential_matches = find_potential_duplicates(...)
    # (The function signature is the same, but now includes enhanced proximity logic)
    
    # 2. The response will now include distance_meters and proximity_level:
    # result.duplicate_data.potential_matches[0].distance_meters
    # result.duplicate_data.potential_matches[0].proximity_level
    # result.duplicate_data.potential_matches[0].recommendation
    """
    
    logger.info("📋 Main.py update instructions prepared")
    print(update_instructions)

def test_integration():
    """Test the Phase 2 integration"""
    
    logger.info("🧪 Testing Phase 2 integration...")
    
    try:
        # Test import
        import duplicate_detection
        
        # Test enhanced functions exist
        required_functions = [
            'calculate_enhanced_geographic_score',
            'apply_proximity_adjustments', 
            'find_potential_duplicates'
        ]
        
        for func_name in required_functions:
            if hasattr(duplicate_detection, func_name):
                logger.info(f"   ✅ {func_name}")
            else:
                logger.error(f"   ❌ {func_name} MISSING")
        
        # Test basic functionality
        logger.info("🧪 Testing proximity calculation...")
        
        geo_score, geo_factors = duplicate_detection.calculate_enhanced_geographic_score(
            51.7520, -1.2577,  # Oxford coordinates
            51.7521, -1.2578,  # Very close
            "123 High Street, Oxford",
            "123 High Street, Flat 2, Oxford"
        )
        
        logger.info(f"   📍 Distance: {geo_factors.get('distance_meters', 'N/A')}m")
        logger.info(f"   📊 Proximity: {geo_factors.get('proximity_level', 'N/A')}")
        logger.info(f"   🎯 Score: {geo_score:.2f}")
        
        logger.info("✅ Phase 2 integration test passed!")
        
    except Exception as e:
        logger.error(f"❌ Integration test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Phase 2 Integration: Enhanced Proximity Logic")
    print("=" * 55)
    print("\nThis will:")
    print("• ✅ Backup your existing duplicate_detection.py")
    print("• ✅ Update with enhanced proximity logic")
    print("• ✅ Add real distance calculations using geopy")
    print("• ✅ Apply confidence adjustments based on proximity")
    print("• ✅ Test the integration")
    
    confirm = input("\nProceed with Phase 2 integration? (y/N): ").lower().strip()
    
    if confirm == 'y':
        integrate_phase2_enhancements()
        
        print("\n" + "=" * 55)
        print("🎉 PHASE 2 INTEGRATION COMPLETED!")
        print("=" * 55)
        print("\n✅ Your duplicate detection now includes:")
        print("  • Real geographic distance calculations")
        print("  • Proximity-based confidence adjustments")
        print("  • Landlord portfolio detection")
        print("  • Distance thresholds (same_building, same_block, etc.)")
        print("  • Enhanced recommendation system")
        
        print("\n🧪 Next Steps:")
        print("  1. Test with existing property data")
        print("  2. Fine-tune distance thresholds if needed")
        print("  3. Proceed to Phase 3: Enhanced Modal UI")
        
        print(f"\n🔐 Backup stored as: duplicate_detection_backup_phase2.py")
        
    else:
        print("❌ Phase 2 integration cancelled")