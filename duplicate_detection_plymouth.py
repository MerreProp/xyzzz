#!/usr/bin/env python3
"""
Find Existing Duplicates in Database
Run this script to identify properties that may be duplicates due to the bug
"""

import sys
import os
from typing import List, Dict, Any, Tuple
from geopy.distance import geodesic
from collections import defaultdict
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import Property, PropertyAnalysis
from crud import PropertyCRUD, AnalysisCRUD
from duplicate_detection import calculate_multi_factor_confidence_score


def find_coordinate_duplicates(max_distance_meters: int = 50) -> List[Dict]:
    """Find properties that are very close together (likely duplicates)"""
    
    db = SessionLocal()
    try:
        # Get all properties with coordinates
        properties_with_coords = db.query(Property).filter(
            Property.latitude.isnot(None),
            Property.longitude.isnot(None)
        ).all()
        
        print(f"🔍 Checking {len(properties_with_coords)} properties with coordinates...")
        
        duplicate_groups = []
        processed_ids = set()
        
        for i, prop1 in enumerate(properties_with_coords):
            if str(prop1.id) in processed_ids:
                continue
                
            # Find all properties within max_distance_meters
            nearby_properties = []
            
            for j, prop2 in enumerate(properties_with_coords):
                if i == j or str(prop2.id) in processed_ids:
                    continue
                
                try:
                    distance = geodesic(
                        (prop1.latitude, prop1.longitude),
                        (prop2.latitude, prop2.longitude)
                    ).meters
                    
                    if distance <= max_distance_meters:
                        nearby_properties.append({
                            'property': prop2,
                            'distance_meters': round(distance, 1)
                        })
                        
                except Exception as e:
                    print(f"⚠️ Error calculating distance: {e}")
                    continue
            
            if nearby_properties:
                # Get analysis data for confidence calculation
                prop1_analysis = AnalysisCRUD.get_latest_analysis(db, prop1.id)
                
                group = {
                    'primary_property': {
                        'id': str(prop1.id),
                        'url': prop1.url,
                        'address': prop1.address,
                        'coordinates': (prop1.latitude, prop1.longitude),
                        'created_at': prop1.created_at.isoformat() if prop1.created_at else None,
                        'analysis': {
                            'monthly_income': float(prop1_analysis.monthly_income) if prop1_analysis and prop1_analysis.monthly_income else None,
                            'total_rooms': prop1_analysis.total_rooms if prop1_analysis else None,
                            'advertiser_name': prop1_analysis.advertiser_name if prop1_analysis else None
                        } if prop1_analysis else None
                    },
                    'nearby_properties': []
                }
                
                # Mark primary as processed
                processed_ids.add(str(prop1.id))
                
                for nearby in nearby_properties:
                    prop2 = nearby['property']
                    prop2_analysis = AnalysisCRUD.get_latest_analysis(db, prop2.id)
                    
                    # Calculate confidence score
                    confidence_score = 0.0
                    if prop1_analysis and prop2_analysis:
                        try:
                            existing_data = {
                                'address': prop1.address,
                                'latitude': prop1.latitude,
                                'longitude': prop1.longitude,
                                'latest_analysis': {
                                    'monthly_income': float(prop1_analysis.monthly_income) if prop1_analysis.monthly_income else None,
                                    'total_rooms': prop1_analysis.total_rooms,
                                    'advertiser_name': prop1_analysis.advertiser_name
                                }
                            }
                            
                            confidence_score, _ = calculate_multi_factor_confidence_score(
                                existing_property=existing_data,
                                new_address=prop2.address,
                                new_latitude=prop2.latitude,
                                new_longitude=prop2.longitude,
                                new_price=float(prop2_analysis.monthly_income) if prop2_analysis.monthly_income else None,
                                new_room_count=prop2_analysis.total_rooms,
                                new_advertiser=prop2_analysis.advertiser_name
                            )
                        except Exception as e:
                            print(f"⚠️ Error calculating confidence: {e}")
                    
                    nearby_prop_data = {
                        'id': str(prop2.id),
                        'url': prop2.url,
                        'address': prop2.address,
                        'coordinates': (prop2.latitude, prop2.longitude),
                        'distance_meters': nearby['distance_meters'],
                        'confidence_score': round(confidence_score, 3),
                        'created_at': prop2.created_at.isoformat() if prop2.created_at else None,
                        'analysis': {
                            'monthly_income': float(prop2_analysis.monthly_income) if prop2_analysis and prop2_analysis.monthly_income else None,
                            'total_rooms': prop2_analysis.total_rooms if prop2_analysis else None,
                            'advertiser_name': prop2_analysis.advertiser_name if prop2_analysis else None
                        } if prop2_analysis else None
                    }
                    
                    group['nearby_properties'].append(nearby_prop_data)
                    processed_ids.add(str(prop2.id))
                
                # Sort by confidence score
                group['nearby_properties'].sort(key=lambda x: x['confidence_score'], reverse=True)
                duplicate_groups.append(group)
        
        return duplicate_groups
        
    finally:
        db.close()


