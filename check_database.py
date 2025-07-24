# check_database.py - Check what's actually in the database

import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from sqlalchemy.orm import Session
    from database import get_db
    from models import Property
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

def check_database_state():
    """Check current state of properties in database"""
    db = next(get_db())
    
    try:
        # Get total count
        total_properties = db.query(Property).count()
        print(f"📊 Total properties in database: {total_properties}")
        
        if total_properties == 0:
            print("❌ No properties found in database!")
            return
        
        # Check city field status
        properties_with_city = db.query(Property).filter(
            Property.city.isnot(None),
            Property.city != ''
        ).count()
        
        properties_without_city = db.query(Property).filter(
            (Property.city.is_(None)) | (Property.city == '')
        ).count()
        
        print(f"✅ Properties WITH city field: {properties_with_city}")
        print(f"❌ Properties WITHOUT city field: {properties_without_city}")
        
        # Get sample properties without city
        if properties_without_city > 0:
            print("\n🔍 Sample properties missing city field:")
            sample_properties = db.query(Property).filter(
                (Property.city.is_(None)) | (Property.city == '')
            ).limit(5).all()
            
            for i, prop in enumerate(sample_properties, 1):
                print(f"{i}. ID: {prop.id}")
                print(f"   Address: {prop.address}")
                print(f"   City: {repr(prop.city)}")
                print(f"   Area: {repr(prop.area)}")
                print()
        
        # Get sample properties with city
        if properties_with_city > 0:
            print("✅ Sample properties WITH city field:")
            sample_with_city = db.query(Property).filter(
                Property.city.isnot(None),
                Property.city != ''
            ).limit(3).all()
            
            for i, prop in enumerate(sample_with_city, 1):
                print(f"{i}. ID: {prop.id}")
                print(f"   Address: {prop.address}")
                print(f"   City: {repr(prop.city)}")
                print(f"   Area: {repr(prop.area)}")
                print()
        
        # Check what unique city values exist
        unique_cities = db.query(Property.city).filter(
            Property.city.isnot(None),
            Property.city != ''
        ).distinct().all()
        
        if unique_cities:
            print(f"🏙️ Unique cities in database: {[city[0] for city in unique_cities]}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_database_state()