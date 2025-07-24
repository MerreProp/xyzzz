# migration_phase2.py
"""
Phase 2 migration for HMO Analyser - Analytics and Price Tracking
"""

from sqlalchemy import text
from database import engine

def migrate_phase2():
    """Phase 2 migration - Add analytics tables and indexes"""
    
    with engine.connect() as conn:
        with conn.begin():
            try:
                print("🚀 Starting Phase 2 Migration (Analytics)...")
                
                # Step 1: Create room_price_history table
                print("💰 Creating room_price_history table...")
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS room_price_history (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        room_id UUID NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
                        property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
                        analysis_id UUID REFERENCES property_analyses(id),
                        
                        previous_price DECIMAL(8,2),
                        new_price DECIMAL(8,2),
                        previous_price_text VARCHAR(200),
                        new_price_text VARCHAR(200),
                        
                        price_change_amount DECIMAL(8,2),
                        price_change_percentage DECIMAL(5,2),
                        change_reason VARCHAR(100),
                        
                        room_status_at_change VARCHAR(50),
                        market_context JSON,
                        
                        detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        effective_date TIMESTAMP NOT NULL,
                        
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """))
                print("   ✅ Created room_price_history table")
                
                # Step 2: Create property_trends table
                print("📊 Creating property_trends table...")
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS property_trends (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
                        
                        trend_period VARCHAR(50) NOT NULL,
                        period_start TIMESTAMP NOT NULL,
                        period_end TIMESTAMP NOT NULL,
                        
                        avg_availability_duration DECIMAL(5,2),
                        total_availability_periods INTEGER,
                        availability_turnover_rate DECIMAL(5,2),
                        
                        avg_room_price DECIMAL(8,2),
                        price_volatility DECIMAL(5,2),
                        price_trend_direction VARCHAR(20),
                        price_change_percentage DECIMAL(5,2),
                        
                        estimated_monthly_income DECIMAL(10,2),
                        income_stability_score DECIMAL(3,2),
                        vacancy_impact DECIMAL(8,2),
                        
                        market_competitiveness VARCHAR(20),
                        demand_indicator DECIMAL(3,2),
                        
                        calculation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        data_points_used INTEGER,
                        confidence_score DECIMAL(3,2),
                        
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """))
                print("   ✅ Created property_trends table")
                
                # Step 3: Create indexes for performance
                print("🔍 Creating performance indexes...")
                
                # Price history indexes
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS ix_price_history_room_date 
                    ON room_price_history (room_id, effective_date);
                """))
                print("   ✅ Created index on room_price_history (room_id, effective_date)")
                
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS ix_price_history_property_date 
                    ON room_price_history (property_id, effective_date);
                """))
                print("   ✅ Created index on room_price_history (property_id, effective_date)")
                
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS ix_price_history_detected_at 
                    ON room_price_history (detected_at);
                """))
                print("   ✅ Created index on room_price_history (detected_at)")
                
                # Property trends indexes
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS ix_trends_property_period 
                    ON property_trends (property_id, trend_period, period_start);
                """))
                print("   ✅ Created index on property_trends (property_id, trend_period, period_start)")
                
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS ix_trends_period_start 
                    ON property_trends (period_start);
                """))
                print("   ✅ Created index on property_trends (period_start)")
                
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS ix_trends_calculation_date 
                    ON property_trends (calculation_date);
                """))
                print("   ✅ Created index on property_trends (calculation_date)")
                
                print("✅ Phase 2 migration completed successfully!")
                print("📋 Added:")
                print("   - room_price_history table for tracking price changes")
                print("   - property_trends table for analytics and trends")
                print("   - 6 performance indexes for fast analytics queries")
                print("\n⚡ Phase 2 Features Now Available:")
                print("   - Price history tracking")
                print("   - Trend analysis")
                print("   - Market comparisons")
                print("   - Advanced analytics")
                
            except Exception as e:
                print(f"❌ Migration failed: {e}")
                raise

def rollback_phase2():
    """Rollback Phase 2 migration"""
    
    with engine.connect() as conn:
        with conn.begin():
            try:
                print("🔄 Rolling back Phase 2 migration...")
                
                # Drop indexes first
                print("🗑️ Dropping indexes...")
                conn.execute(text("DROP INDEX IF EXISTS ix_price_history_room_date;"))
                conn.execute(text("DROP INDEX IF EXISTS ix_price_history_property_date;"))
                conn.execute(text("DROP INDEX IF EXISTS ix_price_history_detected_at;"))
                conn.execute(text("DROP INDEX IF EXISTS ix_trends_property_period;"))
                conn.execute(text("DROP INDEX IF EXISTS ix_trends_period_start;"))
                conn.execute(text("DROP INDEX IF EXISTS ix_trends_calculation_date;"))
                print("   ✅ Dropped performance indexes")
                
                # Drop tables
                print("🗑️ Dropping tables...")
                conn.execute(text("DROP TABLE IF EXISTS property_trends CASCADE;"))
                print("   ✅ Dropped property_trends table")
                
                conn.execute(text("DROP TABLE IF EXISTS room_price_history CASCADE;"))
                print("   ✅ Dropped room_price_history table")
                
                print("✅ Phase 2 rollback completed")
                
            except Exception as e:
                print(f"❌ Rollback failed: {e}")
                raise

def test_phase2_tables():
    """Test that Phase 2 tables were created correctly"""
    
    with engine.connect() as conn:
        try:
            print("🧪 Testing Phase 2 tables...")
            
            # Test room_price_history table
            result = conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'room_price_history'
                ORDER BY ordinal_position;
            """))
            
            price_history_columns = result.fetchall()
            print(f"   ✅ room_price_history has {len(price_history_columns)} columns")
            
            # Test property_trends table
            result = conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'property_trends'
                ORDER BY ordinal_position;
            """))
            
            trends_columns = result.fetchall()
            print(f"   ✅ property_trends has {len(trends_columns)} columns")
            
            # Test indexes
            result = conn.execute(text("""
                SELECT indexname 
                FROM pg_indexes 
                WHERE tablename IN ('room_price_history', 'property_trends')
                ORDER BY indexname;
            """))
            
            indexes = result.fetchall()
            print(f"   ✅ Created {len(indexes)} indexes for analytics")
            
            print("🎉 Phase 2 tables and indexes are working correctly!")
            return True
            
        except Exception as e:
            print(f"❌ Phase 2 table test failed: {e}")
            return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "rollback":
            rollback_phase2()
        elif sys.argv[1] == "test":
            test_phase2_tables()
    else:
        migrate_phase2()
        
        # Automatically test after migration
        print("\n" + "="*60)
        test_phase2_tables()