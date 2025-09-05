#!/usr/bin/env python3
# retry_failed_geocoding.py
"""
Retry geocoding for Oxford properties that failed the first time
Uses improved geocoding strategies on only the failed addresses
"""

from database import SessionLocal
from hmo_registry.database_models import HMORegistry
from hmo_registry.utils.improved_geocoding import geocode_address, get_geocoding_statistics
from sqlalchemy import and_
import time

def retry_failed_geocoding():
    """Retry geocoding for addresses that failed previously"""
    
    db = SessionLocal()
    
    try:
        print("🔍 Finding failed geocoding attempts...")
        
        # Find Oxford records that weren't geocoded
        failed_records = db.query(HMORegistry).filter(
            and_(
                HMORegistry.city == 'oxford',
                HMORegistry.geocoded == False
            )
        ).all()
        
        print(f"📊 Found {len(failed_records)} failed addresses to retry")
        
        if len(failed_records) == 0:
            print("✅ No failed addresses found - all Oxford properties are geocoded!")
            return
        
        # Ask user if they want to proceed
        choice = input(f"\nRetry geocoding for {len(failed_records)} addresses? (Y/n): ").strip().lower()
        if choice == 'n':
            print("❌ Cancelled")
            return
        
        print(f"\n🚀 Starting retry process...")
        start_time = time.time()
        
        success_count = 0
        batch_size = 50
        
        for i, record in enumerate(failed_records):
            print(f"🔍 [{i+1}/{len(failed_records)}] Retrying: {record.raw_address}")
            
            # Try improved geocoding
            coords = geocode_address(record.raw_address)
            
            if coords:
                # Update the record
                record.latitude = coords[0]
                record.longitude = coords[1]
                record.geocoded = True
                record.geocoding_source = 'improved_retry'
                record.processing_notes = 'Geocoded on retry with improved strategies'
                
                success_count += 1
                print(f"  ✅ Success: {coords[0]}, {coords[1]}")
            else:
                print(f"  ❌ Still failed")
            
            # Commit in batches
            if (i + 1) % batch_size == 0:
                db.commit()
                print(f"📦 Committed batch {i + 1}/{len(failed_records)}")
                time.sleep(1)  # Brief pause between batches
        
        # Final commit
        db.commit()
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n✅ Retry complete!")
        print(f"⏰ Time taken: {duration/60:.1f} minutes")
        print(f"📊 Additional successes: {success_count}/{len(failed_records)}")
        
        # New statistics
        total_geocoded = db.query(HMORegistry).filter(
            and_(HMORegistry.city == 'oxford', HMORegistry.geocoded == True)
        ).count()
        
        total_records = db.query(HMORegistry).filter(HMORegistry.city == 'oxford').count()
        new_success_rate = (total_geocoded / total_records * 100) if total_records > 0 else 0
        
        print(f"\n📈 Updated Statistics:")
        print(f"  - Total records: {total_records}")
        print(f"  - Now geocoded: {total_geocoded} ({new_success_rate:.1f}%)")
        print(f"  - Improvement: +{success_count} addresses ({success_count/len(failed_records)*100:.1f}% of failures)")
        
        # Show geocoding method statistics
        geocoding_stats = get_geocoding_statistics()
        print(f"\n📊 Retry Geocoding Performance:")
        print(f"  - Retry requests: {geocoding_stats['total_requests']}")
        print(f"  - Retry successes: {geocoding_stats['successful_requests']}")
        print(f"  - Retry success rate: {geocoding_stats['success_rate']}%")
        
    finally:
        db.close()

def show_failed_addresses_sample():
    """Show a sample of addresses that failed geocoding"""
    
    db = SessionLocal()
    
    try:
        failed_records = db.query(HMORegistry).filter(
            and_(
                HMORegistry.city == 'oxford',
                HMORegistry.geocoded == False
            )
        ).limit(20).all()
        
        print(f"📋 Sample of failed addresses ({len(failed_records)} shown):")
        for i, record in enumerate(failed_records, 1):
            print(f"  {i:2d}. {record.case_number}: {record.raw_address}")
            if record.postcode:
                print(f"      Postcode: {record.postcode}")
            else:
                print(f"      No postcode found")
    
    finally:
        db.close()

def main():
    """Main function"""
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'sample':
            show_failed_addresses_sample()
        elif command == 'retry':
            retry_failed_geocoding()
        else:
            print("❌ Unknown command")
            print("Usage:")
            print("  python3 retry_failed_geocoding.py sample  - Show sample of failed addresses")
            print("  python3 retry_failed_geocoding.py retry   - Retry geocoding failed addresses")
    else:
        print("🎯 Oxford HMO Geocoding Retry Tool")
        print("\nThis will retry geocoding for the ~565 addresses that failed initially")
        print("Using improved geocoding strategies for better success rates")
        
        print("\nUsage:")
        print("  python3 retry_failed_geocoding.py sample  - See what failed")
        print("  python3 retry_failed_geocoding.py retry   - Retry failed addresses")

if __name__ == "__main__":
    main()