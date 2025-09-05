# fix_last_endpoint.py
"""
Quick fix for the UUID 'last' endpoint issue
"""

def fix_last_endpoint():
    """Add the missing /api/properties/last endpoint to main.py"""
    
    print("🔧 Fixing UUID 'last' endpoint issue...")
    
    try:
        with open("main.py", "r") as f:
            content = f.read()
        
        # Check if the endpoint already exists
        if "@app.get(\"/api/properties/last\")" in content:
            print("✅ /api/properties/last endpoint already exists")
            return True
        
        # Find a good place to insert the new endpoint
        # Look for other property endpoints
        insert_point = None
        
        if "@app.get(\"/api/properties/{property_id}\")" in content:
            # Insert before the parameterized endpoint
            pattern = "@app.get(\"/api/properties/{property_id}\")"
            insert_point = content.find(pattern)
        elif "def get_property_details" in content:
            # Insert before the get_property_details function
            pattern = "def get_property_details"
            insert_point = content.find(pattern)
        
        if insert_point:
            # Create the new endpoint
            new_endpoint = '''
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
            
            # Insert the new endpoint
            updated_content = content[:insert_point] + new_endpoint + content[insert_point:]
            
            # Write back to file
            with open("main.py", "w") as f:
                f.write(updated_content)
            
            print("✅ Added /api/properties/last endpoint to main.py")
            print("💡 The 500 error should be fixed now")
            return True
        else:
            print("⚠️ Could not find suitable insertion point")
            print("💡 Please manually add the endpoint to main.py:")
            print('''
@app.get("/api/properties/last")
async def get_last_property(db: Session = Depends(get_db)):
    """Get the most recently created property"""
    try:
        last_property = (db.query(Property)
                        .order_by(desc(Property.created_at))
                        .first())
        
        if not last_property:
            raise HTTPException(status_code=404, detail="No properties found")
        
        latest_analysis = AnalysisCRUD.get_latest_analysis(db, last_property.id)
        
        return {
            "property": last_property,
            "latest_analysis": latest_analysis
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting last property: {str(e)}")
''')
            return False
    
    except Exception as e:
        print(f"❌ Could not fix endpoint: {e}")
        return False

if __name__ == "__main__":
    print("🔧 UUID 'Last' Endpoint Fix")
    print("=" * 30)
    
    success = fix_last_endpoint()
    
    if success:
        print("\n✅ Fix applied successfully!")
        print("\n🔄 Please restart your API server to apply the changes:")
        print("   1. Stop the server (Ctrl+C)")
        print("   2. Restart: python3 -m uvicorn main:app --reload")
        print("\n🧪 Then test property analysis again!")
    else:
        print("\n❌ Could not apply automatic fix")
        print("💡 Please manually add the endpoint as shown above")