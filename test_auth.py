# test_auth.py - Updated to use your existing UUID functions

import sys
import os
sys.path.append('.')

from database import SessionLocal, engine
from models import Base, User, ContactList, ContactListPermission, PermissionLevel
from auth import get_password_hash, verify_password, authenticate_user
import uuid
from datetime import datetime

def test_authentication_system():
    print("🔍 Testing Authentication System...")
    
    # Test database connection
    try:
        db = SessionLocal()
        print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return
    
    # Test password hashing
    try:
        test_password = "test123"
        hashed = get_password_hash(test_password)
        verify_result = verify_password(test_password, hashed)
        print(f"✅ Password hashing works: {verify_result}")
        if not verify_result:
            print("❌ Password verification failed!")
            return
    except Exception as e:
        print(f"❌ Password hashing failed: {e}")
        return
    
    # Check if tables exist and create them if needed
    try:
        users_count = db.query(User).count()
        print(f"✅ User table exists, count: {users_count}")
    except Exception as e:
        print(f"❌ User table issue: {e}")
        print("🔧 Creating/updating database tables...")
        try:
            Base.metadata.create_all(bind=engine)
            print("✅ Tables created successfully")
        except Exception as create_error:
            print(f"❌ Failed to create tables: {create_error}")
            return
    
    # List existing users
    try:
        existing_users = db.query(User).all()
        print(f"📊 Existing users ({len(existing_users)}):")
        for user in existing_users:
            print(f"   - {user.email} (Active: {user.is_active})")
    except Exception as e:
        print(f"❌ Failed to query users: {e}")
    
    # Create a test user
    try:
        # Clean up any existing test user
        existing_user = db.query(User).filter(User.email == "test@example.com").first()
        if existing_user:
            db.delete(existing_user)
            db.commit()
            print("🧹 Cleaned up existing test user")
        
        # Create new test user directly (using your UUID system)
        test_user = User(
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            hashed_password=get_password_hash("password123"),
            is_active=True,
            is_verified=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        print(f"✅ Test user created: test@example.com / password123 (ID: {test_user.id})")
        
        # Test authentication
        auth_user = authenticate_user(db, "test@example.com", "password123")
        if auth_user:
            print("✅ Authentication test successful")
            print(f"   User ID: {auth_user.id}")
            print(f"   User Email: {auth_user.email}")
            print(f"   User Active: {auth_user.is_active}")
        else:
            print("❌ Authentication test failed")
            
        # Test wrong password
        wrong_auth = authenticate_user(db, "test@example.com", "wrongpassword")
        if not wrong_auth:
            print("✅ Wrong password correctly rejected")
        else:
            print("❌ Wrong password was accepted!")
            
    except Exception as e:
        print(f"❌ User creation/authentication failed: {e}")
        print(f"   Error type: {type(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
    
    finally:
        db.close()

if __name__ == "__main__":
    test_authentication_system()