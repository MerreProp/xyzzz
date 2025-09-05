#!/usr/bin/env python3
"""
Oxford HMO License Database Integration Script - FIXED VERSION
==============================================================

Integrates Oxford license renewal data with the HMO registry database.
Uses the correct field names from the actual database model.
"""

import sys
import os
import logging
from datetime import datetime
from typing import List, Dict

# Add project path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def integrate_oxford_data():
    """Main function to integrate Oxford data with database"""
    
    print("="*70)
    print("OXFORD HMO LICENSE DATABASE INTEGRATION - FIXED VERSION")
    print("="*70)
    
    # 1. Load Oxford data
    print("\n1. Loading Oxford license data...")
    try:
        from hmo_registry.cities.oxford_renewal import OxfordLicenseRenewalAnalyzer
        analyzer = OxfordLicenseRenewalAnalyzer()
        oxford_data = analyzer.get_hmo_data(force_refresh=True, enable_geocoding=True)
        print(f"✓ Loaded {len(oxford_data)} Oxford records")
    except Exception as e:
        print(f"✗ Error loading Oxford data: {e}")
        return False
    
    if not oxford_data:
        print("✗ No Oxford data to integrate")
        return False
    
    # 2. Database connection and models
    print("\n2. Setting up database connection...")
    try:
        from database import SessionLocal, engine
        from hmo_registry.database_models import HMORegistry, Base
        
        # Create tables if they don't exist
        Base.metadata.create_all(bind=engine)
        
        db = SessionLocal()
        print("✓ Database connection established")
    except Exception as e:
        print(f"✗ Database connection error: {e}")
        return False
    
    try:
        # 3. Check existing Oxford records
        print("\n3. Checking existing Oxford records in database...")
        existing_records = db.query(HMORegistry).filter(
            HMORegistry.city == 'oxford'
        ).all()
        
        existing_case_numbers = {record.case_number for record in existing_records}
        print(f"✓ Found {len(existing_records)} existing Oxford records")
        
        # 4. Process new data
        print("\n4. Processing Oxford data for database integration...")
        
        new_records = 0
        updated_records = 0
        skipped_records = 0
        errors = 0
        
        for i, record in enumerate(oxford_data):
            try:
                case_number = record.get('case_number')
                if not case_number:
                    skipped_records += 1
                    continue
                
                # Check if record exists
                existing_record = db.query(HMORegistry).filter(
                    HMORegistry.case_number == case_number,
                    HMORegistry.city == 'oxford'
                ).first()
                
                # Prepare record data using CORRECT field names
                record_data = {
                    'case_number': case_number,
                    'city': 'oxford',
                    'source': 'oxford_excel_renewal',  # NOT 'data_source'
                    'raw_address': record.get('address', ''),  # NOT 'standardized_address'
                    'postcode': record.get('postcode'),
                    'latitude': record.get('latitude'),
                    'longitude': record.get('longitude'),
                    'geocoded': record.get('geocoded', False),
                    'geocoding_source': 'postcode.io' if record.get('geocoded') else None,
                    'licence_status': record.get('licence_status'),
                    'total_occupants': record.get('total_occupants'),
                    'total_units': record.get('total_units'),
                    'data_source_url': None,  # Not available from Excel
                    'data_quality_score': 1.0,  # High quality - direct from council
                    'processing_notes': 'Imported from Oxford Council Excel register',
                    'updated_at': datetime.now(),  # NOT 'last_updated'
                    'source_last_updated': datetime.now()
                }
                
                # Handle license dates
                if record.get('licence_start_date'):
                    try:
                        record_data['licence_start_date'] = datetime.fromisoformat(
                            record['licence_start_date'].replace('T00:00:00', '')
                        ).date()
                    except:
                        pass
                
                if record.get('licence_expiry_date'):
                    try:
                        record_data['licence_expiry_date'] = datetime.fromisoformat(
                            record['licence_expiry_date'].replace('T00:00:00', '')
                        ).date()
                    except:
                        pass
                
                if existing_record:
                    # Update existing record
                    for key, value in record_data.items():
                        if hasattr(existing_record, key):
                            setattr(existing_record, key, value)
                    updated_records += 1
                else:
                    # Create new record (set created_at for new records)
                    record_data['created_at'] = datetime.now()
                    new_record = HMORegistry(**record_data)
                    db.add(new_record)
                    new_records += 1
                
                # Progress indicator
                if (i + 1) % 500 == 0:
                    print(f"  Processed {i + 1}/{len(oxford_data)} records...")
                    
            except Exception as e:
                errors += 1
                logger.error(f"Error processing record {case_number}: {e}")
                continue
        
        # 5. Commit changes
        print(f"\n5. Committing changes to database...")
        try:
            db.commit()
            print("✓ Database changes committed successfully")
        except Exception as e:
            print(f"✗ Error committing to database: {e}")
            db.rollback()
            return False
        
        # 6. Summary
        print(f"\n6. Integration Summary:")
        print(f"  Total Oxford records processed: {len(oxford_data)}")
        print(f"  New records added: {new_records}")
        print(f"  Existing records updated: {updated_records}")
        print(f"  Records skipped: {skipped_records}")
        print(f"  Errors encountered: {errors}")
        
        # 7. Verification
        print(f"\n7. Database verification...")
        total_oxford_records = db.query(HMORegistry).filter(
            HMORegistry.city == 'oxford'
        ).count()
        
        active_licenses = db.query(HMORegistry).filter(
            HMORegistry.city == 'oxford',
            HMORegistry.licence_status == 'active'
        ).count()
        
        expired_licenses = db.query(HMORegistry).filter(
            HMORegistry.city == 'oxford',
            HMORegistry.licence_status == 'expired'
        ).count()
        
        geocoded_records = db.query(HMORegistry).filter(
            HMORegistry.city == 'oxford',
            HMORegistry.geocoded == True
        ).count()
        
        with_start_dates = db.query(HMORegistry).filter(
            HMORegistry.city == 'oxford',
            HMORegistry.licence_start_date.is_not(None)
        ).count()
        
        with_expiry_dates = db.query(HMORegistry).filter(
            HMORegistry.city == 'oxford',
            HMORegistry.licence_expiry_date.is_not(None)
        ).count()
        
        print(f"  Total Oxford records in database: {total_oxford_records}")
        print(f"  Active licenses: {active_licenses}")
        print(f"  Expired licenses: {expired_licenses}")
        print(f"  Geocoded records: {geocoded_records}")
        print(f"  Records with start dates: {with_start_dates}")
        print(f"  Records with expiry dates: {with_expiry_dates}")
        print(f"  Geocoding rate: {(geocoded_records/total_oxford_records*100):.1f}%")
        print(f"  Date completeness: {(with_expiry_dates/total_oxford_records*100):.1f}%")
        
        return True
        
    finally:
        db.close()

