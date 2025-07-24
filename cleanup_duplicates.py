# cleanup_duplicates.py - Run this once to fix existing duplicates

import sys
import os
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from sqlalchemy.orm import Session
    from database import get_db
    from crud import RoomCRUD
    from models import Room
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running this script from your project directory")
    print("and that database.py, crud.py, and models.py exist")
    sys.exit(1)

def cleanup_duplicate_rooms_for_property(db: Session, property_id: str):
    """Clean up duplicate rooms for a specific property"""
    print(f"\n🧹 Cleaning up duplicate rooms for property: {property_id}")
    
    # Get all rooms for this property
    all_rooms = (db.query(Room)
                .filter(Room.property_id == property_id)
                .order_by(Room.first_seen_date)  # Keep the oldest room
                .all())
    
    if not all_rooms:
        print("   No rooms found for this property")
        return
    
    print(f"   Found {len(all_rooms)} total rooms")
    
    # Group rooms by their stable base key
    rooms_by_base_key = {}
    for room in all_rooms:
        base_key = RoomCRUD.generate_room_base_key(room.room_identifier)
        if base_key not in rooms_by_base_key:
            rooms_by_base_key[base_key] = []
        rooms_by_base_key[base_key].append(room)
    
    print(f"   Grouped into {len(rooms_by_base_key)} unique base keys")
    
    deleted_count = 0
    kept_count = 0
    
    for base_key, duplicate_rooms in rooms_by_base_key.items():
        if len(duplicate_rooms) > 1:
            print(f"\n   🔍 Processing duplicates for base key: '{base_key}'")
            
            # Sort by first_seen_date to keep the oldest
            duplicate_rooms.sort(key=lambda x: x.first_seen_date or datetime.min)
            
            # Keep the first (oldest) room
            room_to_keep = duplicate_rooms[0]
            rooms_to_delete = duplicate_rooms[1:]
            
            print(f"      ✅ Keeping: '{room_to_keep.room_identifier}' (First seen: {room_to_keep.first_seen_date})")
            
            # Update the kept room with the latest information
            latest_room = duplicate_rooms[-1]  # Most recent room
            if latest_room != room_to_keep:
                print(f"      🔄 Updating kept room with latest info from: '{latest_room.room_identifier}'")
                room_to_keep.room_identifier = latest_room.room_identifier
                room_to_keep.current_status = latest_room.current_status
                room_to_keep.current_price = latest_room.current_price
                room_to_keep.last_seen_date = latest_room.last_seen_date
                room_to_keep.times_seen = sum(r.times_seen for r in duplicate_rooms)
                room_to_keep.times_changed = sum(r.times_changed for r in duplicate_rooms)
            
            # Delete the duplicates
            for room_to_delete in rooms_to_delete:
                print(f"      ❌ Deleting: '{room_to_delete.room_identifier}' (ID: {room_to_delete.id})")
                db.delete(room_to_delete)
                deleted_count += 1
            
            kept_count += 1
        else:
            print(f"   ✅ No duplicates for base key: '{base_key}'")
            kept_count += 1
    
    # Commit all changes
    db.commit()
    
    print(f"\n📊 Cleanup Summary:")
    print(f"   ✅ Rooms kept: {kept_count}")
    print(f"   ❌ Duplicates deleted: {deleted_count}")
    print(f"   🎯 Total rooms after cleanup: {kept_count}")

def main():
    """Run the cleanup for your specific property"""
    db = next(get_db())
    
    # Your property ID
    property_id = "442ab036-0e27-4ab0-a16f-263670fd204d"
    
    try:
        cleanup_duplicate_rooms_for_property(db, property_id)
        print("\n🎉 Cleanup completed successfully!")
    except Exception as e:
        print(f"\n❌ Error during cleanup: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()