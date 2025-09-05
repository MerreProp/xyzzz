# test_phase2_data.py
"""
Generate realistic test data to demonstrate Phase 2 proximity logic
Creates test scenarios that showcase different proximity detection cases
"""

import requests
import json
from datetime import datetime
import time

# Test scenarios designed to showcase Phase 2 features
TEST_SCENARIOS = [
    {
        "name": "Same Building - Different Units",
        "description": "Same landlord, same building, different flat numbers",
        "properties": [
            {
                "url": "https://www.spareroom.co.uk/flatshare/test_same_building_1",
                "address": "123 High Street, Flat A, Oxford OX1 1AA",
                "latitude": 51.7520,
                "longitude": -1.2577,
                "monthly_income": 500,
                "total_rooms": 4,
                "advertiser": "John Smith Properties"
            },
            {
                "url": "https://www.spareroom.co.uk/flatshare/test_same_building_2", 
                "address": "123 High Street, Flat B, Oxford OX1 1AA",
                "latitude": 51.7521,  # ~11m apart
                "longitude": -1.2578,
                "monthly_income": 480,
                "total_rooms": 4,
                "advertiser": "John Smith Properties"
            }
        ],
        "expected": {
            "distance": "~11m",
            "proximity_level": "same_building",
            "confidence_boost": "15%",
            "recommendation": "user_choice",
            "reason": "Same landlord + very close proximity"
        }
    },
    {
        "name": "Portfolio Properties - Same Block",
        "description": "Same landlord, different houses on same street", 
        "properties": [
            {
                "url": "https://www.spareroom.co.uk/flatshare/test_portfolio_1",
                "address": "45 Oak Street, Oxford OX2 2BB",
                "latitude": 51.7530,
                "longitude": -1.2580,
                "monthly_income": 650,
                "total_rooms": 5,
                "advertiser": "Premier Student Lets"
            },
            {
                "url": "https://www.spareroom.co.uk/flatshare/test_portfolio_2",
                "address": "47 Oak Street, Oxford OX2 2BB", 
                "latitude": 51.7532,  # ~67m apart
                "longitude": -1.2585,
                "monthly_income": 600,
                "total_rooms": 4,
                "advertiser": "Premier Student Lets"
            }
        ],
        "expected": {
            "distance": "~67m",
            "proximity_level": "same_block",
            "confidence_boost": "10%", 
            "recommendation": "user_choice",
            "reason": "Portfolio properties - same landlord"
        }
    },
    {
        "name": "Same Building - Different Landlords",
        "description": "Very close properties but different landlords",
        "properties": [
            {
                "url": "https://www.spareroom.co.uk/flatshare/test_building_diff_1",
                "address": "78 Mill Lane, Oxford OX3 3CC",
                "latitude": 51.7540,
                "longitude": -1.2590,
                "monthly_income": 400,
                "total_rooms": 3,
                "advertiser": "Alice Johnson"
            },
            {
                "url": "https://www.spareroom.co.uk/flatshare/test_building_diff_2",
                "address": "78 Mill Lane, Flat 2, Oxford OX3 3CC",
                "latitude": 51.7540,  # ~15m apart
                "longitude": -1.2591,
                "monthly_income": 420,
                "total_rooms": 3,
                "advertiser": "Bob Wilson"
            }
        ],
        "expected": {
            "distance": "~15m",
            "proximity_level": "same_building",
            "confidence_boost": "8%",
            "recommendation": "user_choice",
            "reason": "Very close despite different landlords"
        }
    },
    {
        "name": "Far Apart Properties",
        "description": "Properties in different areas of the city",
        "properties": [
            {
                "url": "https://www.spareroom.co.uk/flatshare/test_far_1",
                "address": "12 North Street, Oxford OX4 4DD",
                "latitude": 51.7450,
                "longitude": -1.2400,
                "monthly_income": 550,
                "total_rooms": 4,
                "advertiser": "City Properties"
            },
            {
                "url": "https://www.spareroom.co.uk/flatshare/test_far_2",
                "address": "89 South Road, Oxford OX1 5EE",
                "latitude": 51.7600,  # ~1.8km apart
                "longitude": -1.2800,
                "monthly_income": 580,
                "total_rooms": 4,
                "advertiser": "City Properties"
            }
        ],
        "expected": {
            "distance": "~1800m",
            "proximity_level": "different_area",
            "confidence_penalty": "10%",
            "recommendation": "separate",
            "reason": "Properties far apart despite same advertiser"
        }
    },
    {
        "name": "Exact Address Match",
        "description": "Same exact address - likely same property, different rooms",
        "properties": [
            {
                "url": "https://www.spareroom.co.uk/flatshare/test_exact_1",
                "address": "56 Victoria Road, Oxford OX2 6FF",
                "latitude": 51.7510,
                "longitude": -1.2560,
                "monthly_income": 475,
                "total_rooms": 6,
                "advertiser": "Oxford Student Housing"
            },
            {
                "url": "https://www.spareroom.co.uk/flatshare/test_exact_2",
                "address": "56 Victoria Road, Oxford OX2 6FF",
                "latitude": 51.7511,  # ~8m apart (GPS variance)
                "longitude": -1.2561,
                "monthly_income": 450,
                "total_rooms": 6,
                "advertiser": "Oxford Student Housing"
            }
        ],
        "expected": {
            "distance": "~8m",
            "proximity_level": "same_address",
            "confidence_boost": "20%",
            "recommendation": "user_choice",
            "reason": "Exact address match with same landlord"
        }
    }
]

