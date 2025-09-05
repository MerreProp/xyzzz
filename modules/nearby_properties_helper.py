# nearby_properties_helper.py
"""
Phase 4: Helper functions for nearby properties context
Additional utility functions for enhanced duplicate detection
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

def calculate_property_density(
    db: Session,
    latitude: float,
    longitude: float,
    radius_meters: int = 500
) -> Dict[str, Any]:
    """Calculate property density in area for context"""
    
    try:
        density_query = db.execute(
            text("""
            SELECT 
                COUNT(*) as total_properties,
                COUNT(DISTINCT pa.advertiser_name) as unique_advertisers,
                AVG(pa.monthly_income) as avg_income,
                AVG(pa.total_rooms) as avg_rooms
            FROM properties p
            LEFT JOIN property_analyses pa ON p.id = pa.property_id
            WHERE p.latitude IS NOT NULL 
              AND p.longitude IS NOT NULL
              AND (6371000 * acos(cos(radians(:lat)) * cos(radians(p.latitude)) * 
                   cos(radians(p.longitude) - radians(:lng)) + sin(radians(:lat)) * 
                   sin(radians(p.latitude)))) <= :radius
            """),
            {"lat": latitude, "lng": longitude, "radius": radius_meters}
        ).fetchone()
        
        if density_query:
            return {
                "total_properties": density_query.total_properties or 0,
                "unique_advertisers": density_query.unique_advertisers or 0,
                "avg_monthly_income": float(density_query.avg_income) if density_query.avg_income else None,
                "avg_rooms": float(density_query.avg_rooms) if density_query.avg_rooms else None,
                "radius_meters": radius_meters,
                "density_per_km2": round((density_query.total_properties or 0) / (3.14159 * (radius_meters/1000)**2), 2)
            }
        
        return {"total_properties": 0, "radius_meters": radius_meters}
        
    except Exception as e:
        logger.error(f"Error calculating property density: {e}")
        return {"error": str(e)}

def find_landlord_portfolio_properties(
    db: Session,
    advertiser_name: str,
    limit: int = 10
) -> List[Dict]:
    """Find other properties by same landlord/advertiser"""
    
    if not advertiser_name or len(advertiser_name) < 3:
        return []
    
    try:
        portfolio_query = db.execute(
            text("""
            SELECT DISTINCT
                p.id,
                p.address,
                p.postcode,
                pa.total_rooms,
                pa.monthly_income,
                pa.created_at
            FROM properties p
            JOIN property_analyses pa ON p.id = pa.property_id
            WHERE LOWER(pa.advertiser_name) ILIKE LOWER(:advertiser)
            ORDER BY pa.created_at DESC
            LIMIT :limit
            """),
            {"advertiser": f"%{advertiser_name}%", "limit": limit}
        ).fetchall()
        
        return [
            {
                "property_id": str(row.id),
                "address": row.address,
                "postcode": row.postcode,
                "total_rooms": row.total_rooms,
                "monthly_income": float(row.monthly_income) if row.monthly_income else None,
                "added_date": row.created_at.isoformat() if row.created_at else None
            }
            for row in portfolio_query
        ]
        
    except Exception as e:
        logger.error(f"Error finding portfolio properties: {e}")
        return []

def get_area_market_context(
    db: Session,
    postcode_prefix: str,
    property_type: str = "hmo"
) -> Dict[str, Any]:
    """Get market context for the area"""
    
    try:
        # Extract first part of postcode (e.g., "OX1" from "OX1 2AB")
        area_prefix = postcode_prefix.split()[0] if postcode_prefix else ""
        
        market_query = db.execute(
            text("""
            SELECT 
                COUNT(*) as total_properties,
                AVG(pa.monthly_income) as avg_income,
                MIN(pa.monthly_income) as min_income,
                MAX(pa.monthly_income) as max_income,
                AVG(pa.total_rooms) as avg_rooms,
                COUNT(DISTINCT pa.advertiser_name) as unique_landlords
            FROM properties p
            JOIN property_analyses pa ON p.id = pa.property_id
            WHERE p.postcode ILIKE :area_pattern
              AND pa.monthly_income IS NOT NULL
            """),
            {"area_pattern": f"{area_prefix}%"}
        ).fetchone()
        
        if market_query and market_query.total_properties > 0:
            return {
                "area": area_prefix,
                "total_properties": market_query.total_properties,
                "avg_monthly_income": float(market_query.avg_income) if market_query.avg_income else None,
                "income_range": {
                    "min": float(market_query.min_income) if market_query.min_income else None,
                    "max": float(market_query.max_income) if market_query.max_income else None
                },
                "avg_rooms": float(market_query.avg_rooms) if market_query.avg_rooms else None,
                "unique_landlords": market_query.unique_landlords,
                "market_activity": "high" if market_query.total_properties > 50 else "medium" if market_query.total_properties > 20 else "low"
            }
        
        return {"area": area_prefix, "total_properties": 0}
        
    except Exception as e:
        logger.error(f"Error getting market context: {e}")
        return {"error": str(e)}

def analyze_portfolio_patterns(
    db: Session,
    advertiser_name: str,
    property_latitude: float = None,
    property_longitude: float = None
) -> Dict[str, Any]:
    """Analyze patterns in landlord's property portfolio"""
    
    try:
        # Get portfolio properties
        portfolio = find_landlord_portfolio_properties(db, advertiser_name, limit=20)
        
        if len(portfolio) < 2:
            return {"portfolio_size": len(portfolio), "analysis": "Insufficient data"}
        
        # Calculate portfolio metrics
        total_rooms = [p["total_rooms"] for p in portfolio if p["total_rooms"]]
        incomes = [p["monthly_income"] for p in portfolio if p["monthly_income"]]
        
        analysis = {
            "portfolio_size": len(portfolio),
            "avg_rooms_per_property": sum(total_rooms) / len(total_rooms) if total_rooms else None,
            "avg_income_per_property": sum(incomes) / len(incomes) if incomes else None,
            "portfolio_consistency": "high" if len(set(total_rooms)) <= 2 else "medium" if len(set(total_rooms)) <= 4 else "low",
            "geographic_spread": "unknown"  # Would need coordinates to calculate
        }
        
        # Portfolio patterns
        if analysis["avg_rooms_per_property"]:
            if analysis["avg_rooms_per_property"] > 8:
                analysis["property_type"] = "large_hmo"
            elif analysis["avg_rooms_per_property"] > 5:
                analysis["property_type"] = "medium_hmo"
            else:
                analysis["property_type"] = "small_hmo_or_houseshare"
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error analyzing portfolio patterns: {e}")
        return {"error": str(e)}

