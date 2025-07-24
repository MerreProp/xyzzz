"""
Database migration for Contact Book Phase 1
Adds contact tables to existing PostgreSQL database
"""

from sqlalchemy import text
from database import SessionLocal, engine
from models import Base

def migrate_contacts_phase1():
    """Add contact tables to the database"""
    print("🚀 Starting Contact Book Phase 1 Migration...")
    
    try:
        # Create all tables defined in models
        Base.metadata.create_all(bind=engine)
        print("✅ Contact tables created successfully")
        
        # Test the tables
        with SessionLocal() as db:
            # Test contact_lists table
            result = db.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'contact_lists'
                ORDER BY ordinal_position;
            """))
            
            list_columns = result.fetchall()
            print(f"   ✅ contact_lists table has {len(list_columns)} columns")
            
            # Test contacts table
            result = db.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'contacts'
                ORDER BY ordinal_position;
            """))
            
            contact_columns = result.fetchall()
            print(f"   ✅ contacts table has {len(contact_columns)} columns")
            
            # Test contact_favorites table
            result = db.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'contact_favorites'
                ORDER BY ordinal_position;
            """))
            
            favorites_columns = result.fetchall()
            print(f"   ✅ contact_favorites table has {len(favorites_columns)} columns")
            
            print("🎉 Contact Book Phase 1 migration completed successfully!")
            return True
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

def rollback_contacts_phase1():
    """Remove contact tables (for development/testing)"""
    print("🔄 Rolling back Contact Book Phase 1...")
    
    try:
        with SessionLocal() as db:
            # Drop tables in reverse order due to foreign keys
            db.execute(text("DROP TABLE IF EXISTS contact_favorites CASCADE;"))
            db.execute(text("DROP TABLE IF EXISTS contacts CASCADE;"))
            db.execute(text("DROP TABLE IF EXISTS contact_lists CASCADE;"))
            db.commit()
            
        print("✅ Contact tables removed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Rollback failed: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        rollback_contacts_phase1()
    else:
        migrate_contacts_phase1()