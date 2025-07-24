# modules/scraper.py
"""
Web scraping and HTML parsing functions for HMO Analyser - FIXED VERSION
"""

from datetime import datetime
import uuid
import requests
from bs4 import BeautifulSoup
from config import DEFAULT_HEADERS, REQUEST_TIMEOUT
from crud import RoomAvailabilityPeriodCRUD, RoomCRUD
from models import Room
from modules.calculator import remove_pcm_from_price, calculate_rental_income


def status_detector(badge_element):
    """Detect the status of the listing from the badge element"""
    if not badge_element:
        return 'Unknown'
    
    # Get both class and text
    classes = badge_element.get('class', [])
    text = badge_element.get_text().strip()
    
    # Check modifier classes first
    for class_name in classes:
        if 'featured' in class_name:
            return 'Featured Today'
        elif 'new' in class_name:
            return 'New Today' if 'today' in text.lower() else 'New'
        elif 'boosted' in class_name:
            return 'Boosted'
    
    # Fallback to text matching
    if 'featured' in text.lower():
        return 'Featured Today'
    elif 'new' in text.lower():
        return 'New Today' if 'today' in text.lower() else 'New'
    elif 'boosted' in text.lower():
        return 'Boosted'
    
    return 'Available'  # Default status


def picture_detector(soup):
    """Detect the main picture URL from the listing"""
    main_image_div = soup.find('dt', class_='photo-gallery__main-image-dt')
    
    if main_image_div:
        # Look for a tag with title starting with "Photo 1"
        photo_link = main_image_div.find('a', title=lambda x: x and x.startswith('Photo 1'))
        
        if photo_link:
            photo_url = photo_link.get('href', '')
            photo_title = photo_link.get('title', '')
            
            # Check if title contains room information
            room_info = None
            if ':' in photo_title:
                # Extract everything after the colon
                room_part = photo_title.split(':', 1)[1].strip()
                if room_part.startswith('Room '):
                    room_info = room_part
            
            return photo_url, photo_title, room_info
    
    return None, None, None

@staticmethod
def mark_all_property_rooms_as_taken(db: requests.Session, property_id, analysis_id=None):
    """Mark all rooms for a property as taken (for expired listings)"""
    # Handle UUID format
    if isinstance(property_id, uuid.UUID):
        property_id = str(property_id)
    if isinstance(analysis_id, uuid.UUID):
        analysis_id = str(analysis_id)
    
    current_time = datetime.utcnow()
    
    # Get all rooms for this property
    rooms = (db.query(Room)
            .filter(Room.property_id == property_id)
            .all())
    
    updated_rooms = []
    
    for room in rooms:
        # Only update if the room is currently available
        if room.current_status == 'available':
            old_status = room.current_status
            room.current_status = 'taken'
            room.last_seen_date = current_time
            room.times_changed += 1
            
            # Log the status change
            RoomCRUD.create_room_change(
                db, room.id, property_id, analysis_id,
                "status_change", old_status, "taken",
                f"Room marked as taken due to expired listing"
            )
            
            # End current availability period
            RoomAvailabilityPeriodCRUD.end_current_period(
                db,
                room_id=room.id,
                end_date=current_time,
                end_analysis_id=analysis_id
            )
            
            updated_rooms.append(room)
            print(f"🔄 Updated room {room.room_number} from {old_status} to taken")
    
    db.commit()
    
    return {
        "updated_rooms": updated_rooms,
        "total_changes": len(updated_rooms)
    }



