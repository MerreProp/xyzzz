# modules/coordinates.py
"""
Coordinate extraction and geocoding functions for HMO Analyser
Enhanced with UK Postcode API for accurate location data
"""

import requests
import re
import traceback
from config import DEFAULT_HEADERS, REQUEST_TIMEOUT, NOMINATIM_BASE_URL, NOMINATIM_USER_AGENT

# ======================================
# COMPREHENSIVE ENGLISH CITIES AND TOWNS LIST
# ======================================

# Official English Cities (55 total from UK Government)
OFFICIAL_CITIES = [
    "Bath", "Birmingham", "Bradford", "Brighton and Hove", "Bristol", 
    "Cambridge", "Canterbury", "Carlisle", "Chelmsford", "Chester", 
    "Chichester", "Colchester", "Coventry", "Derby", "Doncaster", 
    "Durham", "Ely", "Exeter", "Gloucester", "Hereford", 
    "Kingston upon Hull", "Lancaster", "Leeds", "Leicester", "Lichfield", 
    "Lincoln", "Liverpool", "London", "Manchester", "Milton Keynes", 
    "Newcastle upon Tyne", "Norwich", "Nottingham", "Oxford", "Peterborough", 
    "Plymouth", "Portsmouth", "Preston", "Ripon", "Salford", 
    "Salisbury", "Sheffield", "Southampton", "Southend-on-Sea", "St Albans", 
    "Stoke-on-Trent", "Sunderland", "Truro", "Wakefield", "Wells", 
    "Westminster", "Winchester", "Wolverhampton", "Worcester", "York"
]

# Major Towns and Urban Areas (population >75,000 or significant localities)
MAJOR_TOWNS = [
    "Abingdon", "Accrington", "Aldershot", "Ashford", "Ashton-under-Lyne",
    "Aylesbury", "Banbury", "Barnsley", "Basildon", "Basingstoke",
    "Bedford", "Bicester", "Blackburn", "Blackpool", "Bolton",
    "Bournemouth", "Bracknell", "Bridgwater", "Burnley", "Burton upon Trent",
    "Bury", "Cannock", "Chatham", "Cheltenham", "Chesterfield",
    "Chippenham", "Chorley", "Clacton-on-Sea", "Colchester", "Corby",
    "Crawley", "Crewe", "Darlington", "Dartford", "Dover",
    "Dudley", "Eastbourne", "Ellesmere Port", "Epsom", "Evesham",
    "Farnborough", "Folkestone", "Gillingham", "Gosport", "Gravesend",
    "Great Yarmouth", "Grimsby", "Guildford", "Harlow", "Harrogate",
    "Hastings", "Haywards Heath", "Hemel Hempstead", "High Wycombe", "Hinckley",
    "Horsham", "Huddersfield", "Huntingdon", "Ipswich", "Keighley",
    "Kettering", "Kidderminster", "King's Lynn", "Leamington Spa", "Letchworth",
    "Leyland", "Lowestoft", "Luton", "Macclesfield", "Maidenhead",
    "Maidstone", "Mansfield", "Margate", "Medway", "Middlesbrough",
    "Newbury", "Newhaven", "Northampton", "Nuneaton", "Oldham",
    "Paignton", "Poole", "Ramsgate", "Reading", "Redcar",
    "Redditch", "Rochdale", "Rotherham", "Rugby", "Runcorn",
    "Scunthorpe", "Shrewsbury", "Slough", "Solihull", "South Shields",
    "Southport", "Stafford", "Stevenage", "Stockport", "Stockton-on-Tees",
    "Stourbridge", "Stratford-upon-Avon", "Swindon", "Tamworth", "Taunton",
    "Telford", "Thanet", "Torbay", "Torquay", "Trowbridge",
    "Tunbridge Wells", "Walsall", "Warrington", "Watford", "Wellingborough",
    "Weston-super-Mare", "Weymouth", "Wigan", "Woking", "Worthing",
    "Yeovil"
]

