#!/usr/bin/env python3
"""
Swindon Database Integration Script
==================================
Adds the processed Swindon HMO data to your existing database
"""

import pandas as pd
import sqlite3
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def integrate_swindon_to_database():
    """Add Swindon data to your existing HMO database"""
    
    print("🏠 Integrating Swindon HMO Data into Database")
    print("=" * 50)
    
    # Load the processed CSV
    try:
        df = pd.read_csv('swindon_hmo_processed.csv')
        logger.info(f"✅ Loaded {len(df)} records from CSV")
        
        # Show sample data
        print(f"📊 Sample data:")
        print(df.head(2).to_string())
        
    except FileNotFoundError:
        logger.error("❌ swindon_hmo_processed.csv not found. Run the processing script first.")
        return False
    except Exception as e:
        logger.error(f"❌ Error loading CSV: {e}")
        return False
    
    # Connect to your existing database
    try:
        # Update this path to match your database location
        db_path = 'hmo_analyser.db'
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        logger.info(f"✅ Connected to database: {db_path}")
        
        # Check existing tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"📋 Existing tables: {tables}")
        
    except Exception as e:
        logger.error(f"❌ Database connection error: {e}")
        return False
    
    try:
        # Create HMO registry table if it doesn't exist (based on your existing schema)
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS hmo_registries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT NOT NULL,
            source_type TEXT,
            source_url TEXT,
            case_number TEXT UNIQUE,
            raw_address TEXT,
            standardized_address TEXT,
            postcode TEXT,
            latitude DECIMAL(10,8),
            longitude DECIMAL(11,8),
            geocoded BOOLEAN DEFAULT FALSE,
            geocoding_source TEXT,
            licence_status TEXT DEFAULT 'active',
            licence_holder_name TEXT,
            data_quality_score DECIMAL(3,2),
            processing_notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            source_last_updated DATETIME
        )
        """
        
        cursor.execute(create_table_sql)
        logger.info("✅ HMO registry table ready")
        
        # Insert Swindon data
        inserted_count = 0
        updated_count = 0
        error_count = 0
        
        for index, row in df.iterrows():
            try:
                # Check if record already exists
                cursor.execute(
                    "SELECT id FROM hmo_registries WHERE case_number = ?",
                    (row['case_number'],)
                )
                existing = cursor.fetchone()
                
                # Prepare data
                data = {
                    'city': 'swindon',
                    'source_type': 'excel',
                    'source_url': 'manual_upload_swindon',
                    'case_number': row['case_number'],
                    'raw_address': row['raw_address'],
                    'standardized_address': row['cleaned_address'],
                    'postcode': row['postcode'] if pd.notna(row['postcode']) else None,
                    'latitude': row['latitude'] if pd.notna(row['latitude']) else None,
                    'longitude': row['longitude'] if pd.notna(row['longitude']) else None,
                    'geocoded': bool(row['geocoded']),
                    'geocoding_source': 'postcodes.io' if row['geocoded'] else None,
                    'licence_status': 'active',  # Assume active since no expiry dates
                    'licence_holder_name': row['licence_holder'],
                    'data_quality_score': row['quality_score'],
                    'processing_notes': f'Imported from Swindon Excel on {datetime.now().strftime("%Y-%m-%d")}',
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat(),
                    'source_last_updated': datetime.now().isoformat()
                }
                
                if existing:
                    # Update existing record
                    update_sql = """
                    UPDATE hmo_registries SET
                        raw_address=?, standardized_address=?, postcode=?,
                        latitude=?, longitude=?, geocoded=?, geocoding_source=?,
                        licence_holder_name=?, data_quality_score=?, 
                        processing_notes=?, updated_at=?, source_last_updated=?
                    WHERE case_number=?
                    """
                    
                    cursor.execute(update_sql, (
                        data['raw_address'], data['standardized_address'], data['postcode'],
                        data['latitude'], data['longitude'], data['geocoded'], data['geocoding_source'],
                        data['licence_holder_name'], data['data_quality_score'],
                        data['processing_notes'], data['updated_at'], data['source_last_updated'],
                        data['case_number']
                    ))
                    updated_count += 1
                    
                else:
                    # Insert new record
                    insert_sql = """
                    INSERT INTO hmo_registries (
                        city, source_type, source_url, case_number, raw_address,
                        standardized_address, postcode, latitude, longitude, geocoded,
                        geocoding_source, licence_status, licence_holder_name,
                        data_quality_score, processing_notes, created_at, updated_at,
                        source_last_updated
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    
                    cursor.execute(insert_sql, (
                        data['city'], data['source_type'], data['source_url'], data['case_number'],
                        data['raw_address'], data['standardized_address'], data['postcode'],
                        data['latitude'], data['longitude'], data['geocoded'],
                        data['geocoding_source'], data['licence_status'], data['licence_holder_name'],
                        data['data_quality_score'], data['processing_notes'], data['created_at'],
                        data['updated_at'], data['source_last_updated']
                    ))
                    inserted_count += 1
                
            except Exception as e:
                logger.error(f"❌ Error processing record {row['case_number']}: {e}")
                error_count += 1
                continue
        
        # Commit changes
        conn.commit()
        
        print(f"\n✅ Database integration complete!")
        print(f"   📊 Records inserted: {inserted_count}")
        print(f"   ♻️  Records updated: {updated_count}")
        print(f"   ❌ Errors: {error_count}")
        
        # Show final statistics
        cursor.execute("SELECT COUNT(*) FROM hmo_registries WHERE city = 'swindon'")
        swindon_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM hmo_registries WHERE city = 'oxford'")
        oxford_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM hmo_registries")
        total_count = cursor.fetchone()[0]
        
        print(f"\n📈 Final Database Statistics:")
        print(f"   🏛️  Oxford HMOs: {oxford_count}")
        print(f"   🏭 Swindon HMOs: {swindon_count}")
        print(f"   📊 Total HMOs: {total_count}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Database integration error: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

def update_api_endpoints():
    """Instructions for updating API endpoints"""
    
    print(f"\n🔗 Next Steps - Update API Endpoints:")
    print(f"=" * 40)
    
    print(f"1. Update your HMO registry endpoints to include Swindon:")
    print(f"   - Add 'swindon' to HMORegistryCity enum")
    print(f"   - Update get_available_cities() to include Swindon")
    print(f"   - Test: GET /api/hmo-registry/cities/swindon")
    
    print(f"\n2. Update your frontend map to show both cities:")
    print(f"   - Add city selector (Oxford/Swindon/Both)")
    print(f"   - Update map bounds to include Swindon coordinates")
    print(f"   - Add different colors/icons for each city")
    
    print(f"\n3. Test the integration:")
    print(f"   curl http://localhost:8001/api/hmo-registry/cities/swindon")

if __name__ == "__main__":
    success = integrate_swindon_to_database()
    
    if success:
        update_api_endpoints()
        print(f"\n🎉 Swindon is ready to be added to your map!")
    else:
        print(f"\n❌ Integration failed. Check the errors above.")