def extract_price_section(url, analysis_data):
    """Extract only the specific price section from SpareRoom listing"""
    
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)
    
    try:
        print(f"🔍 Fetching URL...")
        response = session.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        print(f"✅ Page loaded")
        
        # Look for the specific section
        price_section = soup.find('section', class_='feature feature--price_room_only')
        
        if price_section:
            print("\n✅ FOUND: <section class='feature feature--price_room_only'>")
            
            # Check bills inclusion
            _check_bills_inclusion(soup, analysis_data)
            
            # Check landlord type
            _check_landlord_type(soup, analysis_data)
            
            # Check household gender
            _check_household_gender(soup, analysis_data)
            
            # Check advertiser details
            _check_advertiser_details(soup, analysis_data)
            
            # Check listing status
            _check_listing_status(soup, analysis_data)
            
            # Check main picture
            _check_main_picture(soup, analysis_data)
            
            # ✅ FIXED: Check if listing is expired AFTER extracting other data
            is_expired = _check_listing_expired(soup, analysis_data)
            
            if is_expired:
                # ✅ FIXED: For expired listings, don't create any room tracking entries
                print("💰 Calculating rental potential for expired listing...")
                keys = price_section.find_all(class_='feature-list__key')
                values = price_section.find_all(class_='feature-list__value')
                
                # Get total rooms from household section
                actual_total_rooms = _get_total_rooms_count(soup, len(keys))
                
                # Calculate what the income would be if active
                monthly_income, annual_income = calculate_rental_income(keys, values, actual_total_rooms)
                analysis_data['Monthly Income'] = monthly_income
                analysis_data['Annual Income'] = annual_income
                analysis_data['Total Rooms'] = actual_total_rooms
                
                print(f"📊 Rental potential preserved: £{monthly_income}/month, £{annual_income}/year")
                
                # ✅ CRITICAL: Set flag and empty room list to prevent any room processing
                analysis_data['_EXPIRED_LISTING'] = True
                analysis_data['All Rooms List'] = []  # No room entries to process
                
                print("🚫 Listing expired - will update existing room statuses only")
            else:
                # Process room data normally for active listings
                _process_room_data(price_section, soup, analysis_data)
            
        else:
            print("❌ Section <section class='feature feature--price_room_only'> NOT FOUND")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def _check_bills_inclusion(soup, analysis_data):
    """Check if bills are included"""
    print("\n🔍 CHECKING BILLS INCLUSION...")
    bills_section = soup.find('section', class_='feature feature--extra-cost')
    
    if bills_section:
        print("✅ FOUND: <section class='feature feature--extra-cost'>")
        
        bills_keys = bills_section.find_all(class_='feature-list__key')
        bills_values = bills_section.find_all(class_='feature-list__value')
        
        bills_included = False
        for i in range(min(len(bills_keys), len(bills_values))):
            key_text = bills_keys[i].get_text().strip()
            value_text = bills_values[i].get_text().strip()
            
            if key_text == "Bills included?":
                print(f"📋 Bills included? → '{value_text}'")
                analysis_data['Bills Included'] = value_text
                if value_text.lower() == "yes":
                    bills_included = True
                    print("✅ Bills are included - proceeding with listing")
                else:
                    bills_included = False
                    analysis_data['Meets Requirements'] = 'No - Bills not included'
                    print("❌ Bills are NOT included - ignoring this listing")
                break
        
        if not bills_included:
            print("\n🚫 LISTING IGNORED: Bills are not included")
    else:
        print("❌ Bills section not found - assuming bills not included")
        analysis_data['Bills Included'] = 'Not found'
        analysis_data['Meets Requirements'] = 'No - Cannot verify bills'


def _check_landlord_type(soup, analysis_data):
    """Check if landlord lives in"""
    print("\n🔍 CHECKING LANDLORD TYPE...")
    advertiser_div = soup.find('div', class_='advertiser-info')
    
    if advertiser_div:
        print("✅ FOUND: <div class='advertiser-info'>")
        
        em_tag = advertiser_div.find('em')
        
        if em_tag:
            em_text = em_tag.get_text().strip().lower()
            print(f"📋 Landlord type: '{em_text}'")
            analysis_data['Landlord Type'] = em_text.title()
            
            if em_text == "live in landlord":
                print("❌ Live-in landlord detected - ignoring this listing")
                if 'Meets Requirements' not in analysis_data or analysis_data['Meets Requirements'] == 'Yes':
                    analysis_data['Meets Requirements'] = 'No - Live-in landlord'
                else:
                    analysis_data['Meets Requirements'] += ', Live-in landlord'
            else:
                print("✅ Not a live-in landlord - proceeding with listing")
                if 'Meets Requirements' not in analysis_data:
                    analysis_data['Meets Requirements'] = 'Yes'
        else:
            print("❌ No <em> tag found in advertiser-info")
            analysis_data['Landlord Type'] = 'Not specified'
            if 'Meets Requirements' not in analysis_data:
                analysis_data['Meets Requirements'] = 'Yes'
    else:
        print("❌ advertiser-info div not found")
        analysis_data['Landlord Type'] = 'Not found'
        if 'Meets Requirements' not in analysis_data:
            analysis_data['Meets Requirements'] = 'Yes'


