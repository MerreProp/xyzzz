#!/usr/bin/env python3
"""
Check for and clean up duplicate Cherwell HMO records
"""

import sys
import os
from collections import Counter
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from hmo_registry.database_models import HMORegistry

def check_duplicates():
    """Check for duplicate records in the database"""
    
    print("🔍 CHECKING CHERWELL DUPLICATES")
    print("=" * 50)
    
    db = SessionLocal()
    try:
        # Get all Cherwell records
        cherwell_records = db.query(HMORegistry).filter(
            HMORegistry.city.like('cherwell_%')
        ).all()
        
        print(f"📊 Total Cherwell records in database: {len(cherwell_records)}")
        
        # Group by location
        locations = {}
        for record in cherwell_records:
            city = record.city
            if city not in locations:
                locations[city] = []
            locations[city].append(record)
        
        for city, records in locations.items():
            print(f"\n📍 {city.upper().replace('CHERWELL_', '')}:")
            print(f"   Total records: {len(records)}")
            
            # Check for address duplicates
            addresses = [r.raw_address for r in records]
            address_counts = Counter(addresses)
            duplicates = {addr: count for addr, count in address_counts.items() if count > 1}
            
            if duplicates:
                print(f"   🔄 Duplicate addresses found: {len(duplicates)}")
                print(f"   📋 Top duplicates:")
                for addr, count in sorted(duplicates.items(), key=lambda x: x[1], reverse=True)[:5]:
                    print(f"      {count}x: {addr[:60]}...")
                
                # Show details for first duplicate
                first_duplicate_addr = list(duplicates.keys())[0]
                duplicate_records = [r for r in records if r.raw_address == first_duplicate_addr]
                print(f"\n   🔍 Example duplicate records for: {first_duplicate_addr[:50]}...")
                for i, record in enumerate(duplicate_records):
                    case_num = record.case_number or 'No case number'
                    created = record.created_at.strftime('%Y-%m-%d %H:%M:%S') if record.created_at else 'Unknown'
                    print(f"      Record {i+1}: Case={case_num}, Created={created}")
            else:
                print(f"   ✅ No address duplicates found")
        
        return locations
        
    finally:
        db.close()

def clean_duplicates(dry_run=True):
    """Clean up duplicate records (keeping the oldest)"""
    
    print(f"\n🧹 CLEANING DUPLICATES ({'DRY RUN' if dry_run else 'LIVE RUN'})")
    print("=" * 50)
    
    db = SessionLocal()
    try:
        total_removed = 0
        
        for city_name in ['cherwell_banbury', 'cherwell_bicester', 'cherwell_kidlington']:
            print(f"\n📍 Processing {city_name.replace('cherwell_', '').upper()}...")
            
            # Get all records for this city
            records = db.query(HMORegistry).filter(HMORegistry.city == city_name).all()
            
            # Group by address
            address_groups = {}
            for record in records:
                addr = record.raw_address
                if addr not in address_groups:
                    address_groups[addr] = []
                address_groups[addr].append(record)
            
            city_removed = 0
            
            for address, group in address_groups.items():
                if len(group) > 1:
                    # Sort by created_at (keep oldest)
                    group.sort(key=lambda x: x.created_at or datetime.min)
                    keep_record = group[0]  # Keep the oldest
                    remove_records = group[1:]  # Remove the rest
                    
                    print(f"   🔄 Address: {address[:50]}...")
                    print(f"      Keeping: {keep_record.case_number} (created: {keep_record.created_at})")
                    
                    for record in remove_records:
                        print(f"      Removing: {record.case_number} (created: {record.created_at})")
                        if not dry_run:
                            db.delete(record)
                        city_removed += 1
            
            print(f"   📊 {city_name}: {city_removed} duplicates {'would be' if dry_run else ''} removed")
            total_removed += city_removed
        
        if not dry_run:
            db.commit()
            print(f"\n✅ Committed changes to database")
        
        print(f"\n📊 Total duplicates {'would be' if dry_run else ''} removed: {total_removed}")
        
        # Show final counts
        if not dry_run:
            final_counts = {}
            for city_name in ['cherwell_banbury', 'cherwell_bicester', 'cherwell_kidlington']:
                count = db.query(HMORegistry).filter(HMORegistry.city == city_name).count()
                final_counts[city_name] = count
            
            print(f"\n📊 Final counts after cleanup:")
            for city, count in final_counts.items():
                city_display = city.replace('cherwell_', '').upper()
                print(f"   {city_display}: {count} records")
            
            total_final = sum(final_counts.values())
            print(f"   TOTAL CHERWELL: {total_final} records")
        
        return total_removed
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        db.rollback()
        return 0
    finally:
        db.close()

