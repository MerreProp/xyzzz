#!/usr/bin/env python3
"""
Test PDF Extraction for HMO Data
================================

Quick test script to verify PDF extraction works with your files.
Let's test this first before building the full integration.
"""

import pandas as pd
import os
import sys
from typing import List, Dict, Optional

# Test different PDF extraction methods
def test_extraction_methods():
    """Test which PDF extraction method works best"""
    
    print("🔍 TESTING PDF EXTRACTION METHODS")
    print("=" * 40)
    
    # Check what's available
    methods_available = []
    
    try:
        import tabula
        methods_available.append("tabula-py")
        print("✅ tabula-py available")
    except ImportError:
        print("❌ tabula-py not available (pip install tabula-py)")
    
    try:
        methods_available.append("pdfplumber") 
        print("✅ pdfplumber available")
    except ImportError:
        print("❌ pdfplumber not available (pip install pdfplumber)")
    
    try:
        import PyPDF2
        methods_available.append("PyPDF2")
        print("✅ PyPDF2 available")
    except ImportError:
        print("❌ PyPDF2 not available (pip install PyPDF2)")
    
    if not methods_available:
        print("\n⚠️  No PDF libraries available!")
        print("Install one with:")
        print("  pip install tabula-py  # Best for tables, requires Java")
        print("  pip install pdfplumber  # Pure Python, good for complex layouts")
        return False
    
    return methods_available

def test_tabula_extraction():
    """Test tabula-py extraction"""
    
    try:
        import tabula
    except ImportError:
        return None
    
    print("\n📄 Testing tabula-py extraction...")
    
    # Test Vale of White Horse
    vale_file = "Vale_HMO-licence-register_Jul-25.pdf"
    if os.path.exists(vale_file):
        print(f"   Testing {vale_file}...")
        try:
            # Try to read tables
            dfs = tabula.read_pdf(vale_file, pages='1', multiple_tables=True)
            print(f"   Found {len(dfs)} tables on page 1")
            
            if dfs:
                df = dfs[0]
                print(f"   First table: {df.shape[0]} rows, {df.shape[1]} columns")
                print(f"   Columns: {list(df.columns)}")
                print(f"   First few rows:")
                print(df.head(3))
                return df
        except Exception as e:
            print(f"   ❌ Tabula failed: {e}")
    else:
        print(f"   ❌ File not found: {vale_file}")
    
    return None

def test_pdfplumber_extraction():
    """Test pdfplumber extraction"""
    
    try:
        import pdfplumber
    except ImportError:
        return None
    
    print("\n📄 Testing pdfplumber extraction...")
    
    vale_file = "Vale_HMO-licence-register_Jul-25.pdf"
    if os.path.exists(vale_file):
        print(f"   Testing {vale_file}...")
        try:
            with pdfplumber.open(vale_file) as pdf:
                first_page = pdf.pages[0]
                print(f"   PDF has {len(pdf.pages)} pages")
                
                # Extract tables from first page
                tables = first_page.extract_tables()
                print(f"   Found {len(tables)} tables on page 1")
                
                if tables:
                    table = tables[0]
                    print(f"   First table: {len(table)} rows")
                    print(f"   Headers: {table[0] if table else 'None'}")
                    print(f"   First data row: {table[1] if len(table) > 1 else 'None'}")
                    
                    # Convert to DataFrame
                    if len(table) > 1:
                        df = pd.DataFrame(table[1:], columns=table[0])
                        return df
        except Exception as e:
            print(f"   ❌ PDFplumber failed: {e}")
    else:
        print(f"   ❌ File not found: {vale_file}")
    
    return None

