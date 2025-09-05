#!/usr/bin/env python3
"""
Diagnostic script to check date_found issues
Run this to see what's happening with property created_at dates
"""

import sys
from sqlalchemy import create_engine, text
from database import DATABASE_URL
from models import Property, PropertyAnalysis

def diagnose_date_found():
    """Check property created_at vs analysis dates"""
    try:
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as connection:
            # Query to show property created_at vs analysis dates
            query = text("""
                SELECT 
                    CAST(p.id AS TEXT) as property_id,
                    p.address,
                    p.created_at as property_created_at,
                    COUNT(pa.id) as total_analyses,
                    MIN(pa.created_at) as first_analysis_date,
                    MAX(pa.created_at) as latest_analysis_date,
                    (CASE 
                        WHEN p.created_at::timestamp != MIN(pa.created_at)::timestamp 
                        THEN 'DATE MISMATCH' 
                        ELSE 'OK' 
                    END) as status
                FROM properties p
                LEFT JOIN property_analyses pa ON CAST(p.id AS TEXT) = CAST(pa.property_id AS TEXT)
                GROUP BY p.id, p.address, p.created_at
                ORDER BY p.created_at DESC
                LIMIT 20
            """)
            
            result = connection.execute(query)
            rows = result.fetchall()
            
            print("🔍 PROPERTY DATE ANALYSIS:")
            print("=" * 100)
            print(f"{'Property ID':<36} {'Address':<30} {'Created At':<20} {'Analyses':<10} {'Status':<15}")
            print("-" * 100)
            
            mismatches = 0
            for row in rows:
                property_id = row[0]
                address = (row[1][:27] + "...") if row[1] and len(row[1]) > 30 else (row[1] or "No Address")
                created_at = str(row[2])[:19] if row[2] else "None"
                total_analyses = row[3]
                status = row[6]
                
                if status == 'DATE MISMATCH':
                    mismatches += 1
                
                print(f"{property_id:<36} {address:<30} {created_at:<20} {total_analyses:<10} {status:<15}")
                
                # Show detailed info for mismatched properties
                if status == 'DATE MISMATCH':
                    first_analysis = str(row[4])[:19] if row[4] else "None"
                    latest_analysis = str(row[5])[:19] if row[5] else "None"
                    print(f"  └─ First Analysis: {first_analysis}, Latest: {latest_analysis}")
            
            print("-" * 100)
            print(f"📊 SUMMARY: {mismatches} properties have date mismatches")
            
            if mismatches > 0:
                print("\n⚠️  ISSUE DETECTED:")
                print("Some properties have created_at dates that don't match their first analysis date.")
                print("This suggests the property created_at is being updated during re-analysis.")
                
                # Check a specific property in detail
                print("\n🔍 DETAILED ANALYSIS OF FIRST MISMATCHED PROPERTY:")
                
                detail_query = text("""
                    SELECT 
                        CAST(p.id AS TEXT) as property_id,
                        p.address,
                        p.created_at as property_created,
                        p.updated_at as property_updated,
                        CAST(pa.id AS TEXT) as analysis_id,
                        pa.created_at as analysis_created,
                        pa.listing_status
                    FROM properties p
                    LEFT JOIN property_analyses pa ON CAST(p.id AS TEXT) = CAST(pa.property_id AS TEXT)
                    WHERE p.created_at::timestamp != (
                        SELECT MIN(pa2.created_at)::timestamp
                        FROM property_analyses pa2 
                        WHERE CAST(pa2.property_id AS TEXT) = CAST(p.id AS TEXT)
                    )
                    ORDER BY CAST(p.id AS TEXT), pa.created_at
                    LIMIT 10
                """)
                
                detail_result = connection.execute(detail_query)
                detail_rows = detail_result.fetchall()
                
                for row in detail_rows:
                    print(f"Property: {row[1]}")
                    print(f"  Property Created: {row[2]}")
                    print(f"  Property Updated: {row[3]}")
                    print(f"  Analysis Created: {row[5]}")
                    print(f"  Status: {row[6]}")
                    print()
            
            else:
                print("\n✅ NO ISSUES FOUND:")
                print("All properties have created_at dates that match their first analysis.")
                print("The date_found should be working correctly.")
            
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("🔄 Starting date_found diagnosis...")
    diagnose_date_found()
    print("✅ Diagnosis complete!")