#!/usr/bin/env python3
"""
Check the actual fields in the HMORegistry database model
"""

import sys
import os

# Add project path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def check_database_model():
    """Check what fields exist in the HMORegistry model"""
    
    print("="*60)
    print("CHECKING HMO REGISTRY DATABASE MODEL")
    print("="*60)
    
    try:
        from hmo_registry.database_models import HMORegistry
        from sqlalchemy import inspect
        
        print("✓ Successfully imported HMORegistry model")
        
        # Get the model's columns
        inspector = inspect(HMORegistry)
        columns = inspector.columns
        
        print(f"\nHMORegistry model has {len(columns)} columns:")
        print("-" * 40)
        
        for column_name, column in columns.items():
            column_type = str(column.type)
            nullable = "NULL" if column.nullable else "NOT NULL"
            primary_key = "PRIMARY KEY" if column.primary_key else ""
            
            print(f"{column_name:<25} {column_type:<20} {nullable:<10} {primary_key}")
        
        # Also try to get column names directly from the class
        print(f"\nAlternative method - Class attributes:")
        print("-" * 40)
        
        for attr_name in dir(HMORegistry):
            if not attr_name.startswith('_') and not callable(getattr(HMORegistry, attr_name)):
                attr = getattr(HMORegistry, attr_name)
                if hasattr(attr, 'type'):  # SQLAlchemy column
                    print(f"{attr_name:<25} {str(attr.type):<20}")
        
        return list(columns.keys())
        
    except Exception as e:
        print(f"Error checking model: {e}")
        return None

def check_existing_record():
    """Check what fields exist in actual database records"""
    
    print(f"\n" + "="*60)
    print("CHECKING EXISTING DATABASE RECORDS")
    print("="*60)
    
    try:
        from database import SessionLocal
        from hmo_registry.database_models import HMORegistry
        
        db = SessionLocal()
        
        # Get one existing record
        existing_record = db.query(HMORegistry).first()
        
        if existing_record:
            print("✓ Found existing record, checking its attributes:")
            print("-" * 40)
            
            for attr_name in dir(existing_record):
                if not attr_name.startswith('_') and not callable(getattr(existing_record, attr_name)):
                    try:
                        value = getattr(existing_record, attr_name)
                        if value is not None:
                            value_str = str(value)[:30] + "..." if len(str(value)) > 30 else str(value)
                        else:
                            value_str = "None"
                        print(f"{attr_name:<25} = {value_str}")
                    except:
                        print(f"{attr_name:<25} = <could not access>")
        else:
            print("No existing records found in database")
        
        db.close()
        
    except Exception as e:
        print(f"Error checking existing records: {e}")

def suggest_field_mapping():
    """Suggest the correct field mapping based on what we find"""
    
    print(f"\n" + "="*60)
    print("SUGGESTED FIELD MAPPING")
    print("="*60)
    
    # Common field name variations
    field_mapping_suggestions = {
        'case_number': ['case_number', 'case_num', 'reference', 'license_id'],
        'address': ['address', 'raw_address', 'property_address', 'location'],
        'standardized_address': ['standardized_address', 'clean_address', 'formatted_address', 'address'],
        'postcode': ['postcode', 'postal_code', 'zip_code'],
        'latitude': ['latitude', 'lat'],
        'longitude': ['longitude', 'lng', 'lon'],
        'geocoded': ['geocoded', 'is_geocoded'],
        'licence_holder': ['licence_holder', 'license_holder', 'holder_name', 'agent_name'],
        'licence_status': ['licence_status', 'license_status', 'status'],
        'licence_start_date': ['licence_start_date', 'license_start_date', 'start_date', 'issued_date'],
        'licence_expiry_date': ['licence_expiry_date', 'license_expiry_date', 'expiry_date', 'end_date'],
        'total_occupants': ['total_occupants', 'occupants', 'max_occupants'],
        'data_source': ['data_source', 'source'],
        'last_updated': ['last_updated', 'updated_at', 'modified_date']
    }
    
    print("If the integration failed, here are common field name alternatives:")
    print("-" * 60)
    
    for intended_field, alternatives in field_mapping_suggestions.items():
        print(f"{intended_field:<25} -> {', '.join(alternatives)}")

if __name__ == "__main__":
    # Check the model structure
    available_fields = check_database_model()
    
    # Check existing records
    check_existing_record()
    
    # Provide suggestions
    suggest_field_mapping()
    
    print(f"\n" + "="*60)
    print("NEXT STEPS:")
    print("1. Check the field names above")
    print("2. Update the integration script with correct field names")
    print("3. Re-run the integration")
    print("="*60)