# normalize_cities.py - Fix incorrectly stored city data

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

def normalize_cities():
    """Normalize city data - move Oxford neighborhoods from city to area field"""
    db = next(get_db())
    
    try:
        # Define Oxford neighborhoods that are incorrectly stored as cities
        oxford_neighborhoods = [
            'Cowley',
            'Cutteslowe', 
            'East Oxford',
            'New Marston',
            'Wood Farm'
        ]
        
        # Also handle South Oxfordshire areas
        south_oxon_areas = [
            'Ladygrove'
        ]
        
        updated_count = 0
        
        print("🔄 Normalizing city data...")
        
        # Fix Oxford neighborhoods
        for neighborhood in oxford_neighborhoods:
            properties = db.query(Property).filter(Property.city == neighborhood).all()
            
            for prop in properties:
                print(f"📍 Fixing: {prop.address}")
                print(f"   Before: City='{prop.city}', Area='{prop.area}'")
                
                # Move the neighborhood to area field and set city to Oxford
                prop.area = neighborhood
                prop.city = 'Oxford'
                
                print(f"   After:  City='{prop.city}', Area='{prop.area}'")
                print()
                updated_count += 1
        
        # Fix South Oxfordshire areas
        for area in south_oxon_areas:
            properties = db.query(Property).filter(Property.city == area).all()
            
            for prop in properties:
                print(f"📍 Fixing: {prop.address}")
                print(f"   Before: City='{prop.city}', Area='{prop.area}'")
                
                # Move to area field and set city to South Oxfordshire
                prop.area = area
                prop.city = 'South Oxfordshire'
                
                print(f"   After:  City='{prop.city}', Area='{prop.area}'")
                print()
                updated_count += 1
        
        # Commit the changes
        db.commit()
        print(f"✅ Successfully normalized {updated_count} properties!")
        
        # Show final city distribution
        print("\n📊 Final city distribution:")
        cities = db.query(Property.city).distinct().all()
        for city in cities:
            count = db.query(Property).filter(Property.city == city[0]).count()
            print(f"   {city[0]}: {count} properties")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    normalize_cities()