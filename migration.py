from sqlalchemy import text
from database import engine

def migrate_database():
    """Update the analysis_tasks table to support bulk updates"""
    
    with engine.connect() as conn:
        # Start a transaction
        with conn.begin():
            try:
                # Make property_id nullable
                conn.execute(text("""
                    ALTER TABLE analysis_tasks 
                    ALTER COLUMN property_id DROP NOT NULL;
                """))
                
                # Add task_type column if it doesn't exist
                conn.execute(text("""
                    DO $$ 
                    BEGIN 
                        BEGIN
                            ALTER TABLE analysis_tasks 
                            ADD COLUMN task_type VARCHAR(50) DEFAULT 'individual';
                        EXCEPTION
                            WHEN duplicate_column THEN 
                                RAISE NOTICE 'Column task_type already exists';
                        END;
                    END $$;
                """))
                
                # Create index on task_type
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS ix_analysis_tasks_task_type 
                    ON analysis_tasks (task_type);
                """))
                
                # Update existing records to have task_type = 'individual'
                conn.execute(text("""
                    UPDATE analysis_tasks 
                    SET task_type = 'individual' 
                    WHERE task_type IS NULL;
                """))
                
                print("✅ Database migration completed successfully!")
                
            except Exception as e:
                print(f"❌ Migration failed: {e}")
                raise

if __name__ == "__main__":
    migrate_database()