#!/usr/bin/env python3
"""
Debug PDF Pages - See What's Happening on Each Page
===================================================

Let's examine what data is on each page and why we're only getting
records from page 1.
"""

import pdfplumber
import pandas as pd
import os

def debug_pdf_structure(pdf_path: str):
    """Debug the structure of each page in the PDF"""
    
    print(f"🔍 DEBUGGING {pdf_path}")
    print("=" * 50)
    
    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        return
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            print(f"📄 PDF has {len(pdf.pages)} pages")
            
            for page_num, page in enumerate(pdf.pages):
                print(f"\n📋 PAGE {page_num + 1}")
                print("-" * 20)
                
                # Extract tables
                tables = page.extract_tables()
                print(f"Tables found: {len(tables)}")
                
                if tables:
                    for table_num, table in enumerate(tables):
                        print(f"\nTable {table_num + 1}:")
                        print(f"  Rows: {len(table)}")
                        print(f"  Columns: {len(table[0]) if table else 0}")
                        
                        # Show first few rows
                        print("  First 3 rows:")
                        for i, row in enumerate(table[:3]):
                            print(f"    Row {i}: {row}")
                        
                        # Show last few rows  
                        if len(table) > 3:
                            print("  Last 2 rows:")
                            for i, row in enumerate(table[-2:]):
                                print(f"    Row {len(table)-2+i}: {row}")
                
                # Also try extracting text to see raw content
                text = page.extract_text()
                if text:
                    lines = text.split('\n')
                    print(f"\nText lines: {len(lines)}")
                    print("First 5 text lines:")
                    for i, line in enumerate(lines[:5]):
                        print(f"  {i}: {line}")
                
                # Look for address-like patterns
                address_lines = []
                for line in lines:
                    if any(indicator in line.lower() for indicator in ['road', 'street', 'way', 'close', 'avenue', 'drive']):
                        address_lines.append(line)
                
                print(f"Potential address lines: {len(address_lines)}")
                for addr in address_lines[:3]:
                    print(f"  {addr}")
                
                print("\n" + "="*30)
    
    except Exception as e:
        print(f"❌ Error debugging PDF: {e}")

def test_different_extraction_strategies():
    """Test different ways to extract data from the PDFs"""
    
    print("\n🧪 TESTING DIFFERENT EXTRACTION STRATEGIES")
    print("=" * 45)
    
    pdf_path = "Vale_HMO-licence-register_Jul-25.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        return
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            
            # Strategy 1: Extract all tables with different settings
            print("\n1️⃣ Strategy 1: Default table extraction")
            page2 = pdf.pages[1]  # Page 2 (0-indexed)
            
            tables = page2.extract_tables()
            print(f"Page 2 tables: {len(tables)}")
            
            if tables:
                table = tables[0]
                print(f"Table shape: {len(table)} rows")
                print("First 5 rows:")
                for i, row in enumerate(table[:5]):
                    print(f"  {i}: {row}")
            
            # Strategy 2: Extract with different table settings
            print("\n2️⃣ Strategy 2: Custom table extraction")
            
            custom_tables = page2.extract_tables(
                table_settings={
                    "vertical_strategy": "lines_strict",
                    "horizontal_strategy": "lines_strict",
                    "snap_tolerance": 3,
                    "join_tolerance": 3
                }
            )
            
            print(f"Custom extraction tables: {len(custom_tables)}")
            if custom_tables:
                table = custom_tables[0]
                print(f"Custom table shape: {len(table)} rows")
                
            # Strategy 3: Text-based extraction
            print("\n3️⃣ Strategy 3: Text-based parsing")
            
            text = page2.extract_text()
            lines = text.split('\n')
            
            # Look for lines that contain addresses and data
            data_lines = []
            for line in lines:
                # Look for lines with postcodes (UK format)
                if any(part.upper().strip() for part in line.split() if len(part) >= 6 and part.replace(' ', '').isalnum()):
                    # Check if it looks like it has postcode + numbers
                    import re
                    if re.search(r'[A-Z]{1,2}[0-9][0-9A-Z]?\s*[0-9][A-Z]{2}', line.upper()):
                        data_lines.append(line)
            
            print(f"Potential data lines: {len(data_lines)}")
            for line in data_lines[:3]:
                print(f"  {line}")
            
            # Strategy 4: Different page extraction
            print("\n4️⃣ Strategy 4: Page 3 extraction")
            
            if len(pdf.pages) > 2:
                page3 = pdf.pages[2]
                tables3 = page3.extract_tables()
                print(f"Page 3 tables: {len(tables3)}")
                
                if tables3:
                    table = tables3[0]
                    print(f"Page 3 table shape: {len(table)} rows")
                    print("Page 3 first 3 rows:")
                    for i, row in enumerate(table[:3]):
                        print(f"  {i}: {row}")
    
    except Exception as e:
        print(f"❌ Error testing strategies: {e}")

