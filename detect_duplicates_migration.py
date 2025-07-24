"""
Migration: Create PropertyURL table for duplicate URL tracking
Date: 2025-01-22
Purpose: Add support for tracking multiple URLs per property to prevent duplicates
"""

from sqlalchemy import Column, String, Boolean, DateTime, Float, ForeignKey, create_engine, text
from sqlalchemy.orm import sessionmaker
import uuid
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Database connection - matches your database.py
DATABASE_URL = os.getenv("DATABASE_URL")

# Handle Railway/Heroku DATABASE_URL format (postgres:// -> postgresql://)
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required")
    
print(f"Using database: {DATABASE_URL}")

def run_migration():
    """Run the migration to create property_urls table"""
    
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        print("🔄 Creating property_urls table...")
        
        # Create the property_urls table with proper UUID types for PostgreSQL
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS property_urls (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            property_id UUID NOT NULL,
            url TEXT NOT NULL UNIQUE,
            is_primary BOOLEAN DEFAULT FALSE,
            detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            confidence_score REAL,
            FOREIGN KEY (property_id) REFERENCES properties (id) ON DELETE CASCADE
        );
        """
        
        session.execute(text(create_table_sql))
        
        # Create indexes for better performance
        index_sql = [
            "CREATE INDEX IF NOT EXISTS ix_property_urls_property_id ON property_urls (property_id);",
            "CREATE INDEX IF NOT EXISTS ix_property_urls_url ON property_urls (url);",
            "CREATE INDEX IF NOT EXISTS ix_property_urls_confidence ON property_urls (confidence_score);",
        ]
        
        for sql in index_sql:
            session.execute(text(sql))
        
        session.commit()
        print("✅ property_urls table created successfully!")
        
        # Test the table
        test_sql = "SELECT COUNT(*) FROM property_urls;"
        result = session.execute(text(test_sql)).fetchone()
        print(f"✅ Table test passed - {result[0]} records found")
        
        # Verify the table structure
        verify_sql = """
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'property_urls'
        ORDER BY ordinal_position;
        """
        result = session.execute(text(verify_sql)).fetchall()
        print("✅ Table structure:")
        for column_name, data_type in result:
            print(f"   - {column_name}: {data_type}")
        
        print("\n🎉 Migration completed successfully!")
        print("The duplicate detection system is now ready to use.")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Migration failed: {str(e)}")
        raise
    finally:
        session.close()

def rollback_migration():
    """Rollback the migration (drop the table)"""
    
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        print("🔄 Rolling back migration...")
        
        # Drop the table
        drop_sql = "DROP TABLE IF EXISTS property_urls CASCADE;"
        session.execute(text(drop_sql))
        session.commit()
        
        print("✅ property_urls table dropped successfully!")
        return True
        
    except Exception as e:
        session.rollback()
        print(f"❌ Rollback failed: {e}")
        return False
    finally:
        session.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "rollback":
            rollback_migration()
        elif sys.argv[1] == "test":
            # Test existing table
            engine = create_engine(DATABASE_URL)
            Session = sessionmaker(bind=engine)
            session = Session()
            try:
                result = session.execute(text("SELECT COUNT(*) FROM property_urls;")).fetchone()
                print(f"✅ property_urls table exists with {result[0]} records")
            except Exception as e:
                print(f"❌ Table test failed: {e}")
            finally:
                session.close()
    else:
        run_migration()