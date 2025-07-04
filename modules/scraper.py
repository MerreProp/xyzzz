# modules/scraper.py
"""
Web scraping and HTML parsing functions for HMO Analyser
"""

import requests
from bs4 import BeautifulSoup
from config import DEFAULT_HEADERS, REQUEST_TIMEOUT
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
            
            # Process room data
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


def _process_room_data(price_section, soup, analysis_data):
    """Process room data from the price section"""
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
    
    # Process room availability
    print(f"\n🔗 ROOM AVAILABILITY ANALYSIS:")
    
    available_rooms = []
    available_rooms_details = []
    taken_rooms = []
    room_details_list = []
    all_rooms_list = []
    
    for i in range(min(len(keys), len(values))):
        key_text = keys[i].get_text().strip()
        value_text = values[i].get_text().strip()
        
        room_detail = f"{key_text} - {value_text}"
        room_details_list.append(room_detail)
        
        if value_text.upper() == "(NOW LET)":
            taken_rooms.append((key_text, value_text))
            clean_price = remove_pcm_from_price(key_text)
            all_rooms_list.append(f"{i+1} - {clean_price}")
        else:
            available_rooms.append((key_text, value_text))
            clean_price = remove_pcm_from_price(key_text)
            available_rooms_details.append(f"{len(available_rooms)} - {clean_price}")
            all_rooms_list.append(f"{i+1} - {clean_price} ({value_text})")
    
    # Store room data
    analysis_data['Room Details'] = '; '.join(room_details_list)
    analysis_data['Listed Rooms'] = len(keys)
    analysis_data['Available Rooms Details'] = available_rooms_details
    analysis_data['All Rooms List'] = all_rooms_list
    
    # Get total rooms from household section
    actual_total_rooms = _get_total_rooms_count(soup, len(keys))
    
    # Store room counts
    analysis_data['Total Rooms'] = actual_total_rooms
    analysis_data['Available Rooms'] = len(available_rooms)
    
    unlisted_rooms = actual_total_rooms - len(keys) if actual_total_rooms > len(keys) else 0
    total_taken = len(taken_rooms) + unlisted_rooms
    analysis_data['Taken Rooms'] = total_taken
    
    # Calculate rental income
    monthly_income, annual_income = calculate_rental_income(keys, values, actual_total_rooms)
    analysis_data['Monthly Income'] = monthly_income
    analysis_data['Annual Income'] = annual_income
    
    # Print summary
    _print_room_summary(available_rooms, taken_rooms, actual_total_rooms, len(keys), total_taken, unlisted_rooms)


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


def _print_room_summary(available_rooms, taken_rooms, actual_total_rooms, listed_rooms, total_taken, unlisted_rooms):
    """Print room summary"""
    print(f"\n✅ AVAILABLE ROOMS ({len(available_rooms)}):")
    if available_rooms:
        for i, (price, room_type) in enumerate(available_rooms, 1):
            print(f"  {i}: '{price}' → '{room_type}'")
    else:
        print("  No available rooms found")
    
    print(f"\n❌ TAKEN ROOMS ({len(taken_rooms)}):")
    if taken_rooms:
        for i, (price, status) in enumerate(taken_rooms, 1):
            print(f"  {i}: '{price}' → '{status}'")
    else:
        print("  No taken rooms found")
    
    print(f"\n📊 SUMMARY:")
    print(f"  Total rooms in house: {actual_total_rooms}")
    print(f"  Rooms listed: {listed_rooms}")
    print(f"  Available: {len(available_rooms)}")
    
    print(f"  Taken: {total_taken}", end="")
    if unlisted_rooms > 0:
        print(f" (includes {unlisted_rooms} unlisted/occupied)")
    else:
        print()