#!/usr/bin/env python3
"""
Simple Oxford HMO Verification
==============================
Check if the main fix worked - are active HMOs now showing as active?
"""

def verify_oxford_fix():
    """Simple verification of Oxford HMO fix"""
    print("🔍 Simple Oxford HMO Integration Verification")
    print("=" * 50)
    
    try:
        from database import SessionLocal
        from hmo_registry.database_models import HMORegistry
        from datetime import date
        
        db = SessionLocal()
        
        print("✅ Connected to database")
        
        # Check Oxford HMO records
        print("\n📊 Oxford HMO Statistics:")
        print("-" * 30)
        
        # Total Oxford records
        total_oxford = db.query(HMORegistry).filter(
            HMORegistry.city == 'oxford'
        ).count()
        print(f"Total Oxford HMO records: {total_oxford}")
        
        # Active licences (not expired)
        today = date.today()
        active_licences = db.query(HMORegistry).filter(
            HMORegistry.city == 'oxford',
            HMORegistry.licence_expiry_date >= today
        ).count()
        print(f"Active licences (not expired): {active_licences}")
        
        # Expired licences
        expired_licences = db.query(HMORegistry).filter(
            HMORegistry.city == 'oxford',
            HMORegistry.licence_expiry_date < today
        ).count()
        print(f"Expired licences: {expired_licences}")
        
        # Licences without expiry date
        no_expiry = db.query(HMORegistry).filter(
            HMORegistry.city == 'oxford',
            HMORegistry.licence_expiry_date.is_(None)
        ).count()
        print(f"Records without expiry date: {no_expiry}")
        
        # Recent updates (from our fix)
        from datetime import datetime, timedelta
        recent_cutoff = datetime.now() - timedelta(hours=1)
        recent_updates = db.query(HMORegistry).filter(
            HMORegistry.city == 'oxford',
            HMORegistry.updated_at >= recent_cutoff
        ).count()
        print(f"Recently updated records (last hour): {recent_updates}")
        
        print("\n📋 Sample Active Records:")
        print("-" * 30)
        
        # Show sample active records
        sample_active = db.query(HMORegistry).filter(
            HMORegistry.city == 'oxford',
            HMORegistry.licence_expiry_date >= today
        ).limit(5).all()
        
        for i, record in enumerate(sample_active, 1):
            expiry_str = record.licence_expiry_date.strftime('%Y-%m-%d') if record.licence_expiry_date else 'No date'
            print(f"{i}. {record.case_number}")
            print(f"   Address: {record.raw_address[:60]}...")
            print(f"   Expires: {expiry_str}")
            print()
        
        # Success assessment
        print("🎯 Integration Success Assessment:")
        print("-" * 40)
        
        if total_oxford >= 3000:
            print("✅ Good number of Oxford records found")
        else:
            print("⚠️ Fewer Oxford records than expected")
        
        if active_licences >= 2900:  # Expect ~3000 active from our processing
            print("✅ High number of active licences - fix likely successful!")
        elif active_licences >= 1000:
            print("⚠️ Moderate number of active licences")  
        else:
            print("❌ Low number of active licences - may need investigation")
        
        active_percentage = (active_licences / total_oxford * 100) if total_oxford > 0 else 0
        print(f"📈 Active licence rate: {active_percentage:.1f}%")
        
        if active_percentage >= 90:
            print("🎉 EXCELLENT - Most licences are active!")
        elif active_percentage >= 70:
            print("✅ GOOD - Majority of licences are active")
        else:
            print("⚠️ Many licences appear expired - may need review")
        
        if recent_updates >= 2000:
            print("✅ Many records were recently updated - our fix ran successfully!")
        
        return {
            'total_oxford': total_oxford,
            'active_licences': active_licences,
            'expired_licences': expired_licences,
            'active_percentage': active_percentage,
            'recent_updates': recent_updates,
            'success': active_percentage >= 70 and total_oxford >= 1000
        }
        
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        return {'success': False, 'error': str(e)}
    
    finally:
        if 'db' in locals():
            db.close()


if __name__ == "__main__":
    result = verify_oxford_fix()
    
    print("\n" + "=" * 50)
    if result.get('success'):
        print("🎉 VERIFICATION PASSED - Oxford HMO integration is working!")
        print("Your active HMOs should now show as active on the map.")
    else:
        print("⚠️ Verification had issues - check the results above")
        
    print("\nNext steps:")
    print("1. Restart your web application")
    print("2. Check your map to see if active HMOs are now showing correctly")
    print("3. The fix updated licence expiry dates from the official register")