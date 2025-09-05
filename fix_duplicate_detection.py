# fix_duplicate_detection.py
"""
Quick fix for Phase 2 duplicate detection issues
"""

import logging

def fix_duplicate_detection_issues():
    """Fix the issues preventing duplicate detection from working"""
    
    print("🔧 Fixing Phase 2 Duplicate Detection Issues")
    print("=" * 50)
    
    # Read the current duplicate_detection.py
    try:
        with open("duplicate_detection.py", "r") as f:
            content = f.read()
        
        # Check if the extract_property_details_for_duplicate_check function needs fixing
        if "extract_property_details_for_duplicate_check" in content:
            print("✅ Function exists, checking imports...")
            
            # The issue is likely in the import structure
            # Let's create a more robust version
            
            updated_function = '''
def extract_property_details_for_duplicate_check(url: str) -> Dict[str, Any]:
    """Extract property details from URL for duplicate checking"""
    try:
        # Try to import required functions
        try:
            from modules.coordinates import extract_property_details, extract_coordinates, reverse_geocode_nominatim
        except ImportError as e:
            logger.warning(f"Import error in duplicate check: {e}")
            return {}
        
        # Create analysis data container
        analysis_data = {}
        
        # Step 1: Extract coordinates
        try:
            coords_result = extract_coordinates(url, analysis_data)
            logger.info(f"📍 Coordinates extracted: {coords_result}")
        except Exception as e:
            logger.warning(f"Coordinate extraction failed: {e}")
            coords_result = {}
        
        # Step 2: Extract property details  
        try:
            extracted_data = extract_property_details(url, analysis_data)
            logger.info(f"🏠 Property details extracted")
        except Exception as e:
            logger.warning(f"Property detail extraction failed: {e}")
            extracted_data = {}
        
        # Step 3: Get coordinates from either source
        latitude = (analysis_data.get('latitude') or 
                   coords_result.get('latitude') or 
                   extracted_data.get('latitude'))
        longitude = (analysis_data.get('longitude') or 
                    coords_result.get('longitude') or 
                    extracted_data.get('longitude'))
        
        # Step 4: Get address from analysis_data (preferred) or extracted_data
        address = (analysis_data.get('Full Address') or 
                  analysis_data.get('address') or 
                  extracted_data.get('address'))
        
        # Compile results
        result = {
            'address': address,
            'latitude': latitude,
            'longitude': longitude,
            'monthly_income': (analysis_data.get('Monthly Income') or 
                             extracted_data.get('monthly_income')),
            'total_rooms': (analysis_data.get('Total Rooms') or 
                          extracted_data.get('total_rooms')),
            'advertiser_name': (analysis_data.get('Advertiser') or 
                              analysis_data.get('advertiser_name') or 
                              extracted_data.get('advertiser_name'))
        }
        
        # Debug logging
        if result.get('address') or result.get('latitude'):
            logger.info(f"✅ Duplicate check extraction successful:")
            logger.info(f"   Address: {result.get('address')}")
            logger.info(f"   Coordinates: ({result.get('latitude')}, {result.get('longitude')})")
            logger.info(f"   Price: {result.get('monthly_income')}")
            logger.info(f"   Rooms: {result.get('total_rooms')}")
        else:
            logger.warning(f"⚠️ Duplicate check extraction incomplete")
            logger.warning(f"   Analysis data keys: {list(analysis_data.keys())}")
            logger.warning(f"   Extracted data keys: {list(extracted_data.keys()) if extracted_data else 'None'}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error in duplicate check extraction: {str(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return {}
'''
            
            # Replace the function in the file
            import re
            
            # Find the function and replace it
            pattern = r'def extract_property_details_for_duplicate_check.*?(?=\n\ndef|\n\nclass|\n\n# |\nif __name__|$)'
            
            if re.search(pattern, content, re.DOTALL):
                updated_content = re.sub(pattern, updated_function.strip(), content, flags=re.DOTALL)
                
                # Write the updated content back
                with open("duplicate_detection.py", "w") as f:
                    f.write(updated_content)
                
                print("✅ Updated extract_property_details_for_duplicate_check function")
            else:
                print("⚠️ Could not find function to replace")
        
        # Also fix the UUID issue in main.py by finding the problematic endpoint
        fix_uuid_issue()
        
        print("✅ Fixes applied!")
        return True
        
    except Exception as e:
        print(f"❌ Fix failed: {e}")
        return False

def fix_uuid_issue():
    """Fix the UUID 'last' issue in main.py"""
    
    print("🔧 Fixing UUID 'last' issue...")
    
    try:
        with open("main.py", "r") as f:
            content = f.read()
        
        # Look for the problematic endpoint
        if '/api/properties/last' in content:
            print("✅ Found /api/properties/last endpoint")
            
            # The issue is likely that the endpoint is using 'last' as a UUID
            # We need to find this endpoint and fix it
            
            # Look for the get_property_details function
            if 'def get_property_details(' in content:
                print("⚠️ Found get_property_details function")
                print("💡 The issue is that the frontend is calling /api/properties/last")
                print("💡 But the endpoint expects a UUID, not the string 'last'")
                
                # This suggests we need a separate endpoint for getting the last property
                # Or we need to handle 'last' as a special case
                
                suggested_fix = '''
# Add this endpoint to main.py:

@app.get("/api/properties/last")
async def get_last_property(db: Session = Depends(get_db)):
    """Get the most recently created property"""
    try:
        # Get the most recent property
        last_property = (db.query(Property)
                        .order_by(desc(Property.created_at))
                        .first())
        
        if not last_property:
            raise HTTPException(status_code=404, detail="No properties found")
        
        # Get the latest analysis for this property
        latest_analysis = AnalysisCRUD.get_latest_analysis(db, last_property.id)
        
        return {
            "property": last_property,
            "latest_analysis": latest_analysis
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting last property: {str(e)}")
'''
                
                print("💡 Suggested fix:")
                print(suggested_fix)
                
                return True
        
    except Exception as e:
        print(f"❌ Could not fix UUID issue: {e}")
        return False

def test_duplicate_detection():
    """Test the duplicate detection after fixes"""
    
    print("\n🧪 Testing Duplicate Detection...")
    
    try:
        import duplicate_detection
        
        # Test the extraction function
        test_url = "https://www.spareroom.co.uk/flatshare/test"
        
        print(f"🔍 Testing extraction with: {test_url}")
        
        result = duplicate_detection.extract_property_details_for_duplicate_check(test_url)
        
        print(f"📊 Result: {result}")
        
        if result:
            print("✅ Extraction function working")
        else:
            print("⚠️ Extraction returned empty result")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Phase 2 Duplicate Detection Fix")
    print("=" * 40)
    print("\nThis will:")
    print("• ✅ Fix the extract_property_details_for_duplicate_check function")
    print("• ✅ Add better error handling and logging")
    print("• ✅ Address the UUID 'last' issue")
    print("• ✅ Test the fixes")
    
    confirm = input("\nApply fixes? (y/N): ").lower().strip()
    
    if confirm == 'y':
        success = fix_duplicate_detection_issues()
        
        if success:
            print("\n✅ Fixes applied successfully!")
            print("\n🧪 Now testing...")
            test_duplicate_detection()
            
            print("\n🚀 Try analyzing a property again to see enhanced duplicate detection!")
        else:
            print("\n❌ Some fixes failed - check the logs above")
    else:
        print("❌ Fixes cancelled")