#!/usr/bin/env python3
"""
Migration Script 002: Multi-Account Support
Purpose: Update database for multi-account eBay management system
Date: 2025-01-21
Safe to run: YES (adds new tables and columns, preserves existing data)
"""

import sqlite3
import os
from datetime import datetime

# Database file path
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "ebay_optimizer.db")

def backup_database():
    """Create backup of current database"""
    backup_path = f"{DB_PATH}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    if os.path.exists(DB_PATH):
        import shutil
        shutil.copy2(DB_PATH, backup_path)
        print(f"✅ Database backup created: {backup_path}")
    else:
        print("⚠️  Database file not found, will create new one")

def execute_sql(cursor, sql, description):
    """Execute SQL with error handling"""
    try:
        cursor.execute(sql)
        print(f"✅ {description}")
    except sqlite3.Error as e:
        if "already exists" in str(e).lower() or "duplicate column name" in str(e).lower():
            print(f"⚠️  {description} (already exists)")
        else:
            print(f"❌ Error in {description}: {e}")
            raise

def migrate_database():
    """Run migration to add multi-account support"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("🚀 Starting Migration 002: Multi-Account Support")
    print("="*50)
    
    try:
        # 1. Add new columns to existing tables
        print("\n📝 Step 1: Enhancing existing tables...")
        
        # Add account_id to listings
        execute_sql(cursor, """
        ALTER TABLE listings ADD COLUMN account_id INTEGER REFERENCES accounts(id)
        """, "Added account_id to listings")
        
        # Add source_product_id to listings
        execute_sql(cursor, """
        ALTER TABLE listings ADD COLUMN source_product_id TEXT REFERENCES source_products(id)
        """, "Added source_product_id to listings")
        
        # Add draft_listing_id to listings
        execute_sql(cursor, """
        ALTER TABLE listings ADD COLUMN draft_listing_id TEXT REFERENCES draft_listings(id)
        """, "Added draft_listing_id to listings")
        
        # Rename item_id to ebay_item_id in listings for clarity
        execute_sql(cursor, """
        ALTER TABLE listings ADD COLUMN ebay_item_id TEXT
        """, "Added ebay_item_id to listings")
        
        # Add listing_type to listings
        execute_sql(cursor, """
        ALTER TABLE listings ADD COLUMN listing_type TEXT DEFAULT 'fixed'
        """, "Added listing_type to listings")
        
        # Add ebay_url to listings
        execute_sql(cursor, """
        ALTER TABLE listings ADD COLUMN ebay_url TEXT
        """, "Added ebay_url to listings")
        
        # Add account_id to orders
        execute_sql(cursor, """
        ALTER TABLE orders ADD COLUMN account_id INTEGER REFERENCES accounts(id)
        """, "Added account_id to orders")
        
        # Add ebay_order_id to orders
        execute_sql(cursor, """
        ALTER TABLE orders ADD COLUMN ebay_order_id TEXT
        """, "Added ebay_order_id to orders")
        
        # Add ebay_transaction_id to orders
        execute_sql(cursor, """
        ALTER TABLE orders ADD COLUMN ebay_transaction_id TEXT
        """, "Added ebay_transaction_id to orders")
        
        # Add customer_username to orders
        execute_sql(cursor, """
        ALTER TABLE orders ADD COLUMN customer_username TEXT
        """, "Added customer_username to orders")
        
        # Add quantity to orders
        execute_sql(cursor, """
        ALTER TABLE orders ADD COLUMN quantity INTEGER DEFAULT 1
        """, "Added quantity to orders")
        
        # Add shipping_cost to orders
        execute_sql(cursor, """
        ALTER TABLE orders ADD COLUMN shipping_cost REAL
        """, "Added shipping_cost to orders")
        
        # Add total_amount to orders
        execute_sql(cursor, """
        ALTER TABLE orders ADD COLUMN total_amount REAL
        """, "Added total_amount to orders")
        
        # Add ebay_fees to orders
        execute_sql(cursor, """
        ALTER TABLE orders ADD COLUMN ebay_fees REAL
        """, "Added ebay_fees to orders")
        
        # Add Google Drive fields to source_products
        execute_sql(cursor, """
        ALTER TABLE source_products ADD COLUMN gdrive_folder_url TEXT
        """, "Added gdrive_folder_url to source_products")
        
        execute_sql(cursor, """
        ALTER TABLE source_products ADD COLUMN image_notes TEXT
        """, "Added image_notes to source_products")
        
        execute_sql(cursor, """
        ALTER TABLE source_products ADD COLUMN is_approved INTEGER DEFAULT 0
        """, "Added is_approved to source_products")
        
        # Rename source_products.name to title for consistency
        execute_sql(cursor, """
        ALTER TABLE source_products ADD COLUMN title TEXT
        """, "Added title to source_products")
        
        # Add Google Sheets integration to accounts
        execute_sql(cursor, """
        ALTER TABLE accounts ADD COLUMN sheet_id TEXT
        """, "Added sheet_id to accounts")
        
        execute_sql(cursor, """
        ALTER TABLE accounts ADD COLUMN sheet_url TEXT
        """, "Added sheet_url to accounts")
        
        # 2. Create new tables
        print("\n🆕 Step 2: Creating new tables...")
        
        # Create draft_listings table
        execute_sql(cursor, """
        CREATE TABLE IF NOT EXISTS draft_listings (
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            account_id INTEGER NOT NULL REFERENCES accounts(id),
            source_product_id TEXT REFERENCES source_products(id),
            
            -- Draft Info (Customized per account)
            title TEXT NOT NULL,
            description TEXT,
            category TEXT,
            price REAL,
            quantity INTEGER DEFAULT 1,
            condition TEXT DEFAULT 'new',
            
            -- Google Drive Images (Edited by employees)
            gdrive_folder_url TEXT,
            image_status TEXT DEFAULT 'pending',
            edited_by TEXT,
            edit_date TEXT,
            
            -- eBay Settings
            listing_type TEXT DEFAULT 'fixed',
            duration_days INTEGER DEFAULT 30,
            start_price REAL,
            buy_it_now_price REAL,
            
            -- Business
            cost_price REAL,
            profit_margin REAL,
            
            -- Status
            status TEXT DEFAULT 'draft',
            scheduled_date TEXT,
            notes TEXT,
            
            -- Timestamps
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """, "Created draft_listings table")
        
        # Create messages table
        execute_sql(cursor, """
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            account_id INTEGER NOT NULL REFERENCES accounts(id),
            listing_id TEXT REFERENCES listings(id),
            order_id TEXT REFERENCES orders(id),
            
            -- Message Info
            ebay_message_id TEXT,
            message_type TEXT DEFAULT 'general',
            subject TEXT,
            message_text TEXT,
            
            -- Participants
            sender_username TEXT,
            recipient_username TEXT,
            direction TEXT,
            
            -- Status
            is_read INTEGER DEFAULT 0,
            is_replied INTEGER DEFAULT 0,
            priority TEXT DEFAULT 'normal',
            
            -- Dates
            message_date TEXT,
            reply_by_date TEXT,
            
            -- Timestamps
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """, "Created messages table")
        
        # Create account_sheets table
        execute_sql(cursor, """
        CREATE TABLE IF NOT EXISTS account_sheets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL REFERENCES accounts(id),
            
            -- Google Sheets Info
            sheet_id TEXT NOT NULL,
            sheet_name TEXT NOT NULL,
            sheet_url TEXT,
            
            -- Sheet Structure
            sheet_type TEXT NOT NULL,
            headers TEXT,
            last_row INTEGER DEFAULT 1,
            
            -- Sync Info
            auto_sync INTEGER DEFAULT 1,
            sync_frequency INTEGER DEFAULT 60,
            last_sync TEXT,
            sync_status TEXT DEFAULT 'pending',
            
            -- Timestamps
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            
            UNIQUE(account_id, sheet_type)
        )
        """, "Created account_sheets table")
        
        # 3. Create indexes for performance
        print("\n📊 Step 3: Creating performance indexes...")
        
        # Listings indexes
        execute_sql(cursor, """
        CREATE INDEX IF NOT EXISTS idx_listings_account ON listings(account_id, status)
        """, "Created index on listings(account_id, status)")
        
        execute_sql(cursor, """
        CREATE INDEX IF NOT EXISTS idx_listings_source_product ON listings(source_product_id)
        """, "Created index on listings(source_product_id)")
        
        execute_sql(cursor, """
        CREATE INDEX IF NOT EXISTS idx_listings_ebay_item ON listings(ebay_item_id)
        """, "Created index on listings(ebay_item_id)")
        
        # Orders indexes
        execute_sql(cursor, """
        CREATE INDEX IF NOT EXISTS idx_orders_account ON orders(account_id, order_date)
        """, "Created index on orders(account_id, order_date)")
        
        execute_sql(cursor, """
        CREATE INDEX IF NOT EXISTS idx_orders_ebay ON orders(ebay_order_id, ebay_transaction_id)
        """, "Created index on orders(ebay_order_id, ebay_transaction_id)")
        
        # Draft listings indexes
        execute_sql(cursor, """
        CREATE INDEX IF NOT EXISTS idx_draft_account ON draft_listings(account_id, status)
        """, "Created index on draft_listings(account_id, status)")
        
        execute_sql(cursor, """
        CREATE INDEX IF NOT EXISTS idx_draft_source_product ON draft_listings(source_product_id)
        """, "Created index on draft_listings(source_product_id)")
        
        execute_sql(cursor, """
        CREATE INDEX IF NOT EXISTS idx_draft_image_status ON draft_listings(image_status)
        """, "Created index on draft_listings(image_status)")
        
        # Messages indexes
        execute_sql(cursor, """
        CREATE INDEX IF NOT EXISTS idx_messages_account ON messages(account_id, is_read)
        """, "Created index on messages(account_id, is_read)")
        
        execute_sql(cursor, """
        CREATE INDEX IF NOT EXISTS idx_messages_priority ON messages(priority, is_replied)
        """, "Created index on messages(priority, is_replied)")
        
        # Account sheets indexes
        execute_sql(cursor, """
        CREATE INDEX IF NOT EXISTS idx_account_sheets_sync ON account_sheets(auto_sync, last_sync)
        """, "Created index on account_sheets(auto_sync, last_sync)")
        
        # 4. Data migration - copy existing data
        print("\n🔄 Step 4: Migrating existing data...")
        
        # Copy existing item_id to ebay_item_id
        execute_sql(cursor, """
        UPDATE listings SET ebay_item_id = item_id WHERE item_id IS NOT NULL
        """, "Migrated item_id to ebay_item_id")
        
        # Copy existing source_products.name to title where title is null
        execute_sql(cursor, """
        UPDATE source_products SET title = name WHERE title IS NULL AND name IS NOT NULL
        """, "Migrated source_products.name to title")
        
        # Set default account_id for existing listings (use first account or create default)
        cursor.execute("SELECT COUNT(*) FROM accounts")
        account_count = cursor.fetchone()[0]
        
        if account_count == 0:
            # Create default account for existing data
            execute_sql(cursor, """
            INSERT INTO accounts (user_id, ebay_username, email, status, created_at, updated_at)
            SELECT 1, 'default_account', 'default@ebay.com', 'active', 
                   datetime('now'), datetime('now')
            WHERE NOT EXISTS (SELECT 1 FROM accounts WHERE id = 1)
            """, "Created default account for migration")
        
        # Set account_id for existing listings
        execute_sql(cursor, """
        UPDATE listings SET account_id = 1 WHERE account_id IS NULL
        """, "Set default account_id for existing listings")
        
        # Set account_id for existing orders
        execute_sql(cursor, """
        UPDATE orders SET account_id = 1 WHERE account_id IS NULL
        """, "Set default account_id for existing orders")
        
        # 5. Insert sample data for testing
        print("\n🎯 Step 5: Inserting sample data...")
        
        # Insert sample draft listing
        execute_sql(cursor, """
        INSERT OR IGNORE INTO draft_listings (
            id, user_id, account_id, title, description, price, 
            gdrive_folder_url, image_status, status, created_at
        ) VALUES (
            'DRAFT001', 1, 1, 'Sample Draft Listing', 
            'This is a sample draft listing for testing',
            99.99, 'https://drive.google.com/drive/folders/sample_folder',
            'pending', 'draft', datetime('now')
        )
        """, "Inserted sample draft listing")
        
        # Insert sample message
        execute_sql(cursor, """
        INSERT OR IGNORE INTO messages (
            id, user_id, account_id, message_type, subject, 
            message_text, sender_username, direction, 
            is_read, priority, created_at
        ) VALUES (
            'MSG001', 1, 1, 'question', 'Sample Question',
            'This is a sample message for testing',
            'test_buyer', 'inbound', 0, 'normal', datetime('now')
        )
        """, "Inserted sample message")
        
        # Insert sample account sheet mapping
        execute_sql(cursor, """
        INSERT OR IGNORE INTO account_sheets (
            account_id, sheet_id, sheet_name, sheet_type,
            headers, auto_sync, created_at
        ) VALUES (
            1, 'sample_sheet_id', 'Account 1 - Listings', 'listings',
            '["Listing ID", "eBay Item ID", "Title", "Price", "Status"]',
            1, datetime('now')
        )
        """, "Inserted sample account sheet mapping")
        
        # Commit all changes
        conn.commit()
        
        print("\n" + "="*50)
        print("🎉 Migration 002 completed successfully!")
        print("✅ Enhanced existing tables with multi-account support")
        print("✅ Added 3 new tables: draft_listings, messages, account_sheets")
        print("✅ Created performance indexes")
        print("✅ Migrated existing data safely")
        print("✅ Added sample data for testing")
        print("\n📋 Next Steps:")
        print("1. Update API endpoints to support multi-account")
        print("2. Update frontend to handle new tables")
        print("3. Test multi-account workflow")
        print("="*50)
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Migration failed: {e}")
        raise
    finally:
        conn.close()

def verify_migration():
    """Verify migration was successful"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("\n🔍 Verifying migration...")
    
    # Check new tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    expected_tables = ['draft_listings', 'messages', 'account_sheets']
    for table in expected_tables:
        if table in tables:
            print(f"✅ Table {table} exists")
        else:
            print(f"❌ Table {table} missing")
    
    # Check new columns in existing tables
    cursor.execute("PRAGMA table_info(listings)")
    listing_columns = [row[1] for row in cursor.fetchall()]
    
    expected_columns = ['account_id', 'source_product_id', 'draft_listing_id', 'ebay_item_id']
    for column in expected_columns:
        if column in listing_columns:
            print(f"✅ Column listings.{column} exists")
        else:
            print(f"❌ Column listings.{column} missing")
    
    # Count records
    cursor.execute("SELECT COUNT(*) FROM draft_listings")
    draft_count = cursor.fetchone()[0]
    print(f"📊 Draft listings: {draft_count} records")
    
    cursor.execute("SELECT COUNT(*) FROM messages")
    message_count = cursor.fetchone()[0]
    print(f"📊 Messages: {message_count} records")
    
    cursor.execute("SELECT COUNT(*) FROM account_sheets")
    sheet_count = cursor.fetchone()[0]
    print(f"📊 Account sheets: {sheet_count} records")
    
    conn.close()
    print("✅ Migration verification completed")

if __name__ == "__main__":
    print("🚀 eBay Optimizer - Multi-Account Migration")
    print("="*50)
    
    # Create backup
    backup_database()
    
    # Run migration
    migrate_database()
    
    # Verify results
    verify_migration()
    
    print("\n🎯 Migration completed successfully!")
    print("Database is ready for multi-account eBay management.")