def _check_household_gender(soup, analysis_data):
    """Check current household gender"""
    print("\n🔍 CHECKING HOUSEHOLD GENDER...")
    household_section = soup.find('section', class_='feature feature--current-household')
    
    if household_section:
        print("✅ FOUND: <section class='feature feature--current-household'>")
        
        household_keys = household_section.find_all(class_='feature-list__key')
        household_values = household_section.find_all(class_='feature-list__value')
        
        gender_found = False
        for i in range(min(len(household_keys), len(household_values))):
            key_text = household_keys[i].get_text().strip()
            value_text = household_values[i].get_text().strip()
            
            if key_text == "Gender":
                print(f"👥 Gender: '{value_text}'")
                analysis_data['Household Gender'] = value_text
                gender_found = True
                break
        
        if not gender_found:
            print("❌ 'Gender' key not found in household section")
            analysis_data['Household Gender'] = 'Not found'
    else:
        print("❌ Current household section not found")
        analysis_data['Household Gender'] = 'Not found'


def _check_advertiser_details(soup, analysis_data):
    """Check advertiser name and profile"""
    print("\n🔍 CHECKING ADVERTISER NAME...")
    name_element = soup.find('strong', class_='profile-photo__name', itemprop='name')
    
    if name_element:
        advertiser_name = name_element.get_text().strip()
        print(f"👤 Advertiser: '{advertiser_name}'")
        analysis_data['Advertiser Name'] = advertiser_name
    else:
        print("❌ Advertiser name not found")
        analysis_data['Advertiser Name'] = 'Not found'
    
    # Check advertiser profile link
    profile_link = soup.find('a', title="View the advertiser's profile")
    if profile_link:
        profile_url = profile_link.get('href', '')
        print(f"🔗 Profile link: '{profile_url}'")
    else:
        print("❌ Advertiser profile link not found")


def _check_listing_status(soup, analysis_data):
    """Check listing status"""
    print("\n🔍 CHECKING LISTING STATUS...")
    badge_element = soup.find('div', class_='ad-detail__badge')
    
    if badge_element:
        status = status_detector(badge_element)
        print(f"📊 Listing status: '{status}'")
        analysis_data['Listing Status'] = status
        
        badge_classes = ' '.join(badge_element.get('class', []))
        badge_text = badge_element.get_text().strip()
        print(f"🏷️ Badge classes: '{badge_classes}'")
        print(f"🏷️ Badge text: '{badge_text}'")
    else:
        print("❌ Status badge not found")
        analysis_data['Listing Status'] = 'Not found'


def _check_main_picture(soup, analysis_data):
    """Check main picture"""
    print("\n🔍 CHECKING MAIN PICTURE...")
    photo_url, photo_title, room_info = picture_detector(soup)
    
    if photo_url:
        print(f"📷 Main picture: '{photo_url}'")
        analysis_data['Main Photo URL'] = photo_url
        if room_info:
            print(f"🏠 Photo shows: '{room_info}'")
        else:
            print(f"🏷️ Photo title: '{photo_title}'")
    else:
        print("❌ Main picture not found")
        analysis_data['Main Photo URL'] = 'Not found'


# ✅ NEW STATUS DETECTION FUNCTIONS
def _is_room_taken(value_text):
    """
    ✅ NEW: Determine if a room is definitely taken
    Returns True only if there's clear evidence the room is unavailable
    """
    value_upper = value_text.upper().strip()
    
    taken_indicators = [
        "(NOW LET)",
        "TAKEN",
        "RESERVED", 
        "PENDING",
        "UNAVAILABLE",
        "NOT AVAILABLE",
        "OCCUPIED",
        "LET AGREED"
    ]
    
    return any(indicator in value_upper for indicator in taken_indicators)


