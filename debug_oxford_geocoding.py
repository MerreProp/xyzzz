#!/usr/bin/env python3
# debug_oxford_geocoding.py
"""
Debug why Oxford HMO geocoding is failing for many properties
Test different geocoding strategies to achieve 100% success rate
"""

import requests
import pandas as pd
from io import StringIO
from typing import Optional, Tuple, List
import urllib.parse
import time
import re

# Try different geocoding services and strategies
class GeocodingDebugger:
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'HMO-Analyser/1.0 (Property Analysis Tool)'
        })
        self.failed_addresses = []
        self.success_count = 0
        self.total_count = 0
    
    def extract_postcode(self, address: str) -> Optional[str]:
        """Extract UK postcode with multiple patterns"""
        if not address:
            return None
        
        # Multiple postcode patterns to catch edge cases
        patterns = [
            r'\b([A-Z]{1,2}[0-9R][0-9A-Z]? ?[0-9][A-Z]{2})\b',  # Standard
            r'\b([A-Z]{1,2}[0-9]{1,2}[A-Z]? ?[0-9][A-Z]{2})\b',  # Alternative
            r'([A-Z]{2}[0-9] ?[0-9][A-Z]{2})',  # Specific patterns
            r'([A-Z][0-9] ?[0-9][A-Z]{2})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, address.upper())
            if match:
                postcode = match.group(1).strip()
                # Format with space if needed
                if len(postcode) > 3 and ' ' not in postcode:
                    postcode = postcode[:-3] + ' ' + postcode[-3:]
                return postcode
        
        return None
    
    def clean_address(self, address: str) -> str:
        """Clean address for better geocoding"""
        # Remove extra whitespace
        address = re.sub(r'\s+', ' ', address.strip())
        
        # Fix common issues
        address = address.replace('  ', ' ')
        address = address.replace(' ,', ',')
        
        # Ensure proper capitalization
        parts = address.split()
        cleaned_parts = []
        for part in parts:
            if part.isupper() and len(part) > 1:
                part = part.title()
            cleaned_parts.append(part)
        
        return ' '.join(cleaned_parts)
    
    def geocode_nominatim(self, address: str) -> Optional[Tuple[float, float]]:
        """Geocode using Nominatim with multiple strategies"""
        
        strategies = [
            address,  # Original
            f"{address}, Oxford, UK",  # Add city/country
            f"{address}, Oxford, Oxfordshire, UK",  # Add county
            self.clean_address(address),  # Cleaned version
            f"{self.clean_address(address)}, Oxford, UK",  # Cleaned + location
        ]
        
        for i, search_address in enumerate(strategies):
            try:
                encoded_address = urllib.parse.quote(search_address)
                url = f"https://nominatim.openstreetmap.org/search?q={encoded_address}&format=json&limit=1&countrycodes=gb"
                
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                
                if data and len(data) > 0:
                    result = data[0]
                    lat = float(result['lat'])
                    lon = float(result['lon'])
                    print(f"✅ Strategy {i+1} worked: {search_address} -> {lat}, {lon}")
                    return (lat, lon)
                
                time.sleep(0.1)  # Rate limiting
                
            except Exception as e:
                print(f"❌ Strategy {i+1} failed for '{search_address}': {e}")
                continue
        
        return None
    
    def geocode_postcodes_io(self, postcode: str) -> Optional[Tuple[float, float]]:
        """Geocode using postcodes.io API (UK-specific, very reliable)"""
        if not postcode:
            return None
        
        try:
            url = f"https://api.postcodes.io/postcodes/{postcode.replace(' ', '')}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 200 and 'result' in data:
                    result = data['result']
                    lat = float(result['latitude'])
                    lon = float(result['longitude'])
                    print(f"🇬🇧 Postcodes.io: {postcode} -> {lat}, {lon}")
                    return (lat, lon)
        
        except Exception as e:
            print(f"❌ Postcodes.io failed for '{postcode}': {e}")
        
        return None
    
    def geocode_comprehensive(self, address: str) -> Optional[Tuple[float, float]]:
        """Try multiple geocoding strategies in order"""
        
        print(f"\n🔍 Geocoding: {address}")
        
        # Strategy 1: Extract postcode and use postcodes.io (most reliable for UK)
        postcode = self.extract_postcode(address)
        if postcode:
            print(f"📮 Found postcode: {postcode}")
            coords = self.geocode_postcodes_io(postcode)
            if coords:
                return coords
        
        # Strategy 2: Use Nominatim with multiple address formats
        coords = self.geocode_nominatim(address)
        if coords:
            return coords
        
        # Strategy 3: Try just the postcode area if we have one
        if postcode:
            postcode_area = postcode.split()[0] if ' ' in postcode else postcode[:-3]
            coords = self.geocode_postcodes_io(postcode_area)
            if coords:
                print(f"🏘️ Using postcode area: {postcode_area}")
                return coords
        
        print(f"❌ All strategies failed for: {address}")
        return None
    
    def test_oxford_sample(self, sample_size: int = 50):
        """Test geocoding on a sample of Oxford properties"""
        
        print(f"🧪 Testing geocoding on {sample_size} Oxford properties...")
        
        # Fetch Oxford data
        CSV_URL = "https://oxopendata.github.io/register-of-houses-in-multiple-occupation/data/hmo-simplified-register.csv"
        
        try:
            response = self.session.get(CSV_URL, timeout=30)
            response.raise_for_status()
            
            df = pd.read_csv(StringIO(response.text))
            df = df.dropna(subset=['Location'])
            
            # Test sample
            sample_df = df.head(sample_size)
            
            results = []
            self.success_count = 0
            self.total_count = len(sample_df)
            
            print(f"\n🎯 Testing {self.total_count} addresses...")
            
            for _, record in sample_df.iterrows():
                address = str(record['Location']).strip()
                case_number = str(record['Case Number']).strip()
                
                coords = self.geocode_comprehensive(address)
                
                results.append({
                    'case_number': case_number,
                    'address': address,
                    'latitude': coords[0] if coords else None,
                    'longitude': coords[1] if coords else None,
                    'geocoded': coords is not None,
                    'postcode': self.extract_postcode(address)
                })
                
                if coords:
                    self.success_count += 1
                else:
                    self.failed_addresses.append(address)
                
                time.sleep(0.2)  # Rate limiting
            
            # Results
            success_rate = (self.success_count / self.total_count) * 100
            
            print(f"\n📊 GEOCODING RESULTS:")
            print(f"  ✅ Success: {self.success_count}/{self.total_count} ({success_rate:.1f}%)")
            print(f"  ❌ Failed: {len(self.failed_addresses)}")
            
            if self.failed_addresses:
                print(f"\n❌ Failed addresses:")
                for addr in self.failed_addresses[:10]:  # Show first 10
                    print(f"  - {addr}")
                if len(self.failed_addresses) > 10:
                    print(f"  ... and {len(self.failed_addresses) - 10} more")
            
            return results
            
        except Exception as e:
            print(f"❌ Error testing geocoding: {e}")
            return []
    
    def analyze_failures(self, results: List[dict]):
        """Analyze why geocoding failed"""
        
        failed_results = [r for r in results if not r['geocoded']]
        
        if not failed_results:
            print("🎉 No failures to analyze!")
            return
        
        print(f"\n🔍 ANALYZING {len(failed_results)} FAILURES:")
        
        # Pattern analysis
        no_postcode = sum(1 for r in failed_results if not r['postcode'])
        has_postcode = len(failed_results) - no_postcode
        
        print(f"  📮 No postcode found: {no_postcode}")
        print(f"  📮 Has postcode but failed: {has_postcode}")
        
        # Address pattern analysis
        patterns = {
            'flat_numbers': sum(1 for r in failed_results if 'flat' in r['address'].lower()),
            'room_numbers': sum(1 for r in failed_results if 'room' in r['address'].lower()),
            'long_addresses': sum(1 for r in failed_results if len(r['address']) > 50),
            'short_addresses': sum(1 for r in failed_results if len(r['address']) < 20),
        }
        
        print(f"\n📋 Address patterns in failures:")
        for pattern, count in patterns.items():
            if count > 0:
                print(f"  - {pattern}: {count}")


def main():
    """Main testing function"""
    debugger = GeocodingDebugger()
    
    # Test different sample sizes
    print("🚀 Starting comprehensive geocoding test...")
    
    sample_sizes = [100]  # Start small
    
    for size in sample_sizes:
        results = debugger.test_oxford_sample(size)
        debugger.analyze_failures(results)
        
        success_rate = (debugger.success_count / debugger.total_count) * 100
        
        if success_rate >= 95:
            print(f"🎉 Achieved {success_rate:.1f}% success rate with sample of {size}")
            break
        else:
            print(f"📊 Sample {size}: {success_rate:.1f}% success rate - trying larger sample...")
        
        print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    main()