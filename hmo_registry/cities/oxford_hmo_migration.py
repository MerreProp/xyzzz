# oxford_unified_integration.py
"""
Oxford HMO Integration using the unified multi-city schema
Works with the tables created by hmo_migration.py
"""

import requests
import pandas as pd
from io import StringIO
from sqlalchemy import Column, String, Integer, Date, DateTime, Text, Boolean, DECIMAL, ForeignKey, JSON, Index, or_, func
from sqlalchemy.orm import relationship, Session
from sqlalchemy.dialects.postgresql import UUID
from models import Base, get_uuid_column, get_uuid_foreign_key
from database import SessionLocal
from modules.coordinates import extract_coordinates, extract_postcode_from_address
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import logging
from geopy.distance import geodesic
import re

logger = logging.getLogger(__name__)

# =============================================================================
# 1. UNIFIED SCHEMA MODELS (Use tables from hmo_migration.py)
# =============================================================================

class HMORegister(Base):
    """Unified HMO register table for all cities"""
    __tablename__ = "hmo_registers"
    
    id = get_uuid_column()
    
    # Source information
    city = Column(String(100), nullable=False, index=True)
    source_type = Column(String(50), nullable=False)
    source_url = Column(Text)
    last_updated = Column(DateTime, default=datetime.utcnow)
    data_freshness = Column(String(20))
    
    # Property identification
    external_case_number = Column(String(100), index=True)
    raw_address = Column(Text, nullable=False)
    standardized_address = Column(Text)
    postcode = Column(String(20), index=True)
    latitude = Column(DECIMAL(10, 8), index=True)
    longitude = Column(DECIMAL(11, 8), index=True)
    
    # Address components
    street_number = Column(String(20))
    street_name = Column(String(200), index=True)
    area = Column(String(100), index=True)
    district = Column(String(100))
    county = Column(String(100))
    
    # HMO details
    total_occupants = Column(Integer)
    total_units = Column(Integer)
    property_type = Column(String(100))
    
    # Licensing information
    licence_start_date = Column(Date, index=True)
    licence_expiry_date = Column(Date, index=True)
    licence_status = Column(String(50), index=True)
    
    # Landlord information
    licence_holder_name = Column(String(500))
    licence_holder_type = Column(String(100))
    management_company = Column(String(500))
    
    # Metadata
    raw_data = Column(JSON)
    processing_notes = Column(Text)
    confidence_score = Column(DECIMAL(3, 2))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    property_matches = relationship("PropertyHMOMatch", back_populates="hmo_register")


class PropertyHMOMatch(Base):
    """Links SpareRoom properties to HMO register entries"""
    __tablename__ = "property_hmo_matches"
    
    id = get_uuid_column()
    property_id = get_uuid_foreign_key("properties", nullable=False)
    hmo_register_id = get_uuid_foreign_key("hmo_registers", nullable=False)
    
    # Match details
    match_type = Column(String(50), nullable=False)
    confidence_score = Column(DECIMAL(3, 2), nullable=False)
    distance_meters = Column(DECIMAL(8, 2))
    address_similarity = Column(DECIMAL(3, 2))
    postcode_match = Column(Boolean, default=False)
    street_match = Column(Boolean, default=False)
    
    # Verification
    verified_status = Column(String(20), default='unverified')
    verified_by = Column(String(100))
    verified_at = Column(DateTime)
    verification_notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    property = relationship("Property")
    hmo_register = relationship("HMORegister", back_populates="property_matches")


# =============================================================================
# 2. OXFORD DATA FETCHER (Using Unified Schema)
# =============================================================================

