# config.py
"""
Configuration file for HMO Analyser
Contains constants, settings, and default values
"""

# Request headers for web scraping
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# Request timeout settings
REQUEST_TIMEOUT = 30

# Excel file settings
DEFAULT_EXCEL_FILENAME = "HMO_Analysis_Results.xlsx"
EXCEL_SHEET_NAME = "Sheet1"

# Nominatim settings (for reverse geocoding)
NOMINATIM_BASE_URL = "https://nominatim.openstreetmap.org/reverse"
NOMINATIM_USER_AGENT = "SpareRoom Coordinate Extractor/1.0"

# Date format for analysis
DATE_FORMAT = '%d/%m/%y'

# Currency formatting
CURRENCY_SYMBOL = '£'

import os

# Excel export configuration
EXPORTS_DIR = "exports"
EXCEL_FILE_PREFIX = "hmo_analysis_"

# Create exports directory if it doesn't exist
if not os.path.exists(EXPORTS_DIR):
    os.makedirs(EXPORTS_DIR)
    print(f"✅ Created {EXPORTS_DIR} directory")