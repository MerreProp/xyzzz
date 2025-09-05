#!/usr/bin/env python3
"""
Debug Oxford API endpoint and check for duplicates
"""

import sys
import os
from collections import Counter

# Add project path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def check_database_records():
    """Check what's actually in the database"""
    
    print("="*70)
    print("DEBUGGING OXFORD DATABASE RECORDS")
    print("="*70)
    
    try:
        from database import SessionLocal
        from hmo_registry.database_models import HMORegistry
        
        db = SessionLocal()
        
        # Get all Oxford records
        all_oxford = db.query(HMORegistry).filter(
            HMORegistry.city == 'oxford'
        ).all()
        
        print(f"📊 Total Oxford records in database: {len(all_oxford)}")
        
        # Check for duplicates by case number
        case_numbers = [record.case_number for record in all_oxford]
        case_counter = Counter(case_numbers)
        duplicates = {case: count for case, count in case_counter.items() if count > 1}
        
        print(f"🔍 Duplicate case numbers: {len(duplicates)}")
        if duplicates:
            print("   Top 10 duplicates:")
            for case, count in sorted(duplicates.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"     {case}: {count} times")
        
        # Check geocoded records
        geocoded = db.query(HMORegistry).filter(
            HMORegistry.city == 'oxford',
            HMORegistry.geocoded == True,
            HMORegistry.latitude.is_not(None),
            HMORegistry.longitude.is_not(None)
        ).all()
        
        print(f"🗺️ Geocoded Oxford records: {len(geocoded)}")
        
        # Check license statuses
        active = db.query(HMORegistry).filter(
            HMORegistry.city == 'oxford',
            HMORegistry.licence_status == 'active'
        ).count()
        
        expired = db.query(HMORegistry).filter(
            HMORegistry.city == 'oxford',
            HMORegistry.licence_status == 'expired'
        ).count()
        
        unknown = db.query(HMORegistry).filter(
            HMORegistry.city == 'oxford',
            HMORegistry.licence_status.is_(None)
        ).count() + db.query(HMORegistry).filter(
            HMORegistry.city == 'oxford',
            HMORegistry.licence_status == 'unknown'
        ).count()
        
        print(f"📈 License statuses:")
        print(f"   Active: {active}")
        print(f"   Expired: {expired}")
        print(f"   Unknown/None: {unknown}")
        
        # Check sources
        sources = db.query(HMORegistry.source).filter(
            HMORegistry.city == 'oxford'
        ).distinct().all()
        
        print(f"📋 Data sources found:")
        for source in sources:
            count = db.query(HMORegistry).filter(
                HMORegistry.city == 'oxford',
                HMORegistry.source == source[0]
            ).count()
            print(f"   {source[0]}: {count} records")
        
        # Sample geocoded records for API test
        print(f"\n🔬 Sample geocoded records:")
        sample_geocoded = geocoded[:5]
        for record in sample_geocoded:
            print(f"   {record.case_number}: {record.raw_address[:50]}...")
            print(f"     Status: {record.licence_status}, Coords: ({record.latitude}, {record.longitude})")
        
        db.close()
        return len(all_oxford), len(geocoded), len(duplicates)
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        return 0, 0, 0

def test_api_endpoint():
    """Test the API endpoint that the map is calling"""
    
    print(f"\n" + "="*70)
    print("TESTING API ENDPOINT")
    print("="*70)
    
    try:
        import requests
        
        # Test the exact endpoint the map calls
        url = "http://localhost:8001/api/hmo-registry/cities/oxford?enable_geocoding=false"
        print(f"🌐 Testing: {url}")
        
        response = requests.get(url, timeout=30)
        print(f"📡 Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Response structure:")
            print(f"   Success: {data.get('success')}")
            print(f"   Data length: {len(data.get('data', []))}")
            print(f"   Statistics: {data.get('statistics')}")
            
            # Check if data has coordinates
            if data.get('data'):
                geocoded_api = [r for r in data['data'] if r.get('latitude') and r.get('longitude')]
                print(f"🗺️ Records with coordinates in API: {len(geocoded_api)}")
                
                # Sample records
                print(f"\n📋 First 3 API records:")
                for i, record in enumerate(data['data'][:3]):
                    print(f"   Record {i+1}:")
                    print(f"     Case: {record.get('case_number')}")
                    print(f"     Status: {record.get('licence_status')}")
                    print(f"     Coords: ({record.get('latitude')}, {record.get('longitude')})")
                    print(f"     Address: {record.get('address', '')[:50]}...")
            
            return True
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ Error testing API: {e}")
        return False

