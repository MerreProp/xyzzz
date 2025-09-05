# hmo_registry/utils/improved_geocoding.py
"""
Improved geocoding utilities with multiple strategies for maximum success rate
Incorporates lessons learned from debugging Oxford addresses
"""

import requests
import urllib.parse
import time
import re
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class ImprovedGeocoder:
    """High-success-rate geocoder using multiple strategies"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'HMO-Analyser/1.0 (Property Analysis Tool)'
        })
        # Track statistics
        self.total_requests = 0
        self.successful_requests = 0
        self.postcodes_io_success = 0
        self.nominatim_success = 0
    
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
                    logger.debug(f"🇬🇧 Postcodes.io: {postcode} -> {lat}, {lon}")
                    self.postcodes_io_success += 1
                    return (lat, lon)
        
        except Exception as e:
            logger.debug(f"❌ Postcodes.io failed for '{postcode}': {e}")
        
        return None
    
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
                    logger.debug(f"✅ Nominatim strategy {i+1}: {search_address} -> {lat}, {lon}")
                    self.nominatim_success += 1
                    return (lat, lon)
                
                time.sleep(0.1)  # Rate limiting between strategies
                
            except Exception as e:
                logger.debug(f"❌ Nominatim strategy {i+1} failed for '{search_address}': {e}")
                continue
        
        return None
    
    def geocode_address(self, address: str) -> Optional[Tuple[float, float]]:
        """
        Main geocoding function using multiple strategies for maximum success
        This replaces the old geocode_address function
        """
        
        self.total_requests += 1
        
        if not address or not address.strip():
            return None
        
        logger.debug(f"🔍 Geocoding: {address}")
        
        # Strategy 1: Extract postcode and use postcodes.io (most reliable for UK)
        postcode = self.extract_postcode(address)
        if postcode:
            logger.debug(f"📮 Found postcode: {postcode}")
            coords = self.geocode_postcodes_io(postcode)
            if coords:
                self.successful_requests += 1
                return coords
        
        # Strategy 2: Use Nominatim with multiple address formats
        coords = self.geocode_nominatim(address)
        if coords:
            self.successful_requests += 1
            return coords
        
        # Strategy 3: Try just the postcode area if we have one
        if postcode:
            postcode_area = postcode.split()[0] if ' ' in postcode else postcode[:-3]
            coords = self.geocode_postcodes_io(postcode_area)
            if coords:
                logger.debug(f"🏘️ Using postcode area: {postcode_area}")
                self.successful_requests += 1
                return coords
        
        logger.debug(f"❌ All strategies failed for: {address}")
        return None
    
    def get_statistics(self) -> dict:
        """Get geocoding statistics"""
        success_rate = (self.successful_requests / self.total_requests * 100) if self.total_requests > 0 else 0
        
        return {
            'total_requests': self.total_requests,
            'successful_requests': self.successful_requests,
            'success_rate': round(success_rate, 1),
            'postcodes_io_success': self.postcodes_io_success,
            'nominatim_success': self.nominatim_success
        }


# Global geocoder instance
_geocoder = None

def get_geocoder():
    """Get or create the global geocoder instance"""
    global _geocoder
    if _geocoder is None:
        _geocoder = ImprovedGeocoder()
    return _geocoder

def geocode_address(address: str) -> Optional[Tuple[float, float]]:
    """
    Improved geocode function that replaces the old one
    Uses multiple strategies for maximum success rate
    """
    geocoder = get_geocoder()
    return geocoder.geocode_address(address)

def extract_postcode_from_address(address: str) -> Optional[str]:
    """
    Improved postcode extraction
    """
    geocoder = get_geocoder()
    return geocoder.extract_postcode(address)

def get_geocoding_statistics() -> dict:
    """Get current geocoding statistics"""
    geocoder = get_geocoder()
    return geocoder.get_statistics()