# Smaller Towns and Localities (important for property searches)
SMALLER_TOWNS = [
    "Alton", "Amersham", "Andover", "Arundel", "Bakewell",
    "Beaconsfield", "Berkhamsted", "Blandford Forum", "Bognor Regis", "Bridport",
    "Buckingham", "Bude", "Burnham-on-Sea", "Calne", "Camberley",
    "Chipping Norton", "Cirencester", "Clevedon", "Clitheroe", "Cockermouth",
    "Cranbrook", "Crediton", "Cromer", "Crowborough", "Daventry",
    "Didcot", "Dorchester", "Driffield", "Droitwich", "Dunstable",
    "Dursley", "Fakenham", "Faringdon", "Farnham", "Felixstowe",
    "Frome", "Gainsborough", "Godalming", "Hailsham", "Halesworth",
    "Helston", "Henley-on-Thames", "Hexham", "Honiton", "Horley",
    "Kidlington", "Kingsbridge", "Leighton Buzzard", "Lewes", "Liskeard",
    "Louth", "Ludlow", "Lyme Regis", "Maldon", "Malmesbury",
    "Market Harborough", "Marlborough", "Matlock", "Melksham", "Morpeth",
    "Nantwich", "Newark-on-Trent", "Newmarket", "Newton Abbot", "Oswestry",
    "Otley", "Penrith", "Penzance", "Pershore", "Pickering",
    "Princes Risborough", "Reigate", "Richmond", "Ripon", "Romsey",
    "Ross-on-Wye", "Saffron Walden", "Sevenoaks", "Shaftesbury", "Sherborne",
    "Sidmouth", "Skipton", "St Austell", "St Ives", "Stamford",
    "Stroud", "Sudbury", "Swadlincote", "Tewkesbury", "Thame",
    "Thetford", "Thornbury", "Tiverton", "Totnes", "Towcester",
    "Ulverston", "Uxbridge", "Ventnor", "Wantage", "Warwick",
    "Whitby", "Wimborne", "Windsor", "Wisbech", "Witney",
    "Woodbridge", "Workington"
]

# Combined comprehensive list
ALL_ENGLISH_PLACES = OFFICIAL_CITIES + MAJOR_TOWNS + SMALLER_TOWNS

# Remove duplicates and sort
ENGLISH_CITIES_AND_TOWNS = sorted(list(set(ALL_ENGLISH_PLACES)))

def search_city_in_text(text, cities_list=None):
    """
    Search for any city names that appear in the given text
    Returns the first match found (prioritizing longer/more specific names)
    
    Args:
        text (str): Text to search in (e.g., ward name, district name)
        cities_list (list): Optional custom list, defaults to ENGLISH_CITIES_AND_TOWNS
    
    Returns:
        str or None: First matching city name found, or None if no match
    """
    if not text:
        return None
        
    if cities_list is None:
        cities_list = ENGLISH_CITIES_AND_TOWNS
    
    text_lower = text.lower()
    
    # Sort by length (longest first) to prioritize more specific matches
    sorted_cities = sorted(cities_list, key=len, reverse=True)
    
    for city in sorted_cities:
        if city.lower() in text_lower:
            return city
    
    return None

def find_best_city_match(postcode_data, cities_list=None):
    """
    Enhanced city detection with verification/backup approach
    
    1. First try using admin_district (the API's primary city field)
    2. If that's not in our cities list, then use the enhanced search as backup
    
    Args:
        postcode_data (dict): Data from postcode.io API
        cities_list (list): Optional custom list, defaults to ENGLISH_CITIES_AND_TOWNS
    
    Returns:
        str or None: Best matching city name
    """
    if cities_list is None:
        cities_list = ENGLISH_CITIES_AND_TOWNS
    
    # ✅ STEP 1: Try the API's primary city field (admin_district) first
    api_district = postcode_data.get('admin_district')
    if api_district:
        # Check if the API's district is in our known cities list
        if api_district in cities_list:
            print(f"   ✅ Using API district '{api_district}' (verified in cities list)")
            return api_district
        else:
            print(f"   ⚠️ API district '{api_district}' not in cities list, trying backup search...")
    
    # ✅ STEP 2: Backup - use enhanced search through all fields
    search_fields = [
        'admin_ward',                    # Most specific - often contains actual town name
        'parliamentary_constituency',    # Often contains town name 
        'admin_district',               # District level - may be broader
        'admin_county'                  # Broadest - only as last resort
    ]
    
    # Search each field for city matches
    for field in search_fields:
        if field in postcode_data and postcode_data[field]:
            found_city = search_city_in_text(postcode_data[field], cities_list)
            if found_city:
                print(f"   🔄 Backup found city '{found_city}' in {field}: '{postcode_data[field]}'")
                return found_city
    
    print("   ❌ No city match found in any field")
    return None


# ======================================
# NEW: UK POSTCODE API FUNCTIONS
# ======================================

def extract_postcode_from_address(address):
    """Extract UK postcode from address string"""
    if not address:
        return None
    
    # UK postcode regex pattern
    postcode_pattern = r'([A-Z]{1,2}[0-9R][0-9A-Z]?\s?[0-9][A-Z]{2})'
    match = re.search(postcode_pattern, address.upper())
    
    return match.group(1).strip() if match else None

def extract_postcode_from_content(content):
    """Extract UK postcode from page content"""
    if not content:
        return None
    
    # Look for postcode in page content
    postcode_matches = re.findall(r'([A-Z]{1,2}[0-9R][0-9A-Z]?\s?[0-9][A-Z]{2})', content.upper())
    
    # Return the first postcode found (most likely to be the property postcode)
    return postcode_matches[0] if postcode_matches else None

