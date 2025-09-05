#!/usr/bin/env python3
"""
Diagnostic Swindon Script
========================
This version helps debug what's happening with the processing
"""

import pandas as pd
import re
import requests
import time

def test_geocoding():
    """Test geocoding with a sample address"""
    print("🧪 Testing geocoding with sample address...")
    
    test_address = "133 Manchester Road, Swindon, Wiltshire, UK"
    
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': test_address,
            'format': 'json',
            'limit': 1,
            'countrycodes': 'gb'
        }
        
        headers = {
            'User-Agent': 'SwindonHMORegistry/1.0 (test@example.com)'
        }
        
        print(f"🌐 Requesting: {url}")
        print(f"📝 Query: {test_address}")
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            results = response.json()
            print(f"📋 Results count: {len(results)}")
            
            if results:
                result = results[0]
                lat, lon = float(result['lat']), float(result['lon'])
                print(f"✅ Geocoding successful: ({lat:.6f}, {lon:.6f})")
                print(f"📍 Display name: {result.get('display_name', 'N/A')}")
                return True
            else:
                print("❌ No results returned")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ Geocoding error: {e}")
        return False

def analyze_excel_data():
    """Analyze the Excel data structure"""
    print("📊 Analyzing Excel data...")
    
    try:
        excel_file = "List_of_houses_in_multiple_occupation__HMOs__in_Swindon-2.xlsx"
        df = pd.read_excel(excel_file, sheet_name='List of HMOs')
        
        print(f"✅ Loaded Excel file successfully")
        print(f"📏 Shape: {df.shape}")
        print(f"📋 Original columns: {list(df.columns)}")
        
        # Clean column names
        df.columns = df.columns.str.strip()
        print(f"🧹 Cleaned columns: {list(df.columns)}")
        
        # Show first few rows
        print(f"\n📝 First 3 rows:")
        for i in range(min(3, len(df))):
            row = df.iloc[i]
            print(f"\nRow {i}:")
            print(f"  HMO Address: {repr(row['HMO Address'])}")
            print(f"  Licence Holder: {repr(row['Licence Holder'])}")
            
            # Clean address for testing
            raw_address = str(row['HMO Address']).strip()
            cleaned_address = re.sub(r'\r\n', ' ', raw_address)
            cleaned_address = re.sub(r'\s+', ' ', cleaned_address).strip()
            
            print(f"  Cleaned Address: {repr(cleaned_address)}")
            
            # Check for postcode
            postcode_pattern = r'([A-Z]{1,2}[0-9]{1,2}[A-Z]?\s?[0-9][A-Z]{2})'
            postcode_match = re.search(postcode_pattern, cleaned_address.upper())
            if postcode_match:
                print(f"  Postcode: {postcode_match.group(1)}")
            else:
                print(f"  Postcode: Not found")
        
        return df
        
    except Exception as e:
        print(f"❌ Error analyzing Excel: {e}")
        return None

def test_single_geocoding(address):
    """Test geocoding a single address"""
    print(f"🔍 Testing geocoding for: {address}")
    
    try:
        full_address = f"{address}, Swindon, Wiltshire, UK"
        
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': full_address,
            'format': 'json',
            'limit': 1,
            'countrycodes': 'gb'
        }
        
        headers = {
            'User-Agent': 'SwindonHMORegistry/1.0 (test@example.com)'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            results = response.json()
            if results:
                result = results[0]
                lat, lon = float(result['lat']), float(result['lon'])
                print(f"✅ Success: ({lat:.6f}, {lon:.6f})")
                return lat, lon
            else:
                print(f"❌ No results for: {full_address}")
                return None, None
        else:
            print(f"❌ HTTP {response.status_code}: {response.text[:100]}...")
            return None, None
            
    except Exception as e:
        print(f"❌ Geocoding error: {e}")
        return None, None

def main():
    print("🔍 Swindon HMO Diagnostic Script")
    print("=" * 40)
    
    # Test 1: Basic geocoding test
    print("\n1️⃣ Testing basic geocoding functionality...")
    geocoding_works = test_geocoding()
    
    # Test 2: Analyze Excel data
    print("\n2️⃣ Analyzing Excel data structure...")
    df = analyze_excel_data()
    
    if df is not None and geocoding_works:
        print("\n3️⃣ Testing geocoding with actual data...")
        
        # Test first few addresses
        for i in range(min(3, len(df))):
            row = df.iloc[i]
            raw_address = str(row['HMO Address']).strip()
            cleaned_address = re.sub(r'\r\n', ' ', raw_address)
            cleaned_address = re.sub(r'\s+', ' ', cleaned_address).strip()
            
            print(f"\n🏠 Testing address {i+1}:")
            lat, lon = test_single_geocoding(cleaned_address)
            
            if lat and lon:
                print("  ✅ Geocoding successful!")
            else:
                print("  ❌ Geocoding failed")
            
            time.sleep(1)  # Rate limiting
    
    # Test 3: Check internet connectivity
    print("\n4️⃣ Testing internet connectivity...")
    try:
        response = requests.get("https://httpbin.org/ip", timeout=5)
        if response.status_code == 200:
            print("✅ Internet connection working")
            ip_info = response.json()
            print(f"📡 Your IP: {ip_info.get('origin', 'Unknown')}")
        else:
            print("❌ Internet connection issue")
    except Exception as e:
        print(f"❌ Internet connectivity error: {e}")
    
    print("\n🎯 Diagnostic complete!")
    
    if geocoding_works and df is not None:
        print("✅ Ready to process Swindon data!")
        
        # Ask if user wants to run without geocoding
        choice = input("\n❓ Geocoding seems to work. Run processing without geocoding for speed? (y/N): ").lower().strip()
        if choice == 'y':
            print("💡 Tip: Run the main script with 'N' when asked about geocoding for faster processing")
    else:
        print("❌ Issues detected. Check your internet connection and try again.")

if __name__ == "__main__":
    main()