def _is_room_available(value_text):
    """
    ✅ IMPROVED: Determine if a room is available for rent
    Now includes room types as available indicators
    """
    value_upper = value_text.upper().strip()
    
    # Explicit availability indicators
    available_indicators = [
        "AVAILABLE",
        "TO LET", 
        "FOR RENT",
        "AVAILABLE NOW",
        "IMMEDIATELY AVAILABLE",
        "ROOM AVAILABLE"
    ]
    
    # ✅ NEW: Room type indicators (these suggest the room is being advertised)
    room_type_indicators = [
        "SINGLE",
        "DOUBLE", 
        "ENSUITE",
        "EN-SUITE",
        "MASTER",
        "TWIN",
        "STUDIO",
        "BEDSIT"
    ]
    
    # Status that might indicate availability
    potential_availability = [
        "", 
        "-", 
        "N/A"
    ]
    
    # Check for explicit availability
    if any(indicator in value_upper for indicator in available_indicators):
        return True
    
    # ✅ NEW: Check for room types (if it's just a room type, assume it's available)
    if any(room_type in value_upper for room_type in room_type_indicators):
        return True
        
    # Check for empty/minimal status
    if value_upper in potential_availability:
        return True
    
    return False


# ✅ FIXED ROOM PROCESSING FUNCTION
def _process_room_data(price_section, soup, analysis_data):
    """Process room data from the price section - DEBUG VERSION"""
    print("=" * 60)
    print("📄 HTML CONTENT:")
    print(price_section.prettify())
    
    # Extract room data
    keys = price_section.find_all(class_='feature-list__key')
    values = price_section.find_all(class_='feature-list__value')
    
    print(f"\n🔑 Found {len(keys)} feature-list__key elements:")
    for i, key in enumerate(keys, 1):
        print(f"  {i}: '{key.get_text().strip()}'")
    
    print(f"\n💎 Found {len(values)} feature-list__value elements:")
    for i, value in enumerate(values, 1):
        print(f"  {i}: '{value.get_text().strip()}'")
    
    # ✅ DEBUG: Check the loop range
    loop_range = min(len(keys), len(values))
    print(f"\n🔍 DEBUG: Loop will run {loop_range} times (min of {len(keys)} keys and {len(values)} values)")
    
    # Process room availability
    print(f"\n🔗 ROOM AVAILABILITY ANALYSIS:")
    
    available_rooms = []
    available_rooms_details = []
    taken_rooms = []
    uncertain_rooms = []
    room_details_list = []
    all_rooms_list = []
    
    # ✅ DEBUG: Add iteration counter
    for i in range(loop_range):
        print(f"\n🔄 DEBUG: Processing iteration {i+1}/{loop_range}")
        
        key_text = keys[i].get_text().strip()
        value_text = values[i].get_text().strip()
        
        print(f"   📝 Key: '{key_text}', Value: '{value_text}'")
        
        room_detail = f"{key_text} - {value_text}"
        room_details_list.append(room_detail)
        
        # ✅ DEBUG: Count before processing
        print(f"   📊 Before: Available={len(available_rooms)}, Taken={len(taken_rooms)}, Uncertain={len(uncertain_rooms)}")
        
        # Process room status
        if _is_room_taken(value_text):
            taken_rooms.append((key_text, value_text))
            clean_price = remove_pcm_from_price(key_text)
            all_rooms_list.append(f"{i+1} - {clean_price} (TAKEN)")
            print(f"  ❌ TAKEN: '{key_text}' → '{value_text}'")
            
        elif _is_room_available(value_text):
            available_rooms.append((key_text, value_text))
            clean_price = remove_pcm_from_price(key_text)
            available_rooms_details.append(f"{clean_price} ({value_text})")
            all_rooms_list.append(f"{i+1} - {clean_price} ({value_text})")
            print(f"  ✅ AVAILABLE: '{key_text}' → '{value_text}'")
            
        else:
            uncertain_rooms.append((key_text, value_text))
            clean_price = remove_pcm_from_price(key_text)
            all_rooms_list.append(f"{i+1} - {clean_price} (STATUS UNCLEAR)")
            print(f"  ❓ UNCERTAIN: '{key_text}' → '{value_text}'")
        
        # ✅ DEBUG: Count after processing
        print(f"   📊 After: Available={len(available_rooms)}, Taken={len(taken_rooms)}, Uncertain={len(uncertain_rooms)}")
    
    # ✅ DEBUG: Final counts
    print(f"\n🔍 DEBUG: Final counts after loop:")
    print(f"   Available rooms list: {len(available_rooms)} items")
    print(f"   Taken rooms list: {len(taken_rooms)} items")
    print(f"   Uncertain rooms list: {len(uncertain_rooms)} items")
    print(f"   Total: {len(available_rooms) + len(taken_rooms) + len(uncertain_rooms)}")
    
    # Continue with the rest of your existing logic...
    total_listed_rooms = len(keys)
    confirmed_available = len(available_rooms)
    confirmed_taken = len(taken_rooms)
    uncertain_count = len(uncertain_rooms)
    
    print(f"\n📊 ROOM STATUS SUMMARY:")
    print(f"  Total listed: {total_listed_rooms}")
    print(f"  Confirmed available: {confirmed_available}")
    print(f"  Confirmed taken: {confirmed_taken}")
    print(f"  Uncertain status: {uncertain_count}")
    
    # Get total rooms from household section
    actual_total_rooms = _get_total_rooms_count(soup, len(keys))
    
    # Store data
    analysis_data['Total Rooms'] = actual_total_rooms
    analysis_data['Available Rooms'] = confirmed_available
    analysis_data['Listed Rooms'] = total_listed_rooms
    analysis_data['Uncertain Rooms'] = uncertain_count
    
    # ✅ IMPROVED: Better taken room calculation
    unlisted_rooms = actual_total_rooms - total_listed_rooms if actual_total_rooms > total_listed_rooms else 0
    
    # Assume uncertain rooms are taken (conservative approach)
    total_taken = confirmed_taken + uncertain_count + unlisted_rooms
    analysis_data['Taken Rooms'] = total_taken
    
    # Store room data
    analysis_data['Room Details'] = '; '.join(room_details_list)
    analysis_data['Available Rooms Details'] = available_rooms_details
    analysis_data['All Rooms List'] = all_rooms_list
    analysis_data['Uncertain Rooms Details'] = uncertain_rooms  # ✅ NEW: Store uncertain room details
    
    # Calculate rental income
    monthly_income, annual_income = calculate_rental_income(keys, values, actual_total_rooms)
    analysis_data['Monthly Income'] = monthly_income
    analysis_data['Annual Income'] = annual_income
    
    # Print summary
    _print_room_summary_fixed(available_rooms, taken_rooms, uncertain_rooms, actual_total_rooms, total_listed_rooms, total_taken, unlisted_rooms)


