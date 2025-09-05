
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
    if re.search(r'[A-Z]{1,2}[0-9][0-9A-Z]?\s*[0-9][A-Z]{2}', row_text.upper()):
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
