# migration_simple_phase1.py
"""
Simplified Phase 1 migration that avoids PostgreSQL syntax issues
"""

from sqlalchemy import text
from database import engine

def migrate_phase1_simple():
    """Simple Phase 1 migration without complex PostgreSQL syntax"""
    
    with engine.connect() as conn:
        with conn.begin():
            try:
                print("🚀 Starting Phase 1 Migration (Simple Version)...")
                
                # Step 1: Add date_gone and date_returned to rooms table (simple approach)
                print("📅 Adding date tracking to rooms table...")
                try:
                    conn.execute(text("ALTER TABLE rooms ADD COLUMN date_gone TIMESTAMP;"))
                    print("   ✅ Added date_gone column")
                except Exception as e:
                    if "already exists" in str(e) or "duplicate column" in str(e):
                        print("   ⚠️  date_gone column already exists")
                    else:
                        raise
                
                try:
                    conn.execute(text("ALTER TABLE rooms ADD COLUMN date_returned TIMESTAMP;"))
                    print("   ✅ Added date_returned column")
                except Exception as e:
                    if "already exists" in str(e) or "duplicate column" in str(e):
                        print("   ⚠️  date_returned column already exists")
                    else:
                        raise
                
                # Step 2: Create room_availability_periods table
                print("🏠 Creating room_availability_periods table...")
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS room_availability_periods (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        room_id UUID NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
                        period_start_date TIMESTAMP NOT NULL,
                        period_end_date TIMESTAMP,
                        price_at_start DECIMAL(8,2),
                        price_text_at_start VARCHAR(200),
                        room_type_at_start VARCHAR(200),
                        room_identifier_at_start VARCHAR(500),
                        discovery_analysis_id UUID REFERENCES property_analyses(id),
                        end_analysis_id UUID REFERENCES property_analyses(id),
                        duration_days INTEGER,
                        is_current_period BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """))
                print("   ✅ Created room_availability_periods table")
                
                # Step 3: Add enhanced tracking fields to rooms table
                print("📊 Adding period tracking to rooms table...")
                try:
                    conn.execute(text("ALTER TABLE rooms ADD COLUMN current_availability_period_id UUID REFERENCES room_availability_periods(id);"))
                    print("   ✅ Added current_availability_period_id column")
                except Exception as e:
                    if "already exists" in str(e) or "duplicate column" in str(e):
                        print("   ⚠️  current_availability_period_id column already exists")
                    else:
                        raise
                
                try:
                    conn.execute(text("ALTER TABLE rooms ADD COLUMN total_availability_periods INTEGER DEFAULT 0;"))
                    print("   ✅ Added total_availability_periods column")
                except Exception as e:
                    if "already exists" in str(e) or "duplicate column" in str(e):
                        print("   ⚠️  total_availability_periods column already exists")
                    else:
                        raise
                
                try:
                    conn.execute(text("ALTER TABLE rooms ADD COLUMN average_availability_duration DECIMAL(5,2);"))
                    print("   ✅ Added average_availability_duration column")
                except Exception as e:
                    if "already exists" in str(e) or "duplicate column" in str(e):
                        print("   ⚠️  average_availability_duration column already exists")
                    else:
                        raise
                
                # Step 4: Create indexes for performance
                print("🔍 Creating indexes...")
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_rooms_date_gone ON rooms (date_gone);"))
                print("   ✅ Created index on rooms.date_gone")
                
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_room_periods_room_id ON room_availability_periods (room_id);"))
                print("   ✅ Created index on room_availability_periods.room_id")
                
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_room_periods_current ON room_availability_periods (is_current_period);"))
                print("   ✅ Created index on room_availability_periods.is_current_period")
                
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_room_periods_dates ON room_availability_periods (period_start_date, period_end_date);"))
                print("   ✅ Created index on room_availability_periods dates")
                
                print("✅ Phase 1 migration completed successfully!")
                print("📋 Added:")
                print("   - date_gone, date_returned to rooms table")
                print("   - room_availability_periods table") 
                print("   - period tracking fields to rooms table")
                print("   - performance indexes")
                print("\n⚠️  Note: Automatic statistics calculation will be handled in the application code")
                
            except Exception as e:
                print(f"❌ Migration failed: {e}")
                raise

def rollback_phase1_simple():
    """Simple rollback for Phase 1"""
    
    with engine.connect() as conn:
        with conn.begin():
            try:
                print("🔄 Rolling back Phase 1 migration...")
                
                # Drop table first
                conn.execute(text("DROP TABLE IF EXISTS room_availability_periods CASCADE;"))
                print("   ✅ Dropped room_availability_periods table")
                
                # Remove added columns from rooms
                try:
                    conn.execute(text("ALTER TABLE rooms DROP COLUMN IF EXISTS date_gone;"))
                    print("   ✅ Removed date_gone column")
                except:
                    pass
                
                try:
                    conn.execute(text("ALTER TABLE rooms DROP COLUMN IF EXISTS date_returned;"))
                    print("   ✅ Removed date_returned column")
                except:
                    pass
                
                try:
                    conn.execute(text("ALTER TABLE rooms DROP COLUMN IF EXISTS current_availability_period_id;"))
                    print("   ✅ Removed current_availability_period_id column")
                except:
                    pass
                
                try:
                    conn.execute(text("ALTER TABLE rooms DROP COLUMN IF EXISTS total_availability_periods;"))
                    print("   ✅ Removed total_availability_periods column")
                except:
                    pass
                
                try:
                    conn.execute(text("ALTER TABLE rooms DROP COLUMN IF EXISTS average_availability_duration;"))
                    print("   ✅ Removed average_availability_duration column")
                except:
                    pass
                
                print("✅ Phase 1 rollback completed")
                
            except Exception as e:
                print(f"❌ Rollback failed: {e}")
                raise

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        rollback_phase1_simple()
    else:
        migrate_phase1_simple()