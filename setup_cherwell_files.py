#!/usr/bin/env python3
"""
Quick setup script to create all necessary files for Cherwell integration
Run this to fix the import errors and get your integration working
"""

import os
from pathlib import Path

def create_file_structure():
    """Create the necessary file structure for Cherwell integration"""
    
    print("🔧 SETTING UP CHERWELL INTEGRATION FILES")
    print("=" * 50)
    
    base_dir = Path.cwd()
    
    # Create directories
    directories = [
        "hmo_registry/utils",
        "hmo_registry/cities", 
        "data/cherwell/processed"
    ]
    
    for directory in directories:
        dir_path = base_dir / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ Directory: {directory}")
    
    # Create __init__.py files
    init_files = [
        "hmo_registry/__init__.py",
        "hmo_registry/utils/__init__.py",
        "hmo_registry/cities/__init__.py"
    ]
    
    for init_file in init_files:
        init_path = base_dir / init_file
        if not init_path.exists():
            init_path.write_text("# Auto-generated __init__.py\n")
            print(f"✅ Created: {init_file}")
        else:
            print(f"✅ Exists: {init_file}")
    
    # Check for required CSV files
    csv_files = [
        "data/cherwell/processed/cherwell_banbury_hmo.csv",
        "data/cherwell/processed/cherwell_bicester_hmo.csv",
        "data/cherwell/processed/cherwell_kidlington_hmo.csv"
    ]
    
    missing_files = []
    for csv_file in csv_files:
        csv_path = base_dir / csv_file
        if csv_path.exists():
            print(f"✅ CSV exists: {csv_file}")
        else:
            print(f"❌ Missing: {csv_file}")
            missing_files.append(csv_file)
    
    # Check for Python modules that need to be created
    required_modules = {
        "hmo_registry/base_data_source.py": "Base data source class",
        "hmo_registry/utils/improved_geocoding.py": "Improved geocoding utilities",
        "hmo_registry/cities/cherwell_banbury.py": "Banbury HMO data source",
        "hmo_registry/cities/cherwell_bicester.py": "Bicester HMO data source", 
        "hmo_registry/cities/cherwell_kidlington.py": "Kidlington HMO data source"
    }
    
    missing_modules = []
    for module_file, description in required_modules.items():
        module_path = base_dir / module_file
        if module_path.exists():
            print(f"✅ Module exists: {module_file}")
        else:
            print(f"❌ Missing: {module_file} ({description})")
            missing_modules.append(module_file)
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 SETUP SUMMARY")
    print("=" * 50)
    
    if not missing_files and not missing_modules:
        print("🎉 ALL FILES READY!")
        print("\n✅ You can now:")
        print("   1. Start your server: uvicorn main:app --reload --port 8001")
        print("   2. Test the integration: python3 test_cherwell_integration.py")
        return True
    else:
        print("❌ MISSING FILES DETECTED")
        
        if missing_files:
            print(f"\n📄 Missing CSV files ({len(missing_files)}):")
            for file in missing_files:
                print(f"   • {file}")
            print("\n💡 To fix: Make sure your Cherwell CSV files are in data/cherwell/processed/")
        
        if missing_modules:
            print(f"\n🐍 Missing Python modules ({len(missing_modules)}):")
            for module in missing_modules:
                print(f"   • {module}")
            print("\n💡 To fix: Create these modules using the provided code artifacts")
        
        return False

def test_imports():
    """Test if the required imports work"""
    print("\n🧪 TESTING IMPORTS")
    print("=" * 30)
    
    try:
        from hmo_registry.base_data_source import BaseHMODataSource
        print("✅ BaseHMODataSource imported")
    except ImportError as e:
        print(f"❌ BaseHMODataSource import failed: {e}")
        return False
    
    try:
        from hmo_registry.utils.improved_geocoding import geocode_address
        print("✅ Improved geocoding imported")
    except ImportError as e:
        print(f"❌ Improved geocoding import failed: {e}")
    
    try:
        from hmo_registry.cities.cherwell_banbury import CherwellBanburyHMOMapData
        print("✅ Banbury module imported")
    except ImportError as e:
        print(f"❌ Banbury module import failed: {e}")
        return False
    
    try:
        from hmo_registry.cities.cherwell_bicester import CherwellBicesterHMOMapData
        print("✅ Bicester module imported")
    except ImportError as e:
        print(f"❌ Bicester module import failed: {e}")
        return False
    
    try:
        from hmo_registry.cities.cherwell_kidlington import CherwellKidlingtonHMOMapData
        print("✅ Kidlington module imported")
    except ImportError as e:
        print(f"❌ Kidlington module import failed: {e}")
        return False
    
    return True

def main():
    """Main setup function"""
    
    # Step 1: Create file structure
    structure_ok = create_file_structure()
    
    if structure_ok:
        # Step 2: Test imports
        imports_ok = test_imports()
        
        if imports_ok:
            print("\n🎉 SETUP COMPLETE!")
            print("Your Cherwell integration should now work.")
            print("\nNext step: Start your server and test the endpoints")
            return 0
        else:
            print("\n❌ Import errors detected. Please create the missing modules.")
            return 1
    else:
        print("\n❌ File structure incomplete. Please create the missing files.")
        return 1

if __name__ == "__main__":
    exit(main())