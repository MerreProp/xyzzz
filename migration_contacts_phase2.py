"""
Database migration for Contact Book Phase 2
Adds user authentication and permission system
"""

from sqlalchemy import text
from database import SessionLocal, engine
from models import Base, PermissionLevel
import uuid
from datetime import datetime

def migrate_contacts_phase2():
    """Add user authentication and permission system"""
    print("🚀 Starting Contact Book Phase 2 Migration...")
    
    try:
        with SessionLocal() as db:
            # Create enum type first
            print("📝 Creating enum types...")
            try:
                db.execute(text("CREATE TYPE permissionlevel AS ENUM ('owner', 'editor', 'viewer')"))
                db.commit()
                print("✅ Created permissionlevel enum")
            except Exception as e:
                if "already exists" in str(e):
                    print("✅ permissionlevel enum already exists")
                    db.rollback()
                else:
                    raise e
            
            # Create new tables
            Base.metadata.create_all(bind=engine)
            print("✅ New tables created successfully")
            
            # Create a default admin user for migration
            admin_user_id = str(uuid.uuid4())
            admin_email = "admin@example.com"
            admin_username = "admin"
            
            # Check if admin user already exists
            existing_admin = db.execute(text("""
                SELECT id FROM users WHERE email = :email OR username = :username
            """), {"email": admin_email, "username": admin_username}).fetchone()
            
            if not existing_admin:
                # Create admin user (password: admin123 - change this!)
                # You'll need to hash this password properly in production
                hashed_password = "$2b$12$LQv3c1yqBWVHxkd0LQ4lqeHrNTij.6.TQOqjONJPXfpkZUoOqTYGK"  # admin123
                
                db.execute(text("""
                    INSERT INTO users (id, email, username, full_name, hashed_password, is_active, is_verified, created_at, updated_at)
                    VALUES (:id, :email, :username, :full_name, :hashed_password, :is_active, :is_verified, :created_at, :updated_at)
                """), {
                    "id": admin_user_id,
                    "email": admin_email,
                    "username": admin_username,
                    "full_name": "System Administrator",
                    "hashed_password": hashed_password,
                    "is_active": True,
                    "is_verified": True,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                })
                print(f"✅ Created admin user: {admin_email} (password: admin123)")
            else:
                admin_user_id = existing_admin[0]
                print(f"✅ Using existing admin user: {admin_email}")
            
            # Update existing contact_lists to have created_by reference
            db.execute(text("""
                ALTER TABLE contact_lists 
                ADD COLUMN IF NOT EXISTS created_by UUID REFERENCES users(id)
            """))
            
            # Set all existing contact lists to be owned by admin
            db.execute(text("""
                UPDATE contact_lists 
                SET created_by = :admin_id 
                WHERE created_by IS NULL
            """), {"admin_id": admin_user_id})
            
            # Make created_by NOT NULL after setting values
            db.execute(text("""
                ALTER TABLE contact_lists 
                ALTER COLUMN created_by SET NOT NULL
            """))
            
            # Update existing contacts to have created_by reference
            db.execute(text("""
                ALTER TABLE contacts 
                ADD COLUMN IF NOT EXISTS created_by UUID REFERENCES users(id)
            """))
            
            # Set all existing contacts to be owned by admin
            db.execute(text("""
                UPDATE contacts 
                SET created_by = :admin_id 
                WHERE created_by IS NULL
            """), {"admin_id": admin_user_id})
            
            # Make created_by NOT NULL after setting values
            db.execute(text("""
                ALTER TABLE contacts 
                ALTER COLUMN created_by SET NOT NULL
            """))
            
            # Create owner permissions for all existing contact lists
            existing_lists = db.execute(text("""
                SELECT id FROM contact_lists WHERE created_by = :admin_id
            """), {"admin_id": admin_user_id}).fetchall()
            
            for contact_list in existing_lists:
                # Check if permission already exists
                existing_permission = db.execute(text("""
                    SELECT id FROM contact_list_permissions 
                    WHERE user_id = :user_id AND contact_list_id = :list_id
                """), {
                    "user_id": admin_user_id,
                    "list_id": contact_list[0]
                }).fetchone()
                
                if not existing_permission:
                    permission_id = str(uuid.uuid4())
                    db.execute(text("""
                        INSERT INTO contact_list_permissions (id, user_id, contact_list_id, permission_level, created_at, created_by)
                        VALUES (:id, :user_id, :list_id, :permission_level, :created_at, :created_by)
                    """), {
                        "id": permission_id,
                        "user_id": admin_user_id,
                        "list_id": contact_list[0],
                        "permission_level": "owner",
                        "created_at": datetime.utcnow(),
                        "created_by": admin_user_id
                    })
            
            print(f"✅ Created owner permissions for {len(existing_lists)} contact lists")
            
            # Migrate existing favorites from session-based to user-based
            # For now, we'll just clear them as we can't map sessions to users
            db.execute(text("DELETE FROM contact_favorites"))
            
            # Add user_id column to contact_favorites (replacing session_id)
            db.execute(text("""
                ALTER TABLE contact_favorites 
                DROP COLUMN IF EXISTS session_id
            """))
            
            db.execute(text("""
                ALTER TABLE contact_favorites 
                ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id)
            """))
            
            # Make user_id NOT NULL
            db.execute(text("""
                ALTER TABLE contact_favorites 
                ALTER COLUMN user_id SET NOT NULL
            """))
            
            # Check if unique constraint already exists before adding it
            constraint_exists = db.execute(text("""
                SELECT constraint_name 
                FROM information_schema.table_constraints 
                WHERE table_name = 'contact_favorites' 
                AND constraint_name = 'unique_user_contact_favorite'
                AND constraint_type = 'UNIQUE'
            """)).fetchone()
            
            if not constraint_exists:
                # Add unique constraint (without IF NOT EXISTS which isn't supported)
                db.execute(text("""
                    ALTER TABLE contact_favorites 
                    ADD CONSTRAINT unique_user_contact_favorite 
                    UNIQUE (user_id, contact_id)
                """))
                print("✅ Added unique constraint to contact_favorites")
            else:
                print("✅ Unique constraint already exists on contact_favorites")
            
            db.commit()
            print("🎉 Contact Book Phase 2 migration completed successfully!")
            print(f"📧 Admin login: {admin_email}")
            print("🔑 Admin password: admin123 (CHANGE THIS!)")
            return True
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

