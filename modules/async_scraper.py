"""
Async Web scraping module for HMO Analyser - Production Ready
Replaces synchronous requests with aiohttp for massive performance gains
"""

import asyncio
import aiohttp
from datetime import datetime
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Tuple
import traceback
from asyncio_throttle import Throttler
import ssl
import certifi

# Import your existing config (adjust path as needed)
try:
    from config import DEFAULT_HEADERS, REQUEST_TIMEOUT
except ImportError:
    # Fallback configuration if config.py not found
    DEFAULT_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    REQUEST_TIMEOUT = 30

# Create a throttler to respect SpareRoom's rate limits
# Allow 10 requests per second max
request_throttler = Throttler(rate_limit=10, period=1.0)

class AsyncSessionManager:
    """Manages aiohttp sessions with connection pooling and reuse"""
    
    def __init__(self):
        self._session = None
        self._connector = None
    
    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session with optimized settings"""
        if self._session is None or self._session.closed:
            # Create SSL context with proper certificates
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            
            # Configure connection pool for optimal performance with SSL
            connector = aiohttp.TCPConnector(
                ssl=ssl_context,  # Use the SSL context here
                limit=100,  # Total connection pool size
                limit_per_host=20,  # Connections per host
                ttl_dns_cache=300,  # DNS cache TTL (5 minutes)
                use_dns_cache=True,
                keepalive_timeout=30,
                enable_cleanup_closed=True
            )
            
            timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
            
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers=DEFAULT_HEADERS,
                trust_env=True  # Use system proxy settings if available
            )
            self._connector = connector
            
        return self._session
    
    async def close(self):
        """Clean up session and connector"""
        if self._session and not self._session.closed:
            await self._session.close()
        if self._connector:
            await self._connector.close()

# Global session manager instance
session_manager = AsyncSessionManager()

async def fetch_url_async(url: str, retries: int = 3) -> Tuple[str, int]:
    """
    Async fetch URL with automatic retries and throttling
    Returns: (content, status_code)
    """
    async with request_throttler:
        session = await session_manager.get_session()
        
        for attempt in range(retries):
            try:
                print(f"🔍 Fetching URL (attempt {attempt + 1}): {url}")
                
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        print(f"✅ Successfully fetched {len(content)} characters")
                        return content, response.status
                    else:
                        print(f"⚠️ HTTP {response.status} for {url}")
                        if attempt == retries - 1:
                            return "", response.status
                        
            except asyncio.TimeoutError:
                print(f"⏰ Timeout for {url} (attempt {attempt + 1})")
                if attempt == retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                
            except Exception as e:
                print(f"❌ Error fetching {url}: {e}")
                if attempt == retries - 1:
                    raise
                await asyncio.sleep(1)
    
    return "", 0

async def extract_price_section_async(url: str, analysis_data: Dict) -> Dict:
    """
    Async version of extract_price_section with improved performance
    """
    try:
        content, status_code = await fetch_url_async(url)
        
        if status_code != 200 or not content:
            print(f"❌ Failed to fetch content for {url}")
            return analysis_data
        
        soup = BeautifulSoup(content, 'html.parser')
        print(f"✅ Page parsed successfully")
        
        # Look for the specific section
        price_section = soup.find('section', class_='feature feature--price_room_only')
        
        if price_section:
            print("\n✅ FOUND: <section class='feature feature--price_room_only'>")
            
            # Run all checks in parallel for maximum speed
            await asyncio.gather(
                _check_bills_inclusion_async(soup, analysis_data),
                _check_landlord_type_async(soup, analysis_data),
                _check_household_gender_async(soup, analysis_data),
                _check_advertiser_details_async(soup, analysis_data),
                _check_listing_status_async(soup, analysis_data),
                _check_main_picture_async(soup, analysis_data),
                return_exceptions=True
            )
            
            # Check if listing is expired
            is_expired = await _check_listing_expired_async(soup, analysis_data)
            
            if is_expired:
                await _handle_expired_listing_async(price_section, soup, analysis_data)
            else:
                await _process_room_data_async(price_section, soup, analysis_data)
        else:
            print("❌ Section <section class='feature feature--price_room_only'> NOT FOUND")
        
        return analysis_data
        
    except Exception as e:
        print(f"❌ Error in extract_price_section_async: {e}")
        traceback.print_exc()
        return analysis_data

# Async helper functions - these mirror your existing synchronous functions
async def _check_bills_inclusion_async(soup, analysis_data: Dict) -> None:
    """Async version of bills inclusion check"""
    print("\n🔍 CHECKING BILLS INCLUSION...")
    bills_section = soup.find('section', class_='feature feature--extra-cost')
    
    if bills_section:
        print("✅ FOUND: <section class='feature feature--extra-cost'>")
        
        bills_keys = bills_section.find_all(class_='feature-list__key')
        bills_values = bills_section.find_all(class_='feature-list__value')
        
        for i in range(min(len(bills_keys), len(bills_values))):
            key_text = bills_keys[i].get_text().strip()
            value_text = bills_values[i].get_text().strip()
            
            if key_text == "Bills included?":
                print(f"📋 Bills included: {value_text}")
                analysis_data['Bills Included'] = value_text
                break

async def _check_landlord_type_async(soup, analysis_data: Dict) -> None:
    """Async version of landlord type check"""
    print("\n🔍 CHECKING LANDLORD TYPE...")
    # Add your existing landlord type logic here
    # This is a placeholder - implement based on your existing scraper.py
    pass

async def _check_household_gender_async(soup, analysis_data: Dict) -> None:
    """Async version of household gender check"""
    print("\n🔍 CHECKING HOUSEHOLD GENDER...")
    # Add your existing household gender logic here
    pass

async def _check_advertiser_details_async(soup, analysis_data: Dict) -> None:
    """Async version of advertiser details check"""
    print("\n🔍 CHECKING ADVERTISER DETAILS...")
    # Add your existing advertiser details logic here
    pass

async def _check_listing_status_async(soup, analysis_data: Dict) -> None:
    """Async version of listing status check"""
    print("\n🔍 CHECKING LISTING STATUS...")
    # Add your existing listing status logic here
    pass

async def _check_main_picture_async(soup, analysis_data: Dict) -> None:
    """Async version of main picture check"""
    print("\n🔍 CHECKING MAIN PICTURE...")
    # Add your existing main picture logic here
    pass

async def _check_listing_expired_async(soup, analysis_data: Dict) -> bool:
    """Async version of listing expired check"""
    print("\n🔍 CHECKING IF LISTING EXPIRED...")
    # Add your existing expired listing logic here
    # Return True if expired, False if active
    return False

async def _handle_expired_listing_async(price_section, soup, analysis_data: Dict) -> None:
    """Handle expired listings asynchronously"""
    print("💰 Calculating rental potential for expired listing...")
    analysis_data['_EXPIRED_LISTING'] = True
    analysis_data['All Rooms List'] = []
    
    # Add your existing expired listing logic here

async def _process_room_data_async(price_section, soup, analysis_data: Dict) -> None:
    """Process room data asynchronously"""
    print("\n🏠 PROCESSING ROOM DATA...")
    
    # This is a simplified version - implement based on your existing scraper.py
    keys = price_section.find_all(class_='feature-list__key')
    values = price_section.find_all(class_='feature-list__value')
    
    rooms_list = []
    for i in range(min(len(keys), len(values))):
        key_text = keys[i].get_text().strip()
        value_text = values[i].get_text().strip()
        room_detail = f"{key_text} - {value_text}"
        rooms_list.append(room_detail)
    
    analysis_data['All Rooms List'] = rooms_list
    print(f"📋 Found {len(rooms_list)} room entries")

async def batch_extract_multiple_properties(urls: List[str], max_concurrent: int = 5) -> List[Dict]:
    """
    Extract data from multiple properties concurrently
    This is the key performance improvement - parallel processing
    """
    print(f"🚀 Starting batch extraction of {len(urls)} properties with max {max_concurrent} concurrent requests")
    
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def extract_single_with_semaphore(url: str) -> Dict:
        async with semaphore:
            analysis_data = {'url': url, 'timestamp': datetime.now().isoformat()}
            return await extract_price_section_async(url, analysis_data)
    
    # Create tasks for all URLs
    tasks = [extract_single_with_semaphore(url) for url in urls]
    
    # Execute all tasks concurrently
    start_time = datetime.now()
    results = await asyncio.gather(*tasks, return_exceptions=True)
    end_time = datetime.now()
    
    duration = (end_time - start_time).total_seconds()
    print(f"🎉 Batch extraction completed in {duration:.2f} seconds")
    print(f"📊 Average time per property: {duration/len(urls):.2f} seconds")
    
    # Filter out any exceptions and return successful results
    successful_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"❌ Failed to process {urls[i]}: {result}")
        else:
            successful_results.append(result)
    
    return successful_results

# Cleanup function to call when shutting down
async def cleanup_async_scraper():
    """Clean up resources when shutting down"""
    await session_manager.close()
    print("🧹 Async scraper resources cleaned up")

# Test function
async def test_async_scraper(test_url: str = None):
    """Test the async scraper with a sample URL"""
    if not test_url:
        test_url = "https://www.spareroom.co.uk/flatshare/flatshare_detail.pl?flatshare_id=15208979"
    
    print(f"🧪 Testing async scraper with: {test_url}")
    
    analysis_data = {
        'url': test_url,
        'timestamp': datetime.now().isoformat()
    }
    
    start_time = datetime.now()
    result = await extract_price_section_async(test_url, analysis_data)
    end_time = datetime.now()
    
    duration = (end_time - start_time).total_seconds()
    print(f"⏱️ Async extraction completed in {duration:.2f} seconds")
    
    await cleanup_async_scraper()
    return result

if __name__ == "__main__":
    # Test the async scraper
    asyncio.run(test_async_scraper())