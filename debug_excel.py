# debug_excel.py
# Test Excel loading step by step to find the exact issue

import pandas as pd
import re
from datetime import datetime, timedelta

print("🔍 Testing Excel loading step by step...")

def safe_excel_date_to_datetime(excel_date):
    """Convert Excel serial date to Python datetime - SAFE VERSION"""
    if pd.isna(excel_date) or excel_date == '':
        return None
    try:
        base_date = datetime(1900, 1, 1)
        return base_date + timedelta(days=float(excel_date) - 2)
    except (ValueError, TypeError):
        return None

def safe_extract_postcode(address):
    """Extract postcode without problematic regex"""
    if not address:
        return None
    
    # Use simple string operations instead of regex
    words = str(address).upper().split()
    for word in words:
        # Look for something that looks like a UK postcode (simple check)
        if len(word) >= 5 and len(word) <= 8:
            # Basic format: letters+numbers+space+numbers+letters
            if any(char.isdigit() for char in word) and any(char.isalpha() for char in word):
                return word
    return None

try:
    print("📄 Step 1: Reading Excel file...")
    df = pd.read_excel('HMO Register Copy.xlsx', sheet_name=0, header=None)
    print(f"✅ Excel file read successfully: {len(df)} rows")
    
    print("📄 Step 2: Finding headers...")
    header_rows = []
    for index, row in df.iterrows():
        if any(str(cell).strip() == "Case Number" for cell in row if pd.notna(cell)):
            header_rows.append(index)
            if len(header_rows) >= 3:  # Just find first few for testing
                break
    
    print(f"✅ Found {len(header_rows)} header rows: {header_rows}")
    
    print("📄 Step 3: Processing first data block...")
    if header_rows:
        first_header_row = header_rows[0]
        column_names = df.iloc[first_header_row].tolist()
        print(f"✅ Column names: {column_names[:5]}...")  # Show first 5
        
        # Process just a few rows to test
        test_block = df.iloc[first_header_row + 1:first_header_row + 6]
        print(f"✅ Test block shape: {test_block.shape}")
        
        # Test processing one record
        print("📄 Step 4: Testing record processing...")
        for _, row in test_block.iterrows():
            try:
                # Test safe functions
                first_cell = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
                if first_cell and first_cell != "Case Number":
                    print(f"✅ Processing record: {first_cell}")
                    
                    # Test postcode extraction
                    address = str(row.iloc[1]).strip() if len(row) > 1 and pd.notna(row.iloc[1]) else ""
                    if address:
                        postcode = safe_extract_postcode(address)
                        print(f"  Address: {address[:50]}...")
                        print(f"  Postcode: {postcode}")
                    
                    # Test date conversion (this might be the issue)
                    if len(row) > 4:
                        date_cell = row.iloc[4]
                        if pd.notna(date_cell):
                            converted_date = safe_excel_date_to_datetime(date_cell)
                            print(f"  Date conversion: {date_cell} -> {converted_date}")
                    
                    break  # Just test one record
                    
            except Exception as e:
                print(f"❌ Error processing record: {e}")
                import traceback
                traceback.print_exc()
                break
    
    print("✅ Excel loading test completed successfully!")

except Exception as e:
    print(f"❌ Excel loading test failed: {e}")
    import traceback
    traceback.print_exc()