def get_location_from_uk_postcode(postcode, analysis_data):
    """
    Get accurate location data from UK postcode using postcodes.io API
    NOW ENHANCED with comprehensive English cities list
    """
    try:
        # Clean postcode
        cleaned_postcode = postcode.strip().replace(' ', '').upper()
        
        # Postcodes.io API endpoint
        url = f"https://api.postcodes.io/postcodes/{cleaned_postcode}"
        
        print(f"🔍 Looking up postcode: {postcode}")
        
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        
        if response.status_code == 200:
            data = response.json()
            
            if data['status'] == 200:
                result = data['result']
                
                # Extract basic location data
                location_data = {
                    'postcode': result['postcode'],
                    'latitude': result['latitude'],
                    'longitude': result['longitude'],
                    'ward': result.get('admin_ward'),
                    'district': result.get('admin_district'),
                    'county': result.get('admin_county'),
                    'country': result.get('country'),
                    'constituency': result.get('parliamentary_constituency'),
                    'full_response': result
                }
                
                # ✅ NEW: Use the comprehensive cities list for city detection
                print(f"🔍 Searching for city in postcode data...")
                city = find_best_city_match(result)
                
                # Fallback to district if no city match found
                if not city:
                    city = result.get('admin_district', 'Unknown')
                    print(f"   🔄 No city match found, using district: {city}")
                
                # Store area (ward) separately if different from city
                area = None
                if result.get('admin_ward') and result.get('admin_ward') != city:
                    area = result.get('admin_ward')
                
                # Update analysis data with all location information
                analysis_data.update({
                    'Postcode': location_data['postcode'],
                    'Latitude': location_data['latitude'],
                    'Longitude': location_data['longitude'],
                    'City': city,
                    'Area': area,
                    'District': location_data['district'],
                    'County': location_data['county'],
                    'Country': location_data['country'],
                    'Constituency': location_data['constituency']
                })
                
                # Build formatted address prioritizing actual location over admin areas
                address_parts = []
                if area and area != city:
                    address_parts.append(area)
                if city:
                    address_parts.append(city)
                if location_data['postcode']:
                    address_parts.append(location_data['postcode'])
                
                formatted_address = ', '.join(address_parts)
                analysis_data['Full Address'] = formatted_address
                
                print(f"✅ Postcode lookup successful!")
                print(f"   📍 City: {city}")
                print(f"   📍 Area: {area}")
                print(f"   📍 District: {location_data['district']}")
                print(f"   📍 County: {location_data['county']}")
                print(f"   📍 Coordinates: {location_data['latitude']}, {location_data['longitude']}")
                
                return location_data
                
        print(f"❌ Postcode lookup failed: HTTP {response.status_code}")
        return None
        
    except Exception as e:
        print(f"❌ Error looking up postcode: {e}")
        return None