def test_duplicate_detection_api(base_url="http://localhost:8000"):
    """Test the duplicate detection API with realistic scenarios"""
    
    print("🧪 Phase 2 Duplicate Detection Test Suite")
    print("=" * 55)
    print(f"\nTesting against: {base_url}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    for i, scenario in enumerate(TEST_SCENARIOS, 1):
        print(f"\n{'='*55}")
        print(f"🔬 TEST {i}: {scenario['name']}")
        print(f"📋 {scenario['description']}")
        print("=" * 55)
        
        scenario_results = test_scenario(scenario, base_url)
        results.append({
            "scenario": scenario["name"],
            "results": scenario_results
        })
        
        # Wait between tests to avoid overwhelming the system
        time.sleep(2)
    
    # Print summary
    print("\n" + "=" * 55)
    print("📊 TEST SUMMARY")
    print("=" * 55)
    
    for result in results:
        print(f"\n✅ {result['scenario']}")
        if result['results']:
            for test_result in result['results']:
                print(f"   📈 {test_result}")
        else:
            print(f"   ⚠️ No results captured")
    
    print(f"\n🎯 Tested {len(TEST_SCENARIOS)} scenarios with {sum(len(s['properties']) for s in TEST_SCENARIOS)} properties")
    print("💡 Check your server logs for detailed proximity calculations!")

def test_scenario(scenario, base_url):
    """Test a single scenario"""
    
    scenario_results = []
    properties = scenario["properties"]
    
    # Test each property in the scenario
    for j, prop in enumerate(properties):
        print(f"\n🏠 Property {j+1}: {prop['address']}")
        print(f"📍 Coordinates: ({prop['latitude']}, {prop['longitude']})")
        print(f"💰 Rent: £{prop['monthly_income']}/month")
        print(f"🏠 Rooms: {prop['total_rooms']}")
        print(f"👤 Advertiser: {prop['advertiser']}")
        
        try:
            # Test the analyze endpoint
            response = requests.post(
                f"{base_url}/api/analyze",
                json={"url": prop["url"]},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Analysis started: {result.get('task_id', 'Unknown')}")
                print(f"📝 Message: {result.get('message', 'No message')}")
                
                # Check if duplicate detection occurred
                if 'duplicate' in result.get('message', '').lower():
                    print("🎯 DUPLICATE DETECTION TRIGGERED!")
                    scenario_results.append(f"Property {j+1}: Duplicate detection active")
                else:
                    scenario_results.append(f"Property {j+1}: Analysis completed")
                
            else:
                print(f"❌ Request failed: {response.status_code}")
                print(f"📝 Response: {response.text}")
                scenario_results.append(f"Property {j+1}: Request failed ({response.status_code})")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error: {e}")
            scenario_results.append(f"Property {j+1}: Network error")
        
        # Small delay between properties
        time.sleep(1)
    
    print(f"\n🎯 Expected Results for '{scenario['name']}':")
    expected = scenario["expected"]
    print(f"   📏 Distance: {expected['distance']}")
    print(f"   🏘️ Proximity: {expected['proximity_level']}")
    print(f"   📈 Confidence: {expected.get('confidence_boost', expected.get('confidence_penalty', 'No change'))}")
    print(f"   💡 Recommendation: {expected['recommendation']}")
    print(f"   📋 Reason: {expected['reason']}")
    
    return scenario_results

def test_direct_proximity_calculation():
    """Test proximity calculations directly without API calls"""
    
    print("\n🧮 Direct Proximity Calculation Tests")
    print("=" * 45)
    
    try:
        from duplicate_detection import calculate_enhanced_geographic_score, apply_proximity_adjustments
        
        for i, scenario in enumerate(TEST_SCENARIOS, 1):
            print(f"\n📐 Test {i}: {scenario['name']}")
            
            props = scenario["properties"]
            if len(props) >= 2:
                prop1, prop2 = props[0], props[1]
                
                # Test geographic calculation
                geo_score, geo_factors = calculate_enhanced_geographic_score(
                    prop1["latitude"], prop1["longitude"],
                    prop2["latitude"], prop2["longitude"],
                    prop1["address"], prop2["address"]
                )
                
                print(f"   📍 Distance: {geo_factors.get('distance_meters', 'N/A'):.1f}m")
                print(f"   🏘️ Proximity: {geo_factors.get('proximity_level', 'Unknown')}")
                print(f"   📊 Geo Score: {geo_score:.3f}")
                
                # Test advertiser similarity
                advertiser_sim = 1.0 if prop1["advertiser"] == prop2["advertiser"] else 0.0
                
                # Test confidence adjustments  
                base_confidence = 0.65  # Example base confidence
                adjusted_conf, adjustments = apply_proximity_adjustments(
                    base_confidence, geo_factors, advertiser_sim
                )
                
                print(f"   📈 Base Confidence: {base_confidence:.0%}")
                print(f"   📈 Adjusted Confidence: {adjusted_conf:.0%}")
                print(f"   🔧 Adjustments: {len(adjustments.get('adjustments_applied', []))}")
                
                for adj in adjustments.get('adjustments_applied', []):
                    print(f"      • {adj.get('reason', 'Unknown adjustment')}")
        
        print("\n✅ Direct calculation tests completed!")
        
    except ImportError as e:
        print(f"❌ Could not import functions: {e}")
        print("💡 Make sure duplicate_detection.py is properly updated")

def create_test_data_file():
    """Create a JSON file with test data for reference"""
    
    filename = f"phase2_test_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    test_data = {
        "generated_at": datetime.now().isoformat(),
        "description": "Phase 2 Proximity Logic Test Data",
        "scenarios": TEST_SCENARIOS
    }
    
    with open(filename, 'w') as f:
        json.dump(test_data, f, indent=2)
    
    print(f"📄 Test data saved to: {filename}")
    return filename

if __name__ == "__main__":
    print("🧪 Phase 2 Test Data Generator & Tester")
    print("=" * 50)
    
    print("\nAvailable test options:")
    print("1. 🌐 Test with API calls (requires running server)")
    print("2. 🧮 Test proximity calculations directly")
    print("3. 📄 Generate test data file only")
    print("4. 🚀 Run all tests")
    
    choice = input("\nSelect option (1-4): ").strip()
    
    if choice == "1":
        base_url = input("Enter base URL (default: http://localhost:8000): ").strip() or "http://localhost:8000"
        test_duplicate_detection_api(base_url)
        
    elif choice == "2":
        test_direct_proximity_calculation()
        
    elif choice == "3":
        create_test_data_file()
        
    elif choice == "4":
        print("🚀 Running all tests...")
        create_test_data_file()
        test_direct_proximity_calculation()
        
        print("\n" + "=" * 50)
        api_test = input("Run API tests too? (y/N): ").lower().strip() == 'y'
        if api_test:
            base_url = input("Enter base URL (default: http://localhost:8000): ").strip() or "http://localhost:8000"
            test_duplicate_detection_api(base_url)
        
    else:
        print("❌ Invalid choice")
    
    print("\n🎯 Testing complete!")