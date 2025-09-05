#!/usr/bin/env python3
"""
Test script for the new /api/properties/today endpoint
Run this to verify the backend is working correctly
"""

import requests
import json
from datetime import datetime
import sys

def test_today_endpoint():
    """Test the /api/properties/today endpoint"""
    
    print("🧪 Testing /api/properties/today endpoint")
    print("=" * 50)
    
    try:
        # Test the endpoint
        url = "http://localhost:8001/api/properties/today"  # Adjust port if needed
        print(f"📡 Making request to: {url}")
        
        response = requests.get(url, timeout=10)
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print("✅ SUCCESS! Endpoint is working")
            print(f"📅 Date: {data.get('date', 'N/A')}")
            print(f"🏠 Properties Count: {data.get('count', 0)}")
            
            properties = data.get('properties', [])
            
            if properties:
                print(f"\n📋 Sample Properties:")
                for i, prop in enumerate(properties[:3], 1):  # Show first 3
                    print(f"   {i}. {prop.get('address', 'No address')[:50]}...")
                    print(f"      ID: {prop.get('property_id', 'N/A')}")
                    print(f"      Income: £{prop.get('monthly_income', 0):,}")
                    print(f"      Date Found: {prop.get('date_found', 'N/A')}")
                    print()
                
                if len(properties) > 3:
                    print(f"   ... and {len(properties) - 3} more properties")
            else:
                print("\n📝 No properties added today")
                print("   This is normal if you haven't analyzed any properties today")
            
            # Test the data structure
            print(f"\n🔍 Data Structure Check:")
            if properties:
                first_prop = properties[0]
                required_fields = [
                    'property_id', 'address', 'monthly_income', 'annual_income',
                    'total_rooms', 'available_rooms', 'available_rooms_details',
                    'meets_requirements', 'advertiser_name', 'date_found'
                ]
                
                missing_fields = [field for field in required_fields if field not in first_prop]
                
                if missing_fields:
                    print(f"   ⚠️  Missing fields: {missing_fields}")
                else:
                    print("   ✅ All required fields present")
            
            return True
            
        else:
            print(f"❌ FAILED! HTTP {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR!")
        print("   Make sure your FastAPI server is running on port 8001")
        print("   Start it with: uvicorn main:app --reload --port 8001")
        return False
        
    except requests.exceptions.Timeout:
        print("❌ TIMEOUT ERROR!")
        print("   The request took too long. Check your database connection.")
        return False
        
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        return False

def test_main_properties_endpoint():
    """Test that the main properties endpoint still works"""
    
    print("\n🧪 Testing main /api/properties endpoint (for comparison)")
    print("=" * 60)
    
    try:
        url = "http://localhost:8001/api/properties"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            total_properties = len(data)
            print(f"✅ Main endpoint working - {total_properties} total properties")
            return True
        else:
            print(f"❌ Main endpoint failed - HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Main endpoint error: {e}")
        return False

def main():
    """Run all tests"""
    
    print("🚀 Today's Properties Endpoint Test")
    print("=" * 60)
    print(f"⏰ Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test today endpoint
    today_ok = test_today_endpoint()
    
    # Test main endpoint for comparison
    main_ok = test_main_properties_endpoint()
    
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY:")
    print(f"   Today Endpoint: {'✅ PASS' if today_ok else '❌ FAIL'}")
    print(f"   Main Endpoint:  {'✅ PASS' if main_ok else '❌ FAIL'}")
    
    if today_ok and main_ok:
        print("\n🎉 All tests passed! Your Today section should work.")
        print("\nNext steps:")
        print("1. Add the TodaySection component to your History.jsx")
        print("2. Test the frontend in your browser")
        print("3. Try analyzing a property to see it appear in the Today section")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    exit(main())