def verify_integration():
    """Verify the integration was successful"""
    
    print("\n" + "="*50)
    print("INTEGRATION VERIFICATION")
    print("="*50)
    
    try:
        from database import SessionLocal
        from hmo_registry.database_models import HMORegistry
        
        db = SessionLocal()
        
        # Get sample records with license dates
        sample_records = db.query(HMORegistry).filter(
            HMORegistry.city == 'oxford',
            HMORegistry.licence_expiry_date.is_not(None)
        ).limit(5).all()
        
        print(f"\nSample records with license dates:")
        print(f"{'Case Number':<20} {'Address':<40} {'Status':<10} {'Expires':<12}")
        print("-" * 85)
        
        for record in sample_records:
            address = (record.raw_address or '')[:35]
            expires = record.licence_expiry_date.strftime('%Y-%m-%d') if record.licence_expiry_date else 'None'
            print(f"{record.case_number:<20} {address:<40} {record.licence_status:<10} {expires:<12}")
        
        # Check for licenses expiring soon
        from datetime import date, timedelta
        today = date.today()
        six_months = today + timedelta(days=180)
        
        expiring_soon = db.query(HMORegistry).filter(
            HMORegistry.city == 'oxford',
            HMORegistry.licence_status == 'active',
            HMORegistry.licence_expiry_date.between(today, six_months)
        ).count()
        
        print(f"\nLicenses expiring in next 6 months: {expiring_soon}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"Error during verification: {e}")
        return False

def run_renewal_analysis():
    """Run a sample renewal analysis on the integrated data"""
    
    print("\n" + "="*50)
    print("SAMPLE RENEWAL ANALYSIS")
    print("="*50)
    
    try:
        from database import SessionLocal
        from hmo_registry.database_models import HMORegistry
        from datetime import date, timedelta
        
        db = SessionLocal()
        
        today = date.today()
        
        # Analysis periods
        periods = [
            ("Next 30 days", today + timedelta(days=30)),
            ("Next 60 days", today + timedelta(days=60)),
            ("Next 90 days", today + timedelta(days=90)),
            ("Next 6 months", today + timedelta(days=180)),
            ("Next 12 months", today + timedelta(days=365))
        ]
        
        print(f"Renewal analysis for Oxford HMO licenses:")
        print(f"Analysis date: {today}")
        print()
        
        for period_name, end_date in periods:
            count = db.query(HMORegistry).filter(
                HMORegistry.city == 'oxford',
                HMORegistry.licence_status == 'active',
                HMORegistry.licence_expiry_date.between(today, end_date)
            ).count()
            
            print(f"{period_name:<20}: {count:>4} licenses")
        
        # Get the earliest expiring licenses
        print(f"\nNext 10 licenses to expire:")
        earliest_expiring = db.query(HMORegistry).filter(
            HMORegistry.city == 'oxford',
            HMORegistry.licence_status == 'active',
            HMORegistry.licence_expiry_date >= today
        ).order_by(HMORegistry.licence_expiry_date).limit(10).all()
        
        for record in earliest_expiring:
            days_until = (record.licence_expiry_date - today).days
            address = (record.raw_address or '')[:40]
            print(f"  {record.licence_expiry_date} ({days_until:>3} days): {record.case_number} - {address}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"Error during renewal analysis: {e}")
        return False

if __name__ == "__main__":
    success = True
    
    # Run integration
    success &= integrate_oxford_data()
    
    if success:
        # Verify integration
        success &= verify_integration()
        
        # Run sample analysis
        success &= run_renewal_analysis()
    
    print("\n" + "="*70)
    if success:
        print("🎉 OXFORD DATABASE INTEGRATION COMPLETED SUCCESSFULLY!")
        print("✓ License data integrated with correct field mapping")
        print("✓ Renewal analysis system operational") 
        print("✓ Ready for production use")
    else:
        print("❌ INTEGRATION FAILED - Check error messages above")
    print("="*70)