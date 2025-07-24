# modules/postcodes_io.py
"""
Postcodes.io API integration for UK postcode geocoding
"""

import requests
from typing import Optional, Dict, Any
import asyncio
from config import REQUEST_TIMEOUT

async def geocode_postcode_io(postcode: str) -> Optional[Dict[str, Any]]:
    """
    Geocode using Postcodes.io API for UK postcodes
    """
    try:
        # Clean the postcode
        clean_postcode = postcode.replace(' ', '').upper()
        
        url = f"https://api.postcodes.io/postcodes/{clean_postcode}"
        
        # Use asyncio to make async request
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, 
            lambda: requests.get(url, timeout=REQUEST_TIMEOUT)
        )
        
        if response.status_code == 200:
            data = response.json()
            result = data.get('result', {})
            
            return {
                'postcode': result.get('postcode'),
                'latitude': result.get('latitude'),
                'longitude': result.get('longitude'),
                'city': result.get('admin_district'),  # Maps to your city field
                'area': result.get('admin_ward'),      # Maps to your area field  
                'district': result.get('admin_district'),
                'county': result.get('admin_county'),
                'country': result.get('country', 'England'),
                'constituency': result.get('parliamentary_constituency'),
                'eastings': result.get('eastings'),
                'northings': result.get('northings'),
                'quality': result.get('quality'),
                'eu_electoral_region': result.get('european_electoral_region'),
                'primary_care_trust': result.get('primary_care_trust'),
                'region': result.get('region'),
                'nuts': result.get('nuts')
            }
        else:
            print(f"Postcodes.io API returned status {response.status_code} for postcode {clean_postcode}")
            return None
            
    except Exception as e:
        print(f"Postcodes.io geocoding failed for {postcode}: {e}")
        return None

async def reverse_geocode_postcode_io(lat: float, lon: float) -> Optional[Dict[str, Any]]:
    """
    Reverse geocode using Postcodes.io API
    """
    try:
        url = f"https://api.postcodes.io/postcodes?lon={lon}&lat={lat}"
        
        # Use asyncio to make async request
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, 
            lambda: requests.get(url, timeout=REQUEST_TIMEOUT)
        )
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('result', [])
            
            if results:
                # Return the closest postcode
                closest = results[0]
                return {
                    'postcode': closest.get('postcode'),
                    'distance': closest.get('distance'),  # Distance in meters
                    'latitude': closest.get('latitude'),
                    'longitude': closest.get('longitude'),
                    'city': closest.get('admin_district'),
                    'area': closest.get('admin_ward'),
                    'district': closest.get('admin_district'),
                    'county': closest.get('admin_county'),
                    'country': closest.get('country', 'England')
                }
        else:
            print(f"Postcodes.io reverse geocoding returned status {response.status_code} for coords {lat}, {lon}")
            return None
            
    except Exception as e:
        print(f"Postcodes.io reverse geocoding failed for {lat}, {lon}: {e}")
        return None