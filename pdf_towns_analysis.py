#!/usr/bin/env python3
"""
Towns Analysis from PDFs
========================

Analyze the specific towns mentioned in the PDFs and create town-based
organization for the map.
"""

import pandas as pd
from collections import defaultdict, Counter
import sys
import os

# Add project path for imports
sys.path.insert(0, os.getcwd())

try:
    from database import SessionLocal
    from hmo_registry.database_models import HMORegistry
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False

def analyze_towns_in_database():
    """Analyze the towns/areas in the newly added HMO data"""
    
    if not DATABASE_AVAILABLE:
        print("❌ Database not available")
        return {}
    
    print("🏘️ ANALYZING TOWNS FROM PDF DATA")
    print("=" * 35)
    
    db = SessionLocal()
    town_analysis = {}
    
    try:
        # Get Vale of White Horse properties
        print("\n1️⃣ Vale of White Horse towns:")
        vale_records = db.query(HMORegistry).filter(
            HMORegistry.city == 'vale_of_white_horse'
        ).all()
        
        vale_towns = extract_towns_from_addresses([r.raw_address for r in vale_records])
        town_analysis['vale_of_white_horse'] = vale_towns
        
        for town, count in vale_towns['town_counts'].items():
            print(f"   {town}: {count} properties")
        
        # Get South Oxfordshire properties
        print("\n2️⃣ South Oxfordshire towns:")
        south_oxon_records = db.query(HMORegistry).filter(
            HMORegistry.city == 'south_oxfordshire'
        ).all()
        
        south_oxon_towns = extract_towns_from_addresses([r.raw_address for r in south_oxon_records])
        town_analysis['south_oxfordshire'] = south_oxon_towns
        
        for town, count in south_oxon_towns['town_counts'].items():
            print(f"   {town}: {count} properties")
        
        # Combined analysis
        print(f"\n📊 SUMMARY:")
        print(f"Vale of White Horse: {len(vale_records)} properties in {len(vale_towns['town_counts'])} towns")
        print(f"South Oxfordshire: {len(south_oxon_records)} properties in {len(south_oxon_towns['town_counts'])} towns")
        
        return town_analysis
        
    except Exception as e:
        print(f"❌ Error analyzing towns: {e}")
        return {}
    finally:
        db.close()

def extract_towns_from_addresses(addresses):
    """Extract town information from a list of addresses"""
    
    town_counts = Counter()
    town_postcodes = defaultdict(set)
    sample_addresses = defaultdict(list)
    
    for address in addresses:
        if not address:
            continue
        
        # Split address into parts
        parts = [part.strip() for part in address.split(',')]
        
        # Look for town in the address parts
        town = identify_town_from_address_parts(parts)
        
        if town:
            town_counts[town] += 1
            
            # Extract postcode
            postcode = extract_postcode_from_address(address)
            if postcode:
                town_postcodes[town].add(postcode[:3])  # Postcode area
            
            # Keep sample addresses (max 3 per town)
            if len(sample_addresses[town]) < 3:
                sample_addresses[town].append(address)
    
    return {
        'town_counts': dict(town_counts),
        'town_postcodes': {town: list(postcodes) for town, postcodes in town_postcodes.items()},
        'sample_addresses': dict(sample_addresses)
    }

def identify_town_from_address_parts(address_parts):
    """Identify the town from address parts"""
    
    # Known towns from the PDFs (based on the debug output we saw)
    known_towns = {
        # Vale of White Horse towns
        'oxford': 'Oxford',
        'abingdon': 'Abingdon', 
        'botley': 'Botley',
        'wantage': 'Wantage',
        'kennington': 'Kennington',
        'north hinksey': 'North Hinksey',
        'sutton courtney': 'Sutton Courtney',
        'shippon': 'Shippon',
        'marcham': 'Marcham',
        'appleford': 'Appleford',
        'chilton': 'Chilton',
        'harwell': 'Harwell',
        'frilford heath': 'Frilford Heath',
        
        # South Oxfordshire towns  
        'didcot': 'Didcot',
        'henley on thames': 'Henley-on-Thames',
        'henley': 'Henley-on-Thames',
        'thame': 'Thame',
        'wallingford': 'Wallingford',
        'wheatley': 'Wheatley',
        'sandford': 'Sandford',
        'milton common': 'Milton Common',
        'shiplake': 'Shiplake',
        'clifton hampden': 'Clifton Hampden'
    }
    
    # Look through address parts for town names
    for part in address_parts:
        part_lower = part.lower().strip()
        
        # Direct match
        if part_lower in known_towns:
            return known_towns[part_lower]
        
        # Partial match for compound names
        for town_key, town_name in known_towns.items():
            if town_key in part_lower or part_lower in town_key:
                return town_name
    
    # If no town found, return the last part before postcode (if it looks like a place)
    for part in reversed(address_parts):
        part_clean = part.strip()
        # Skip if it looks like a postcode
        if len(part_clean) >= 6 and any(c.isdigit() for c in part_clean) and any(c.isalpha() for c in part_clean):
            continue
        # Skip if it's very short
        if len(part_clean) < 3:
            continue
        # Return if it looks like a place name
        if part_clean[0].isupper():
            return part_clean
    
    return 'Unknown'

def extract_postcode_from_address(address):
    """Extract UK postcode from address"""
    import re
    
    postcode_pattern = r'([A-Z]{1,2}[0-9R][0-9A-Z]?\s?[0-9][A-Z]{2})'
    match = re.search(postcode_pattern, address.upper())
    
    return match.group(1) if match else None

def create_town_data_sources():
    """Create town-specific data source classes"""
    
    town_analysis = analyze_towns_in_database()
    
    if not town_analysis:
        print("❌ No town analysis available")
        return
    
    print("\n🏗️ CREATING TOWN-BASED DATA SOURCES")
    print("=" * 35)
    
    # Create town configuration
    towns_config = {}
    
    for council, data in town_analysis.items():
        council_name = council.replace('_', ' ').title()
        print(f"\n{council_name}:")
        
        towns_config[council] = {
            'council_name': council_name,
            'towns': {}
        }
        
        for town, count in data['town_counts'].items():
            town_key = town.lower().replace(' ', '_').replace('-', '_')
            postcodes = data['town_postcodes'].get(town, [])
            samples = data['sample_addresses'].get(town, [])
            
            towns_config[council]['towns'][town_key] = {
                'name': town,
                'count': count,
                'postcode_areas': postcodes,
                'sample_addresses': samples[:2]  # Keep 2 samples
            }
            
            print(f"   {town}: {count} properties ({', '.join(postcodes)})")
    
    # Save configuration
    import json
    with open('towns_config.json', 'w') as f:
        json.dump(towns_config, f, indent=2)
    
    print(f"\n💾 Saved town configuration to towns_config.json")
    
    return towns_config

def create_town_based_endpoints():
    """Generate code for town-based API endpoints"""
    
    endpoint_code = '''
# Add these town-based endpoints to your registry_endpoints.py

@router.get("/towns/{council}")
async def get_council_towns(council: str):
    """Get all towns for a specific council"""
    
    town_configs = {
        "vale_of_white_horse": {
            "oxford": {"name": "Oxford", "postcode_areas": ["OX1", "OX2"]},
            "abingdon": {"name": "Abingdon", "postcode_areas": ["OX14"]},
            "botley": {"name": "Botley", "postcode_areas": ["OX2"]},
            "wantage": {"name": "Wantage", "postcode_areas": ["OX12"]},
            "kennington": {"name": "Kennington", "postcode_areas": ["OX1"]},
            "north_hinksey": {"name": "North Hinksey", "postcode_areas": ["OX2"]},