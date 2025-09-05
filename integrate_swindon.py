#!/usr/bin/env python3
"""
Fixed Swindon Integration - Using correct field names from HMORegistry model
"""

import sys
import os
from datetime import datetime
import pandas as pd
import time

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from hmo_registry.database_models import HMORegistry

def integrate_swindon_fixed():
    """Swindon integration with correct field names"""
    
    print("🏠 FIXED SWINDON INTEGRATION")
    print("=" * 50)
    
    # Load the processed Swindon CSV
    try:
        csv_path = 'swindon_hmo_processed.csv'
        df = pd.read_csv(csv_path)
        print(f"✅ Loaded {len(df)} Swindon records from {csv_path}")
        
    except FileNotFoundError:
        print(f"❌ {csv_path} not found. Check the file path.")
        return False
    except Exception as e:
        print(f"❌ Error loading CSV: {e}")
        return False
    
    # Check the actual HMORegistry model fields
    print("\n🔍 Checking HMORegistry model fields...")
    sample_hmo = HMORegistry()
    available_fields = [attr for attr in dir(sample_hmo) if not attr.startswith('_') and not callable(getattr(sample_hmo, attr))]
    print(f"Available fields: {available_fields}")
    
    # Process in small batches
    batch_size = 5
    total_rows = len(df)
    inserted = 0
    updated = 0
    errors = 0
    
    for batch_start in range(0, total_rows, batch_size):
        batch_end = min(batch_start + batch_size, total_rows)
        print(f"📦 Processing batch {batch_start + 1}-{batch_end} of {total_rows}...")
        
        db = SessionLocal()
        
        try:
            batch_inserted = 0
            batch_updated = 0
            
            for idx in range(batch_start, batch_end):
                if idx >= len(df):
                    break
                    
                row = df.iloc[idx]
                
                try:
                    # Extract required fields
                    case_number = str(row.get('case_number', f'SWINDON_{idx:04d}')).strip()
                    raw_address = str(row.get('cleaned_address', row.get('raw_address', ''))).strip()
                    
                    if not raw_address:
                        continue
                    
                    # Check if record exists
                    existing = db.query(HMORegistry).filter(
                        HMORegistry.city == 'swindon',
                        HMORegistry.case_number == case_number
                    ).first()
                    
                    if existing:
                        # Update existing record using ONLY valid fields
                        existing.raw_address = raw_address
                        existing.postcode = str(row.get('postcode', '')).strip()
                        existing.latitude = row.get('latitude') if pd.notna(row.get('latitude')) else None
                        existing.longitude = row.get('longitude') if pd.notna(row.get('longitude')) else None
                        existing.geocoded = bool(row.get('geocoded', False))
                        existing.updated_at = datetime.utcnow()
                        batch_updated += 1
                    else:
                        # Create new record using ONLY valid HMORegistry fields
                        hmo_record = HMORegistry(
                            # Core required fields
                            city='swindon',
                            source='swindon_borough_council',
                            case_number=case_number,
                            raw_address=raw_address,
                            
                            # Optional fields that exist in the model
                            data_source_url='https://www.swindon.gov.uk/',
                            postcode=str(row.get('postcode', '')).strip(),
                            latitude=row.get('latitude') if pd.notna(row.get('latitude')) else None,
                            longitude=row.get('longitude') if pd.notna(row.get('longitude')) else None,
                            geocoded=bool(row.get('geocoded', False)),
                            geocoding_source='postcodes_io' if row.get('geocoded') else None,
                            licence_status='active',
                            total_occupants=None,  # Not in Swindon data
                            total_units=None,      # Not in Swindon data
                            licence_start_date=None,
                            licence_expiry_date=None,
                            data_quality_score=0.7,
                            processing_notes='Integrated from Swindon CSV',
                            created_at=datetime.utcnow(),
                            updated_at=datetime.utcnow(),
                            source_last_updated=datetime.utcnow()
                        )
                        
                        db.add(hmo_record)
                        batch_inserted += 1
                
                except Exception as e:
                    print(f"❌ Error with row {idx}: {e}")
                    errors += 1
                    continue
            
            # Commit the batch
            db.commit()
            print(f"✅ Batch complete: +{batch_inserted} inserted, +{batch_updated} updated")
            
            inserted += batch_inserted
            updated += batch_updated
            
        except Exception as e:
            print(f"❌ Batch failed: {e}")
            db.rollback()
        finally:
            db.close()
        
        # Short pause between batches
        time.sleep(1)
    
    # Check final result
    db = SessionLocal()
    try:
        final_count = db.query(HMORegistry).filter(HMORegistry.city == 'swindon').count()
        geocoded_count = db.query(HMORegistry).filter(
            HMORegistry.city == 'swindon',
            HMORegistry.geocoded == True
        ).count()
        
        print(f"\n✅ INTEGRATION SUMMARY:")
        print(f"   📈 New records: {inserted}")
        print(f"   🔄 Updated: {updated}")
        print(f"   ❌ Errors: {errors}")
        print(f"   📊 Total Swindon in DB: {final_count}")
        print(f"   🗺️  Geocoded: {geocoded_count}/{final_count} ({geocoded_count/final_count*100:.1f}%)" if final_count > 0 else "")
        
        return final_count > 0
        
    except Exception as e:
        print(f"❌ Error checking results: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = integrate_swindon_fixed()
    if success:
        print("\n🎉 Swindon integration successful!")
        print("Test with: GET /api/hmo-registry/cities/swindon")
    else:
        print("\n💥 Integration had issues.")
    
    sys.exit(0 if success else 1)