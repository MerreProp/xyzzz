# modules/coordinates.py
"""
Coordinate extraction and geocoding functions for HMO Analyser
"""

import requests
import re
import traceback
from config import DEFAULT_HEADERS, REQUEST_TIMEOUT, NOMINATIM_BASE_URL, NOMINATIM_USER_AGENT


def extract_coordinates(url, analysis_data):
    """Extract coordinates from SpareRoom listing"""
    
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)
    
    try:
        print(f"🔍 Fetching URL...")
        response = session.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        
        content = response.text
        print(f"✅ Page loaded successfully")
        
        # Method 1: Direct regex search for the location object
        print("\n📍 Searching for coordinates in JavaScript...")
        
        # Pattern to find the location object
        location_pattern = r'location:\s*{\s*latitude:\s*"([^"]+)"\s*,\s*longitude:\s*"([^"]+)"\s*,?\s*}'
        
        match = re.search(location_pattern, content)
        
        if match:
            latitude = match.group(1)
            longitude = match.group(2)
            
            print(f"\n✅ COORDINATES FOUND!")
            print(f"   📍 Latitude: {latitude}")
            print(f"   📍 Longitude: {longitude}")
            print(f"\n🔗 View on Google Maps: https://www.google.com/maps?q={latitude},{longitude}")
            print(f"🔗 View on Apple Maps: https://maps.apple.com/?ll={latitude},{longitude}&q={latitude},{longitude}")
            
            # Store in global data
            analysis_data['Latitude'] = float(latitude)
            analysis_data['Longitude'] = float(longitude)
            
            return {
                'latitude': float(latitude),
                'longitude': float(longitude),
                'found': True
            }
        
        # Method 2: Alternative pattern (in case formatting varies)
        alt_pattern = r'latitude["\']?\s*:\s*["\']?([+-]?\d+\.?\d*)["\']?\s*,\s*longitude["\']?\s*:\s*["\']?([+-]?\d+\.?\d*)'
        
        match = re.search(alt_pattern, content, re.IGNORECASE)
        
        if match:
            latitude = match.group(1)
            longitude = match.group(2)
            
            print(f"\n✅ COORDINATES FOUND (alternative pattern)!")
            print(f"   📍 Latitude: {latitude}")
            print(f"   📍 Longitude: {longitude}")
            print(f"\n🔗 View on Google Maps: https://www.google.com/maps?q={latitude},{longitude}")
            print(f"🔗 View on Apple Maps: https://maps.apple.com/?ll={latitude},{longitude}&q={latitude},{longitude}")
            
            # Store in global data
            analysis_data['Latitude'] = float(latitude)
            analysis_data['Longitude'] = float(longitude)
            
            return {
                'latitude': float(latitude),
                'longitude': float(longitude),
                'found': True
            }
        
        # Method 3: Look for _sr.page object
        page_obj_pattern = r'_sr\.page\s*=\s*{([^}]+location:[^}]+)}'
        match = re.search(page_obj_pattern, content, re.DOTALL)
        
        if match:
            print("📍 Found _sr.page object, searching within it...")
            page_content = match.group(1)
            
            # Search within the page object
            loc_match = re.search(r'latitude:\s*"([^"]+)"\s*,\s*longitude:\s*"([^"]+)"', page_content)
            if loc_match:
                latitude = loc_match.group(1)
                longitude = loc_match.group(2)
                
                print(f"\n✅ COORDINATES FOUND in _sr.page!")
                print(f"   📍 Latitude: {latitude}")
                print(f"   📍 Longitude: {longitude}")
                print(f"\n🔗 View on Google Maps: https://www.google.com/maps?q={latitude},{longitude}")
                print(f"🔗 View on Apple Maps: https://maps.apple.com/?ll={latitude},{longitude}&q={latitude},{longitude}")
                
                # Store in global data
                analysis_data['Latitude'] = float(latitude)
                analysis_data['Longitude'] = float(longitude)
                
                return {
                    'latitude': float(latitude),
                    'longitude': float(longitude),
                    'found': True
                }
        
        print("\n❌ Coordinates not found")
        print("💡 The page structure might have changed")
        
        # Save page for debugging
        with open('coordinate_debug.html', 'w', encoding='utf-8') as f:
            f.write(content)
        print("💾 Page saved as 'coordinate_debug.html' for debugging")
        
        return {'found': False}
        
    except Exception as e:
        print(f"❌ Error: {e}")
        traceback.print_exc()
        return {'found': False, 'error': str(e)}


def extract_property_details(url, analysis_data):
    """Extract coordinates and other property details"""
    
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)
    
    try:
        response = session.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        content = response.text
        
        # Extract various details
        details = {}
        
        # Coordinates
        location_match = re.search(r'location:\s*{\s*latitude:\s*"([^"]+)"\s*,\s*longitude:\s*"([^"]+)"', content)
        if location_match:
            details['latitude'] = float(location_match.group(1))
            details['longitude'] = float(location_match.group(2))
        
        # Property ID
        id_match = re.search(r'advert:\s*{[^}]*id:\s*"(\d+)"', content)
        if id_match:
            details['property_id'] = id_match.group(1)
            analysis_data['Property ID'] = id_match.group(1)
        
        # Title
        title_match = re.search(r'share_title:\s*"([^"]+)"', content)
        if title_match:
            details['title'] = title_match.group(1)
            analysis_data['Title'] = title_match.group(1)
        
        # Apple Maps Token (if needed for future use)
        token_match = re.search(r'apple_maps_token:\s*"([^"]+)"', content)
        if token_match:
            details['apple_maps_token'] = token_match.group(1)
        
        return details
        
    except Exception as e:
        print(f"❌ Error extracting details: {e}")
        return {}


def reverse_geocode_nominatim(lat, lon, analysis_data):
    """Get address from coordinates using OpenStreetMap's Nominatim service (free, no API key needed)"""
    try:
        params = {
            'lat': lat,
            'lon': lon,
            'format': 'json',
            'addressdetails': 1
        }
        headers = {
            'User-Agent': NOMINATIM_USER_AGENT
        }
        
        response = requests.get(NOMINATIM_BASE_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if 'address' in data:
            addr = data['address']
            
            # Build a formatted address
            address_parts = []
            
            # Street address
            if 'house_number' in addr:
                address_parts.append(addr['house_number'])
            if 'road' in addr:
                address_parts.append(addr['road'])
            
            # Area/Suburb
            if 'suburb' in addr:
                address_parts.append(addr['suburb'])
            elif 'neighbourhood' in addr:
                address_parts.append(addr['neighbourhood'])
            
            # City
            if 'city' in addr:
                address_parts.append(addr['city'])
            elif 'town' in addr:
                address_parts.append(addr['town'])
            
            # Postcode
            if 'postcode' in addr:
                address_parts.append(addr['postcode'])
                analysis_data['Postcode'] = addr['postcode']
            
            formatted_address = ', '.join(filter(None, address_parts))
            
            # Store in global data
            analysis_data['Full Address'] = formatted_address or data.get('display_name', 'Address not found')
            
            return {
                'formatted_address': formatted_address or data.get('display_name', 'Address not found'),
                'components': addr,
                'full_response': data
            }
        
        return {'formatted_address': 'Address not found', 'components': {}, 'full_response': data}
        
    except Exception as e:
        print(f"⚠️  Error with reverse geocoding: {e}")
        return None