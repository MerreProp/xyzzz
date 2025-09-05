# oxford_hmo_integration.py
"""
Oxford HMO Register Integration - Phase 1 Implementation
Simple, focused integration to get Oxford HMO data working with your existing system
"""

import requests
import pandas as pd
from io import StringIO
from sqlalchemy import Column, String, Integer, Date, DateTime, Text, Boolean, DECIMAL, ForeignKey, JSON, Index, or_
from sqlalchemy.orm import relationship, Session
from sqlalchemy.dialects.postgresql import UUID
from models import Base, Property, get_uuid_column, get_uuid_foreign_key
from database import SessionLocal
from coordinates import extract_coordinates, extract_postcode_from_address
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import logging
from geopy.distance import geodesic
import re

logger = logging.getLogger(__name__)

# =============================================================================
# 1. SIMPLIFIED DATABASE MODELS FOR OXFORD
# =============================================================================

class OxfordHMO(Base):
    """Simplified Oxford HMO register table"""
    __tablename__ = "oxford_hmo_register"
    
    id = get_uuid_column()
    
    # Oxford-specific fields (matching their CSV)
    case_number = Column(String(100), unique=True, nullable=False, index=True)
    location = Column(Text, nullable=False)  # Raw address from Oxford
    total_occupants = Column(Integer)
    total_units = Column(Integer)
    licence_commenced = Column(Date)
    licence_expires = Column(Date, index=True)
    
    # Standardized fields for matching
    standardized_address = Column(Text)
    postcode = Column(String(20), index=True)
    latitude = Column(DECIMAL(10, 8), index=True)
    longitude = Column(DECIMAL(11, 8), index=True)
    
    # Data quality fields
    geocoded_successfully = Column(Boolean, default=False)
    confidence_score = Column(DECIMAL(3, 2))  # 0-1 confidence in data quality
    processing_notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    property_matches = relationship("PropertyOxfordHMOMatch", back_populates="oxford_hmo")
    
    __table_args__ = (
        Index('idx_oxford_hmo_coords', 'latitude', 'longitude'),
        Index('idx_oxford_hmo_postcode_expires', 'postcode', 'licence_expires'),
    )


class PropertyOxfordHMOMatch(Base):
    """Links SpareRoom properties to Oxford HMO register"""
    __tablename__ = "property_oxford_hmo_matches"
    
    id = get_uuid_column()
    property_id = get_uuid_foreign_key("properties", nullable=False)
    oxford_hmo_id = get_uuid_foreign_key("oxford_hmo_register", nullable=False)
    
    # Match details
    match_type = Column(String(50), nullable=False)  # 'exact_postcode', 'close_proximity', 'street_match'
    confidence_score = Column(DECIMAL(3, 2), nullable=False)  # 0-1 confidence
    distance_meters = Column(DECIMAL(8, 2))  # Distance between addresses
    
    # Verification
    is_verified = Column(Boolean, default=False)
    verified_by = Column(String(100))
    verified_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    property = relationship("Property")
    oxford_hmo = relationship("OxfordHMO", back_populates="property_matches")
    
    __table_args__ = (
        Index('idx_property_oxford_match', 'property_id', 'oxford_hmo_id'),
    )


# =============================================================================
# 2. OXFORD DATA FETCHER
# =============================================================================

