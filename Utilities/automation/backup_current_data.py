#!/usr/bin/env python3
"""
Data Backup Script for eBay Optimizer Refactoring
Creates comprehensive backup before multi-sheet migration
"""

import os
import sys
import json
import sqlite3
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Add the parent directory to sys.path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import create_engine, text
    from app.db.database import get_db
    from app.core.config import settings
    from app.models.database_models import *
except ImportError as e:
    print(f"⚠️ Warning: Could not import database modules: {e}")
    print("Running in standalone mode - will backup database files only")


class DataBackupManager:
    """Manages comprehensive data backup before refactoring"""
    
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_dir = Path(f"backups/pre_multisheet_migration_{self.timestamp}")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"📁 Backup directory: {self.backup_dir}")
        
    def create_full_backup(self) -> Dict[str, Any]:
        """Create comprehensive backup of current system"""
        backup_report = {
            "timestamp": self.timestamp,
            "backup_directory": str(self.backup_dir),
            "success": True,
            "files_backed_up": [],
            "databases_backed_up": [],
            "errors": []
        }
        
        try:
            print("🔄 Starting comprehensive backup...")
            
            # 1. Backup database files
            self.backup_database_files(backup_report)
            
            # 2. Backup configuration files
            self.backup_config_files(backup_report)
            
            # 3. Backup service files
            self.backup_service_files(backup_report)
            
            # 4. Export database data as JSON
            self.export_database_data(backup_report)
            
            # 5. Backup credentials and secrets
            self.backup_credentials(backup_report)
            
            # 6. Create backup manifest
            self.create_backup_manifest(backup_report)
            
            print(f"✅ Backup completed successfully!")
            print(f"📊 Files backed up: {len(backup_report['files_backed_up'])}")
            print(f"🗄️ Databases backed up: {len(backup_report['databases_backed_up'])}")
            
        except Exception as e:
            backup_report["success"] = False
            backup_report["errors"].append(str(e))
            print(f"❌ Backup failed: {e}")
            
        return backup_report
    
    def backup_database_files(self, report: Dict[str, Any]):
        """Backup SQLite database files"""
        print("🗄️ Backing up database files...")
        
        db_files = [
            "backend/ebay_optimizer.db",
            "backend/ebay_optimizer.db-journal",  # SQLite journal file if exists
        ]
        
        for db_file in db_files:
            if os.path.exists(db_file):
                backup_path = self.backup_dir / f"database_{Path(db_file).name}"
                shutil.copy2(db_file, backup_path)
                report["files_backed_up"].append(str(backup_path))
                report["databases_backed_up"].append(db_file)
                print(f"   ✅ {db_file} → {backup_path}")
    
    def backup_config_files(self, report: Dict[str, Any]):
        """Backup configuration files"""
        print("⚙️ Backing up configuration files...")
        
        config_files = [
            "backend/app/core/config.py",
            "backend/app/core/service_config.py", 
            "docker-compose.yml",
            "docker-compose.prod.yml",
            "nginx.conf",
            "nginx.prod.conf",
        ]
        
        for config_file in config_files:
            if os.path.exists(config_file):
                backup_path = self.backup_dir / f"config_{Path(config_file).name}"
                shutil.copy2(config_file, backup_path)
                report["files_backed_up"].append(str(backup_path))
                print(f"   ✅ {config_file} → {backup_path}")
    
    def backup_service_files(self, report: Dict[str, Any]):
        """Backup current service implementation files"""
        print("🔧 Backing up service files...")
        
        service_files = [
            "backend/app/services/google_sheets.py",
            "backend/app/services/enhanced_google_sheets.py",
            "backend/app/services/sync_service.py",
            "backend/app/services/export_service.py",
            "backend/app/repositories/listing.py",
            "backend/app/repositories/order.py",
            "backend/app/repositories/account.py",
        ]
        
        for service_file in service_files:
            if os.path.exists(service_file):
                backup_path = self.backup_dir / f"services_{Path(service_file).name}"
                shutil.copy2(service_file, backup_path)
                report["files_backed_up"].append(str(backup_path))
                print(f"   ✅ {service_file} → {backup_path}")
    
    def export_database_data(self, report: Dict[str, Any]):
        """Export database data as JSON for data integrity verification"""
        print("📊 Exporting database data as JSON...")
        
        try:
            # Try to connect to database
            db_path = "backend/ebay_optimizer.db"
            if not os.path.exists(db_path):
                print("   ⚠️ Database file not found, skipping data export")
                return
                
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            
            # Get all table names
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            exported_data = {}
            
            for table in tables:
                try:
                    cursor = conn.execute(f"SELECT * FROM {table}")
                    rows = cursor.fetchall()
                    
                    # Convert rows to dictionaries
                    table_data = []
                    for row in rows:
                        row_dict = {}
                        for key in row.keys():
                            value = row[key]
                            # Handle datetime and other non-serializable types
                            if isinstance(value, (datetime,)):
                                row_dict[key] = value.isoformat()
                            else:
                                row_dict[key] = value
                        table_data.append(row_dict)
                    
                    exported_data[table] = {
                        "count": len(table_data),
                        "data": table_data
                    }
                    
                    print(f"   ✅ Exported {table}: {len(table_data)} records")
                    
                except Exception as e:
                    print(f"   ⚠️ Error exporting table {table}: {e}")
                    exported_data[table] = {"error": str(e)}
            
            # Save exported data
            json_backup_path = self.backup_dir / "database_export.json"
            with open(json_backup_path, 'w', encoding='utf-8') as f:
                json.dump(exported_data, f, indent=2, ensure_ascii=False)
            
            report["files_backed_up"].append(str(json_backup_path))
            
            # Create summary
            summary = {
                "total_tables": len(tables),
                "total_records": sum(
                    data.get("count", 0) for data in exported_data.values() 
                    if isinstance(data, dict) and "count" in data
                )
            }
            
            summary_path = self.backup_dir / "database_summary.json"
            with open(summary_path, 'w') as f:
                json.dump(summary, f, indent=2)
            
            report["files_backed_up"].append(str(summary_path))
            print(f"   📊 Database summary: {summary['total_records']} total records")
            
            conn.close()
            
        except Exception as e:
            error_msg = f"Database export error: {e}"
            report["errors"].append(error_msg)
            print(f"   ❌ {error_msg}")
    
    def backup_credentials(self, report: Dict[str, Any]):
        """Backup credential files (safely)"""
        print("🔐 Backing up credentials...")
        
        credential_files = [
            "credentials/google-service-account.json",
            "backend/app/core/.env",  # If exists
            ".env",  # Root .env file
        ]
        
        for cred_file in credential_files:
            if os.path.exists(cred_file):
                backup_path = self.backup_dir / f"credentials_{Path(cred_file).name}"
                shutil.copy2(cred_file, backup_path)
                report["files_backed_up"].append(str(backup_path))
                print(f"   ✅ {cred_file} → {backup_path}")
                
                # Create sanitized version (remove sensitive data)
                self.create_sanitized_credential_backup(cred_file, backup_path)
    
    def create_sanitized_credential_backup(self, original_file: str, backup_path: Path):
        """Create sanitized version of credential files"""
        try:
            if original_file.endswith('.json'):
                # For JSON files (Google credentials)
                with open(original_file, 'r') as f:
                    data = json.load(f)
                
                # Sanitize sensitive fields
                sanitized = data.copy()
                sensitive_fields = ['private_key', 'private_key_id', 'client_secret']
                
                for field in sensitive_fields:
                    if field in sanitized:
                        sanitized[field] = "[REDACTED_FOR_SECURITY]"
                
                sanitized_path = backup_path.with_name(f"sanitized_{backup_path.name}")
                with open(sanitized_path, 'w') as f:
                    json.dump(sanitized, f, indent=2)
                    
                print(f"   🔒 Created sanitized version: {sanitized_path}")
                
        except Exception as e:
            print(f"   ⚠️ Could not create sanitized backup: {e}")
    
    def create_backup_manifest(self, report: Dict[str, Any]):
        """Create backup manifest with metadata"""
        manifest = {
            "backup_info": {
                "timestamp": self.timestamp,
                "backup_type": "pre_multisheet_migration",
                "backup_directory": str(self.backup_dir),
                "created_by": "backup_current_data.py",
                "python_version": sys.version,
            },
            "system_info": {
                "current_working_directory": os.getcwd(),
                "platform": sys.platform,
                "files_exist": {
                    "database": os.path.exists("backend/ebay_optimizer.db"),
                    "config": os.path.exists("backend/app/core/config.py"),
                    "google_credentials": os.path.exists("credentials/google-service-account.json"),
                }
            },
            "backup_report": report
        }
        
        manifest_path = self.backup_dir / "backup_manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        print(f"📋 Backup manifest created: {manifest_path}")
    
    def verify_backup_integrity(self) -> bool:
        """Verify backup integrity"""
        print("🔍 Verifying backup integrity...")
        
        critical_files = [
            "database_ebay_optimizer.db",
            "database_export.json",
            "backup_manifest.json"
        ]
        
        missing_files = []
        for file_name in critical_files:
            file_path = self.backup_dir / file_name
            if not file_path.exists():
                missing_files.append(file_name)
        
        if missing_files:
            print(f"❌ Missing critical backup files: {missing_files}")
            return False
        
        print("✅ Backup integrity verified")
        return True


