#!/usr/bin/env python3
"""
Migration 003: Multi-Role Google Sheets Integration
- Add user roles system
- Add Google Sheets sync fields to orders
- Add role-based assignment system
- Add blacklist management
"""

import sqlite3
import uuid
from datetime import datetime

def run_migration():
    """Execute migration 003"""
    conn = sqlite3.connect('ebay_optimizer.db')
    cursor = conn.cursor()
    
    try:
        print("🚀 Running Migration 003: Multi-Role Google Sheets Integration...")
        
        # 1. Create UserRole enum table
        print("📝 Step 1: Creating user roles system...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role_name VARCHAR(50) UNIQUE NOT NULL,
                description TEXT,
                permissions JSON,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert default roles
        default_roles = [
            ('ADMIN', 'System Administrator', '["*"]'),
            ('EBAY_MANAGER', 'eBay Manager - Import orders, manage tracking, blacklist check', 
             '["orders.import", "orders.tracking", "orders.blacklist", "orders.status", "sheets.sync"]'),
            ('FULFILLMENT_STAFF', 'Fulfillment Staff - Process orders, supplier communication, tracking input',
             '["orders.process", "orders.supplier", "orders.tracking_input", "orders.status_update"]'),
        ]
        
        for role_name, description, permissions in default_roles:
            cursor.execute("""
                INSERT OR IGNORE INTO user_roles (role_name, description, permissions)
                VALUES (?, ?, ?)
            """, (role_name, description, permissions))
        
        # 2. Add role_id to users table
        print("📝 Step 2: Adding role support to users...")
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN role_id INTEGER")
            cursor.execute("ALTER TABLE users ADD COLUMN assigned_accounts JSON")  # For eBay accounts assignment
            cursor.execute("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT 1")
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e):
                raise
            print("   ℹ️  User role columns already exist")
        
        # Set default role for existing users (ADMIN)
        cursor.execute("""
            UPDATE users 
            SET role_id = (SELECT id FROM user_roles WHERE role_name = 'ADMIN')
            WHERE role_id IS NULL
        """)
        
        # 3. Update orders table for Google Sheets integration
        print("📝 Step 3: Enhancing orders for Google Sheets sync...")
        orders_columns = [
            ("sync_source", "VARCHAR(50) DEFAULT 'manual'"),  # 'google_sheets', 'manual', 'api'
            ("sheets_row_id", "VARCHAR(100)"),  # Track Google Sheets row
            ("sheets_last_sync", "DATETIME"),  # Last sync timestamp
            ("assigned_to_user_id", "INTEGER"),  # Assigned fulfillment staff
            ("assigned_by_user_id", "INTEGER"),  # Who assigned the order
            ("assignment_date", "DATETIME"),  # When assigned
            ("blacklist_checked", "BOOLEAN DEFAULT 0"),  # Address blacklist status
            ("blacklist_status", "VARCHAR(20)"),  # 'clean', 'flagged', 'blocked'
            ("blacklist_reason", "TEXT"),  # Why flagged/blocked
            ("fulfillment_notes", "TEXT"),  # Notes from fulfillment staff
            ("supplier_sent_date", "DATETIME"),  # When sent to supplier
            ("supplier_name", "VARCHAR(200)"),  # Which supplier used
            ("tracking_added_to_ebay", "BOOLEAN DEFAULT 0"),  # Tracking synced to eBay
            ("ebay_sync_status", "VARCHAR(50)"),  # eBay sync status
            ("last_status_change", "DATETIME"),  # Status change tracking
            ("status_changed_by", "INTEGER"),  # Who changed status
        ]
        
        for column_name, column_def in orders_columns:
            try:
                cursor.execute(f"ALTER TABLE orders ADD COLUMN {column_name} {column_def}")
                print(f"   ✅ Added column: {column_name}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" not in str(e):
                    raise
                print(f"   ℹ️  Column {column_name} already exists")
        
        # 4. Create address blacklist table
        print("📝 Step 4: Creating address blacklist system...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS address_blacklist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                address_pattern TEXT NOT NULL,
                match_type VARCHAR(20) DEFAULT 'contains',  -- 'exact', 'contains', 'regex'
                risk_level VARCHAR(20) DEFAULT 'medium',   -- 'low', 'medium', 'high', 'blocked'
                reason TEXT,
                created_by INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (created_by) REFERENCES users (id)
            )
        """)
        
        # Add some default blacklist patterns
        default_blacklist = [
            ('PO Box', 'contains', 'medium', 'PO Box addresses require verification'),
            ('freight forward', 'contains', 'high', 'Freight forwarding services'),
            ('package forward', 'contains', 'high', 'Package forwarding services'),
            ('mail forward', 'contains', 'high', 'Mail forwarding services'),
            ('Ukraine', 'contains', 'high', 'High-risk region'),
            ('Russia', 'contains', 'blocked', 'Blocked region'),
        ]
        
        for pattern, match_type, risk_level, reason in default_blacklist:
            cursor.execute("""
                INSERT OR IGNORE INTO address_blacklist 
                (address_pattern, match_type, risk_level, reason, created_by)
                VALUES (?, ?, ?, ?, 1)
            """, (pattern, match_type, risk_level, reason))
        
        # 5. Create Google Sheets sync log table
        print("📝 Step 5: Creating Google Sheets sync tracking...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sheets_sync_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sync_type VARCHAR(50),  -- 'import', 'export', 'status_update'
                spreadsheet_id VARCHAR(200),
                sheet_name VARCHAR(100),
                rows_processed INTEGER DEFAULT 0,
                rows_success INTEGER DEFAULT 0,
                rows_error INTEGER DEFAULT 0,
                error_details JSON,
                started_by INTEGER,
                started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                completed_at DATETIME,
                status VARCHAR(20) DEFAULT 'running',  -- 'running', 'completed', 'failed'
                FOREIGN KEY (started_by) REFERENCES users (id)
            )
        """)
        
        # 6. Create order status history table
        print("📝 Step 6: Creating order status history...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS order_status_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id VARCHAR(100) NOT NULL,
                old_status VARCHAR(50),
                new_status VARCHAR(50) NOT NULL,
                changed_by INTEGER,
                change_reason TEXT,
                additional_data JSON,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES orders (id),
                FOREIGN KEY (changed_by) REFERENCES users (id)
            )
        """)
        
        # 7. Create role-based permissions view
        print("📝 Step 7: Creating role-based views...")
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS user_permissions AS
            SELECT 
                u.id as user_id,
                u.email,
                u.username,
                ur.role_name,
                ur.permissions,
                u.assigned_accounts,
                u.is_active
            FROM users u
            LEFT JOIN user_roles ur ON u.role_id = ur.id
        """)
        
        # 8. Update existing orders with default values
        print("📝 Step 8: Updating existing orders...")
        cursor.execute("""
            UPDATE orders 
            SET sync_source = 'existing',
                blacklist_checked = 0,
                blacklist_status = 'pending',
                last_status_change = created_at,
                status_changed_by = user_id
            WHERE sync_source IS NULL
        """)
        
        # 9. Create indexes for performance
        print("📝 Step 9: Creating performance indexes...")
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_orders_sync_source ON orders (sync_source)",
            "CREATE INDEX IF NOT EXISTS idx_orders_sheets_row ON orders (sheets_row_id)",
            "CREATE INDEX IF NOT EXISTS idx_orders_assigned_to ON orders (assigned_to_user_id)",
            "CREATE INDEX IF NOT EXISTS idx_orders_blacklist ON orders (blacklist_status)",
            "CREATE INDEX IF NOT EXISTS idx_orders_status_change ON orders (last_status_change)",
            "CREATE INDEX IF NOT EXISTS idx_blacklist_active ON address_blacklist (is_active)",
            "CREATE INDEX IF NOT EXISTS idx_status_history_order ON order_status_history (order_id)",
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
        
        conn.commit()
        print("✅ Migration 003 completed successfully!")
        
        # Display summary
        cursor.execute("SELECT COUNT(*) FROM user_roles")
        roles_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM address_blacklist")
        blacklist_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM orders")
        orders_count = cursor.fetchone()[0]
        
        print(f"""
📊 Migration Summary:
   👥 User Roles: {roles_count}
   🚫 Blacklist Patterns: {blacklist_count}
   📦 Orders Updated: {orders_count}
   📈 New Tables: 4 (user_roles, address_blacklist, sheets_sync_log, order_status_history)
   🔍 New Indexes: {len(indexes)}
        """)
        
        return True
        
    except Exception as e:
        print(f"❌ Migration 003 failed: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def rollback_migration():
    """Rollback migration 003 (if needed)"""
    print("⚠️  Rollback for migration 003 not implemented - contact admin if needed")
    print("    This migration adds columns and tables that other features may depend on")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--rollback":
        rollback_migration()
    else:
        success = run_migration()
        if success:
            print("🎉 Ready for multi-role Google Sheets integration!")
        else:
            print("💥 Migration failed - check logs above")
            sys.exit(1)