class OxfordHMOFetcher:
    """Fetches and processes Oxford HMO register data for unified schema"""
    
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
    
    def process_oxford_record(self, record: Dict) -> Optional[HMORegister]:
        """Process a single Oxford HMO record into unified schema"""
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
            licence_start_date = self._safe_date(record.get('Licence Commenced'))
            licence_expiry_date = self._safe_date(record.get('Licence Expires'))
            
            # Determine licence status
            licence_status = 'active'
            if licence_expiry_date and licence_expiry_date < datetime.now().date():
                licence_status = 'expired'
            elif not licence_expiry_date:
                licence_status = 'unknown'
            
            # Geocode the address
            full_address = f"{location}, Oxford, UK"
            coords = extract_coordinates(full_address)
            postcode = extract_postcode_from_address(location)
            
            # Parse address components
            address_parts = self._parse_address_components(location)
            
            # Calculate confidence score
            confidence = self._calculate_confidence(record, coords, postcode)
            
            # Create unified HMORegister object
            hmo_register = HMORegister(
                # Source information
                city='oxford',
                source_type='csv',
                source_url=self.CSV_URL,
                last_updated=datetime.utcnow(),
                data_freshness='monthly',
                
                # Property identification
                external_case_number=case_number,
                raw_address=location,
                standardized_address=self._standardize_address(location),
                postcode=postcode,
                latitude=coords[0] if coords else None,
                longitude=coords[1] if coords else None,
                
                # Address components
                street_number=address_parts.get('number'),
                street_name=address_parts.get('street'),
                area=address_parts.get('area'),
                district='Oxford',
                county='Oxfordshire',
                
                # HMO details
                total_occupants=total_occupants,
                total_units=total_units,
                property_type='HMO',  # Oxford register is all HMOs
                
                # Licensing information
                licence_start_date=licence_start_date,
                licence_expiry_date=licence_expiry_date,
                licence_status=licence_status,
                
                # Metadata
                raw_data=record,
                processing_notes=self._generate_processing_notes(record, coords, postcode),
                confidence_score=confidence
            )
            
            return hmo_register
            
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
    
    def _parse_address_components(self, address: str) -> Dict[str, str]:
        """Parse address into components"""
        parts = {}
        
        # Extract house number
        number_match = re.match(r'^(\d+[a-zA-Z]?)', address.strip())
        if number_match:
            parts['number'] = number_match.group(1)
        
        # Extract street name (simplified)
        address_parts = address.split(',')
        if len(address_parts) > 0:
            street_part = address_parts[0].strip()
            # Remove house number from street
            if parts.get('number'):
                street_part = street_part.replace(parts['number'], '').strip()
            parts['street'] = street_part
        
        # Extract area (last part before postcode, if multiple comma-separated parts)
        if len(address_parts) > 1:
            parts['area'] = address_parts[-1].strip()
        
        return parts
    
    def _standardize_address(self, address: str) -> str:
        """Standardize address format"""
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
# 3. ADDRESS MATCHING FOR UNIFIED SCHEMA
# =============================================================================