def test_simple_text_extraction():
    """Test simple text extraction as fallback"""
    
    print("\n📝 Testing simple text extraction...")
    
    # Try PyPDF2 first
    try:
        import PyPDF2
        
        vale_file = "Vale_HMO-licence-register_Jul-25.pdf"
        if os.path.exists(vale_file):
            with open(vale_file, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                first_page = reader.pages[0]
                text = first_page.extract_text()
                
                print(f"   Extracted {len(text)} characters from page 1")
                print("   First 500 characters:")
                print(text[:500])
                
                # Look for addresses
                lines = text.split('\n')
                address_lines = [line for line in lines if any(char.isdigit() for char in line) and len(line) > 10]
                print(f"   Found {len(address_lines)} potential address lines")
                
                return text
    
    except ImportError:
        pass
    
    # Try pdfplumber for text
    try:
        import pdfplumber
        
        vale_file = "Vale_HMO-licence-register_Jul-25.pdf"
        if os.path.exists(vale_file):
            with pdfplumber.open(vale_file) as pdf:
                first_page = pdf.pages[0]
                text = first_page.extract_text()
                
                print(f"   Extracted {len(text)} characters from page 1")
                return text
    
    except ImportError:
        pass
    
    print("   ❌ No text extraction method available")
    return None

def create_test_data_source():
    """Create a simple test data source class"""
    
    code = '''
# test_vale_extraction.py - Quick test of Vale data extraction

import pandas as pd
import os

def extract_vale_data_quick_test():
    """Quick test extraction"""
    
    # Try tabula first
    try:
        import tabula
        
        pdf_file = "Vale_HMO-licence-register_Jul-25.pdf"
        if not os.path.exists(pdf_file):
            print("❌ PDF file not found")
            return None
        
        print("📄 Extracting Vale of White Horse data...")
        
        # Extract all tables from all pages
        dfs = tabula.read_pdf(pdf_file, pages='all', multiple_tables=True)
        print(f"Found {len(dfs)} tables")
        
        if dfs:
            # Combine all tables
            combined_df = pd.concat(dfs, ignore_index=True)
            print(f"Combined: {len(combined_df)} rows, {len(combined_df.columns)} columns")
            
            # Clean column names
            combined_df.columns = [col.strip() if isinstance(col, str) else col for col in combined_df.columns]
            
            # Show what we got
            print("\\nColumns found:")
            for i, col in enumerate(combined_df.columns):
                print(f"  {i}: {col}")
            
            print("\\nFirst few rows:")
            print(combined_df.head())
            
            # Save for inspection
            combined_df.to_csv("vale_extracted_test.csv", index=False)
            print("\\n💾 Saved to vale_extracted_test.csv")
            
            return combined_df
        else:
            print("❌ No tables extracted")
            return None
            
    except ImportError:
        print("❌ tabula-py not available")
        return None
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        return None

if __name__ == "__main__":
    df = extract_vale_data_quick_test()
    if df is not None:
        print("\\n✅ Test extraction successful!")
    else:
        print("\\n❌ Test extraction failed")
'''
    
    with open("test_vale_extraction.py", "w") as f:
        f.write(code)
    
    print("💾 Created test_vale_extraction.py")

def main():
    """Main test function"""
    
    print("🧪 HMO PDF EXTRACTION TEST")
    print("=" * 30)
    
    # Step 1: Check what PDF files we have
    pdf_files = [
        "Vale_HMO-licence-register_Jul-25.pdf",
        "South_HMO-licence-register_Jul-25.pdf"
    ]
    
    print("\\n📁 Checking for PDF files...")
    found_files = []
    for pdf_file in pdf_files:
        if os.path.exists(pdf_file):
            print(f"✅ Found: {pdf_file}")
            found_files.append(pdf_file)
        else:
            print(f"❌ Missing: {pdf_file}")
    
    if not found_files:
        print("\\n⚠️  No PDF files found!")
        print("Make sure the PDF files are in the current directory:")
        print("  - Vale_HMO-licence-register_Jul-25.pdf")
        print("  - South_HMO-licence-register_Jul-25.pdf")
        return False
    
    # Step 2: Test extraction methods
    available_methods = test_extraction_methods()
    if not available_methods:
        return False
    
    # Step 3: Test each method
    test_results = {}
    
    if "tabula-py" in available_methods:
        test_results["tabula"] = test_tabula_extraction()
    
    if "pdfplumber" in available_methods:
        test_results["pdfplumber"] = test_pdfplumber_extraction()
    
    # Always try text extraction as fallback
    test_results["text"] = test_simple_text_extraction()
    
    # Step 4: Results summary
    print("\\n📊 TEST RESULTS SUMMARY")
    print("=" * 25)
    
    for method, result in test_results.items():
        if result is not None:
            if isinstance(result, pd.DataFrame):
                print(f"✅ {method}: Extracted DataFrame with {len(result)} rows")
            else:
                print(f"✅ {method}: Extracted data")
        else:
            print(f"❌ {method}: Failed")
    
    # Step 5: Recommend next steps
    print("\\n🎯 NEXT STEPS:")
    
    successful_methods = [method for method, result in test_results.items() if result is not None]
    
    if "tabula" in successful_methods:
        print("✅ Tabula worked - this is the best option for clean table extraction")
        create_test_data_source()
        print("\\n🚀 To test further:")
        print("   python3 test_vale_extraction.py")
    elif "pdfplumber" in successful_methods:
        print("✅ PDFplumber worked - good alternative for table extraction")
    elif "text" in successful_methods:
        print("⚠️  Only text extraction worked - will need parsing logic")
    else:
        print("❌ No methods worked - may need to try different approaches")
    
    return len(successful_methods) > 0

if __name__ == "__main__":
    success = main()
    if success:
        print("\\n🎉 Testing completed! Ready to build full extraction.")
    else:
        print("\\n❌ Testing failed. Check the issues above.")