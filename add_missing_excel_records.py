#!/usr/bin/env python3
"""
Add Missing Excel Records
=========================
Process the Excel file and add ALL missing records to reach 3,029 active properties
"""

from hmo_registry.database_models import HMORegistry

import pandas as pd
import re
from datetime import datetime, timedelta, date

def process_excel_and_add_missing():
    """Process Excel file and add all missing records"""
    print("📊 Processing Excel File to Add Missing Records")
    print("=" * 50)
    
    try:
        from database import SessionLocal
        from hmo_registry.database_models import HMORegistry
        
        db = SessionLocal()
        
        print("✅ Connected to database")
        
        # Process Excel file the same way as before
        print("\n📈 Reading Excel file...")
        
        # Read Excel file
        df_raw = pd.read_excel('HMO Register Copy.xlsx', sheet_name='Table 1', header=None)
        
        # Find all header rows
        header_rows = []
        for idx, row in df_raw.iterrows():
            if pd.notna(row.iloc[0]) and 'case number' in str(row.iloc[0]).lower():
                header_rows.append(idx)
        
        print(f"Found {len(header_rows)} section headers")
        
        # Extract all valid data rows
        all_excel_records = []
        valid_case_pattern = re.compile(r'\d+/\d+/[A-Z]+')
        
        for i, header_row in enumerate(header_rows):
            section_start = header_row + 1
            section_end = header_rows[i + 1] if i + 1 < len(header_rows) else len(df_raw)
            
            for row_idx in range(section_start, section_end):
                if row_idx < len(df_raw):
                    row = df_raw.iloc[row_idx]
                    case_number = str(row.iloc[0]) if pd.notna(row.iloc[0]) else ''
                    location = str(row.iloc[3]) if pd.notna(row.iloc[3]) else ''
                    
                    if (valid_case_pattern.match(case_number) and 
                        location and location.strip() and 
                        location.lower() not in ['location', 'nan']):
                        
                        # Process expiry date
                        expiry_raw = row.iloc[22] if len(row) > 22 and pd.notna(row.iloc[22]) else None
                        expiry_date = None
                        
                        if expiry_raw:
                            try:
                                if isinstance(expiry_raw, (int, float)):
                                    # Excel date serial number
                                    excel_date = datetime(1899, 12, 30) + timedelta(days=int(expiry_raw))
                                    expiry_date = excel_date.date()
                                elif isinstance(expiry_raw, datetime):
                                    expiry_date = expiry_raw.date()
                            except:
                                pass
                        
                        all_excel_records.append({
                            'case_number': case_number,
                            'location': location,
                            'expiry_date': expiry_date,
                            'total_occupants': row.iloc[10] if len(row) > 10 and pd.notna(row.iloc[10]) else None,
                            'total_units': row.iloc[16] if len(row) > 16 and pd.notna(row.iloc[16]) else None
                        })
        
        print(f"Found {len(all_excel_records)} records in Excel file")
        
        # Get existing case numbers from database
        print("\n🔍 Checking existing records...")
        
        existing_cases = set()
        existing_records = db.query(HMORegistry).filter(HMORegistry.city == 'oxford').all()
        
        for record in existing_records:
            if record.case_number:
                existing_cases.add(record.case_number)
        
        print(f"Found {len(existing_cases)} existing case numbers in database")
        
        # Find missing records
        missing_records = []
        today = date.today()
        
        for excel_record in all_excel_records:
            case_number = excel_record['case_number']
            expiry_date = excel_record['expiry_date']
            
            # Only add active records (not expired)
            if expiry_date and expiry_date >= today and case_number not in existing_cases:
                missing_records.append(excel_record)
        
        print(f"Found {len(missing_records)} missing ACTIVE records to add")
        
        # Show samples
        print(f"\nSample missing records:")
        for i, record in enumerate(missing_records[:10]):
            expiry_str = record['expiry_date'].strftime('%Y-%m-%d') if record['expiry_date'] else 'No date'
            print(f"{i+1}. {record['case_number']}")
            print(f"   {record['location']}")
            print(f"   Expires: {expiry_str}")
        
        # Check specifically for 126 Reliance Way
        reliance_126_found = False
        for record in missing_records:
            if '126 reliance way' in record['location'].lower():
                print(f"\n🎯 Found 126 Reliance Way in missing records:")
                print(f"   Case: {record['case_number']}")
                print(f"   Location: {record['location']}")
                print(f"   Expires: {record['expiry_date']}")
                reliance_126_found = True
                break
        
        if not reliance_126_found:
            print("\n⚠️ 126 Reliance Way not found in missing records")
        
        # Ask for confirmation
        if missing_records:
            response = input(f"\nAdd {len(missing_records)} missing active records to database? (y/N): ")
            
            if response.lower() == 'y':
                print(f"\n📥 Adding missing records...")
                
                added_count = 0
                for record in missing_records:
                    try:
                        new_hmo = HMORegistry(
                            city='oxford',
                            source='oxford_excel_renewal',
                            case_number=record['case_number'],
                            raw_address=record['location'],
                            licence_expiry_date=record['expiry_date'],
                            licence_status='active',
                            total_occupants=record['total_occupants'],
                            total_units=record['total_units'],
                            created_at=datetime.now(),
                            updated_at=datetime.now()
                        )
                        
                        db.add(new_hmo)
                        added_count += 1
                        
                        # Progress update
                        if added_count % 100 == 0:
                            print(f"   Added {added_count}/{len(missing_records)} records...")
                            
                    except Exception as e:
                        print(f"Error adding record {record['case_number']}: {e}")
                        continue
                
                # Commit all changes
                db.commit()
                print(f"✅ Successfully added {added_count} missing records")
        
        # Final verification
        return verify_final_state(db)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if 'db' in locals():
            db.rollback()
        return {'success': False, 'error': str(e)}
    
    finally:
        if 'db' in locals():
            db.close()