def get_duplicate_confidence_breakdown(match_factors: Dict) -> Dict[str, Any]:
    """Get detailed breakdown of confidence factors for UI display"""
    
    breakdown = {
        "primary_factors": [],
        "supporting_factors": [],
        "concerns": [],
        "overall_assessment": ""
    }
    
    # Analyze each factor
    for factor, value in match_factors.items():
        if not isinstance(value, (int, float)):
            continue
            
        factor_info = {
            "name": factor.replace("_", " ").title(),
            "value": value,
            "weight": "high" if value > 0.8 else "medium" if value > 0.5 else "low"
        }
        
        if value > 0.8:
            breakdown["primary_factors"].append(factor_info)
        elif value > 0.4:
            breakdown["supporting_factors"].append(factor_info)
        else:
            breakdown["concerns"].append(factor_info)
    
    # Generate overall assessment
    primary_count = len(breakdown["primary_factors"])
    concern_count = len(breakdown["concerns"])
    
    if primary_count >= 2 and concern_count == 0:
        breakdown["overall_assessment"] = "Strong duplicate candidate"
    elif primary_count >= 1 and concern_count <= 1:
        breakdown["overall_assessment"] = "Likely duplicate - review recommended"
    elif concern_count >= 2:
        breakdown["overall_assessment"] = "Unlikely duplicate - significant differences"
    else:
        breakdown["overall_assessment"] = "Unclear - manual review required"
    
    return breakdown

def format_distance_description(distance_meters: float) -> str:
    """Format distance in human-readable format"""
    
    if distance_meters < 10:
        return f"{distance_meters:.0f}m (same building)"
    elif distance_meters < 50:
        return f"{distance_meters:.0f}m (same block)"
    elif distance_meters < 200:
        return f"{distance_meters:.0f}m (same street)"
    elif distance_meters < 1000:
        return f"{distance_meters:.0f}m (walking distance)"
    else:
        return f"{distance_meters/1000:.1f}km (different area)"

def generate_recommendation_with_reasoning(
    confidence_score: float,
    match_factors: Dict,
    nearby_properties: List[Dict] = None
) -> tuple[str, str]:
    """Generate recommendation with detailed reasoning"""
    
    distance = match_factors.get("distance_meters", float('inf'))
    same_advertiser = match_factors.get("advertiser_similarity", 0) > 0.8
    address_similar = match_factors.get("address_similarity", 0) > 0.7
    
    nearby_count = len(nearby_properties) if nearby_properties else 0
    
    # Auto-link criteria
    if confidence_score >= 0.85 and distance <= 50 and same_advertiser:
        return "auto_link", "High confidence with same location and advertiser"
    
    # Separate criteria  
    if confidence_score < 0.4 and distance > 500:
        return "keep_separate", "Low confidence with significant distance"
    
    # User choice with reasoning
    reasons = []
    
    if distance <= 10:
        reasons.append("same building")
    elif distance <= 100:
        reasons.append("very close proximity")
    
    if same_advertiser:
        reasons.append("same landlord")
    
    if address_similar:
        reasons.append("similar addresses")
    
    if nearby_count > 3:
        reasons.append(f"{nearby_count} other properties nearby")
    
    reason_text = f"Moderate confidence. Consider: {', '.join(reasons)}" if reasons else "Mixed signals - careful review needed"
    
    return "user_choice", reason_text