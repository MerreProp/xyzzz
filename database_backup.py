# database_backup.py
"""
Database Backup Script for Phase 1 Migration
Supports both SQLite and PostgreSQL backups with multiple backup methods
"""

import os
import sys
import subprocess
import shutil
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
import json

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import DATABASE_URL, engine, SessionLocal
from sqlalchemy import text

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseBackup:
    """Handles database backups for SQLite and PostgreSQL"""
    
    def __init__(self):
        self.database_url = DATABASE_URL
        self.backup_dir = Path("database_backups")
        self.backup_dir.mkdir(exist_ok=True)
        
        # Parse database URL to determine type
        if self.database_url.startswith("sqlite"):
            self.db_type = "sqlite"
            self.db_path = self.database_url.replace("sqlite:///", "")
        elif "postgresql" in self.database_url or "postgres" in self.database_url:
            self.db_type = "postgresql"
            self.parsed_url = urlparse(self.database_url)
        else:
            raise ValueError(f"Unsupported database type: {self.database_url}")
    
    def create_backup(self, backup_name: str = None) -> tuple[bool, str]:
        """Create a backup with appropriate method for database type"""
        
        if not backup_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_before_phase1_migration_{timestamp}"
        
        logger.info(f"🗄️  Creating {self.db_type.upper()} database backup: {backup_name}")
        
        try:
            if self.db_type == "sqlite":
                return self._backup_sqlite(backup_name)
            elif self.db_type == "postgresql":
                return self._backup_postgresql(backup_name)
        except Exception as e:
            logger.error(f"❌ Backup failed: {str(e)}")
            return False, str(e)
    
    def _backup_sqlite(self, backup_name: str) -> tuple[bool, str]:
        """Create SQLite backup using multiple methods for reliability"""
        
        backup_files = []
        
        try:
            # Method 1: Simple file copy (fastest)
            if os.path.exists(self.db_path):
                copy_backup = self.backup_dir / f"{backup_name}_copy.db"
                shutil.copy2(self.db_path, copy_backup)
                backup_files.append(str(copy_backup))
                logger.info(f"✅ File copy backup created: {copy_backup}")
            
            # Method 2: SQLite .backup command (most reliable)
            backup_backup = self.backup_dir / f"{backup_name}_backup.db"
            conn = sqlite3.connect(self.db_path)
            backup_conn = sqlite3.connect(str(backup_backup))
            
            # Use SQLite's backup API
            conn.backup(backup_conn)
            backup_conn.close()
            conn.close()
            
            backup_files.append(str(backup_backup))
            logger.info(f"✅ SQLite backup API backup created: {backup_backup}")
            
            # Method 3: SQL dump (for examination/portability)
            dump_backup = self.backup_dir / f"{backup_name}_dump.sql"
            with open(dump_backup, 'w') as f:
                conn = sqlite3.connect(self.db_path)
                for line in conn.iterdump():
                    f.write(f"{line}\n")
                conn.close()
            
            backup_files.append(str(dump_backup))
            logger.info(f"✅ SQL dump backup created: {dump_backup}")
            
            # Create backup manifest
            manifest = self._create_backup_manifest(backup_name, backup_files)
            
            return True, f"SQLite backup successful. Files: {', '.join(backup_files)}"
            
        except Exception as e:
            logger.error(f"❌ SQLite backup failed: {str(e)}")
            return False, str(e)
    
    def _backup_postgresql(self, backup_name: str) -> tuple[bool, str]:
        """Create PostgreSQL backup using pg_dump"""
        
        backup_files = []
        
        try:
            # Extract connection details
            host = self.parsed_url.hostname
            port = self.parsed_url.port or 5432
            database = self.parsed_url.path.lstrip('/')
            username = self.parsed_url.username
            password = self.parsed_url.password
            
            logger.info(f"📡 Connecting to PostgreSQL: {username}@{host}:{port}/{database}")
            
            # Method 1: Custom format backup (recommended)
            custom_backup = self.backup_dir / f"{backup_name}_custom.backup"
            custom_cmd = [
                "pg_dump",
                f"--host={host}",
                f"--port={port}",
                f"--username={username}",
                f"--dbname={database}",
                "--format=custom",
                "--compress=9",
                "--no-password",
                "--verbose",
                f"--file={custom_backup}"
            ]
            
            # Set password environment variable
            env = os.environ.copy()
            if password:
                env['PGPASSWORD'] = password
            
            result = subprocess.run(custom_cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                backup_files.append(str(custom_backup))
                logger.info(f"✅ PostgreSQL custom backup created: {custom_backup}")
            else:
                logger.warning(f"⚠️  Custom backup failed: {result.stderr}")
            
            # Method 2: SQL dump backup (for examination)
            sql_backup = self.backup_dir / f"{backup_name}_dump.sql"
            sql_cmd = [
                "pg_dump",
                f"--host={host}",
                f"--port={port}",
                f"--username={username}",
                f"--dbname={database}",
                "--format=plain",
                "--no-password",
                "--verbose",
                f"--file={sql_backup}"
            ]
            
            result = subprocess.run(sql_cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                backup_files.append(str(sql_backup))
                logger.info(f"✅ PostgreSQL SQL dump created: {sql_backup}")
            else:
                logger.warning(f"⚠️  SQL dump failed: {result.stderr}")
            
            # Method 3: Fallback - SQLAlchemy-based backup for data
            if not backup_files:
                logger.info("📊 Attempting SQLAlchemy-based data backup...")
                data_backup = self._backup_data_via_sqlalchemy(backup_name)
                if data_backup:
                    backup_files.append(data_backup)
            
            if backup_files:
                # Create backup manifest
                manifest = self._create_backup_manifest(backup_name, backup_files)
                return True, f"PostgreSQL backup successful. Files: {', '.join(backup_files)}"
            else:
                return False, "All PostgreSQL backup methods failed"
                
        except FileNotFoundError:
            logger.error("❌ pg_dump not found. Please install PostgreSQL client tools.")
            logger.info("💡 Attempting data-only backup via SQLAlchemy...")
            
            # Fallback to data backup
            data_backup = self._backup_data_via_sqlalchemy(backup_name)
            if data_backup:
                manifest = self._create_backup_manifest(backup_name, [data_backup])
                return True, f"Data-only backup created: {data_backup}"
            else:
                return False, "pg_dump not available and data backup failed"
        
        except Exception as e:
            logger.error(f"❌ PostgreSQL backup failed: {str(e)}")
            return False, str(e)
    
    def _backup_data_via_sqlalchemy(self, backup_name: str) -> str:
        """Backup critical data using SQLAlchemy (fallback method)"""
        
        try:
            logger.info("📊 Creating data-only backup via SQLAlchemy...")
            
            db = SessionLocal()
            
            # Get all table names
            tables_query = text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            """)
            
            if self.db_type == "sqlite":
                tables_query = text("SELECT name FROM sqlite_master WHERE type='table'")
            
            result = db.execute(tables_query)
            tables = [row[0] for row in result.fetchall()]
            
            logger.info(f"📋 Found {len(tables)} tables to backup")
            
            # Create data backup
            backup_data = {
                "backup_info": {
                    "created_at": datetime.now().isoformat(),
                    "database_type": self.db_type,
                    "database_url": self.database_url.split('@')[0] + '@[HIDDEN]',  # Hide credentials
                    "tables": tables,
                    "backup_method": "sqlalchemy_data_only"
                },
                "table_data": {}
            }
            
            # Backup critical tables (avoid large tables for space)
            critical_tables = ['properties', 'property_analyses', 'rooms', 'property_urls', 
                             'room_availability_periods', 'property_changes']
            
            for table in tables:
                if table in critical_tables:
                    try:
                        # Get row count first
                        count_result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                        row_count = count_result.scalar()
                        
                        if row_count > 0 and row_count < 10000:  # Only backup reasonably sized tables
                            rows_result = db.execute(text(f"SELECT * FROM {table}"))
                            columns = list(rows_result.keys())
                            rows = [dict(zip(columns, row)) for row in rows_result.fetchall()]
                            
                            backup_data["table_data"][table] = {
                                "columns": columns,
                                "row_count": row_count,
                                "rows": rows
                            }
                            
                            logger.info(f"  ✅ Backed up {table}: {row_count} rows")
                        else:
                            logger.info(f"  ⚠️  Skipped {table}: {row_count} rows (too large or empty)")
                            
                    except Exception as e:
                        logger.warning(f"  ⚠️  Failed to backup {table}: {str(e)}")
            
            # Save to JSON file
            data_backup_file = self.backup_dir / f"{backup_name}_data.json"
            
            # Custom JSON encoder for datetime and Decimal objects
            def json_serializer(obj):
                if hasattr(obj, 'isoformat'):
                    return obj.isoformat()
                elif hasattr(obj, '__str__'):
                    return str(obj)
                return obj
            
            with open(data_backup_file, 'w') as f:
                json.dump(backup_data, f, indent=2, default=json_serializer)
            
            db.close()
            
            logger.info(f"✅ Data backup created: {data_backup_file}")
            return str(data_backup_file)
            
        except Exception as e:
            logger.error(f"❌ Data backup failed: {str(e)}")
            return None
    
    def _create_backup_manifest(self, backup_name: str, backup_files: list) -> str:
        """Create a manifest file documenting the backup"""
        
        manifest_file = self.backup_dir / f"{backup_name}_manifest.json"
        
        manifest = {
            "backup_name": backup_name,
            "created_at": datetime.now().isoformat(),
            "database_type": self.db_type,
            "database_url": self.database_url.split('@')[0] + '@[HIDDEN]',
            "backup_files": backup_files,
            "backup_purpose": "Phase 1 Migration - Enhanced Duplicate Detection",
            "restore_instructions": self._get_restore_instructions()
        }
        
        with open(manifest_file, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        logger.info(f"📋 Backup manifest created: {manifest_file}")
        return str(manifest_file)
    
    def _get_restore_instructions(self) -> dict:
        """Get database-specific restore instructions"""
        
        if self.db_type == "sqlite":
            return {
                "method_1": "Replace database file: cp backup_file.db original_file.db",
                "method_2": "SQLite restore: sqlite3 new_db.db < backup_dump.sql",
                "notes": "Stop application before replacing database file"
            }
        else:
            return {
                "method_1": "pg_restore --clean --create --verbose backup_file.backup",
                "method_2": "psql -f backup_dump.sql database_name",
                "notes": "Ensure PostgreSQL is running and you have appropriate permissions"
            }
    
    def list_backups(self):
        """List all available backups"""
        
        logger.info(f"📁 Backup directory: {self.backup_dir}")
        
        backup_files = list(self.backup_dir.glob("*"))
        
        if not backup_files:
            logger.info("  📭 No backups found")
            return
        
        logger.info(f"  📋 Found {len(backup_files)} backup files:")
        
        for backup_file in sorted(backup_files):
            file_size = backup_file.stat().st_size
            file_size_mb = file_size / (1024 * 1024)
            modified_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
            
            logger.info(f"    📄 {backup_file.name} ({file_size_mb:.1f} MB, {modified_time.strftime('%Y-%m-%d %H:%M')})")

def create_pre_migration_backup():
    """Main function to create backup before Phase 1 migration"""
    
    print("🗄️  DATABASE BACKUP FOR PHASE 1 MIGRATION")
    print("=" * 50)
    
    backup_system = DatabaseBackup()
    
    print(f"\n📊 Database type detected: {backup_system.db_type.upper()}")
    print(f"📁 Backup location: {backup_system.backup_dir}")
    
    # Check available disk space
    backup_dir_stats = shutil.disk_usage(backup_system.backup_dir)
    free_space_gb = backup_dir_stats.free / (1024**3)
    print(f"💾 Available disk space: {free_space_gb:.1f} GB")
    
    if free_space_gb < 1:
        print("⚠️  WARNING: Less than 1GB free space available")
        confirm = input("Continue anyway? (y/N): ").lower().strip()
        if confirm != 'y':
            print("❌ Backup cancelled")
            return False, "Insufficient disk space"
    
    # Create the backup
    success, message = backup_system.create_backup()
    
    if success:
        print(f"\n✅ BACKUP COMPLETED SUCCESSFULLY!")
        print(f"📄 {message}")
        print(f"\n📋 Backup files created in: {backup_system.backup_dir}")
        
        # List the created files
        backup_system.list_backups()
        
        print(f"\n🔐 Your database is safely backed up!")
        print(f"💡 If migration fails, you can restore from these backup files")
        
        return True, str(backup_system.backup_dir)
    else:
        print(f"\n❌ BACKUP FAILED!")
        print(f"💥 Error: {message}")
        print(f"\n⚠️  DO NOT PROCEED WITH MIGRATION WITHOUT A BACKUP!")
        
        return False, message

if __name__ == "__main__":
    success, result = create_pre_migration_backup()
    
    if success:
        print(f"\n🚀 Ready for Phase 1 migration!")
        print(f"📁 Backups stored in: {result}")
    else:
        print(f"\n❌ Please resolve backup issues before proceeding")
        sys.exit(1)