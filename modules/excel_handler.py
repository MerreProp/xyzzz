# modules/excel_handler.py
"""
Excel file operations for HMO Analyser with organized file storage
"""

import pandas as pd
import os
from datetime import datetime
from config import DEFAULT_EXCEL_FILENAME, EXCEL_SHEET_NAME, CURRENCY_SYMBOL

# Excel export configuration
EXPORTS_DIR = "exports"
EXCEL_FILE_PREFIX = "hmo_analysis_"

# Create exports directory if it doesn't exist
if not os.path.exists(EXPORTS_DIR):
    os.makedirs(EXPORTS_DIR)
    print(f"✅ Created {EXPORTS_DIR} directory")


def save_to_excel(analysis_data, filename=None):
    """Save analysis results to Excel spreadsheet in exports folder"""
    
    if filename is None:
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        property_id = analysis_data.get('Property ID', 'unknown')
        filename = f"{EXCEL_FILE_PREFIX}{property_id}_{timestamp}.xlsx"
    
    # Ensure we're saving to exports directory
    # Remove any path from filename and create full path
    filename = os.path.basename(filename)
    full_path = os.path.join(EXPORTS_DIR, filename)
    
    # Format available rooms for display - use newline instead of semicolon (without pcm)
    available_rooms_display = '\n'.join(analysis_data.get('Available Rooms Details', [])) if analysis_data.get('Available Rooms Details') else None
    
    # Format all rooms for display - use newline instead of semicolon
    all_rooms_display = '\n'.join(analysis_data.get('All Rooms List', [])) if analysis_data.get('All Rooms List') else None
    
    # Reorganize data in the requested order with new column names
    ordered_data = {
        'Url': analysis_data.get('URL'),
        'Property ID': analysis_data.get('Property ID'),
        'Advertiser': analysis_data.get('Advertiser Name'),
        'Address': analysis_data.get('Full Address'),
        'Date found': analysis_data.get('Analysis Date'),
        'Date gone': None,  # To be implemented later
        'Total rooms': analysis_data.get('Total Rooms'),
        'Available rooms': available_rooms_display,
        'All Rooms': all_rooms_display,
        'Rental income pcm': f"{CURRENCY_SYMBOL}{analysis_data.get('Monthly Income'):.0f}" if analysis_data.get('Monthly Income') else None,
        'Rental Income pa': f"{CURRENCY_SYMBOL}{analysis_data.get('Annual Income'):.0f}" if analysis_data.get('Annual Income') else None,
        'Photo': analysis_data.get('Main Photo URL'),
        'Longitude': analysis_data.get('Longitude'),
        'Latitude': analysis_data.get('Latitude')
    }
    
    # Check if file exists (unlikely in exports folder, but just in case)
    if os.path.exists(full_path):
        # Read existing data
        df_existing = pd.read_excel(full_path)
        # Append new data
        df_new = pd.DataFrame([ordered_data])
        df = pd.concat([df_existing, df_new], ignore_index=True)
    else:
        # Create new dataframe
        df = pd.DataFrame([ordered_data])
    
    # Save to Excel with hyperlinks
    with pd.ExcelWriter(full_path, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name=EXCEL_SHEET_NAME)
        
        # Get the workbook and worksheet
        workbook = writer.book
        worksheet = writer.sheets[EXCEL_SHEET_NAME]
        
        # Add hyperlinks for URL and Photo columns
        for row_num in range(2, len(df) + 2):  # Start from row 2 (after header)
            # URL hyperlink (column A)
            url_cell = worksheet.cell(row=row_num, column=1)
            url = url_cell.value
            if url:
                url_cell.value = "Spareroom"
                url_cell.hyperlink = url
                url_cell.style = "Hyperlink"
            
            # Photo hyperlink (column L)
            photo_cell = worksheet.cell(row=row_num, column=12)
            photo_url = photo_cell.value
            if photo_url and photo_url != 'Not found':
                photo_cell.value = "Photo"
                photo_cell.hyperlink = photo_url
                photo_cell.style = "Hyperlink"
        
        # Enable text wrapping for the Available rooms column (column H) and All Rooms column (column I)
        for row in worksheet.iter_rows(min_row=2, max_row=len(df) + 1, min_col=8, max_col=9):
            for cell in row:
                cell.alignment = cell.alignment.copy(wrap_text=True)
    
    print(f"\n💾 Data saved to {full_path}")
    print(f"📊 Total listings in spreadsheet: {len(df)}")
    
    return full_path


def format_currency(amount):
    """Format amount as currency string"""
    if amount is None:
        return None
    return f"{CURRENCY_SYMBOL}{amount:.0f}"


def get_exports_directory():
    """Get the exports directory path"""
    return EXPORTS_DIR


def cleanup_old_exports(days_old=30):
    """Clean up Excel files older than specified days"""
    import glob
    from datetime import timedelta
    
    cutoff_date = datetime.now() - timedelta(days=days_old)
    deleted_count = 0
    
    try:
        for file_path in glob.glob(os.path.join(EXPORTS_DIR, "*.xlsx")):
            file_stat = os.stat(file_path)
            file_date = datetime.fromtimestamp(file_stat.st_ctime)
            
            if file_date < cutoff_date:
                os.remove(file_path)
                deleted_count += 1
                print(f"🗑️ Deleted old file: {file_path}")
        
        print(f"✅ Cleanup complete: {deleted_count} files deleted")
        return deleted_count
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        return 0


def get_export_stats():
    """Get statistics about exported files"""
    import glob
    
    try:
        excel_files = glob.glob(os.path.join(EXPORTS_DIR, "*.xlsx"))
        total_files = len(excel_files)
        
        if total_files == 0:
            return {
                "total_files": 0,
                "total_size_mb": 0,
                "exports_directory": EXPORTS_DIR,
                "oldest_file": None,
                "newest_file": None
            }
        
        # Calculate total size
        total_size = sum(os.path.getsize(f) for f in excel_files)
        total_size_mb = round(total_size / (1024 * 1024), 2)
        
        # Get file dates
        file_dates = []
        for file_path in excel_files:
            file_stat = os.stat(file_path)
            file_dates.append(datetime.fromtimestamp(file_stat.st_ctime))
        
        oldest_file = min(file_dates).strftime("%Y-%m-%d %H:%M:%S") if file_dates else None
        newest_file = max(file_dates).strftime("%Y-%m-%d %H:%M:%S") if file_dates else None
        
        return {
            "total_files": total_files,
            "total_size_mb": total_size_mb,
            "exports_directory": EXPORTS_DIR,
            "oldest_file": oldest_file,
            "newest_file": newest_file
        }
        
    except Exception as e:
        print(f"❌ Error getting export stats: {e}")
        return {
            "total_files": 0,
            "total_size_mb": 0,
            "exports_directory": EXPORTS_DIR,
            "error": str(e)
        }