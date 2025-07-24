# modules/calculator.py
"""
Price calculation and rental income analysis functions for HMO Analyser
"""

import re


def remove_pcm_from_price(price_text):
    """Remove 'pcm' from price text"""
    return price_text.replace(' pcm', '').replace('pcm', '').strip()


def extract_price_from_text(price_text):
    """Extract numerical price from price text and convert pw to pcm"""
    if not price_text:
        return None
        
    # Check if this is a per-week price
    is_per_week = bool(re.search(r'\bpw\b', price_text.lower()))
    
    # Remove currency symbols and common suffixes, then extract numbers
    clean_text = price_text.replace('£', '').replace('pcm', '').replace('pw', '').replace(',', '').strip()
    
    # Use regex to find the first number in the text
    match = re.search(r'(\d+(?:\.\d+)?)', clean_text)
    
    if match:
        try:
            price = float(match.group(1))
            
            # FIXED: Convert per week to per month
            if is_per_week:
                # 1 month = 4.33 weeks on average (52 weeks / 12 months)
                price = price * 4.33
                print(f"💰 Converted weekly price: £{match.group(1)} pw → £{price:.0f} pcm")
            
            return price
        except ValueError:
            return None
    return None



def calculate_rental_income(keys, values, total_rooms):
    """Calculate monthly rental income based on available room data"""
    room_prices = []
    
    # Extract prices from all rooms (both available and taken)
    for i in range(min(len(keys), len(values))):
        key_text = keys[i].get_text().strip()
        value_text = values[i].get_text().strip()
        
        # Extract price from the key (which contains the rent amount)
        price = extract_price_from_text(key_text)
        if price:
            room_prices.append(price)
    
    if not room_prices:
        return None, None
    
    # If we have prices for all rooms, sum them up
    if len(room_prices) == total_rooms:
        monthly_income = sum(room_prices)
        calculation_method = f"Sum of all {len(room_prices)} room rents"
    else:
        # If we only have some rooms, calculate average and multiply by total rooms
        average_price = sum(room_prices) / len(room_prices)
        monthly_income = average_price * total_rooms
        calculation_method = f"Average of {len(room_prices)} rooms (£{average_price:.0f}) × {total_rooms} total rooms"
    
    annual_income = monthly_income * 12
    
    print(f"\n💰 RENTAL INCOME CALCULATION:")
    print(f"   Method: {calculation_method}")
    print(f"   Room prices found: {room_prices}")
    print(f"   Monthly income: £{monthly_income:.0f}")
    print(f"   Annual income: £{annual_income:.0f}")
    
    return monthly_income, annual_income


def calculate_rental_income(keys, values, total_rooms):
    """Calculate monthly rental income with pw conversion"""
    room_prices = []
    conversions_made = 0
    
    # Extract prices from all rooms (both available and taken)
    for i in range(min(len(keys), len(values))):
        key_text = keys[i].get_text().strip()
        value_text = values[i].get_text().strip()
        
        # FIXED: Extract price with pw conversion
        price = extract_price_from_text(key_text)
        if price:
            room_prices.append(price)
            
            # Count conversions for logging
            if re.search(r'\bpw\b', key_text.lower()):
                conversions_made += 1
    
    if not room_prices:
        return None, None
    
    # If we have prices for all rooms, sum them up
    if len(room_prices) == total_rooms:
        monthly_income = sum(room_prices)
        calculation_method = f"Sum of all {len(room_prices)} room rents"
    else:
        # If we only have some rooms, calculate average and multiply by total rooms
        average_price = sum(room_prices) / len(room_prices)
        monthly_income = average_price * total_rooms
        calculation_method = f"Average of {len(room_prices)} rooms (£{average_price:.0f}) × {total_rooms} total rooms"
    
    annual_income = monthly_income * 12
    
    print(f"\n💰 RENTAL INCOME CALCULATION:")
    print(f"   Method: {calculation_method}")
    print(f"   Room prices found: {[f'£{p:.0f}' for p in room_prices]}")
    if conversions_made > 0:
        print(f"   ⚡ {conversions_made} weekly prices converted to monthly")
    print(f"   Monthly income: £{monthly_income:.0f}")
    print(f"   Annual income: £{annual_income:.0f}")
    
    return monthly_income, annual_income


# 4. ADDITIONAL: Helper function for price conversion (add to calculator.py)
def convert_weekly_to_monthly(weekly_price: float) -> float:
    """Convert weekly rent to monthly rent"""
    # 1 year = 52 weeks = 12 months
    # Therefore 1 month = 52/12 = 4.33 weeks
    return weekly_price * 4.33

def detect_price_period(price_text: str) -> str:
    """Detect if a price is per week, per month, or unknown"""
    if not price_text:
        return "unknown"
    
    text_lower = price_text.lower()
    
    if re.search(r'\bpw\b', text_lower):
        return "weekly"
    elif re.search(r'\bpcm\b|\bper\s+month\b|\bmonth\b', text_lower):
        return "monthly"
    else:
        return "unknown"
    
def log_price_conversion(room_identifier: str, original_price: float, converted_price: float):
    """Log when a weekly price is converted to monthly"""
    print(f"🔄 PRICE CONVERSION: {room_identifier}")
    print(f"   Original: £{original_price:.0f} pw")
    print(f"   Converted: £{converted_price:.0f} pcm")
    print(f"   Multiplier: 4.33 weeks/month")