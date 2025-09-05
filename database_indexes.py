# database_indexes_fixed.py
# Fixed version with correct table names (plural forms)

from database import SessionLocal, engine
from sqlalchemy import text
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_database_indexes():
    """Create all necessary database indexes for performance optimization - FIXED VERSION"""
    
    indexes = [
        # 1. Most critical - latest analysis queries (FIXED: properties -> property_analyses)
        """CREATE INDEX IF NOT EXISTS idx_property_analyses_property_created 
           ON property_analyses (property_id, created_at DESC);""",
        
        # 2. Property ordering (FIXED: property -> properties)
        """CREATE INDEX IF NOT EXISTS idx_properties_created_at 
           ON properties (created_at DESC);""",
        
        # 3. Room lookups (FIXED: room -> rooms)
        """CREATE INDEX IF NOT EXISTS idx_rooms_property_id 
           ON rooms (property_id);""",
        
        # 4. Room availability periods (FIXED: room_availability_period -> room_availability_periods)
        """CREATE INDEX IF NOT EXISTS idx_room_availability_periods_room_id 
           ON room_availability_periods (room_id);""",
        
        # 5. Room price history
        """CREATE INDEX IF NOT EXISTS idx_room_price_history_room_id 
           ON room_price_history (room_id);""",
        
        # 6. Property changes (FIXED: property_change -> property_changes)
        """CREATE INDEX IF NOT EXISTS idx_property_changes_property_detected 
           ON property_changes (property_id, detected_at DESC);""",
        
        # 7. Change type queries (FIXED: property_change -> property_changes)
        """CREATE INDEX IF NOT EXISTS idx_property_changes_type_detected 
           ON property_changes (change_type, detected_at DESC);""",
        
        # 8. Composite analysis index (FIXED: property_analysis -> property_analyses)
        """CREATE INDEX IF NOT EXISTS idx_property_analyses_composite 
           ON property_analyses (property_id, created_at DESC, id);""",
        
        # 9. Property search (FIXED: property -> properties)
        """CREATE INDEX IF NOT EXISTS idx_properties_search 
           ON properties (address, postcode, city);""",
        
        # 10. Room price filtering (FIXED: room -> rooms)
        """CREATE INDEX IF NOT EXISTS idx_rooms_current_price 
           ON rooms (current_price) WHERE current_price IS NOT NULL;"""
    ]
    
    # Table statistics updates (FIXED: use plural table names)
    analyze_commands = [
        "ANALYZE properties;",
        "ANALYZE property_analyses;", 
        "ANALYZE rooms;",
        "ANALYZE room_availability_periods;",
        "ANALYZE room_price_history;",
        "ANALYZE property_changes;"
    ]
    
    db = SessionLocal()
    
    try:
        logger.info("🔧 Creating database indexes for performance optimization...")
        
        # Create indexes
        created_count = 0
        for i, index_sql in enumerate(indexes, 1):
            try:
                db.execute(text(index_sql))
                db.commit()
                logger.info(f"✅ Created index {i}/{len(indexes)}")
                created_count += 1
            except Exception as e:
                logger.error(f"❌ Failed to create index {i}: {e}")
                db.rollback()
        
        logger.info("📊 Updating table statistics...")
        
        # Update statistics
        analyzed_count = 0
        for analyze_sql in analyze_commands:
            try:
                db.execute(text(analyze_sql))
                db.commit()
                logger.info(f"✅ Updated statistics: {analyze_sql}")
                analyzed_count += 1
            except Exception as e:
                logger.error(f"❌ Failed to analyze: {e}")
                db.rollback()
        
        logger.info("🎯 Database optimization completed!")
        logger.info(f"📊 Summary: {created_count}/{len(indexes)} indexes created, {analyzed_count}/{len(analyze_commands)} tables analyzed")
        
        # Verify indexes were created
        verify_indexes(db)
        
    except Exception as e:
        logger.error(f"❌ Database optimization failed: {e}")
        db.rollback()
    finally:
        db.close()

def verify_indexes(db):
    """Verify that indexes were created successfully"""
    
    try:
        # PostgreSQL query to list indexes
        result = db.execute(text("""
            SELECT indexname FROM pg_indexes 
            WHERE indexname LIKE 'idx_%'
            ORDER BY indexname;
        """))
        
        indexes = [row[0] for row in result.fetchall()]
        
        if indexes:
            logger.info(f"✅ Successfully created {len(indexes)} indexes:")
            for idx in indexes:
                logger.info(f"  - {idx}")
        else:
            logger.warning("⚠️ No indexes found - verification may have failed")
            
    except Exception as e:
        logger.warning(f"⚠️ Could not verify indexes: {e}")

if __name__ == "__main__":
    create_database_indexes()