def rollback_contacts_phase2():
    """Remove Phase 2 changes (for development/testing)"""
    print("🔄 Rolling back Contact Book Phase 2...")
    
    try:
        with SessionLocal() as db:
            # Drop new tables in reverse order due to foreign keys
            db.execute(text("DROP TABLE IF EXISTS team_invitations CASCADE;"))
            db.execute(text("DROP TABLE IF EXISTS contact_list_permissions CASCADE;"))
            db.execute(text("DROP TABLE IF EXISTS users CASCADE;"))
            
            # Drop enum type
            db.execute(text("DROP TYPE IF EXISTS permissionlevel CASCADE;"))
            
            # Remove columns from existing tables
            db.execute(text("ALTER TABLE contact_lists DROP COLUMN IF EXISTS created_by CASCADE;"))
            db.execute(text("ALTER TABLE contacts DROP COLUMN IF EXISTS created_by CASCADE;"))
            
            # Restore session-based favorites
            db.execute(text("ALTER TABLE contact_favorites DROP COLUMN IF EXISTS user_id CASCADE;"))
            db.execute(text("ALTER TABLE contact_favorites ADD COLUMN IF NOT EXISTS session_id VARCHAR(255) NOT NULL DEFAULT 'migrated';"))
            
            db.commit()
            
        print("✅ Phase 2 changes rolled back successfully")
        return True
        
    except Exception as e:
        print(f"❌ Rollback failed: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        rollback_contacts_phase2()
    else:
        migrate_contacts_phase2()