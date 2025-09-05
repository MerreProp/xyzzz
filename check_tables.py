#!/usr/bin/env python3
"""
Run the SQL investigation queries through Python
"""

import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

def get_database_connection():
    """Get database connection"""
    load_dotenv()
    
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    if not DATABASE_URL:
        print("❌ No DATABASE_URL found in environment variables")
        return None
    
    return create_engine(DATABASE_URL)

def run_investigation():
    """Run all investigation queries"""
    
    engine = get_database_connection()
    if not engine:
        return
    
    queries = [
        ("1. CHECK WHAT TABLES EXIST", """
            SELECT table_name, table_type 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """),
        
        ("2. LOOK FOR PROPERTY-RELATED TABLES", """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE '%property%'
            ORDER BY table_name;
        """),
        
        ("3. CHECK IF property_analysis TABLE EXISTS", """
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'property_analysis'
            ) as property_analysis_exists;
        """),
        
        ("4. CHECK IF property_analyses TABLE EXISTS", """
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'property_analyses'
            ) as property_analyses_exists;
        """),
        
        ("5. CHECK properties TABLE STRUCTURE", """
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = 'properties'
            ORDER BY ordinal_position;
        """),
        
        ("6. CHECK FOREIGN KEY CONSTRAINTS", """
            SELECT 
                tc.table_name, 
                kcu.column_name, 
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name 
            FROM information_schema.table_constraints AS tc 
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY' 
            AND tc.table_schema = 'public'
            AND (tc.table_name LIKE '%property%' OR ccu.table_name LIKE '%property%')
            ORDER BY tc.table_name, kcu.column_name;
        """),
        
        ("7. CHECK ACTIVE TRANSACTIONS", """
            SELECT 
                pid,
                state,
                query_start,
                state_change,
                left(query, 100) as query_preview
            FROM pg_stat_activity 
            WHERE state != 'idle' 
            AND pid != pg_backend_pid()
            ORDER BY query_start;
        """),
        
        ("8. CHECK DATABASE LOCKS", """
            SELECT 
                pl.pid,
                pl.mode,
                pl.locktype,
                pl.relation::regclass as relation_name,
                left(pa.query, 80) as query_preview
            FROM pg_locks pl
            LEFT JOIN pg_stat_activity pa ON pl.pid = pa.pid
            WHERE pl.granted = false
            ORDER BY pl.pid;
        """),
        
        ("9. CHECK ALL PROPERTY TABLE COLUMNS", """
            SELECT 
                t.table_name,
                c.column_name,
                c.data_type,
                c.is_nullable,
                c.column_default
            FROM information_schema.tables t
            JOIN information_schema.columns c ON t.table_name = c.table_name
            WHERE t.table_schema = 'public' 
            AND t.table_name LIKE '%property%'
            ORDER BY t.table_name, c.ordinal_position;
        """),
        
        ("10. CHECK PROPERTY TABLE INDEXES", """
            SELECT 
                schemaname,
                tablename,
                indexname,
                indexdef
            FROM pg_indexes 
            WHERE schemaname = 'public'
            AND tablename LIKE '%property%'
            ORDER BY tablename, indexname;
        """)
    ]
    
    print("🕵️ Running Database Investigation")
    print("=" * 60)
    
    try:
        with engine.connect() as conn:
            for title, query in queries:
                print(f"\n📋 {title}")
                print("-" * 40)
                
                try:
                    result = conn.execute(text(query))
                    rows = result.fetchall()
                    
                    if rows:
                        # Print column headers
                        columns = result.keys()
                        print(" | ".join(f"{col:20}" for col in columns))
                        print("-" * (25 * len(columns)))
                        
                        # Print rows
                        for row in rows:
                            print(" | ".join(f"{str(val):20}" for val in row))
                        
                        print(f"\n✅ Found {len(rows)} result(s)")
                    else:
                        print("📭 No results found")
                        
                except Exception as e:
                    print(f"❌ Query failed: {e}")
                    
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        
    print(f"\n🎯 Investigation complete!")

if __name__ == "__main__":
    run_investigation()