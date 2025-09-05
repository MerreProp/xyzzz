#!/usr/bin/env python3
"""
Simple import test to identify the exact issue
"""

import sys

def test_individual_imports():
    """Test imports one by one to isolate the issue"""
    
    print("🧪 TESTING INDIVIDUAL IMPORTS")
    print("=" * 40)
    
    # Test 1: Base data source
    try:
        from hmo_registry.base_data_source import BaseHMODataSource
        print("✅ 1. BaseHMODataSource - OK")
    except Exception as e:
        print(f"❌ 1. BaseHMODataSource - FAILED: {e}")
        return False
    
    # Test 2: Improved geocoding 
    try:
        from hmo_registry.utils.improved_geocoding import geocode_address
        print("✅ 2. Improved geocoding - OK")
    except Exception as e:
        print(f"⚠️  2. Improved geocoding - FAILED: {e}")
        # This is OK if it fails, it's not critical
    
    # Test 3: Banbury module
    try:
        from hmo_registry.cities.cherwell_banbury import CherwellBanburyHMOMapData
        print("✅ 3. Banbury module - OK")
    except Exception as e:
        print(f"❌ 3. Banbury module - FAILED: {e}")
        return False
    
    # Test 4: Bicester module  
    try:
        from hmo_registry.cities.cherwell_bicester import CherwellBicesterHMOMapData
        print("✅ 4. Bicester module - OK")
    except Exception as e:
        print(f"❌ 4. Bicester module - FAILED: {e}")
        return False
    
    # Test 5: Kidlington module
    try:
        from hmo_registry.cities.cherwell_kidlington import CherwellKidlingtonHMOMapData
        print("✅ 5. Kidlington module - OK")
    except Exception as e:
        print(f"❌ 5. Kidlington module - FAILED: {e}")
        return False
    
    return True

def test_registry_endpoints():
    """Test if registry endpoints can import"""
    
    print("\n🔗 TESTING REGISTRY ENDPOINTS")
    print("=" * 35)
    
    try:
        from hmo_registry.registry_endpoints import add_hmo_registry_endpoints
        print("✅ Registry endpoints - OK")
        return True
    except Exception as e:
        print(f"❌ Registry endpoints - FAILED: {e}")
        print(f"   Error details: {str(e)}")
        return False

def main():
    """Main test function"""
    
    print("🔍 CHERWELL IMPORT DIAGNOSIS")
    print("=" * 50)
    
    # Test individual modules
    individual_ok = test_individual_imports()
    
    if individual_ok:
        print("\n✅ All individual modules imported successfully!")
        
        # Test registry endpoints
        registry_ok = test_registry_endpoints()
        
        if registry_ok:
            print("\n🎉 ALL IMPORTS WORKING!")
            print("You should be able to start the server now:")
            print("   uvicorn main:app --reload --port 8001")
            return 0
        else:
            print("\n⚠️  Individual modules work, but registry endpoints have issues.")
            print("This might be a different problem in your registry_endpoints.py file.")
            return 1
    else:
        print("\n❌ Some individual modules failed to import.")
        print("Check the error messages above to identify which files need fixing.")
        return 1

if __name__ == "__main__":
    sys.exit(main())