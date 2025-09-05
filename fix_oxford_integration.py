#!/usr/bin/env python3
"""
Complete Oxford HMO Integration Fix
===================================

This script provides a complete solution for fixing the Oxford HMO database
integration issues, including:

1. Enhanced address matching between different data formats
2. Processing the HMO Register Copy Excel file correctly
3. Updating database records with correct active/expired status
4. Verification and testing tools

Usage:
    python fix_oxford_integration.py
"""

import os
import sys
import logging
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_requirements() -> bool:
    """Check if all required files and dependencies are available"""
    print("🔍 Checking requirements...")
    
    required_files = [
        "HMO Register Copy.xlsx"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("❌ Missing required files:")
        for file in missing_files:
            print(f"   - {file}")
        print("\nPlease ensure all files are in the current directory.")
        return False
    
    # Check Python dependencies
    required_modules = [
        'pandas', 'numpy', 'openpyxl', 'sqlalchemy'
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print("❌ Missing required Python modules:")
        for module in missing_modules:
            print(f"   - {module}")
        print("\nInstall them with: pip install " + " ".join(missing_modules))
        return False
    
    print("✅ All requirements satisfied")
    return True


def run_complete_fix() -> Dict[str, Any]:
    """Run the complete Oxford HMO integration fix"""
    print("🚀 Starting Complete Oxford HMO Integration Fix")
    print("=" * 60)
    
    results = {
        'start_time': datetime.now(),
        'steps_completed': [],
        'errors': [],
        'success': False
    }
    
    try:
        # Step 1: Process the HMO Register Copy file
        print("\n📊 Step 1: Processing HMO Register Copy Excel file...")
        from oxford_register_processor import OxfordRegisterProcessor
        
        processor = OxfordRegisterProcessor()
        register_result = processor.process_register_file()
        
        if register_result['success']:
            results['steps_completed'].append('register_processing')
            results['register_stats'] = register_result
            print("   ✅ HMO Register processing completed")
        else:
            results['errors'].append(f"Register processing failed: {register_result.get('error', 'Unknown error')}")
            print(f"   ❌ Register processing failed: {register_result.get('error')}")
            return results
        
        # Step 2: Run enhanced address matching
        print("\n🔗 Step 2: Running enhanced address matching...")
        from enhanced_oxford_matcher import update_oxford_hmo_integration
        
        matching_result = update_oxford_hmo_integration()
        
        if matching_result:
            results['steps_completed'].append('address_matching')
            print("   ✅ Enhanced address matching completed")
        else:
            results['errors'].append("Address matching failed")
            print("   ❌ Address matching failed")
            # Continue anyway as register processing might have fixed the main issue
        
        # Step 3: Verify the results
        print("\n🔍 Step 3: Verifying results...")
        verification_result = verify_oxford_integration()
        
        results['verification'] = verification_result
        results['steps_completed'].append('verification')
        
        if verification_result['active_licences'] > 0:
            print("   ✅ Verification passed - Active licences found")
            results['success'] = True
        else:
            print("   ⚠️ Warning - No active licences found, please check data")
        
        # Step 4: Generate report
        print("\n📋 Step 4: Generating integration report...")
        report = generate_integration_report(results)
        
        print(f"   📄 Report saved to: {report['file_path']}")
        results['report_file'] = report['file_path']
        results['steps_completed'].append('report_generation')
        
        results['end_time'] = datetime.now()
        results['duration'] = results['end_time'] - results['start_time']
        
        return results
        
    except Exception as e:
        logger.error(f"Error during complete fix: {e}")
        results['errors'].append(str(e))
        results['end_time'] = datetime.now()
        return results


def verify_oxford_integration() -> Dict[str, Any]:
    """Verify that the Oxford integration is working correctly"""
    print("   Checking database for Oxford HMO records...")
    
    try:
        from database import SessionLocal
        from hmo_registry.database_models import HMORegistry  # Fixed import
        from models import PropertyHMOMatch  # Fixed import
        from sqlalchemy import func, and_
        from datetime import date
        
        db = SessionLocal()
        
        # Get Oxford HMO statistics
        total_oxford_hmos = db.query(HMORegistry).filter(
            HMORegistry.city == 'oxford'
        ).count()
        
        active_licences = db.query(HMORegistry).filter(
            and_(
                HMORegistry.city == 'oxford',
                HMORegistry.licence_expiry_date >= date.today()
            )
        ).count()
        
        expired_licences = db.query(HMORegistry).filter(
            and_(
                HMORegistry.city == 'oxford',
                HMORegistry.licence_expiry_date < date.today()
            )
        ).count()
        
        # Get matching statistics
        oxford_hmo_ids = [str(hmo.id) for hmo in db.query(HMORegistry).filter(HMORegistry.city == 'oxford')]
        
        total_matches = db.query(PropertyHMOMatch).filter(
            PropertyHMOMatch.hmo_register_id.in_(oxford_hmo_ids)
        ).count()
        
        high_confidence_matches = db.query(PropertyHMOMatch).filter(
            and_(
                PropertyHMOMatch.hmo_register_id.in_(oxford_hmo_ids),
                PropertyHMOMatch.confidence_score >= 0.8
            )
        ).count()
        
        verification_result = {
            'total_oxford_hmos': total_oxford_hmos,
            'active_licences': active_licences,
            'expired_licences': expired_licences,
            'total_matches': total_matches,
            'high_confidence_matches': high_confidence_matches,
            'verification_passed': active_licences > 0 and total_matches > 0
        }
        
        print(f"     Total Oxford HMOs: {total_oxford_hmos}")
        print(f"     Active licences: {active_licences}")
        print(f"     Expired licences: {expired_licences}")
        print(f"     Property matches: {total_matches}")
        print(f"     High confidence matches: {high_confidence_matches}")
        
        return verification_result
        
    except Exception as e:
        logger.error(f"Verification error: {e}")
        return {
            'error': str(e),
            'verification_passed': False
        }
    
    finally:
        if 'db' in locals():
            db.close()


def generate_integration_report(results: Dict[str, Any]) -> Dict[str, str]:
    """Generate a comprehensive integration report"""
    
    report_content = f"""
Oxford HMO Integration Fix Report
===============================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

EXECUTION SUMMARY
-----------------
Status: {'SUCCESS' if results['success'] else 'FAILED'}
Duration: {results.get('duration', 'Unknown')}
Steps Completed: {len(results['steps_completed'])}
Errors: {len(results['errors'])}

STEPS COMPLETED
---------------
"""
    
    for step in results['steps_completed']:
        report_content += f"✅ {step.replace('_', ' ').title()}\n"
    
    if results['errors']:
        report_content += f"\nERRORS ENCOUNTERED\n------------------\n"
        for error in results['errors']:
            report_content += f"❌ {error}\n"
    
    # Add register processing stats if available
    if 'register_stats' in results and results['register_stats']['success']:
        stats = results['register_stats']
        report_content += f"""
HMO REGISTER PROCESSING
-----------------------
Total Records: {stats['total_records']}
Active Records: {stats['active_records']}
Database Updates: {stats['update_stats']['found_matches']}
New Records: {stats['update_stats']['new_records']}
"""
    
    # Add verification results if available
    if 'verification' in results:
        verification = results['verification']
        if 'error' not in verification:
            report_content += f"""
VERIFICATION RESULTS
--------------------
Total Oxford HMOs: {verification['total_oxford_hmos']}
Active Licences: {verification['active_licences']}
Expired Licences: {verification['expired_licences']}
Property Matches: {verification['total_matches']}
High Confidence Matches: {verification['high_confidence_matches']}
Verification Passed: {'YES' if verification['verification_passed'] else 'NO'}
"""
    
    report_content += f"""
NEXT STEPS
----------
1. Restart your web application to see the updated data
2. Check the map to verify HMOs show correct active/expired status
3. Monitor the system for any remaining issues
4. Consider running this fix periodically when the HMO register is updated

FILES GENERATED
---------------
- oxford_hmo_register_processed.csv (processed register data)
- oxford_integration_report.txt (this report)
"""
    
    # Save report to file
    report_file = f"oxford_integration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        return {
            'file_path': report_file,
            'content': report_content
        }
    
    except Exception as e:
        logger.error(f"Error saving report: {e}")
        return {
            'file_path': 'ERROR',
            'content': report_content
        }


def interactive_menu():
    """Interactive menu for running different parts of the fix"""
    while True:
        print("\n🏛️ Oxford HMO Integration Fix Menu")
        print("=" * 40)
        print("1. Run complete fix (recommended)")
        print("2. Test address matching only")
        print("3. Process HMO register file only")
        print("4. Verify current integration status")
        print("5. Check requirements")
        print("6. Exit")
        
        choice = input("\nSelect an option (1-6): ").strip()
        
        if choice == '1':
            if not check_requirements():
                continue
            
            print("\n🚀 Running complete Oxford HMO integration fix...")
            results = run_complete_fix()
            
            if results['success']:
                print("\n🎉 Integration fix completed successfully!")
                print(f"Duration: {results.get('duration', 'Unknown')}")
                if 'report_file' in results:
                    print(f"Report saved to: {results['report_file']}")
            else:
                print("\n❌ Integration fix failed")
                if results['errors']:
                    print("Errors:")
                    for error in results['errors']:
                        print(f"  - {error}")
        
        elif choice == '2':
            print("\n🧪 Testing address matching...")
            try:
                from enhanced_oxford_matcher import test_address_matching
                test_address_matching()
            except ImportError as e:
                print(f"❌ Error importing matcher: {e}")
            except Exception as e:
                print(f"❌ Error running test: {e}")
        
        elif choice == '3':
            if not os.path.exists("HMO Register Copy.xlsx"):
                print("❌ HMO Register Copy.xlsx not found")
                continue
            
            print("\n📊 Processing HMO register file...")
            try:
                from oxford_register_processor import fix_oxford_hmo_status
                fix_oxford_hmo_status()
            except ImportError as e:
                print(f"❌ Error importing processor: {e}")
            except Exception as e:
                print(f"❌ Error processing register: {e}")
        
        elif choice == '4':
            print("\n🔍 Verifying integration status...")
            verification = verify_oxford_integration()
            
            if 'error' in verification:
                print(f"❌ Verification failed: {verification['error']}")
            else:
                print("✅ Verification completed")
                if verification['verification_passed']:
                    print("🎉 Integration appears to be working correctly!")
                else:
                    print("⚠️ Integration may need attention")
        
        elif choice == '5':
            check_requirements()
        
        elif choice == '6':
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice, please select 1-6")


def main():
    """Main entry point"""
    print("🏛️ Oxford HMO Integration Fix Tool")
    print("==================================")
    print()
    print("This tool fixes address matching issues between the Oxford HMO")
    print("database and the HMO Register Copy file, ensuring that active")
    print("licences are not shown as expired on the map.")
    print()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--auto':
            print("🤖 Running in automatic mode...")
            if check_requirements():
                results = run_complete_fix()
                sys.exit(0 if results['success'] else 1)
            else:
                sys.exit(1)
        elif sys.argv[1] == '--help':
            print("Usage:")
            print("  python fix_oxford_integration.py          # Interactive mode")
            print("  python fix_oxford_integration.py --auto   # Automatic mode")
            print("  python fix_oxford_integration.py --help   # Show this help")
            sys.exit(0)
    
    # Run interactive menu
    interactive_menu()


if __name__ == "__main__":
    main()