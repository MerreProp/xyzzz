# test_phase4_fixed.py
"""
Test script for Phase 4 enhanced API responses - FIXED FOR PORT 8001
"""

import requests
import json
import time
from typing import Dict, Any

# 🔧 FIXED: Use port 8001 instead of 8000
API_BASE_URL = "http://localhost:8001"

def test_enhanced_duplicate_response():
    """Test enhanced duplicate detection API"""
    
    print("🧪 Testing Phase 4 Enhanced API Responses")
    print("=" * 50)
    
    # Test URLs that might have duplicates (replace with real URLs from your data)
    test_urls = [
        "https://www.spareroom.co.uk/flatshare/flatshare_detail.pl?flatshare_id=15555667",
        "https://www.spareroom.co.uk/flatshare/flatshare_detail.pl?flatshare_id=15123456",
        "https://www.spareroom.co.uk/flatshare/flatshare_detail.pl?flatshare_id=15789012"
    ]
    
    for i, test_url in enumerate(test_urls, 1):
        print(f"\n🔍 Test {i}: {test_url}")
        print("-" * 40)
        
        try:
            response = requests.post(
                f"{API_BASE_URL}/api/analyze",  # 🔧 FIXED: Use correct port
                json={"url": test_url},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("duplicate_detected"):
                    print("✅ Duplicate detected - checking Phase 4 enhancements...")
                    
                    duplicate_data = data.get("duplicate_data", {})
                    
                    # Check Phase 4 enhancements
                    check_phase4_enhancements(duplicate_data)
                    
                elif data.get("status") == "completed":
                    print("ℹ️  Analysis completed - no duplicates detected")
                    print("   (Try with a property that has potential duplicates)")
                    
                elif data.get("status") == "queued":
                    print("⏳ Analysis queued...")
                    # Could poll for completion here
                    
                else:
                    print(f"📊 Response status: {data.get('status', 'unknown')}")
                    
            else:
                print(f"❌ API request failed: {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                
        except requests.exceptions.Timeout:
            print("⏰ Request timed out - analysis may be taking longer")
        except requests.exceptions.ConnectionError:
            print(f"❌ Connection failed - is the server running on {API_BASE_URL}?")
        except Exception as e:
            print(f"❌ Test failed: {e}")
        
        if i < len(test_urls):
            print(f"\n⏳ Waiting 2 seconds before next test...")
            time.sleep(2)

def check_phase4_enhancements(duplicate_data: Dict[str, Any]):
    """Check if Phase 4 enhancements are present in the response"""
    
    print("\n📋 Phase 4 Enhancement Check:")
    
    # Check for Phase 4 specific fields
    enhancements = {
        "nearby_properties": "nearby_properties" in duplicate_data,
        "existing_property_context": "existing_property" in duplicate_data,
        "new_property_context": "new_property" in duplicate_data,
        "decision_factors": "decision_factors" in duplicate_data,
        "confidence_explanation": "confidence_explanation" in duplicate_data
    }
    
    for feature, present in enhancements.items():
        status = "✅" if present else "❌"
        print(f"  {status} {feature.replace('_', ' ').title()}")
    
    # Show sample data if present
    show_sample_data(duplicate_data)
    
    # Overall assessment
    present_count = sum(enhancements.values())
    total_count = len(enhancements)
    
    print(f"\n📊 Phase 4 Integration: {present_count}/{total_count} features present")
    
    if present_count == total_count:
        print("🎉 Phase 4 fully integrated!")
    elif present_count >= 3:
        print("👍 Phase 4 mostly integrated - check missing features")
    else:
        print("⚠️  Phase 4 integration incomplete - check main.py updates")

def show_sample_data(duplicate_data: Dict[str, Any]):
    """Show sample of Phase 4 enhanced data"""
    
    print("\n📝 Sample Enhanced Data:")
    
    # Nearby properties
    nearby = duplicate_data.get("nearby_properties", [])
    if nearby:
        print(f"\n🏘️  Found {len(nearby)} nearby properties:")
        for prop in nearby[:3]:  # Show first 3
            distance = prop.get('distance', 'N/A')
            address = prop.get('address', 'N/A')[:50] + "..." if len(prop.get('address', '')) > 50 else prop.get('address', 'N/A')
            advertiser = prop.get('advertiser', 'N/A')
            print(f"    • {distance}m - {address} ({advertiser})")
    
    # Confidence explanation
    explanation = duplicate_data.get("confidence_explanation")
    if explanation:
        print(f"\n💡 Confidence Explanation:")
        print(f"    {explanation}")
    
    # Decision factors
    decision_factors = duplicate_data.get("decision_factors", {})
    if decision_factors:
        print(f"\n🎯 Decision Factors:")
        
        high_factors = decision_factors.get("high_confidence_factors", [])
        if high_factors:
            print(f"    High confidence: {', '.join(high_factors)}")
        
        concerns = decision_factors.get("concerns", [])
        if concerns:
            print(f"    Concerns: {', '.join(concerns)}")
        
        distance_analysis = decision_factors.get("distance_analysis", {})
        if distance_analysis and "analysis" in distance_analysis:
            print(f"    Distance: {distance_analysis['analysis']}")
    
    # Property context comparison
    existing_prop = duplicate_data.get("existing_property", {})
    new_prop = duplicate_data.get("new_property", {})
    
    if existing_prop or new_prop:
        print(f"\n🏠 Property Comparison:")
        
        if existing_prop:
            rooms = existing_prop.get("total_rooms", "N/A")
            income = existing_prop.get("monthly_income")
            income_str = f"£{income}" if income else "N/A"
            print(f"    Existing: {rooms} rooms, {income_str}/month")
        
        if new_prop:
            est_rooms = new_prop.get("estimated_rooms", "N/A")
            print(f"    New: ~{est_rooms} rooms (estimated)")

def test_api_health():
    """Test if the API is running and accessible"""
    
    print("🔍 Testing API Health...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/health", timeout=5)  # 🔧 FIXED: Use correct port
        if response.status_code == 200:
            print("✅ API is healthy and accessible")
            return True
        else:
            print(f"⚠️  API responded with status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to API - is it running on {API_BASE_URL}?")
        return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_specific_duplicate_scenario():
    """Test a specific duplicate detection scenario"""
    
    print("\n🎯 Testing Specific Duplicate Scenario")
    print("-" * 40)
    
    # Example test with known duplicate properties
    scenario = {
        "description": "Same property, different URLs",
        "url1": "https://www.spareroom.co.uk/flatshare/flatshare_detail.pl?flatshare_id=15555667",
        "url2": "https://www.spareroom.co.uk/flatshare/flatshare_detail.pl?flatshare_id=15555668",
        "expected_confidence": "> 0.7"
    }
    
    print(f"📋 Scenario: {scenario['description']}")
    print(f"🔗 Testing URL: {scenario['url2']}")
    print(f"🎯 Expected: {scenario['expected_confidence']} confidence")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/analyze",  # 🔧 FIXED: Use correct port
            json={"url": scenario["url2"]},
            timeout=45
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("duplicate_detected"):
                matches = data.get("duplicate_data", {}).get("potential_matches", [])
                if matches:
                    confidence = matches[0].get("confidence_score", 0)
                    print(f"✅ Duplicate detected with confidence: {confidence:.2%}")
                    
                    # Check if Phase 4 data is present
                    duplicate_data = data.get("duplicate_data", {})
                    phase4_features = [
                        "nearby_properties",
                        "confidence_explanation", 
                        "decision_factors"
                    ]
                    
                    present_features = [f for f in phase4_features if f in duplicate_data]
                    print(f"📊 Phase 4 features present: {len(present_features)}/{len(phase4_features)}")
                    
                    return True
                else:
                    print("⚠️  Duplicate detected but no matches in response")
            else:
                print("ℹ️  No duplicates detected for this scenario")
        else:
            print(f"❌ Request failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Scenario test failed: {e}")
    
    return False

def benchmark_response_times():
    """Benchmark API response times with Phase 4 enhancements"""
    
    print("\n⏱️  Benchmarking Response Times")
    print("-" * 40)
    
    test_url = "https://www.spareroom.co.uk/flatshare/flatshare_detail.pl?flatshare_id=15555667"
    times = []
    
    for i in range(3):
        print(f"🔄 Test {i+1}/3...")
        
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{API_BASE_URL}/api/analyze",  # 🔧 FIXED: Use correct port
                json={"url": test_url},
                timeout=60
            )
            
            if response.status_code == 200:
                end_time = time.time()
                duration = end_time - start_time
                times.append(duration)
                print(f"   ✅ Completed in {duration:.2f} seconds")
            else:
                print(f"   ❌ Failed with status: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Failed: {e}")
        
        if i < 2:  # Don't wait after last test
            time.sleep(3)
    
    if times:
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        print(f"\n📊 Performance Summary:")
        print(f"   Average: {avg_time:.2f}s")
        print(f"   Fastest: {min_time:.2f}s") 
        print(f"   Slowest: {max_time:.2f}s")
        
        if avg_time < 10:
            print("   🚀 Performance: Excellent")
        elif avg_time < 20:
            print("   👍 Performance: Good")
        else:
            print("   ⚠️  Performance: Consider optimization")

def main():
    """Main test function"""
    
    print("🧪 Phase 4 Enhanced API Testing Suite")
    print("=" * 50)
    print(f"Testing against: {API_BASE_URL}")
    print("Testing enhanced duplicate detection with nearby properties context")
    print()
    
    # Step 1: Health check
    if not test_api_health():
        print(f"\n❌ Cannot proceed - API not accessible at {API_BASE_URL}")
        print("💡 Make sure your FastAPI server is running:")
        print("   python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8001")
        return
    
    print()
    
    # Step 2: Test enhanced duplicate response
    test_enhanced_duplicate_response()
    
    # Step 3: Test specific scenario
    test_specific_duplicate_scenario()
    
    # Step 4: Benchmark performance
    benchmark_response_times()
    
    print("\n" + "=" * 50)
    print("🎉 Phase 4 Testing Complete!")
    print("=" * 50)
    
    print("\n💡 Next Steps:")
    print("   1. If Phase 4 features are missing, check main.py integration")
    print("   2. Test with your Phase 3 enhanced modal UI")
    print("   3. Try analyzing properties with known duplicates")
    print("   4. Proceed to Phase 5: Database Schema Changes")

if __name__ == "__main__":
    main()