def suggest_fixes():
    """Suggest fixes based on findings"""
    
    print(f"\n" + "="*70)
    print("SUGGESTED FIXES")
    print("="*70)
    
    print("1. 🔧 If API returns 0 geocoded records:")
    print("   - Check that your FastAPI server is running")
    print("   - Verify the API endpoint exists and returns Oxford data")
    print("   - Check that the 'geocoded' field is properly set in database")
    
    print("\n2. 🗑️ If there are many duplicates:")
    print("   - The duplicates are likely from multiple data loads")
    print("   - Consider cleaning up duplicates in database")
    print("   - Implement upsert logic instead of always inserting")
    
    print("\n3. 🎯 Expected vs Actual:")
    print("   - Your integration showed 3,001 new records")
    print("   - If you see 6,212+ total, there are likely duplicates")
    print("   - Clean database should have ~3,001 Oxford records")

def clean_duplicates_option():
    """Option to clean duplicate records"""
    
    print(f"\n" + "="*50)
    print("DUPLICATE CLEANUP OPTION")
    print("="*50)
    
    try:
        from database import SessionLocal
        from hmo_registry.database_models import HMORegistry
        
        db = SessionLocal()
        
        # Find duplicates
        case_numbers = db.query(HMORegistry.case_number).filter(
            HMORegistry.city == 'oxford'
        ).all()
        
        case_counter = Counter([case[0] for case in case_numbers])
        duplicates = {case: count for case, count in case_counter.items() if count > 1}
        
        if duplicates:
            print(f"Found {len(duplicates)} case numbers with duplicates")
            print(f"Total duplicate records: {sum(duplicates.values()) - len(duplicates)}")
            
            response = input("\nDo you want to remove duplicates? (y/N): ").lower().strip()
            
            if response == 'y':
                print("🧹 Cleaning duplicates...")
                
                removed_count = 0
                for case_number in duplicates.keys():
                    # Keep the most recent record, remove others
                    records = db.query(HMORegistry).filter(
                        HMORegistry.city == 'oxford',
                        HMORegistry.case_number == case_number
                    ).order_by(HMORegistry.updated_at.desc()).all()
                    
                    # Remove all but the first (most recent)
                    for record in records[1:]:
                        db.delete(record)
                        removed_count += 1
                
                db.commit()
                print(f"✅ Removed {removed_count} duplicate records")
                
                # Verify cleanup
                remaining = db.query(HMORegistry).filter(
                    HMORegistry.city == 'oxford'
                ).count()
                print(f"📊 Oxford records remaining: {remaining}")
            else:
                print("ℹ️ Skipping duplicate cleanup")
        else:
            print("✅ No duplicates found")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Error in cleanup: {e}")

if __name__ == "__main__":
    # Run diagnostics
    total_records, geocoded_records, duplicate_count = check_database_records()
    api_working = test_api_endpoint()
    
    suggest_fixes()
    
    # Offer duplicate cleanup if needed
    if duplicate_count > 0:
        clean_duplicates_option()
    
    print(f"\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"📊 Database: {total_records} total, {geocoded_records} geocoded")
    print(f"🔄 Duplicates: {duplicate_count} case numbers have duplicates")
    print(f"🌐 API: {'Working' if api_working else 'Not working'}")
    print("="*70)