# hmo_database_migration.py
"""
Database Migration Script for HMO Registry
Adds comprehensive Oxford HMO fields to existing HMORegistry table
"""

import logging
from sqlalchemy import text, MetaData, Table, Column, String, Integer, Date, DateTime, Boolean, JSON, Text, inspect
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import sys
import os

# Add project path
sys.path.insert(0, os.getcwd())

try:
    from database import SessionLocal, engine
    print("✅ Database connection imported successfully")
except ImportError as e:
    print(f"❌ Failed to import database: {e}")
    print("Make sure you're running this from the project root directory")
    sys.exit(1)

logger = logging.getLogger(__name__)

class HMODatabaseMigration:
    """Handles HMO Registry database migrations"""
    
    def __init__(self):
        self.engine = engine
        self.session = SessionLocal()
        
    def check_existing_columns(self) -> dict:
        """Check which columns already exist in HMORegistry table"""
        try:
            # Get current table structure using correct syntax
            inspector = inspect(self.engine)
            
            if not inspector.has_table('hmo_registry'):
                print("⚠️  HMORegistry table does not exist - will need to create it first")
                return {}
            
            existing_columns = [col['name'] for col in inspector.get_columns('hmo_registry')]
            print(f"📋 Existing columns: {existing_columns}")
            
            return {col: True for col in existing_columns}
            
        except Exception as e:
            print(f"❌ Error checking existing columns: {e}")
            return {}
    
    def add_new_columns(self):
        """Add new columns to HMORegistry table"""
        
        # Check if table exists first
        existing_columns = self.check_existing_columns()
        
        if not existing_columns:
            print("📝 Creating HMORegistry table first...")
            success = self.create_hmo_table()
            if not success:
                return False
            # Recheck columns after creating table
            existing_columns = self.check_existing_columns()
        
        # Define new columns to add
        new_columns = {
            # License Information
            'licence_holder': 'TEXT',
            'licence_holder_address': 'TEXT', 
            'licence_holder_type': 'TEXT',
            'licence_status': 'TEXT',
            'licence_start_date': 'DATE',
            'licence_expiry_date': 'DATE',
            
            # Property Details
            'total_occupants': 'INTEGER',
            'total_units': 'INTEGER',
            
            # Agent Information (as JSON string)
            'agents_json': 'TEXT',
            
            # Metadata
            'last_updated': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
            'data_source': 'TEXT',
            'data_source_url': 'TEXT',
            
            # Additional Quality Fields
            'data_quality_score': 'REAL',
            'processing_notes': 'TEXT'
        }
        
        # Add columns that don't exist
        columns_added = 0
        columns_skipped = 0
        
        for column_name, column_type in new_columns.items():
            if column_name in existing_columns:
                print(f"⏭️  Column '{column_name}' already exists, skipping")
                columns_skipped += 1
                continue
            
            try:
                # Add the column
                sql = f"ALTER TABLE hmo_registry ADD COLUMN {column_name} {column_type}"
                self.session.execute(text(sql))
                self.session.commit()
                print(f"✅ Added column: {column_name} ({column_type})")
                columns_added += 1
                
            except SQLAlchemyError as e:
                print(f"❌ Failed to add column '{column_name}': {e}")
                self.session.rollback()
        
        print(f"\n📊 Migration Summary:")
        print(f"  ✅ Columns added: {columns_added}")
        print(f"  ⏭️  Columns skipped: {columns_skipped}")
        
        return columns_added > 0
    
    def create_indexes(self):
        """Create useful indexes for the new columns"""
        
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_hmo_licence_status ON hmo_registry(licence_status)",
            "CREATE INDEX IF NOT EXISTS idx_hmo_licence_expiry ON hmo_registry(licence_expiry_date)",
            "CREATE INDEX IF NOT EXISTS idx_hmo_last_updated ON hmo_registry(last_updated)",
            "CREATE INDEX IF NOT EXISTS idx_hmo_data_source ON hmo_registry(data_source)",
            "CREATE INDEX IF NOT EXISTS idx_hmo_case_number ON hmo_registry(case_number)"
        ]
        
        indexes_created = 0
        
        for index_sql in indexes:
            try:
                self.session.execute(text(index_sql))
                self.session.commit()
                index_name = index_sql.split()[4]  # Extract index name
                print(f"✅ Created index: {index_name}")
                indexes_created += 1
                
            except SQLAlchemyError as e:
                print(f"⚠️  Index creation failed (might already exist): {e}")
                self.session.rollback()
        
        print(f"📊 Created {indexes_created} indexes")
        return indexes_created > 0
    
    def create_hmo_table(self):
        """Create the HMORegistry table if it doesn't exist"""
        try:
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS hmo_registry (
                id SERIAL PRIMARY KEY,
                case_number TEXT,
                raw_address TEXT,
                standardized_address TEXT,
                postcode TEXT,
                latitude REAL,
                longitude REAL,
                geocoded BOOLEAN DEFAULT FALSE,
                city TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            
            self.session.execute(text(create_table_sql))
            self.session.commit()
            print("✅ Created HMORegistry table with basic structure")
            return True
            
        except SQLAlchemyError as e:
            print(f"❌ Failed to create HMORegistry table: {e}")
            self.session.rollback()
            return False
    
    def verify_migration(self):
        """Verify the migration was successful"""
        try:
            # Check final table structure using correct syntax
            inspector = inspect(self.engine)
            
            if not inspector.has_table('hmo_registry'):
                print("❌ Table still doesn't exist after migration")
                return False
                
            final_columns = [col['name'] for col in inspector.get_columns('hmo_registry')]
            
            print(f"\n🔍 Final table structure:")
            print(f"   Total columns: {len(final_columns)}")
            
            # Check for key new columns
            key_columns = ['licence_holder', 'licence_status', 'licence_expiry_date', 'total_occupants', 'last_updated']
            
            for col in key_columns:
                status = "✅" if col in final_columns else "❌"
                print(f"   {status} {col}")
            
            return all(col in final_columns for col in key_columns)
            
        except Exception as e:
            print(f"❌ Error verifying migration: {e}")
            return False
    
    def close(self):
        """Close database connection"""
        self.session.close()

def run_migration():
    """Run the complete migration process"""
    print("🚀 Starting HMO Registry Database Migration")
    print("=" * 50)
    
    migration = HMODatabaseMigration()
    
    try:
        # Step 1: Add new columns
        print("\n📝 Step 1: Adding new columns...")
        columns_success = migration.add_new_columns()
        
        if not columns_success:
            print("⚠️  No new columns were added")
        
        # Step 2: Create indexes
        print("\n📊 Step 2: Creating indexes...")
        migration.create_indexes()
        
        # Step 3: Verify migration
        print("\n🔍 Step 3: Verifying migration...")
        verification_success = migration.verify_migration()
        
        if verification_success:
            print("\n🎉 Migration completed successfully!")
            print("\n📋 Next steps:")
            print("1. Run Oxford analysis: python3 -m hmo_registry.cities.oxford analyze")
            print("2. The new columns will be populated with Oxford data")
            print("3. Check your database to see the new fields")
        else:
            print("\n❌ Migration verification failed!")
            
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        migration.close()

def rollback_migration():
    """Rollback the migration (remove added columns)"""
    print("⚠️  Rolling back HMO Registry Migration")
    print("=" * 40)
    
    # Columns to remove (in case rollback is needed)
    columns_to_remove = [
        'licence_holder', 'licence_holder_address', 'licence_holder_type',
        'licence_status', 'licence_start_date', 'licence_expiry_date',
        'total_occupants', 'total_units', 'agents_json',
        'last_updated', 'data_source', 'data_source_url',
        'data_quality_score', 'processing_notes'
    ]
    
    migration = HMODatabaseMigration()
    
    try:
        for column in columns_to_remove:
            try:
                sql = f"ALTER TABLE hmo_registry DROP COLUMN {column}"
                migration.session.execute(text(sql))
                migration.session.commit()
                print(f"🗑️  Removed column: {column}")
            except SQLAlchemyError as e:
                print(f"⚠️  Could not remove column '{column}': {e}")
                migration.session.rollback()
        
        print("✅ Rollback completed")
        
    except Exception as e:
        print(f"❌ Rollback failed: {e}")
        
    finally:
        migration.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'rollback':
        rollback_migration()
    else:
        run_migration()