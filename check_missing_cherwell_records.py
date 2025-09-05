#!/usr/bin/env python3
"""
Check what Cherwell records are missing and why
"""

import pandas as pd
import sys
import os

def check_missing_records():
    """Check which records were skipped and why"""
    
    print("🔍 CHECKING MISSING CHERWELL RECORDS")
    print("=" * 50)
    
    locations = ['banbury', 'bicester', 'kidlington']
    
    for location in locations:
        csv_path = f"data/cherwell/processed/cherwell_{location}_hmo.csv"
        
        if not os.path.exists(csv_path):
            print(f"❌ CSV not found: {csv_path}")
            continue
            
        print(f"\n📍 {location.upper()}:")
        
        # Read CSV
        df = pd.read_csv(csv_path)
        total_in_csv = len(df)
        
        # Check case numbers
        missing_case_numbers = df[df['case_number'].isna() | (df['case_number'] == '')].copy()
        valid_case_numbers = df[df['case_number'].notna() & (df['case_number'] != '')].copy()
        
        print(f"   📊 Total in CSV: {total_in_csv}")
        print(f"   ✅ Valid case numbers: {len(valid_case_numbers)}")
        print(f"   ❌ Missing case numbers: {len(missing_case_numbers)}")
        
        if len(missing_case_numbers) > 0:
            print(f"   🔍 Records with missing case numbers:")
            for idx, row in missing_case_numbers.head(5).iterrows():
                address = str(row.get('raw_address', 'No address'))[:50]
                print(f"      Row {idx}: {address}...")
        
        # Check for empty addresses
        missing_addresses = df[df['raw_address'].isna() | (df['raw_address'] == '')].copy()
        if len(missing_addresses) > 0:
            print(f"   🏠 Missing addresses: {len(missing_addresses)}")
        
        # Check for duplicates
        if len(valid_case_numbers) > 0:
            duplicates = valid_case_numbers['case_number'].duplicated().sum()
            if duplicates > 0:
                print(f"   🔄 Duplicate case numbers: {duplicates}")

def suggest_fixes():
    """Suggest how to capture the missing records"""
    
    print(f"\n💡 SUGGESTIONS TO CAPTURE MISSING RECORDS:")
    print("=" * 50)
    print("1. **Generate case numbers for missing records:**")
    print("   - Use row index or address hash as case number")
    print("   - Format: 'CHERWELL_BANBURY_001', etc.")
    print()
    print("2. **Relax validation rules:**")
    print("   - Process records even without case numbers")
    print("   - Skip only if both case_number AND address are missing")
    print()
    print("3. **Data quality improvements:**")
    print("   - Check original Cherwell data source")
    print("   - Clean up any parsing issues in CSV processing")

if __name__ == "__main__":
    check_missing_records()
    suggest_fixes()