class OxfordHMOFetcher:
    """Fetches and processes Oxford HMO register data"""
    
    CSV_URL = "https://oxopendata.github.io/register-of-houses-in-multiple-occupation/data/hmo-simplified-register.csv"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'HMO-Analyser/1.0 (Property Analysis Tool)'
        })
    
    def fetch_oxford_data(self) -> List[Dict]:
        """Fetch Oxford HMO register from CSV"""
        try:
            logger.info("Fetching Oxford HMO register data...")
            response = self.session.get(self.CSV_URL, timeout=30)
            response.raise_for_status()
            
            # Parse CSV
            df = pd.read_csv(StringIO(response.text))
            
            # Clean and validate data
            df = df.dropna(subset=['Location'])  # Must have address
            df = df.drop_duplicates(subset=['Case Number'])  # Remove duplicates
            
            logger.info(f"Fetched {len(df)} Oxford HMO records")
            return df.to_dict('records')
            
        except Exception as e:
            logger.error(f"Error fetching Oxford HMO data: {e}")
            return []
    
    def process_oxford_record(self, record: Dict) -> Optional[OxfordHMO]:
        """Process a single Oxford HMO record"""
        try:
            # Extract basic information
            case_number = str(record.get('Case Number', '')).strip()
            location = str(record.get('Location', '')).strip()
            
            if not case_number or not location:
                return None
            
            # Parse numeric fields safely
            total_occupants = self._safe_int(record.get('Total Number Occupants'))
            total_units = self._safe_int(record.get('Total Number Units'))
            
            # Parse dates safely
            licence_commenced = self._safe_date(record.get('Licence Commenced'))
            licence_expires = self._safe_date(record.get('Licence Expires'))
            
            # Geocode the address
            full_address = f"{location}, Oxford, UK"
            coords = extract_coordinates(full_address)
            postcode = extract_postcode_from_address(location)
            
            # Calculate confidence score
            confidence = self._calculate_confidence(record, coords, postcode)
            
            # Create OxfordHMO object
            oxford_hmo = OxfordHMO(
                case_number=case_number,
                location=location,
                total_occupants=total_occupants,
                total_units=total_units,
                licence_commenced=licence_commenced,
                licence_expires=licence_expires,
                standardized_address=self._standardize_address(location),
                postcode=postcode,
                latitude=coords[0] if coords else None,
                longitude=coords[1] if coords else None,
                geocoded_successfully=coords is not None,
                confidence_score=confidence,
                processing_notes=self._generate_processing_notes(record, coords, postcode)
            )
            
            return oxford_hmo
            
        except Exception as e:
            logger.warning(f"Error processing Oxford record {record}: {e}")
            return None
    
    def _safe_int(self, value) -> Optional[int]:
        """Safely convert to integer"""
        if pd.isna(value) or value == '':
            return None
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return None
    
    def _safe_date(self, value) -> Optional[datetime]:
        """Safely convert to date"""
        if pd.isna(value) or value == '':
            return None
        try:
            return pd.to_datetime(value).date()
        except (ValueError, TypeError):
            return None
    
    def _standardize_address(self, address: str) -> str:
        """Standardize address format"""
        # Basic standardization - you can enhance this
        address = address.strip()
        address = re.sub(r'\s+', ' ', address)  # Remove extra spaces
        address = address.replace(',', ', ')  # Standardize comma spacing
        return address
    
    def _calculate_confidence(self, record: Dict, coords: Optional[Tuple], postcode: Optional[str]) -> float:
        """Calculate confidence score for Oxford record"""
        score = 0.0
        
        # Has coordinates
        if coords:
            score += 0.4
        
        # Has postcode
        if postcode:
            score += 0.3
        
        # Has occupancy info
        if self._safe_int(record.get('Total Number Occupants')):
            score += 0.1
        
        # Has unit info
        if self._safe_int(record.get('Total Number Units')):
            score += 0.1
        
        # Has valid dates
        if self._safe_date(record.get('Licence Expires')):
            score += 0.1
        
        return min(score, 1.0)
    
    def _generate_processing_notes(self, record: Dict, coords: Optional[Tuple], postcode: Optional[str]) -> str:
        """Generate processing notes"""
        notes = []
        
        if not coords:
            notes.append("Failed to geocode address")
        if not postcode:
            notes.append("No postcode extracted")
        if not self._safe_int(record.get('Total Number Occupants')):
            notes.append("Missing occupant count")
        
        return "; ".join(notes) if notes else "Processed successfully"


# =============================================================================
# 3. ADDRESS MATCHING FOR OXFORD
# =============================================================================