def main():
    """Main backup execution"""
    print("🚀 Starting eBay Optimizer Data Backup")
    print("=" * 50)
    
    backup_manager = DataBackupManager()
    
    # Create comprehensive backup
    backup_report = backup_manager.create_full_backup()
    
    if backup_report["success"]:
        # Verify backup integrity
        if backup_manager.verify_backup_integrity():
            print("\n🎉 Backup completed successfully!")
            print(f"📁 Backup location: {backup_report['backup_directory']}")
            print(f"📊 Files backed up: {len(backup_report['files_backed_up'])}")
            
            # Create restore instructions
            restore_instructions = f"""
# RESTORE INSTRUCTIONS

To restore this backup:

1. Stop the application:
   docker-compose down

2. Restore database:
   cp {backup_report['backup_directory']}/database_ebay_optimizer.db backend/ebay_optimizer.db

3. Restore configuration files:
   # Copy config files back to their original locations
   
4. Restore credentials:
   cp {backup_report['backup_directory']}/credentials_* credentials/

5. Restart application:
   docker-compose up -d

Created: {backup_report['timestamp']}
"""
            
            restore_file = backup_manager.backup_dir / "RESTORE_INSTRUCTIONS.md"
            with open(restore_file, 'w') as f:
                f.write(restore_instructions)
            
            print(f"📖 Restore instructions: {restore_file}")
            
        else:
            print("❌ Backup verification failed!")
            return 1
    else:
        print("❌ Backup failed!")
        print("Errors:")
        for error in backup_report["errors"]:
            print(f"   - {error}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)