def _get_total_rooms_count(soup, listed_rooms_count):
    """Get total room count from household section"""
    print("\n🔍 VERIFYING TOTAL ROOM COUNT...")
    actual_total_rooms = listed_rooms_count  # Default to current count
    
    household_section = soup.find('section', class_='feature feature--current-household')
    
    if household_section:
        total_rooms_keys = household_section.find_all(class_='feature-list__key')
        total_rooms_values = household_section.find_all(class_='feature-list__value')
        
        for i in range(min(len(total_rooms_keys), len(total_rooms_values))):
            key_text = total_rooms_keys[i].get_text().strip()
            value_text = total_rooms_values[i].get_text().strip()
            
            if key_text == "Total # rooms":
                try:
                    household_total = int(value_text)
                    print(f"📋 Total rooms according to household section: {household_total}")
                    
                    if household_total != listed_rooms_count:
                        print(f"⚠️  Room count mismatch! Listed rooms: {listed_rooms_count}, Actual total: {household_total}")
                        print(f"✅ Using household total: {household_total}")
                        actual_total_rooms = household_total
                    else:
                        print(f"✅ Room counts match: {household_total}")
                except ValueError:
                    print(f"❌ Could not parse total rooms value: '{value_text}'")
                break
    
    return actual_total_rooms