def create_improved_extractor():
    """Create an improved extraction function"""
    
    improved_code = '''
def extract_all_hmo_data(pdf_path: str) -> List[Dict]:
    """Improved extraction that handles all pages properly"""
    
    all_records = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            print(f"Processing page {page_num + 1}...")
            
            # Method 1: Try table extraction
            tables = page.extract_tables()
            
            if tables:
                for table in tables:
                    records = process_table_flexible(table, page_num + 1)
                    all_records.extend(records)
            
            # Method 2: If no table data, try text parsing
            if not any(tables):
                text_records = extract_from_text(page.extract_text(), page_num + 1)
                all_records.extend(text_records)
    
    return all_records

def process_table_flexible(table: List[List], page_num: int) -> List[Dict]:
    """More flexible table processing"""
    
    if len(table) < 2:
        return []
    
    records = []
    
    # Skip header row(s) and process data
    for i, row in enumerate(table):
        if i == 0:  # Skip header
            continue
            
        # Look for valid data in any row
        if has_property_data(row):
            record = parse_property_row(row, page_num)
            if record:
                records.append(record)
    
    return records

def has_property_data(row: List) -> bool:
    """Check if row contains property data"""
    
    row_text = ' '.join([str(cell) if cell else '' for cell in row])
    
    # Look for UK postcode pattern
    import re
    if re.search(r'[A-Z]{1,2}[0-9][0-9A-Z]?\\s*[0-9][A-Z]{2}', row_text.upper()):
        return True
    
    # Look for address indicators + numbers
    if any(indicator in row_text.lower() for indicator in ['road', 'street', 'way', 'close', 'avenue']):
        if any(cell and str(cell).isdigit() for cell in row):
            return True
    
    return False

def parse_property_row(row: List, page_num: int) -> Dict:
    """Parse a property data row"""
    
    # This would contain the logic to extract address, postcode, 
    # occupants, etc. from the row data
    
    record = {
        'page_num': page_num,
        'raw_row': row,
        # ... extract specific fields
    }
    
    return record
'''
    
    print("\n📝 IMPROVED EXTRACTOR CODE")
    print("=" * 30)
    print("Here's the improved extraction approach:")
    print(improved_code)
    
    # Save the improved code
    with open("improved_extractor.py", "w") as f:
        f.write(improved_code)
    
    print("\n💾 Saved improved extraction code to improved_extractor.py")

def main():
    """Main debug function"""
    
    # Debug Vale of White Horse PDF
    debug_pdf_structure("Vale_HMO-licence-register_Jul-25.pdf")
    
    # Debug South Oxfordshire PDF  
    debug_pdf_structure("South_HMO-licence-register_Jul-25.pdf")
    
    # Test different extraction strategies
    test_different_extraction_strategies()
    
    # Create improved extractor
    create_improved_extractor()

if __name__ == "__main__":
    main()