def show_final_stats():
    """Show final statistics"""
    
    print(f"\n📊 FINAL CHERWELL STATISTICS")
    print("=" * 50)
    
    db = SessionLocal()
    try:
        total_cherwell = db.query(HMORegistry).filter(
            HMORegistry.city.like('cherwell_%')
        ).count()
        
        total_all = db.query(HMORegistry).count()
        
        # Breakdown by city
        banbury = db.query(HMORegistry).filter(HMORegistry.city == 'cherwell_banbury').count()
        bicester = db.query(HMORegistry).filter(HMORegistry.city == 'cherwell_bicester').count()
        kidlington = db.query(HMORegistry).filter(HMORegistry.city == 'cherwell_kidlington').count()
        
        print(f"Banbury: {banbury} records")
        print(f"Bicester: {bicester} records") 
        print(f"Kidlington: {kidlington} records")
        print(f"Total Cherwell: {total_cherwell} records")
        print(f"Total All HMOs: {total_all} records")
        
        # Geocoding stats
        geocoded_cherwell = db.query(HMORegistry).filter(
            HMORegistry.city.like('cherwell_%'),
            HMORegistry.geocoded == True
        ).count()
        
        geocoding_rate = (geocoded_cherwell / total_cherwell * 100) if total_cherwell > 0 else 0
        print(f"Geocoded: {geocoded_cherwell}/{total_cherwell} ({geocoding_rate:.1f}%)")
        
        # Expected totals from CSV
        expected = {'banbury': 114, 'bicester': 77, 'kidlington': 32}
        print(f"\n📈 Coverage vs CSV files:")
        print(f"Banbury: {banbury}/{expected['banbury']} = {(banbury/expected['banbury']*100):.1f}%")
        print(f"Bicester: {bicester}/{expected['bicester']} = {(bicester/expected['bicester']*100):.1f}%")
        print(f"Kidlington: {kidlington}/{expected['kidlington']} = {(kidlington/expected['kidlington']*100):.1f}%")
        
    finally:
        db.close()

def main():
    """Main function"""
    print("🏠 CHERWELL DUPLICATE CHECKER & CLEANER")
    print("=" * 60)
    
    # Check for duplicates
    locations = check_duplicates()
    
    # Check if there are any duplicates to clean
    has_duplicates = False
    for city, records in locations.items():
        addresses = [r.raw_address for r in records]
        address_counts = Counter(addresses)
        duplicates = {addr: count for addr, count in address_counts.items() if count > 1}
        if duplicates:
            has_duplicates = True
            break
    
    if has_duplicates:
        # First do a dry run
        print("\n" + "="*60)
        removed_count = clean_duplicates(dry_run=True)
        
        if removed_count > 0:
            print(f"\n❓ Found {removed_count} duplicate records.")
            print("Would you like to remove them? (This will keep the oldest record for each address)")
            
            # For automation, let's assume yes - but in real use you'd want user input
            response = "y"  # input("Remove duplicates? (y/n): ").lower().strip()
            
            if response == 'y':
                print("\n🧹 Removing duplicates...")
                actual_removed = clean_duplicates(dry_run=False)
                print(f"✅ Removed {actual_removed} duplicate records")
            else:
                print("Keeping duplicates as requested")
    else:
        print("\n✅ No duplicates found!")
    
    # Show final statistics
    show_final_stats()

if __name__ == "__main__":
    main()