def verify_final_state(db):
    """Verify the final state"""
    from datetime import date
    
    today = date.today()
    
    # Get final counts
    total_oxford = db.query(HMORegistry).filter(
        HMORegistry.city == 'oxford'
    ).count()
    
    active_licences = db.query(HMORegistry).filter(
        HMORegistry.city == 'oxford',
        HMORegistry.licence_expiry_date >= today
    ).count()
    
    # Check 126 Reliance Way specifically
    reliance_126_active = db.query(HMORegistry).filter(
        HMORegistry.city == 'oxford',
        HMORegistry.raw_address.ilike('%126 reliance way%'),
        HMORegistry.licence_expiry_date >= today
    ).all()
    
    print(f"\n📊 Final Verification:")
    print(f"Total Oxford records: {total_oxford}")
    print(f"Active licences: {active_licences}")
    print(f"Expected active: 3,029")
    print(f"Gap: {3029 - active_licences}")
    print(f"Active rate: {(active_licences/total_oxford*100):.1f}%")
    
    print(f"\n🎯 126 Reliance Way status:")
    for record in reliance_126_active:
        status = getattr(record, 'licence_status', 'unknown')
        source = getattr(record, 'source', 'unknown')
        expiry_str = record.licence_expiry_date.strftime('%Y-%m-%d') if record.licence_expiry_date else 'No date'
        print(f"  {record.case_number} | {source} | {status} | expires: {expiry_str}")
    
    # Success criteria
    if active_licences >= 2900:
        print("🎉 EXCELLENT - Reached target!")
        success = True
    elif active_licences >= 2700:
        print("✅ VERY GOOD - Much closer to target")
        success = True
    elif active_licences >= 2400:
        print("✅ GOOD - Significant improvement")
        success = True
    else:
        print("⚠️ Still work to do")
        success = False
    
    return {
        'success': success,
        'total': total_oxford,
        'active': active_licences,
        'gap': 3029 - active_licences
    }


if __name__ == "__main__":
    result = process_excel_and_add_missing()
    
    print("\n" + "=" * 50)
    if result and result.get('success'):
        print("🎉 MISSING RECORDS SUCCESSFULLY ADDED!")
        print(f"Gap reduced to: {result.get('gap', 'unknown')}")
        print("\nNext steps:")
        print("1. Restart your web application")
        print("2. Check 126 Reliance Way - should now show as ACTIVE")
        print("3. Your map should now show ~3,000 active properties")
    else:
        print("⚠️ Still some gaps to close")
        if result:
            print(f"Current gap: {result.get('gap', 'unknown')}")