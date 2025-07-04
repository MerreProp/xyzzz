# modules/calculator.py
"""
Price calculation and rental income analysis functions for HMO Analyser
"""

import re


def remove_pcm_from_price(price_text):
    """Remove 'pcm' from price text"""
    return price_text.replace(' pcm', '').replace('pcm', '').strip()


def extract_price_from_text(price_text):
    """Extract numerical price from price text (e.g., '£650 pcm' -> 650)"""
    # Remove currency symbols and 'pcm', then extract numbers
    clean_text = price_text.replace('£', '').replace('pcm', '').replace(',', '').strip()
    
    # Use regex to find the first number in the text
    match = re.search(r'(\d+(?:\.\d+)?)', clean_text)
    
    if match:
        try:
            return float(match.group(1))
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