def find_address_duplicates() -> List[Dict]:
    """Find properties with very similar addresses"""
    
    db = SessionLocal()
    try:
        # Get all properties with addresses
        properties = db.query(Property).filter(Property.address.isnot(None)).all()
        
        print(f"🔍 Checking {len(properties)} properties with addresses...")
        
        # Group by normalized address
        address_groups = defaultdict(list)
        
        for prop in properties:
            # Simple normalization
            normalized = prop.address.lower().strip()
            normalized = normalized.replace(',', '').replace('.', '')
            normalized = ' '.join(normalized.split())  # Normalize whitespace
            
            address_groups[normalized].append(prop)
        
        # Find groups with multiple properties
        duplicate_groups = []
        for address, props in address_groups.items():
            if len(props) > 1:
                group = {
                    'normalized_address': address,
                    'properties': []
                }
                
                for prop in props:
                    analysis = AnalysisCRUD.get_latest_analysis(db, prop.id)
                    group['properties'].append({
                        'id': str(prop.id),
                        'url': prop.url,
                        'address': prop.address,
                        'coordinates': (prop.latitude, prop.longitude) if prop.latitude and prop.longitude else None,
                        'created_at': prop.created_at.isoformat() if prop.created_at else None,
                        'analysis': {
                            'monthly_income': float(analysis.monthly_income) if analysis and analysis.monthly_income else None,
                            'total_rooms': analysis.total_rooms if analysis else None,
                            'advertiser_name': analysis.advertiser_name if analysis else None
                        } if analysis else None
                    })
                
                duplicate_groups.append(group)
        
        return duplicate_groups
        
    finally:
        db.close()


