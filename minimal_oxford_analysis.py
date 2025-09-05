# minimal_oxford_analysis.py
# Run this to test the analysis without going through the module system

import sys
import os
sys.path.insert(0, os.getcwd())

print("🔍 Running minimal Oxford analysis test...")

try:
    # Import directly without going through the module command system
    from hmo_registry.cities.oxford_renewal import OxfordLicenseRenewalAnalyzer
    
    print("✅ Import successful")
    
    # Create analyzer
    analyzer = OxfordLicenseRenewalAnalyzer()
    print("✅ Analyzer created")
    
    # Test loading Excel data first (this is where the issue might be)
    print("\n📊 Testing Excel data loading...")
    try:
        new_data = analyzer.load_new_excel_data()
        print(f"✅ Excel data loaded: {len(new_data)} records")
    except Exception as e:
        print(f"❌ Excel loading failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Test loading existing data
    print("\n📊 Testing existing data loading...")
    try:
        existing_data = analyzer.load_existing_oxford_data()
        print(f"✅ Existing data loaded: {len(existing_data)} records")
    except Exception as e:
        print(f"❌ Existing data loading failed: {e}")
        # This might fail if no database, but continue
        existing_data = []
    
    # Test the analysis
    print("\n🔍 Testing license renewal analysis...")
    try:
        analysis = analyzer.analyze_license_renewals()
        
        if 'error' in analysis:
            print(f"❌ Analysis failed: {analysis['error']}")
        else:
            print(f"✅ Analysis completed successfully!")
            print(f"📊 Analysis Summary:")
            print(f"  📄 Existing records: {analysis.get('existing_records', 0):,}")
            print(f"  📋 New Excel records: {analysis.get('new_excel_records', 0):,}")
            print(f"  ✅ Exact case matches: {analysis.get('exact_case_matches', 0):,}")
            print(f"  🏠 Address matches: {analysis.get('address_matches', 0):,}")
            print(f"  🔄 Renewed licenses: {analysis.get('renewed_licenses', 0):,}")
            print(f"  ❌ Still expired: {analysis.get('still_expired', 0):,}")
            print(f"  🆕 New properties: {analysis.get('new_properties', 0):,}")
            print(f"  📍 Geocoded new properties: {analysis.get('geocoded_new_properties', 0):,}")
            print(f"  📈 Total final records: {analysis.get('total_final_records', 0):,}")
    
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()

except Exception as e:
    print(f"❌ Import or setup failed: {e}")
    import traceback
    traceback.print_exc()