def geocode_address(address):
    """
    Geocode a plain address string using Nominatim API
    This is separate from extract_coordinates which is for SpareRoom URLs
    
    Args:
        address (str): Plain address string to geocode
    
    Returns:
        tuple: (latitude, longitude) or None if geocoding fails
    """
    import requests
    import urllib.parse
    import time
    
    if not address or not address.strip():
        return None
    
    try:
        # Clean and prepare address for geocoding
        clean_address = address.strip()
        
        # Add UK to address if not already present
        if 'UK' not in clean_address.upper() and 'UNITED KINGDOM' not in clean_address.upper():
            clean_address += ', UK'
        
        # URL encode the address for the API request
        encoded_address = urllib.parse.quote(clean_address)
        
        # Build proper Nominatim URL
        nominatim_url = f"https://nominatim.openstreetmap.org/search?q={encoded_address}&format=json&limit=1&countrycodes=gb"
        
        # Make the API request with proper headers
        headers = {
            'User-Agent': 'HMO-Analyser/1.0 (Property Analysis Tool)'
        }
        
        # Add a small delay to be respectful to the API
        time.sleep(0.1)
        
        response = requests.get(nominatim_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data and len(data) > 0:
            result = data[0]
            lat = float(result['lat'])
            lon = float(result['lon'])
            
            print(f"✅ Geocoded '{address}' -> {lat}, {lon}")
            return (lat, lon)
        else:
            print(f"❌ No coordinates found for: {clean_address}")
            return None
        
    except Exception as e:
        print(f"🔍 Geocoding failed for '{address}': {e}")
        return None


# ======================================
# ENHANCED COORDINATE EXTRACTION
# ======================================

def extract_coordinates(url, analysis_data):
    """Enhanced coordinate extraction that prioritizes UK postcode API"""
    
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)
    
    try:
        print(f"🔍 Fetching URL...")
        response = session.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        
        content = response.text
        print(f"✅ Page loaded successfully")
        
        # STEP 1: Try to extract postcode from page content and use UK API
        print("\n🇬🇧 Trying UK Postcode API first...")
        postcode = extract_postcode_from_content(content)
        
        if postcode:
            print(f"🔍 Found postcode in page content: {postcode}")
            uk_data = get_location_from_uk_postcode(postcode, analysis_data)
            
            if uk_data:
                return {
                    'latitude': uk_data['latitude'],
                    'longitude': uk_data['longitude'],
                    'found': True,
                    'source': 'uk_postcode_api'
                }
        
        # STEP 2: Fallback to SpareRoom coordinate extraction
        print("\n📍 Trying SpareRoom coordinate extraction...")
        
        # Method 1: Direct regex search for the location object
        location_pattern = r'location:\s*{\s*latitude:\s*"([^"]+)"\s*,\s*longitude:\s*"([^"]+)"\s*,?\s*}'
        
        match = re.search(location_pattern, content)
        
        if match:
            latitude = float(match.group(1))
            longitude = float(match.group(2))
            
            print(f"\n✅ COORDINATES FOUND from SpareRoom!")
            print(f"   📍 Latitude: {latitude}")
            print(f"   📍 Longitude: {longitude}")
            
            # Store in global data
            analysis_data['Latitude'] = latitude
            analysis_data['Longitude'] = longitude
            
            # Try to get UK location data from these coordinates if we don't have postcode data yet
            if not postcode:
                print("🔍 Getting UK location data from coordinates...")
                reverse_geocode_result = reverse_geocode_nominatim(latitude, longitude, analysis_data)
                
                # If we get a postcode from reverse geocoding, try UK API
                if analysis_data.get('Postcode'):
                    uk_data = get_location_from_uk_postcode(analysis_data['Postcode'], analysis_data)
                    if uk_data:
                        # Update with more accurate UK data
                        analysis_data.update({
                            'Latitude': uk_data['latitude'],
                            'Longitude': uk_data['longitude'],
                        })
                        return {
                            'latitude': uk_data['latitude'],
                            'longitude': uk_data['longitude'],
                            'found': True,
                            'source': 'spareroom_coords_then_uk_api'
                        }
            
            return {
                'latitude': latitude,
                'longitude': longitude,
                'found': True,
                'source': 'spareroom_coordinates'
            }
        
        # Method 2: Alternative coordinate pattern
        alt_pattern = r'latitude["\']?\s*:\s*["\']?([+-]?\d+\.?\d*)["\']?\s*,\s*longitude["\']?\s*:\s*["\']?([+-]?\d+\.?\d*)'
        
        match = re.search(alt_pattern, content, re.IGNORECASE)
        
        if match:
            latitude = float(match.group(1))
            longitude = float(match.group(2))
            
            print(f"\n✅ COORDINATES FOUND (alternative pattern)!")
            print(f"   📍 Latitude: {latitude}")
            print(f"   📍 Longitude: {longitude}")
            
            # Store in global data
            analysis_data['Latitude'] = latitude
            analysis_data['Longitude'] = longitude
            
            return {
                'latitude': latitude,
                'longitude': longitude,
                'found': True,
                'source': 'spareroom_coordinates_alt'
            }
        
        print("\n❌ No coordinates or postcode found")
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
    

def extract_postcode_from_address(address):
    """
    Extract UK postcode from address string using regex
    
    Args:
        address (str): Address string containing postcode
    
    Returns:
        str: Extracted postcode or None if not found
    """
    if not address:
        return None
    
    # UK postcode regex pattern - matches various formats
    postcode_patterns = [
        r'\b([A-Z]{1,2}[0-9R][0-9A-Z]? ?[0-9][A-Z]{2})\b',  # Standard format
        r'\b([A-Z]{1,2}[0-9]{1,2} ?[0-9][A-Z]{2})\b',       # Alternative format
    ]
    
    for pattern in postcode_patterns:
        match = re.search(pattern, address.upper())
        if match:
            postcode = match.group(1).strip()
            # Format postcode with space if needed
            if len(postcode) > 3 and ' ' not in postcode:
                postcode = postcode[:-3] + ' ' + postcode[-3:]
            return postcode
    
    return None


# ======================================
# KEEP EXISTING FUNCTIONS (Updated)
# ======================================

def reverse_geocode_nominatim(lat, lon, analysis_data):
    """Get address from coordinates using OpenStreetMap's Nominatim service (backup method)"""
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
            
            # Store in global data (only if not already populated by UK API)
            if not analysis_data.get('Full Address'):
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
        
        # Coordinates (this now calls the enhanced function)
        coords_result = extract_coordinates(url, analysis_data)
        if coords_result.get('found'):
            details['latitude'] = coords_result['latitude']
            details['longitude'] = coords_result['longitude']
        
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