class OxfordAddressMatcher:
    """Match SpareRoom properties to Oxford HMO register"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def find_oxford_matches(self, property_id: str) -> List[Dict]:
        """Find Oxford HMO matches for a SpareRoom property"""
        from crud import PropertyCRUD
        
        property_obj = PropertyCRUD.get_property_by_id(self.db, property_id)
        if not property_obj:
            return []
        
        matches = []
        
        # Strategy 1: Exact postcode match
        if property_obj.postcode:
            postcode_matches = self._find_by_postcode(property_obj)
            matches.extend(postcode_matches)
        
        # Strategy 2: Geographic proximity (within 50m for Oxford - it's a dense city)
        if property_obj.latitude and property_obj.longitude:
            proximity_matches = self._find_by_proximity(property_obj, radius_meters=50)
            matches.extend(proximity_matches)
        
        # Remove duplicates and sort by confidence
        unique_matches = {}
        for match in matches:
            hmo_id = match['oxford_hmo_id']
            if hmo_id not in unique_matches or match['confidence_score'] > unique_matches[hmo_id]['confidence_score']:
                unique_matches[hmo_id] = match
        
        return sorted(unique_matches.values(), key=lambda x: x['confidence_score'], reverse=True)
    
    def _find_by_postcode(self, property_obj) -> List[Dict]:
        """Find matches by exact postcode"""
        matches = []
        
        oxford_hmos = (self.db.query(OxfordHMO)
                      .filter(OxfordHMO.postcode == property_obj.postcode)
                      .all())
        
        for hmo in oxford_hmos:
            confidence = 0.8  # High confidence for postcode match
            distance = self._calculate_distance(property_obj, hmo)
            
            # Boost confidence if very close
            if distance and distance < 25:  # Within 25 meters
                confidence = 0.95
            
            matches.append({
                'oxford_hmo_id': str(hmo.id),
                'match_type': 'exact_postcode',
                'confidence_score': confidence,
                'distance_meters': distance,
                'hmo_data': hmo
            })
        
        return matches
    
    def _find_by_proximity(self, property_obj, radius_meters: int = 50) -> List[Dict]:
        """Find matches by geographic proximity"""
        matches = []
        
        # Get Oxford HMOs with coordinates
        oxford_hmos = (self.db.query(OxfordHMO)
                      .filter(
                          OxfordHMO.latitude.isnot(None),
                          OxfordHMO.longitude.isnot(None)
                      )
                      .all())
        
        for hmo in oxford_hmos:
            distance = self._calculate_distance(property_obj, hmo)
            
            if distance and distance <= radius_meters:
                # Confidence decreases with distance
                confidence = max(0.3, 1.0 - (distance / radius_meters) * 0.4)
                
                matches.append({
                    'oxford_hmo_id': str(hmo.id),
                    'match_type': 'close_proximity',
                    'confidence_score': confidence,
                    'distance_meters': distance,
                    'hmo_data': hmo
                })
        
        return matches
    
    def _calculate_distance(self, property_obj, oxford_hmo) -> Optional[float]:
        """Calculate distance between property and Oxford HMO"""
        if not all([property_obj.latitude, property_obj.longitude, 
                   oxford_hmo.latitude, oxford_hmo.longitude]):
            return None
        
        try:
            point1 = (float(property_obj.latitude), float(property_obj.longitude))
            point2 = (float(oxford_hmo.latitude), float(oxford_hmo.longitude))
            return geodesic(point1, point2).meters
        except:
            return None
    
    def create_match(self, property_id: str, oxford_hmo_id: str, 
                    match_type: str, confidence: float, distance: Optional[float] = None) -> PropertyOxfordHMOMatch:
        """Create a verified match"""
        match = PropertyOxfordHMOMatch(
            property_id=property_id,
            oxford_hmo_id=oxford_hmo_id,
            match_type=match_type,
            confidence_score=confidence,
            distance_meters=distance,
            is_verified=confidence >= 0.8,  # Auto-verify high confidence matches
            verified_by='system_auto' if confidence >= 0.8 else None,
            verified_at=datetime.utcnow() if confidence >= 0.8 else None
        )
        
        self.db.add(match)
        self.db.commit()
        self.db.refresh(match)
        
        return match


# =============================================================================
# 4. OXFORD INTEGRATION ORCHESTRATOR
# =============================================================================

class OxfordHMOIntegrator:
    """Main class to orchestrate Oxford HMO integration"""
    
    def __init__(self):
        self.fetcher = OxfordHMOFetcher()
    
    def update_oxford_register(self) -> Dict[str, int]:
        """Update Oxford HMO register data"""
        db = SessionLocal()
        
        try:
            # Fetch latest data
            raw_data = self.fetcher.fetch_oxford_data()
            if not raw_data:
                return {'error': 'No data fetched'}
            
            # Clear existing Oxford data
            deleted_count = db.query(OxfordHMO).delete()
            logger.info(f"Cleared {deleted_count} existing Oxford HMO records")
            
            # Process and save new data
            processed_count = 0
            geocoded_count = 0
            
            for record in raw_data:
                oxford_hmo = self.fetcher.process_oxford_record(record)
                if oxford_hmo:
                    db.add(oxford_hmo)
                    processed_count += 1
                    if oxford_hmo.geocoded_successfully:
                        geocoded_count += 1
            
            db.commit()
            
            logger.info(f"Processed {processed_count} Oxford HMO records ({geocoded_count} geocoded)")
            
            return {
                'total_records': len(raw_data),
                'processed_records': processed_count,
                'geocoded_records': geocoded_count,
                'geocoding_success_rate': (geocoded_count / processed_count * 100) if processed_count > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error updating Oxford register: {e}")
            db.rollback()
            return {'error': str(e)}
        
        finally:
            db.close()
    
    def match_oxford_properties(self, limit: int = 1000) -> Dict[str, int]:
        """Match SpareRoom properties to Oxford HMO register"""
        db = SessionLocal()
        matcher = OxfordAddressMatcher(db)
        
        try:
            # Get Oxford properties (properties with city = 'Oxford' or postcode starting with 'OX')
            from crud import PropertyCRUD
            
            oxford_properties = (db.query(db.query(Property).filter(
                or_(
                    Property.city.ilike('%oxford%'),
                    Property.postcode.ilike('OX%'),
                    Property.address.ilike('%oxford%')
                )
            ).limit(limit).all()))
            
            total_matches = 0
            high_confidence_matches = 0
            
            for property_obj in oxford_properties:
                # Skip if already has Oxford matches
                existing_matches = (db.query(PropertyOxfordHMOMatch)
                                  .filter(PropertyOxfordHMOMatch.property_id == str(property_obj.id))
                                  .count())
                
                if existing_matches > 0:
                    continue
                
                # Find potential matches
                potential_matches = matcher.find_oxford_matches(str(property_obj.id))
                
                # Create high-confidence matches automatically
                for match in potential_matches:
                    if match['confidence_score'] >= 0.7:  # Lower threshold for Oxford
                        try:
                            matcher.create_match(
                                str(property_obj.id),
                                match['oxford_hmo_id'],
                                match['match_type'],
                                match['confidence_score'],
                                match.get('distance_meters')
                            )
                            total_matches += 1
                            if match['confidence_score'] >= 0.8:
                                high_confidence_matches += 1
                            break  # Only create one match per property
                        except Exception as e:
                            logger.warning(f"Error creating Oxford match: {e}")
            
            logger.info(f"Created {total_matches} Oxford matches ({high_confidence_matches} high confidence)")
            
            return {
                'properties_checked': len(oxford_properties),
                'total_matches_created': total_matches,
                'high_confidence_matches': high_confidence_matches
            }
            
        except Exception as e:
            logger.error(f"Error matching Oxford properties: {e}")
            return {'error': str(e)}
        
        finally:
            db.close()
    
    def get_oxford_statistics(self) -> Dict:
        """Get Oxford HMO register statistics"""
        db = SessionLocal()
        
        try:
            # Basic counts
            total_hmos = db.query(OxfordHMO).count()
            geocoded_hmos = db.query(OxfordHMO).filter(OxfordHMO.geocoded_successfully == True).count()
            active_licences = db.query(OxfordHMO).filter(
                or_(
                    OxfordHMO.licence_expires.is_(None),
                    OxfordHMO.licence_expires >= datetime.now().date()
                )
            ).count()
            
            # Match statistics
            total_matches = db.query(PropertyOxfordHMOMatch).count()
            verified_matches = db.query(PropertyOxfordHMOMatch).filter(
                PropertyOxfordHMOMatch.is_verified == True
            ).count()
            
            # Average confidence
            from sqlalchemy import func
            avg_confidence = db.query(func.avg(PropertyOxfordHMOMatch.confidence_score)).scalar() or 0
            
            return {
                'total_hmo_records': total_hmos,
                'geocoded_records': geocoded_hmos,
                'geocoding_success_rate': (geocoded_hmos / total_hmos * 100) if total_hmos > 0 else 0,
                'active_licences': active_licences,
                'expired_licences': total_hmos - active_licences,
                'total_property_matches': total_matches,
                'verified_matches': verified_matches,
                'average_match_confidence': float(avg_confidence),
                'match_verification_rate': (verified_matches / total_matches * 100) if total_matches > 0 else 0
            }
            
        finally:
            db.close()


# =============================================================================
# 5. API ENDPOINTS FOR OXFORD
# =============================================================================

def add_oxford_hmo_endpoints(app):
    """Add Oxford HMO endpoints to FastAPI app"""
    
    integrator = OxfordHMOIntegrator()
    
    @app.post("/api/oxford-hmo/update")
    async def update_oxford_register():
        """Update Oxford HMO register"""
        try:
            result = integrator.update_oxford_register()
            return result
        except Exception as e:
            from fastapi import HTTPException
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/oxford-hmo/match-properties")
    async def match_oxford_properties():
        """Match properties to Oxford HMO register"""
        try:
            result = integrator.match_oxford_properties()
            return result
        except Exception as e:
            from fastapi import HTTPException
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/oxford-hmo/statistics")
    async def get_oxford_statistics():
        """Get Oxford HMO statistics"""
        try:
            stats = integrator.get_oxford_statistics()
            return stats
        except Exception as e:
            from fastapi import HTTPException
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/oxford-hmo/property/{property_id}")
    async def get_property_oxford_status(property_id: str):
        """Get Oxford HMO status for a specific property"""
        db = SessionLocal()
        try:
            matches = (db.query(PropertyOxfordHMOMatch)
                      .join(OxfordHMO)
                      .filter(PropertyOxfordHMOMatch.property_id == property_id)
                      .order_by(PropertyOxfordHMOMatch.confidence_score.desc())
                      .all())
            
            if not matches:
                return {
                    'is_oxford_hmo': False,
                    'confidence': 0.0,
                    'matches': []
                }
            
            best_match = matches[0]
            hmo = best_match.oxford_hmo
            
            return {
                'is_oxford_hmo': True,
                'confidence': float(best_match.confidence_score),
                'best_match': {
                    'case_number': hmo.case_number,
                    'address': hmo.location,
                    'total_occupants': hmo.total_occupants,
                    'total_units': hmo.total_units,
                    'licence_expires': hmo.licence_expires.isoformat() if hmo.licence_expires else None,
                    'match_type': best_match.match_type,
                    'distance_meters': float(best_match.distance_meters) if best_match.distance_meters else None,
                    'is_verified': best_match.is_verified
                },
                'all_matches': len(matches)
            }
            
        finally:
            db.close()


# =============================================================================
# 6. ENHANCED PROPERTY DATA WITH OXFORD HMO STATUS
# =============================================================================

def enhance_properties_with_oxford_hmo(properties: List[Dict]) -> List[Dict]:
    """Add Oxford HMO status to property data"""
    db = SessionLocal()
    
    try:
        for property_data in properties:
            property_id = property_data.get('property_id')
            if not property_id:
                continue
            
            # Get Oxford HMO matches
            matches = (db.query(PropertyOxfordHMOMatch)
                      .join(OxfordHMO)
                      .filter(PropertyOxfordHMOMatch.property_id == property_id)
                      .order_by(PropertyOxfordHMOMatch.confidence_score.desc())
                      .all())
            
            if matches:
                best_match = matches[0]
                hmo = best_match.oxford_hmo
                
                property_data.update({
                    'is_oxford_hmo': True,
                    'oxford_hmo_confidence': float(best_match.confidence_score),
                    'oxford_hmo_case_number': hmo.case_number,
                    'oxford_hmo_occupants': hmo.total_occupants,
                    'oxford_hmo_expires': hmo.licence_expires.isoformat() if hmo.licence_expires else None,
                    'oxford_hmo_verified': best_match.is_verified
                })
            else:
                property_data.update({
                    'is_oxford_hmo': False,
                    'oxford_hmo_confidence': 0.0
                })
        
        return properties
        
    finally:
        db.close()


# =============================================================================
# 7. OXFORD SETUP AND TESTING
# =============================================================================

def setup_oxford_integration():
    """Setup Oxford HMO integration"""
    from database import engine
    
    print("🏛️ Setting up Oxford HMO integration...")
    
    # Create tables
    try:
        OxfordHMO.__table__.create(engine, checkfirst=True)
        PropertyOxfordHMOMatch.__table__.create(engine, checkfirst=True)
        print("✅ Oxford HMO tables created")
    except Exception as e:
        print(f"⚠️ Table creation warning: {e}")
    
    # Initialize integrator
    integrator = OxfordHMOIntegrator()
    
    # Update Oxford register
    print("📥 Fetching Oxford HMO register...")
    update_result = integrator.update_oxford_register()
    
    if 'error' in update_result:
        print(f"❌ Error updating Oxford register: {update_result['error']}")
        return False
    
    print(f"✅ Oxford register updated:")
    print(f"  - {update_result['processed_records']} records processed")
    print(f"  - {update_result['geocoded_records']} successfully geocoded")
    print(f"  - {update_result['geocoding_success_rate']:.1f}% geocoding success rate")
    
    # Match properties
    print("🔗 Matching properties to Oxford HMO register...")
    match_result = integrator.match_oxford_properties()
    
    if 'error' in match_result:
        print(f"❌ Error matching properties: {match_result['error']}")
        return False
    
    print(f"✅ Property matching completed:")
    print(f"  - {match_result['properties_checked']} properties checked")
    print(f"  - {match_result['total_matches_created']} matches created")
    print(f"  - {match_result['high_confidence_matches']} high confidence matches")
    
    # Get statistics
    stats = integrator.get_oxford_statistics()
    print(f"\n📊 Oxford HMO Statistics:")
    print(f"  - Total HMO records: {stats['total_hmo_records']}")
    print(f"  - Active licences: {stats['active_licences']}")
    print(f"  - Property matches: {stats['total_property_matches']}")
    print(f"  - Average match confidence: {stats['average_match_confidence']:.2f}")
    
    print("\n🎉 Oxford HMO integration setup complete!")
    return True


def test_oxford_integration():
    """Test Oxford HMO integration"""
    print("🧪 Testing Oxford HMO integration...")
    
    integrator = OxfordHMOIntegrator()
    
    # Test 1: Check data quality
    stats = integrator.get_oxford_statistics()
    print(f"📊 Current statistics: {stats}")
    
    # Test 2: Test a specific property match
    db = SessionLocal()
    try:
        # Find a property in Oxford
        from models import Property
        oxford_property = (db.query(Property)
                          .filter(Property.city.ilike('%oxford%'))
                          .first())
        
        if oxford_property:
            matcher = OxfordAddressMatcher(db)
            matches = matcher.find_oxford_matches(str(oxford_property.id))
            print(f"🔍 Test property {oxford_property.address}: {len(matches)} potential matches")
            
            if matches:
                best_match = matches[0]
                print(f"  Best match: {best_match['confidence_score']:.2f} confidence")
        
    finally:
        db.close()
    
    print("✅ Oxford integration test completed")


if __name__ == "__main__":
    # Run setup
    success = setup_oxford_integration()
    
    if success:
        # Test the integration
        test_oxford_integration()
        
        print("\n📋 Next steps:")
        print("1. Add Oxford endpoints to your main.py FastAPI app")
        print("2. Update your /api/properties endpoint to include Oxford HMO data")
        print("3. Update your map frontend to show Oxford HMO status")
        print("4. Set up daily updates for Oxford register")
    else:
        print("❌ Oxford integration setup failed. Check logs for details.")