def _print_room_summary_fixed(available_rooms, taken_rooms, uncertain_rooms, actual_total_rooms, listed_rooms, total_taken, unlisted_rooms):
    """✅ IMPROVED: Print comprehensive room summary with uncertainty tracking"""
    print(f"\n✅ CONFIRMED AVAILABLE ROOMS ({len(available_rooms)}):")
    if available_rooms:
        for i, (price, room_type) in enumerate(available_rooms, 1):
            print(f"  {i}: '{price}' → '{room_type}'")
    else:
        print("  No confirmed available rooms found")
    
    print(f"\n❌ CONFIRMED TAKEN ROOMS ({len(taken_rooms)}):")
    if taken_rooms:
        for i, (price, status) in enumerate(taken_rooms, 1):
            print(f"  {i}: '{price}' → '{status}'")
    else:
        print("  No confirmed taken rooms found")
    
    print(f"\n❓ UNCERTAIN STATUS ROOMS ({len(uncertain_rooms)}):")
    if uncertain_rooms:
        for i, (price, status) in enumerate(uncertain_rooms, 1):
            print(f"  {i}: '{price}' → '{status}' (assuming taken)")
    else:
        print("  No rooms with uncertain status")
    
    print(f"\n📊 FINAL SUMMARY:")
    print(f"  Total rooms in house: {actual_total_rooms}")
    print(f"  Rooms listed: {listed_rooms}")
    print(f"  Confirmed available: {len(available_rooms)}")
    print(f"  Confirmed taken: {len(taken_rooms)}")
    print(f"  Uncertain (treated as taken): {len(uncertain_rooms)}")
    
    print(f"  Total taken: {total_taken}", end="")
    if unlisted_rooms > 0:
        print(f" (includes {unlisted_rooms} unlisted/occupied)")
    else:
        print()
    
    print(f"\n⚠️  CONSERVATIVE APPROACH: Only counting explicitly available rooms")
    print(f"   This prevents overestimating availability when room status is unclear")


# ADD this function to scraper.py

def _check_listing_expired(soup, analysis_data):
    """Check if the listing is expired/not accepting applications"""
    print("\n🔍 CHECKING IF LISTING IS EXPIRED...")
    
    # Look for the expired listing indicator
    expired_div = soup.find('div', class_='listing-contact__expired')
    
    if expired_div:
        expired_text = expired_div.get_text().strip()
        print(f"🚫 LISTING EXPIRED: '{expired_text}'")
        
        # ✅ FIXED: Only update availability-related fields, preserve property info
        analysis_data['Listing Status'] = 'Expired - Not Accepting Applications'
        analysis_data['Available Rooms'] = 0
        analysis_data['Available Rooms Details'] = []
        analysis_data['Meets Requirements'] = 'No - Listing expired'
        
        # ✅ PRESERVE: Keep Monthly Income, Annual Income, Total Rooms, etc.
        # These represent the property's rental potential when it was active
        # Don't set them to 0 - let them be calculated from the last known data
        
        print("📊 Status: Listing marked as expired - availability set to 0, preserving rental data")
        return True  # Listing is expired
    else:
        print("✅ Listing is active - proceeding with room analysis")
        return False  # Listing is active
    
def _check_listing_expired(soup, analysis_data):
    """Check if the listing is expired/not accepting applications"""
    print("\n🔍 CHECKING IF LISTING IS EXPIRED...")
    
    # Look for the expired listing indicator
    expired_div = soup.find('div', class_='listing-contact__expired')
    
    if expired_div:
        expired_text = expired_div.get_text().strip()
        print(f"🚫 LISTING EXPIRED: '{expired_text}'")
        
        # ✅ FIXED: Only update availability-related fields, preserve property info
        analysis_data['Listing Status'] = 'Expired - Not Accepting Applications'
        analysis_data['Available Rooms'] = 0
        analysis_data['Available Rooms Details'] = []
        analysis_data['Meets Requirements'] = 'No - Listing expired'
        
        # ✅ PRESERVE: Keep Monthly Income, Annual Income, Total Rooms, etc.
        # These represent the property's rental potential when it was active
        # Don't set them to 0 - let them be calculated from the last known data
        
        print("📊 Status: Listing marked as expired - availability set to 0, preserving rental data")
        return True  # Listing is expired
    else:
        print("✅ Listing is active - proceeding with room analysis")
        return False  # Listing is active