def generate_duplicate_report():
    """Generate comprehensive duplicate report"""
    
    print("🔍 DUPLICATE DETECTION REPORT")
    print("=" * 60)
    
    # Find coordinate-based duplicates
    print("\n📍 COORDINATE-BASED DUPLICATES (≤50m)")
    print("-" * 40)
    
    coord_duplicates = find_coordinate_duplicates(max_distance_meters=50)
    
    if coord_duplicates:
        total_potential_duplicates = sum(len(group['nearby_properties']) for group in coord_duplicates)
        print(f"Found {len(coord_duplicates)} clusters with {total_potential_duplicates} potential duplicates")
        
        # Show high confidence matches
        high_confidence_count = 0
        for group in coord_duplicates:
            for nearby in group['nearby_properties']:
                if nearby['confidence_score'] >= 0.7:
                    high_confidence_count += 1
                    print(f"\n🚨 HIGH CONFIDENCE DUPLICATE ({nearby['confidence_score']:.1%})")
                    print(f"   Primary: {group['primary_property']['address']}")
                    print(f"   Duplicate: {nearby['address']}")
                    print(f"   Distance: {nearby['distance_meters']}m")
                    print(f"   Primary ID: {group['primary_property']['id']}")
                    print(f"   Duplicate ID: {nearby['id']}")
        
        print(f"\n🔥 {high_confidence_count} HIGH CONFIDENCE duplicates found!")
    else:
        print("✅ No coordinate-based duplicates found")
    
    # Find address-based duplicates
    print(f"\n🏠 ADDRESS-BASED DUPLICATES")
    print("-" * 40)
    
    address_duplicates = find_address_duplicates()
    
    if address_duplicates:
        print(f"Found {len(address_duplicates)} groups with duplicate addresses")
        
        for group in address_duplicates[:5]:  # Show first 5
            print(f"\n📍 {group['normalized_address']}")
            for prop in group['properties']:
                print(f"   - {prop['id']}: {prop['address']}")
                print(f"     Created: {prop['created_at']}")
    else:
        print("✅ No address-based duplicates found")
    
    # Save detailed report
    report_data = {
        'coordinate_duplicates': coord_duplicates,
        'address_duplicates': address_duplicates,
        'summary': {
            'coordinate_clusters': len(coord_duplicates),
            'address_clusters': len(address_duplicates),
            'total_coordinate_duplicates': sum(len(group['nearby_properties']) for group in coord_duplicates),
            'high_confidence_duplicates': sum(
                1 for group in coord_duplicates 
                for nearby in group['nearby_properties'] 
                if nearby['confidence_score'] >= 0.7
            )
        }
    }
    
    with open('duplicate_report.json', 'w') as f:
        json.dump(report_data, f, indent=2, default=str)
    
    print(f"\n💾 Detailed report saved to: duplicate_report.json")
    
    return report_data


def suggest_cleanup_actions(report_data: Dict):
    """Suggest actions to clean up duplicates"""
    
    print(f"\n🛠️ CLEANUP SUGGESTIONS")
    print("=" * 60)
    
    high_confidence = report_data['summary']['high_confidence_duplicates']
    
    if high_confidence > 0:
        print(f"\n🎯 IMMEDIATE ACTION REQUIRED:")
        print(f"   {high_confidence} high-confidence duplicates found")
        print(f"   These should be merged or linked immediately")
        
        print(f"\n📋 RECOMMENDED ACTIONS:")
        print(f"   1. Review high-confidence matches manually")
        print(f"   2. Use PropertyURL linking for confirmed duplicates")
        print(f"   3. Delete redundant property records")
        print(f"   4. Update room tracking to primary property")
    
    coordinate_clusters = report_data['summary']['coordinate_clusters']
    if coordinate_clusters > 0:
        print(f"\n📍 COORDINATE REVIEW:")
        print(f"   {coordinate_clusters} property clusters within 50m")
        print(f"   Review each cluster for potential duplicates")
    
    address_clusters = report_data['summary']['address_clusters'] 
    if address_clusters > 0:
        print(f"\n🏠 ADDRESS REVIEW:")
        print(f"   {address_clusters} properties with identical addresses")
        print(f"   Check if these are the same property")
    
    print(f"\n⚠️ PREVENTION:")
    print(f"   Apply the duplicate detection fix to prevent future duplicates")


if __name__ == "__main__":
    print("🔍 EXISTING DUPLICATE FINDER")
    print("=" * 60)
    print("This script will identify existing duplicates in your database")
    print("that may have been created due to the duplicate detection bug.")
    print()
    
    confirm = input("Run duplicate detection scan? (y/N): ").lower().strip()
    
    if confirm == 'y':
        try:
            report_data = generate_duplicate_report()
            suggest_cleanup_actions(report_data)
            
            print(f"\n✅ SCAN COMPLETE!")
            print(f"Check duplicate_report.json for full details")
            
        except Exception as e:
            print(f"❌ Error during scan: {e}")
            import traceback
            print(f"Full error: {traceback.format_exc()}")
    else:
        print("Scan cancelled")