class UnifiedAddressMatcher:
    """Match SpareRoom properties to unified HMO register"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def find_hmo_matches(self, property_id: str, city: str = None) -> List[Dict]:
        """Find HMO matches for a SpareRoom property"""
        from crud import PropertyCRUD
        
        property_obj = PropertyCRUD.get_property_by_id(self.db, property_id)
        if not property_obj:
            return []
        
        matches = []
        
        # Build query for HMO registers
        query = self.db.query(HMORegister)
        if city:
            query = query.filter(HMORegister.city == city.lower())
        
        # Strategy 1: Exact postcode match
        if property_obj.postcode:
            postcode_matches = self._find_by_postcode(property_obj, query)
            matches.extend(postcode_matches)
        
        # Strategy 2: Geographic proximity
        if property_obj.latitude and property_obj.longitude:
            proximity_matches = self._find_by_proximity(property_obj, query, radius_meters=50)
            matches.extend(proximity_matches)
        
        # Remove duplicates and sort by confidence
        unique_matches = {}
        for match in matches:
            hmo_id = match['hmo_register_id']
            if hmo_id not in unique_matches or match['confidence_score'] > unique_matches[hmo_id]['confidence_score']:
                unique_matches[hmo_id] = match
        
        return sorted(unique_matches.values(), key=lambda x: x['confidence_score'], reverse=True)
    
    def _find_by_postcode(self, property_obj, base_query) -> List[Dict]:
        """Find matches by exact postcode"""
        matches = []
        
        hmo_registers = base_query.filter(HMORegister.postcode == property_obj.postcode).all()
        
        for hmo in hmo_registers:
            confidence = 0.8  # High confidence for postcode match
            distance = self._calculate_distance(property_obj, hmo)
            
            # Boost confidence if very close
            if distance and distance < 25:  # Within 25 meters
                confidence = 0.95
            
            matches.append({
                'hmo_register_id': str(hmo.id),
                'match_type': 'exact_postcode',
                'confidence_score': confidence,
                'distance_meters': distance,
                'hmo_data': hmo
            })
        
        return matches
    
    def _find_by_proximity(self, property_obj, base_query, radius_meters: int = 50) -> List[Dict]:
        """Find matches by geographic proximity"""
        matches = []
        
        hmo_registers = base_query.filter(
            HMORegister.latitude.isnot(None),
            HMORegister.longitude.isnot(None)
        ).all()
        
        for hmo in hmo_registers:
            distance = self._calculate_distance(property_obj, hmo)
            
            if distance and distance <= radius_meters:
                # Confidence decreases with distance
                confidence = max(0.3, 1.0 - (distance / radius_meters) * 0.4)
                
                matches.append({
                    'hmo_register_id': str(hmo.id),
                    'match_type': 'close_proximity',
                    'confidence_score': confidence,
                    'distance_meters': distance,
                    'hmo_data': hmo
                })
        
        return matches
    
    def _calculate_distance(self, property_obj, hmo_register) -> Optional[float]:
        """Calculate distance between property and HMO register"""
        if not all([property_obj.latitude, property_obj.longitude, 
                   hmo_register.latitude, hmo_register.longitude]):
            return None
        
        try:
            point1 = (float(property_obj.latitude), float(property_obj.longitude))
            point2 = (float(hmo_register.latitude), float(hmo_register.longitude))
            return geodesic(point1, point2).meters
        except:
            return None
    
    def create_match(self, property_id: str, hmo_register_id: str, 
                    match_type: str, confidence: float, distance: Optional[float] = None,
                    address_similarity: Optional[float] = None) -> PropertyHMOMatch:
        """Create a verified match"""
        
        match = PropertyHMOMatch(
            property_id=property_id,
            hmo_register_id=hmo_register_id,
            match_type=match_type,
            confidence_score=confidence,
            distance_meters=distance,
            address_similarity=address_similarity,
            postcode_match=(match_type == 'exact_postcode'),
            street_match=(address_similarity and address_similarity > 0.5),
            verified_status='verified' if confidence >= 0.8 else 'unverified',
            verified_by='system_auto' if confidence >= 0.8 else None,
            verified_at=datetime.utcnow() if confidence >= 0.8 else None
        )
        
        self.db.add(match)
        self.db.commit()
        self.db.refresh(match)
        
        return match


# =============================================================================
# 4. OXFORD INTEGRATION ORCHESTRATOR (Unified Schema)
# =============================================================================

class OxfordUnifiedIntegrator:
    """Main class to orchestrate Oxford HMO integration with unified schema"""
    
    def __init__(self):
        self.fetcher = OxfordHMOFetcher()
    
    def update_oxford_register(self) -> Dict[str, int]:
        """Update Oxford HMO register data in unified schema"""
        db = SessionLocal()
        
        try:
            # Fetch latest data
            raw_data = self.fetcher.fetch_oxford_data()
            if not raw_data:
                return {'error': 'No data fetched'}
            
            # Clear existing Oxford data from unified table
            deleted_count = db.query(HMORegister).filter(HMORegister.city == 'oxford').delete()
            logger.info(f"Cleared {deleted_count} existing Oxford HMO records")
            
            # Process and save new data
            processed_count = 0
            geocoded_count = 0
            
            for record in raw_data:
                hmo_register = self.fetcher.process_oxford_record(record)
                if hmo_register:
                    db.add(hmo_register)
                    processed_count += 1
                    if hmo_register.latitude and hmo_register.longitude:
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
        matcher = UnifiedAddressMatcher(db)
        
        try:
            # Get Oxford properties (properties with city = 'Oxford' or postcode starting with 'OX')
            from models import Property
            
            oxford_properties = (db.query(Property).filter(
                or_(
                    Property.city.ilike('%oxford%'),
                    Property.postcode.ilike('OX%'),
                    Property.address.ilike('%oxford%')
                )
            ).limit(limit).all())
            
            total_matches = 0
            high_confidence_matches = 0
            
            for property_obj in oxford_properties:
                # Skip if already has matches
                existing_matches = (db.query(PropertyHMOMatch)
                                  .filter(PropertyHMOMatch.property_id == str(property_obj.id))
                                  .count())
                
                if existing_matches > 0:
                    continue
                
                # Find potential matches (Oxford only)
                potential_matches = matcher.find_hmo_matches(str(property_obj.id), city='oxford')
                
                # Create high-confidence matches automatically
                for match in potential_matches:
                    if match['confidence_score'] >= 0.7:  # Lower threshold for Oxford
                        try:
                            matcher.create_match(
                                str(property_obj.id),
                                match['hmo_register_id'],
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
            # Basic counts for Oxford
            total_hmos = db.query(HMORegister).filter(HMORegister.city == 'oxford').count()
            geocoded_hmos = db.query(HMORegister).filter(
                HMORegister.city == 'oxford',
                HMORegister.latitude.isnot(None),
                HMORegister.longitude.isnot(None)
            ).count()
            
            active_licences = db.query(HMORegister).filter(
                HMORegister.city == 'oxford',
                or_(
                    HMORegister.licence_expiry_date.is_(None),
                    HMORegister.licence_expiry_date >= datetime.now().date()
                )
            ).count()
            
            # Match statistics for Oxford
            oxford_hmo_ids = [str(hmo.id) for hmo in db.query(HMORegister).filter(HMORegister.city == 'oxford').all()]
            
            total_matches = db.query(PropertyHMOMatch).filter(
                PropertyHMOMatch.hmo_register_id.in_(oxford_hmo_ids)
            ).count()
            
            verified_matches = db.query(PropertyHMOMatch).filter(
                PropertyHMOMatch.hmo_register_id.in_(oxford_hmo_ids),
                PropertyHMOMatch.verified_status == 'verified'
            ).count()
            
            # Average confidence for Oxford matches
            avg_confidence = db.query(func.avg(PropertyHMOMatch.confidence_score)).filter(
                PropertyHMOMatch.hmo_register_id.in_(oxford_hmo_ids)
            ).scalar() or 0
            
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
# 5. API ENDPOINTS FOR UNIFIED SCHEMA
# =============================================================================

def add_oxford_unified_endpoints(app):
    """Add Oxford HMO endpoints using unified schema"""
    
    integrator = OxfordUnifiedIntegrator()
    
    @app.post("/api/hmo/oxford/update")
    async def update_oxford_register():
        """Update Oxford HMO register"""
        try:
            result = integrator.update_oxford_register()
            return result
        except Exception as e:
            from fastapi import HTTPException
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/hmo/oxford/match-properties")
    async def match_oxford_properties():
        """Match properties to Oxford HMO register"""
        try:
            result = integrator.match_oxford_properties()
            return result
        except Exception as e:
            from fastapi import HTTPException
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/hmo/oxford/statistics")
    async def get_oxford_statistics():
        """Get Oxford HMO statistics"""
        try:
            stats = integrator.get_oxford_statistics()
            return stats
        except Exception as e:
            from fastapi import HTTPException
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/hmo/property/{property_id}")
    async def get_property_hmo_status(property_id: str):
        """Get HMO status for a specific property (all cities)"""
        db = SessionLocal()
        try:
            matches = (db.query(PropertyHMOMatch)
                      .join(HMORegister)
                      .filter(PropertyHMOMatch.property_id == property_id)
                      .order_by(PropertyHMOMatch.confidence_score.desc())
                      .all())
            
            if not matches:
                return {
                    'is_licensed_hmo': False,
                    'confidence': 0.0,
                    'matches': []
                }
            
            best_match = matches[0]
            hmo = best_match.hmo_register
            
            return {
                'is_licensed_hmo': True,
                'confidence': float(best_match.confidence_score),
                'city': hmo.city,
                'best_match': {
                    'case_number': hmo.external_case_number,
                    'address': hmo.raw_address,
                    'total_occupants': hmo.total_occupants,
                    'total_units': hmo.total_units,
                    'licence_expires': hmo.licence_expiry_date.isoformat() if hmo.licence_expiry_date else None,
                    'licence_status': hmo.licence_status,
                    'match_type': best_match.match_type,
                    'distance_meters': float(best_match.distance_meters) if best_match.distance_meters else None,
                    'verified': best_match.verified_status == 'verified'
                },
                'all_matches': len(matches)
            }
            
        finally:
            db.close()


# =============================================================================
# 6. ENHANCED PROPERTY DATA WITH UNIFIED SCHEMA
# =============================================================================

def enhance_properties_with_hmo_status(properties: List[Dict]) -> List[Dict]:
    """Add HMO status from unified schema to property data"""
    db = SessionLocal()
    
    try:
        for property_data in properties:
            property_id = property_data.get('property_id')
            if not property_id:
                continue
            
            # Get HMO matches from unified schema
            matches = (db.query(PropertyHMOMatch)
                      .join(HMORegister)
                      .filter(PropertyHMOMatch.property_id == property_id)
                      .order_by(PropertyHMOMatch.confidence_score.desc())
                      .all())
            
            if matches:
                best_match = matches[0]
                hmo = best_match.hmo_register
                
                property_data.update({
                    'is_licensed_hmo': True,
                    'hmo_confidence': float(best_match.confidence_score),
                    'hmo_city': hmo.city,
                    'hmo_case_number': hmo.external_case_number,
                    'hmo_occupants': hmo.total_occupants,
                    'hmo_units': hmo.total_units,
                    'hmo_expires': hmo.licence_expiry_date.isoformat() if hmo.licence_expiry_date else None,
                    'hmo_status': hmo.licence_status,
                    'hmo_verified': best_match.verified_status == 'verified',
                    'hmo_match_type': best_match.match_type
                })
            else:
                property_data.update({
                    'is_licensed_hmo': False,
                    'hmo_confidence': 0.0
                })
        
        return properties
        
    finally:
        db.close()


# =============================================================================
# 7. SETUP AND TESTING FOR UNIFIED SCHEMA
# =============================================================================

def setup_oxford_unified_integration():
    """Setup Oxford HMO integration using unified schema"""
    
    print("🏛️ Setting up Oxford HMO integration (unified schema)...")
    
    # Check if tables exist
    from database import engine
    from sqlalchemy import inspect
    
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    required_tables = ['hmo_registers', 'property_hmo_matches']
    missing_tables = [table for table in required_tables if table not in tables]
    
    if missing_tables:
        print(f"❌ Missing required tables: {missing_tables}")
        print("Please run the migration script first:")
        print("python3 -c \"from hmo_migration import create_hmo_tables_manually; create_hmo_tables_manually()\"")
        return False
    
    print("✅ Required tables found")
    
    # Initialize integrator
    integrator = OxfordUnifiedIntegrator()
    
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


def test_oxford_unified_integration():
    """Test Oxford HMO integration with unified schema"""
    print("🧪 Testing Oxford HMO integration (unified schema)...")
    
    integrator = OxfordUnifiedIntegrator()
    
    # Test 1: Check data quality
    stats = integrator.get_oxford_statistics()
    print(f"📊 Current statistics: {stats}")
    
    # Test 2: Test a specific property match
    db = SessionLocal()
    try:
        # Find a property in Oxford
        from models import Property
        oxford_property = (db.query(Property)
                          .filter(
                              or_(
                                  Property.city.ilike('%oxford%'),
                                  Property.postcode.ilike('OX%')
                              )
                          )
                          .first())
        
        if oxford_property:
            matcher = UnifiedAddressMatcher(db)
            matches = matcher.find_hmo_matches(str(oxford_property.id), city='oxford')
            print(f"🔍 Test property {oxford_property.address}: {len(matches)} potential matches")
            
            if matches:
                best_match = matches[0]
                print(f"  Best match: {best_match['confidence_score']:.2f} confidence")
                print(f"  HMO case: {best_match['hmo_data'].external_case_number}")
        else:
            print("⚠️ No Oxford properties found in database")
        
    finally:
        db.close()
    
    print("✅ Oxford unified integration test completed")


# =============================================================================
# 8. MIGRATION UTILITIES
# =============================================================================

def migrate_to_unified_schema():
    """Utility to migrate from city-specific to unified schema (if needed later)"""
    print("🔄 Migration utility available for future use")
    # This would be implemented if migrating from oxford-specific tables
    pass


def cleanup_oxford_data():
    """Cleanup Oxford data from unified schema"""
    db = SessionLocal()
    
    try:
        # Remove Oxford matches first (due to foreign key constraints)
        oxford_hmo_ids = [str(hmo.id) for hmo in db.query(HMORegister).filter(HMORegister.city == 'oxford').all()]
        
        if oxford_hmo_ids:
            matches_deleted = db.query(PropertyHMOMatch).filter(
                PropertyHMOMatch.hmo_register_id.in_(oxford_hmo_ids)
            ).delete(synchronize_session=False)
            
            # Remove Oxford HMO records
            hmos_deleted = db.query(HMORegister).filter(HMORegister.city == 'oxford').delete()
            
            db.commit()
            
            print(f"🧹 Cleanup completed:")
            print(f"  - {matches_deleted} Oxford matches removed")
            print(f"  - {hmos_deleted} Oxford HMO records removed")
        else:
            print("ℹ️ No Oxford data found to cleanup")
    
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        db.rollback()
    
    finally:
        db.close()


# =============================================================================
# 9. DAILY UPDATE AUTOMATION
# =============================================================================

def daily_oxford_update():
    """Daily automated update for Oxford HMO data"""
    print(f"🔄 Daily Oxford HMO update started at {datetime.now()}")
    
    integrator = OxfordUnifiedIntegrator()
    
    try:
        # Update Oxford register
        update_result = integrator.update_oxford_register()
        
        if 'error' not in update_result:
            print(f"✅ Oxford register updated: {update_result['processed_records']} records")
            
            # Match new properties
            match_result = integrator.match_oxford_properties()
            
            if 'error' not in match_result:
                print(f"✅ Property matching completed: {match_result['total_matches_created']} new matches")
            else:
                print(f"⚠️ Property matching failed: {match_result['error']}")
        else:
            print(f"⚠️ Oxford register update failed: {update_result['error']}")
    
    except Exception as e:
        print(f"❌ Daily update failed: {e}")
    
    print(f"🔄 Daily Oxford HMO update completed at {datetime.now()}")


# =============================================================================
# 10. MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "setup":
            success = setup_oxford_unified_integration()
            if success:
                test_oxford_unified_integration()
        
        elif command == "test":
            test_oxford_unified_integration()
        
        elif command == "update":
            daily_oxford_update()
        
        elif command == "cleanup":
            cleanup_oxford_data()
        
        elif command == "stats":
            integrator = OxfordUnifiedIntegrator()
            stats = integrator.get_oxford_statistics()
            print("📊 Oxford HMO Statistics:")
            for key, value in stats.items():
                print(f"  {key}: {value}")
        
        else:
            print("❌ Unknown command. Available commands:")
            print("  setup   - Setup Oxford integration")
            print("  test    - Test the integration")
            print("  update  - Run daily update")
            print("  cleanup - Remove Oxford data")
            print("  stats   - Show statistics")
    
    else:
        # Default: run setup
        print("🚀 Running Oxford HMO integration setup...")
        success = setup_oxford_unified_integration()
        
        if success:
            print("\n📋 Next steps:")
            print("1. Add to your main.py:")
            print("   from oxford_unified_integration import add_oxford_unified_endpoints")
            print("   add_oxford_unified_endpoints(app)")
            print("\n2. Update your properties endpoint:")
            print("   from oxford_unified_integration import enhance_properties_with_hmo_status")
            print("   enhanced_properties = enhance_properties_with_hmo_status(properties)")
            print("\n3. Test the API endpoints:")
            print("   curl http://localhost:8000/api/hmo/oxford/statistics")
            print("   curl http://localhost:8000/api/hmo/property/{property_id}")
            print("\n4. Set up daily updates:")
            print("   python3 oxford_unified_integration.py update")
        else:
            print("❌ Setup failed. Please check the error messages above.")