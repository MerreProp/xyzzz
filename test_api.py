#!/usr/bin/env python3
"""
Test script for the FastAPI HMO Analyser API
"""

import requests
import json
import time
from datetime import datetime

# API base URL
BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test the health check endpoint"""
    print("🔍 Testing health check endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        response.raise_for_status()
        
        data = response.json()
        print(f"✅ Health check passed!")
        print(f"   Status: {data['status']}")
        print(f"   Active tasks: {data['active_tasks']}")
        print(f"   Completed analyses: {data['completed_analyses']}")
        return True
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_root_endpoint():
    """Test the root endpoint"""
    print("\n🔍 Testing root endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/")
        response.raise_for_status()
        
        data = response.json()
        print(f"✅ Root endpoint working!")
        print(f"   API: {data['message']}")
        print(f"   Version: {data['version']}")
        return True
        
    except Exception as e:
        print(f"❌ Root endpoint failed: {e}")
        return False

def test_property_analysis(test_url):
    """Test property analysis with a real SpareRoom URL"""
    print(f"\n🔍 Testing property analysis...")
    print(f"   URL: {test_url}")
    
    try:
        # Start analysis
        print("📤 Starting analysis...")
        response = requests.post(
            f"{BASE_URL}/api/analyze",
            json={"url": test_url},
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        
        data = response.json()
        task_id = data["task_id"]
        
        print(f"✅ Analysis started!")
        print(f"   Task ID: {task_id}")
        print(f"   Status: {data['status']}")
        
        # Monitor progress
        print(f"\n👀 Monitoring progress...")
        max_attempts = 30  # Maximum 5 minutes (30 * 10 seconds)
        attempt = 0
        
        while attempt < max_attempts:
            try:
                status_response = requests.get(f"{BASE_URL}/api/analysis/{task_id}")
                status_response.raise_for_status()
                
                status_data = status_response.json()
                status = status_data["status"]
                progress = status_data["progress"]
                
                print(f"   Status: {status}")
                
                # Show progress details
                for step, step_status in progress.items():
                    emoji = {
                        "pending": "⏳",
                        "running": "🔄", 
                        "completed": "✅",
                        "failed": "❌",
                        "skipped": "⏭️"
                    }.get(step_status, "❓")
                    
                    print(f"   {emoji} {step}: {step_status}")
                
                if status == "completed":
                    print(f"\n🎉 Analysis completed successfully!")
                    
                    # Show results summary
                    result = status_data.get("result", {})
                    if result:
                        print(f"\n📊 Results Summary:")
                        print(f"   Property ID: {result.get('Property ID', 'N/A')}")
                        print(f"   Address: {result.get('Full Address', 'N/A')}")
                        print(f"   Total Rooms: {result.get('Total Rooms', 'N/A')}")
                        print(f"   Available Rooms: {result.get('Available Rooms', 'N/A')}")
                        print(f"   Monthly Income: £{result.get('Monthly Income', 'N/A')}")
                        print(f"   Annual Income: £{result.get('Annual Income', 'N/A')}")
                        print(f"   Bills Included: {result.get('Bills Included', 'N/A')}")
                        print(f"   Meets Requirements: {result.get('Meets Requirements', 'N/A')}")
                        
                        if result.get('Latitude') and result.get('Longitude'):
                            print(f"   Location: {result['Latitude']}, {result['Longitude']}")
                    
                    return task_id
                
                elif status == "failed":
                    print(f"\n❌ Analysis failed!")
                    error = status_data.get("error")
                    if error:
                        print(f"   Error: {error}")
                    return None
                
                # Wait before next check
                time.sleep(10)
                attempt += 1
                
            except Exception as e:
                print(f"❌ Error checking status: {e}")
                time.sleep(10)
                attempt += 1
        
        print(f"\n⏰ Analysis timed out after {max_attempts * 10} seconds")
        return None
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return None

def test_properties_list():
    """Test getting all properties"""
    print(f"\n🔍 Testing properties list endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/properties")
        response.raise_for_status()
        
        properties = response.json()
        
        print(f"✅ Properties list retrieved!")
        print(f"   Total properties: {len(properties)}")
        
        if properties:
            print(f"\n📋 Properties:")
            for i, prop in enumerate(properties, 1):
                print(f"   {i}. {prop.get('address', 'N/A')} - £{prop.get('monthly_income', 'N/A')}/month")
        
        return True
        
    except Exception as e:
        print(f"❌ Properties list failed: {e}")
        return False

def test_excel_export(task_id):
    """Test Excel export functionality"""
    if not task_id:
        print(f"\n⏭️ Skipping Excel export test (no task_id)")
        return False
    
    print(f"\n🔍 Testing Excel export...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/export/{task_id}")
        response.raise_for_status()
        
        # Save the Excel file
        filename = f"test_export_{task_id}.xlsx"
        with open(filename, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ Excel export successful!")
        print(f"   File saved as: {filename}")
        print(f"   File size: {len(response.content)} bytes")
        
        return True
        
    except Exception as e:
        print(f"❌ Excel export failed: {e}")
        return False

def main():
    """Run all API tests"""
    print("🚀 Starting FastAPI HMO Analyser API Tests")
    print("=" * 60)
    
    # Test basic endpoints
    if not test_health_check():
        print("\n❌ Basic health check failed. Is the API running?")
        print("   Run: python main.py")
        return
    
    if not test_root_endpoint():
        print("\n❌ Root endpoint failed")
        return
    
    # Test property analysis with a sample URL
    print("\n" + "=" * 60)
    print("🏠 PROPERTY ANALYSIS TEST")
    print("=" * 60)
    
    # You can replace this with a real SpareRoom URL for testing
    test_url = input("\n📝 Enter a SpareRoom URL to test (or press Enter to skip): ").strip()
    
    task_id = None
    if test_url:
        task_id = test_property_analysis(test_url)
    else:
        print("⏭️ Skipping property analysis test")
    
    # Test other endpoints
    test_properties_list()
    test_excel_export(task_id)
    
    print("\n" + "=" * 60)
    print("🎉 API Testing Complete!")
    print("=" * 60)
    
    if task_id:
        print(f"\n💡 You can now:")
        print(f"   - View analysis details: GET {BASE_URL}/api/analysis/{task_id}")
        print(f"   - Download Excel: GET {BASE_URL}/api/export/{task_id}")
        print(f"   - View all properties: GET {BASE_URL}/api/properties")

if __name__ == "__main__":
    main()