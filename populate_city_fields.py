# populate_city_fields.py - FIXED VERSION

import sys
import os
from datetime import datetime
import re

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from sqlalchemy.orm import Session
    from database import get_db
    from models import Property
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

def extract_city_from_address(address):
    """Extract city from address string - IMPROVED for your specific data"""
    if not address:
        return None, None
    
    # Clean and split address
    address_parts = [part.strip() for part in address.split(',')]
    
    # Direct city mappings based on your actual data
    city_mappings = {
        # Swindon variations
        'south swindon': 'Swindon',
        'kingshill': 'Swindon',
        
        # Oxford variations  
        'east oxford': 'Oxford',
        'city centre': 'Oxford',
        'cowley': 'Oxford',
        'new marston': 'Oxford', 
        'wood farm': 'Oxford',
        'cutteslowe': 'Oxford',
        
        # Banbury variations
        'grimsbury': 'Banbury',
        
        # Bicester variations
        'kings end': 'Bicester',
        'glory farm': 'Bicester',
        
        # South Oxfordshire (keep as is)
        'south oxfordshire': 'South Oxfordshire',
        'ladygrove': 'South Oxfordshire'
    }
    
    # Look for postcode to find the right part
    postcode_index = None
    for i, part in enumerate(address_parts):
        # UK postcode pattern
        if re.match(r'^[A-Z]{1,2}[0-9]{1,2}[A-Z]?\s?[0-9][A-Z]{2}$', part.upper().strip()):
            postcode_index = i
            break
    
    if postcode_index is None or postcode_index == 0:
        # No postcode found or postcode is first element, try different approach
        # Look for known cities directly in address parts
        for part in address_parts:
            part_lower = part.lower().strip()
            if part_lower in city_mappings:
                return city_mappings[part_lower], part.strip()
            elif part_lower in ['swindon', 'oxford', 'banbury', 'bicester']:
                return part.strip(), None
        return None, None
    
    # Work backwards from postcode
    city = None
    area = None
    
    # The part immediately before postcode is usually the main city
    if postcode_index >= 1:
        potential_city = address_parts[postcode_index - 1].lower().strip()
        
        if potential_city in city_mappings:
            city = city_mappings[potential_city]
            # Area is the part before that
            if postcode_index >= 2:
                area = address_parts[postcode_index - 2].strip()
        elif potential_city in ['swindon', 'oxford', 'banbury', 'bicester']:
            city = potential_city.title()
            if postcode_index >= 2:
                area = address_parts[postcode_index - 2].strip()
    
    # If still no city found, check all parts
    if not city:
        for part in address_parts:
            part_lower = part.lower().strip()
            if part_lower in city_mappings:
                city = city_mappings[part_lower]
                break
            elif part_lower in ['swindon', 'oxford', 'banbury', 'bicester']:
                city = part_lower.title()
                break
    
    return city, area

def populate_city_fields():
    """Populate city and area fields for properties that are missing them"""
    db = next(get_db())
    
    try:
        # Get all properties that are missing city field
        properties = db.query(Property).filter(
            (Property.city.is_(None)) | (Property.city == '')
        ).all()
        
        print(f"Found {len(properties)} properties missing city field")
        
        updated_count = 0
        failed_count = 0
        
        for property_obj in properties:
            if property_obj.address:
                city, area = extract_city_from_address(property_obj.address)
                
                if city:
                    property_obj.city = city
                    if area and area != city:
                        property_obj.area = area
                    
                    print(f"✅ Updated property {property_obj.id}: City='{city}', Area='{area}'")
                    print(f"   Address: {property_obj.address}")
                    updated_count += 1
                else:
                    print(f"❌ Could not extract city from: {property_obj.address}")
                    failed_count += 1
        
        db.commit()
        print(f"\n🎉 Successfully updated {updated_count} properties!")
        print(f"❌ Failed to process {failed_count} properties")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    populate_city_fields()