#!/usr/bin/env python3
"""
Phase 5: Room-URL Mapping Database Schema Migration
Run this script to add the necessary columns for Phase 5 functionality
"""

import sys
import os
from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker

# Add the parent directory to the path so we can import from the project
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_phase5_migration():
    """Run Phase 5 database schema migration"""
    
    # Import your database configuration
    try:
        from database import engine, SessionLocal
        print("✅ Connected to database")
    except ImportError:
        print("❌ Could not import database configuration")
        print("Make sure you're running this from your project directory")
        return False
    
    db = SessionLocal()
    
    try:
        print("🔧 Phase 5: Room-URL Mapping Schema Migration")
        print("=" * 50)
        
        # 1. Add URL-to-Room Mapping columns
        print("📋 Step 1: Adding room source URL tracking...")
        
        try:
            # Add source_url column to rooms table if it doesn't exist
            db.execute(text("""
                ALTER TABLE rooms 
                ADD COLUMN IF NOT EXISTS source_url TEXT;
            """))
            print("   ✅ Added rooms.source_url column")
        except Exception as e:
            print(f"   ⚠️ rooms.source_url: {e}")
        
        try:
            # Add url_confidence column to rooms table
            db.execute(text("""
                ALTER TABLE rooms 
                ADD COLUMN IF NOT EXISTS url_confidence FLOAT DEFAULT 1.0;
            """))
            print("   ✅ Added rooms.url_confidence column")
        except Exception as e:
            print(f"   ⚠️ rooms.url_confidence: {e}")
        
        # 2. Add URL metadata to property_urls table
        print("📋 Step 2: Enhancing property_urls table...")
        
        try:
            # Add distance_meters column
            db.execute(text("""
                ALTER TABLE property_urls 
                ADD COLUMN IF NOT EXISTS distance_meters FLOAT;
            """))
            print("   ✅ Added property_urls.distance_meters column")
        except Exception as e:
            print(f"   ⚠️ property_urls.distance_meters: {e}")
        
        try:
            # Add proximity_level column
            db.execute(text("""
                ALTER TABLE property_urls 
                ADD COLUMN IF NOT EXISTS proximity_level VARCHAR(50);
            """))
            print("   ✅ Added property_urls.proximity_level column")
        except Exception as e:
            print(f"   ⚠️ property_urls.proximity_level: {e}")
        
        try:
            # Add linked_by column
            db.execute(text("""
                ALTER TABLE property_urls 
                ADD COLUMN IF NOT EXISTS linked_by VARCHAR(20) DEFAULT 'system';
            """))
            print("   ✅ Added property_urls.linked_by column")
        except Exception as e:
            print(f"   ⚠️ property_urls.linked_by: {e}")
        
        try:
            # Add user_confirmed column
            db.execute(text("""
                ALTER TABLE property_urls 
                ADD COLUMN IF NOT EXISTS user_confirmed BOOLEAN DEFAULT FALSE;
            """))
            print("   ✅ Added property_urls.user_confirmed column")
        except Exception as e:
            print(f"   ⚠️ property_urls.user_confirmed: {e}")
        
        # 3. Add Room History Preservation
        print("📋 Step 3: Adding room history preservation...")
        
        try:
            # Add source_url to room_availability_periods
            db.execute(text("""
                ALTER TABLE room_availability_periods 
                ADD COLUMN IF NOT EXISTS source_url TEXT;
            """))
            print("   ✅ Added room_availability_periods.source_url column")
        except Exception as e:
            print(f"   ⚠️ room_availability_periods.source_url: {e}")
        
        try:
            # Add source_url to room_changes
            db.execute(text("""
                ALTER TABLE room_changes 
                ADD COLUMN IF NOT EXISTS source_url TEXT;
            """))
            print("   ✅ Added room_changes.source_url column")
        except Exception as e:
            print(f"   ⚠️ room_changes.source_url: {e}")
        
        # 4. Add Room Linking Capabilities
        print("📋 Step 4: Adding room linking capabilities...")
        
        try:
            # Add linked_room_id for room linking
            db.execute(text("""
                ALTER TABLE rooms 
                ADD COLUMN IF NOT EXISTS linked_room_id VARCHAR(50);
            """))
            print("   ✅ Added rooms.linked_room_id column")
        except Exception as e:
            print(f"   ⚠️ rooms.linked_room_id: {e}")
        
        try:
            # Add is_primary_instance for room linking
            db.execute(text("""
                ALTER TABLE rooms 
                ADD COLUMN IF NOT EXISTS is_primary_instance BOOLEAN DEFAULT TRUE;
            """))
            print("   ✅ Added rooms.is_primary_instance column")
        except Exception as e:
            print(f"   ⚠️ rooms.is_primary_instance: {e}")
        
        # 5. Create Duplicate Decision Tracking Table
        print("📋 Step 5: Creating duplicate decision tracking...")
        
        try:
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS duplicate_decisions (
                    id VARCHAR(50) PRIMARY KEY DEFAULT gen_random_uuid(),
                    new_url TEXT NOT NULL,
                    existing_property_id VARCHAR(50) NOT NULL,
                    confidence_score FLOAT NOT NULL,
                    distance_meters FLOAT,
                    user_decision VARCHAR(20) NOT NULL, -- 'link', 'separate'
                    decided_at TIMESTAMP DEFAULT NOW(),
                    match_factors JSONB,
                    
                    FOREIGN KEY (existing_property_id) REFERENCES properties(id) ON DELETE CASCADE
                );
            """))
            print("   ✅ Created duplicate_decisions table")
        except Exception as e:
            print(f"   ⚠️ duplicate_decisions table: {e}")
        
        # 6. Create Index for Geographic Searches
        print("📋 Step 6: Creating geographic indices...")
        
        try:
            db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_properties_location 
                ON properties (latitude, longitude);
            """))
            print("   ✅ Created geographic index on properties")
        except Exception as e:
            print(f"   ⚠️ Geographic index: {e}")
        
        # 7. Commit all changes
        db.commit()
        
        # 8. Verify Migration Success
        print("\n📋 Step 7: Verifying migration...")
        
        # Check property_urls columns
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'property_urls' 
            AND column_name IN ('distance_meters', 'proximity_level', 'linked_by', 'user_confirmed')
        """)).fetchall()
        
        property_urls_columns = [row.column_name for row in result]
        
        # Check rooms columns
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'rooms' 
            AND column_name IN ('source_url', 'url_confidence', 'linked_room_id', 'is_primary_instance')
        """)).fetchall()
        
        rooms_columns = [row.column_name for row in result]
        
        # Check duplicate_decisions table
        result = db.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name = 'duplicate_decisions'
        """)).fetchall()
        
        duplicate_table_exists = len(result) > 0
        
        print("\n🎯 Migration Results:")
        print(f"   PropertyURL columns: {len(property_urls_columns)}/4 ({property_urls_columns})")
        print(f"   Room columns: {len(rooms_columns)}/4 ({rooms_columns})")
        print(f"   Duplicate decisions table: {'✅' if duplicate_table_exists else '❌'}")
        
        success = (
            len(property_urls_columns) >= 4 and 
            len(rooms_columns) >= 4 and 
            duplicate_table_exists
        )
        
        if success:
            print("\n🎉 Phase 5 Database Migration COMPLETED!")
            print("✅ All schema changes applied successfully")
            print("🚀 Ready for Phase 5 CRUD and API updates")
            return True
        else:
            print("\n⚠️ Phase 5 Migration PARTIALLY completed")
            print("❌ Some schema changes may have failed")
            print("💡 Check the errors above and run migration again if needed")
            return False
            
    except Exception as e:
        print(f"\n❌ Migration failed with error: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def check_phase5_readiness():
    """Check if the database is ready for Phase 5"""
    
    try:
        from database import SessionLocal
        db = SessionLocal()
        
        print("🔍 Checking Phase 5 Readiness...")
        
        # Check required tables exist
        tables_check = db.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name IN ('properties', 'property_urls', 'rooms', 'room_availability_periods', 'room_changes')
        """)).fetchall()
        
        required_tables = {'properties', 'property_urls', 'rooms', 'room_availability_periods', 'room_changes'}
        existing_tables = {row.table_name for row in tables_check}
        
        missing_tables = required_tables - existing_tables
        
        if missing_tables:
            print(f"❌ Missing required tables: {missing_tables}")
            return False
        
        print("✅ All required tables exist")
        
        # Check if migration is needed
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'property_urls' 
            AND column_name IN ('distance_meters', 'proximity_level', 'linked_by', 'user_confirmed')
        """)).fetchall()
        
        if len(result) < 4:
            print("⚠️ Phase 5 migration needed")
            return False
        
        print("✅ Phase 5 schema already applied")
        return True
        
    except Exception as e:
        print(f"❌ Readiness check failed: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Phase 5: Room-URL Mapping Migration Tool")
    print("=" * 50)
    
    if check_phase5_readiness():
        print("\n✅ Database is already ready for Phase 5!")
        print("💡 No migration needed.")
    else:
        print("\n🔧 Running Phase 5 migration...")
        success = run_phase5_migration()
        
        if success:
            print("\n🎊 Migration completed successfully!")
            print("📋 Next steps:")
            print("   1. Update your models.py to include new columns")
            print("   2. Update CRUD functions for room URL tracking")
            print("   3. Test the enhanced duplicate detection")
        else:
            print("\n💥 Migration encountered issues")
            print("🔧 Please check the errors above and resolve them")