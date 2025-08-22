#!/usr/bin/env python3
"""
Enhanced Database Migration: Supplier and Product Management Schema
Date: 2025-08-22
Purpose: Adds comprehensive supplier management and product catalog functionality
Features: Performance tracking, pricing optimization, inventory management
"""

import sqlite3
import os
import sys
from pathlib import Path

# Add backend to path for imports
backend_path = Path(__file__).parent.parent
sys.path.append(str(backend_path))

def create_enhanced_tables(cursor):
    """Create enhanced supplier and product management tables"""
    
    print("🏗️  Creating supplier management tables...")
    
    # Create suppliers table with comprehensive management features
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL,
            company_name VARCHAR(150),
            contact_person VARCHAR(100),
            email VARCHAR(100),
            phone VARCHAR(20),
            address TEXT,
            country VARCHAR(50),
            website VARCHAR(200),
            business_type VARCHAR(50) DEFAULT 'manufacturer',
            
            -- Performance tracking
            performance_rating DECIMAL(3,2) DEFAULT 0.0,
            reliability_score INTEGER DEFAULT 50,
            total_orders INTEGER DEFAULT 0,
            successful_orders INTEGER DEFAULT 0,
            average_delivery_days INTEGER DEFAULT 15,
            
            -- Business terms
            payment_terms VARCHAR(100) DEFAULT 'NET 30',
            minimum_order_value DECIMAL(10,2) DEFAULT 0.0,
            currency VARCHAR(10) DEFAULT 'USD',
            discount_tier VARCHAR(20) DEFAULT 'standard',
            
            -- Internal tracking
            status VARCHAR(20) DEFAULT 'active',
            priority_level INTEGER DEFAULT 3,
            notes TEXT,
            tags VARCHAR(500),
            
            -- Timestamps
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_contact_date TIMESTAMP,
            
            UNIQUE(email)
        )
    ''')
    
    # Create products table with comprehensive catalog features
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku VARCHAR(50) NOT NULL UNIQUE,
            name VARCHAR(200) NOT NULL,
            description TEXT,
            category VARCHAR(100),
            subcategory VARCHAR(100),
            brand VARCHAR(100),
            
            -- Supplier relationships
            primary_supplier_id INTEGER,
            backup_supplier_id INTEGER,
            
            -- Pricing and costs
            cost_price DECIMAL(10,2),
            selling_price DECIMAL(10,2),
            profit_margin_percent DECIMAL(5,2),
            retail_price DECIMAL(10,2),
            
            -- Inventory management
            stock_level INTEGER DEFAULT 0,
            reorder_point INTEGER DEFAULT 10,
            max_stock_level INTEGER DEFAULT 100,
            stock_status VARCHAR(20) DEFAULT 'in_stock',
            
            -- Physical properties
            weight_kg DECIMAL(8,3),
            dimensions_cm VARCHAR(50),
            color VARCHAR(50),
            size VARCHAR(50),
            material VARCHAR(100),
            
            -- eBay listing optimization
            ebay_category_id VARCHAR(20),
            ebay_condition VARCHAR(30) DEFAULT 'New',
            shipping_cost DECIMAL(8,2) DEFAULT 0.0,
            handling_days INTEGER DEFAULT 1,
            
            -- Performance tracking
            total_sales INTEGER DEFAULT 0,
            total_revenue DECIMAL(12,2) DEFAULT 0.0,
            average_rating DECIMAL(3,2) DEFAULT 0.0,
            return_rate_percent DECIMAL(5,2) DEFAULT 0.0,
            
            -- Status and metadata
            status VARCHAR(20) DEFAULT 'active',
            tags VARCHAR(500),
            notes TEXT,
            
            -- Timestamps
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_sold_date TIMESTAMP,
            
            FOREIGN KEY (primary_supplier_id) REFERENCES suppliers(id),
            FOREIGN KEY (backup_supplier_id) REFERENCES suppliers(id)
        )
    ''')
    
    # Create supplier_products junction table for many-to-many relationships
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS supplier_products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            
            -- Supplier-specific product details
            supplier_sku VARCHAR(100),
            supplier_name VARCHAR(200),
            supplier_cost DECIMAL(10,2),
            lead_time_days INTEGER DEFAULT 7,
            minimum_quantity INTEGER DEFAULT 1,
            
            -- Quality and reliability
            quality_rating INTEGER DEFAULT 5,
            last_order_date TIMESTAMP,
            total_ordered INTEGER DEFAULT 0,
            defect_rate_percent DECIMAL(5,2) DEFAULT 0.0,
            
            -- Status and preferences
            is_preferred BOOLEAN DEFAULT FALSE,
            status VARCHAR(20) DEFAULT 'active',
            notes TEXT,
            
            -- Timestamps
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
            UNIQUE(supplier_id, product_id)
        )
    ''')
    
    # Create price_history table for cost tracking
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            supplier_id INTEGER,
            
            -- Price tracking
            old_cost DECIMAL(10,2),
            new_cost DECIMAL(10,2),
            old_selling_price DECIMAL(10,2),
            new_selling_price DECIMAL(10,2),
            
            -- Change details
            change_reason VARCHAR(100),
            change_type VARCHAR(20), -- 'cost_increase', 'cost_decrease', 'price_update'
            impact_percent DECIMAL(5,2),
            
            -- Context
            changed_by VARCHAR(100),
            notes TEXT,
            
            -- Timestamp
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
            FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE SET NULL
        )
    ''')
    
    # Create order_items table for detailed order line items
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER,
            
            -- Item details
            sku VARCHAR(50),
            product_name VARCHAR(200),
            quantity INTEGER NOT NULL,
            unit_price DECIMAL(10,2),
            unit_cost DECIMAL(10,2),
            total_price DECIMAL(10,2),
            total_cost DECIMAL(10,2),
            profit_amount DECIMAL(10,2),
            profit_margin_percent DECIMAL(5,2),
            
            -- Fulfillment details
            supplier_id INTEGER,
            supplier_order_id VARCHAR(100),
            tracking_number VARCHAR(100),
            fulfillment_status VARCHAR(30) DEFAULT 'pending',
            shipped_date TIMESTAMP,
            delivered_date TIMESTAMP,
            
            -- Quality tracking
            customer_rating INTEGER,
            customer_feedback TEXT,
            return_requested BOOLEAN DEFAULT FALSE,
            return_reason VARCHAR(200),
            
            -- Timestamps
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL,
            FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE SET NULL
        )
    ''')
    
    print("✅ Enhanced supplier and product tables created successfully")

def create_indexes(cursor):
    """Create indexes for better query performance"""
    
    print("🔍 Creating performance indexes...")
    
    # Supplier indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_suppliers_status ON suppliers(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_suppliers_performance ON suppliers(performance_rating DESC)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_suppliers_country ON suppliers(country)')
    
    # Product indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_category ON products(category, subcategory)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_supplier ON products(primary_supplier_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_status ON products(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_stock ON products(stock_level)')
    
    # Junction table indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_supplier_products_supplier ON supplier_products(supplier_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_supplier_products_product ON supplier_products(product_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_supplier_products_preferred ON supplier_products(is_preferred)')
    
    # Price history indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_price_history_product ON price_history(product_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_price_history_date ON price_history(created_at DESC)')
    
    # Order items indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_order_items_product ON order_items(product_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_order_items_supplier ON order_items(supplier_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_order_items_status ON order_items(fulfillment_status)')
    
    print("✅ Performance indexes created successfully")

def update_existing_orders_table(cursor):
    """Add new columns to existing orders table for enhanced functionality"""
    
    print("🔧 Updating existing orders table...")
    
    # Check if orders table exists and add new columns
    cursor.execute("PRAGMA table_info(orders)")
    existing_columns = [column[1] for column in cursor.fetchall()]
    
    new_columns = [
        ('total_cost', 'DECIMAL(10,2)', '0.0'),
        ('total_profit', 'DECIMAL(10,2)', '0.0'),
        ('profit_margin_percent', 'DECIMAL(5,2)', '0.0'),
        ('supplier_count', 'INTEGER', '0'),
        ('fulfillment_complexity', 'VARCHAR(20)', "'simple'"),
        ('estimated_delivery', 'DATE', 'NULL'),
        ('shipping_method', 'VARCHAR(50)', "'standard'"),
        ('shipping_cost', 'DECIMAL(8,2)', '0.0'),
        ('tax_amount', 'DECIMAL(8,2)', '0.0'),
        ('discount_amount', 'DECIMAL(8,2)', '0.0'),
        ('customer_notes', 'TEXT', 'NULL'),
        ('internal_notes', 'TEXT', 'NULL'),
        ('risk_level', 'VARCHAR(20)', "'low'"),
        ('priority', 'INTEGER', '3')
    ]
    
    for col_name, col_type, default_value in new_columns:
        if col_name not in existing_columns:
            cursor.execute(f'ALTER TABLE orders ADD COLUMN {col_name} {col_type} DEFAULT {default_value}')
            print(f"  ➕ Added column: {col_name}")
    
    print("✅ Orders table updated successfully")

def insert_sample_data(cursor):
    """Insert sample data for testing and demonstration"""
    
    print("📊 Inserting sample data...")
    
    # Sample suppliers
    suppliers_data = [
        ('AliExpress Premium Supplier', 'Guangzhou Trading Co.', 'Li Wei', 'li.wei@gztrade.com', '+86-20-1234-5678', 
         'Guangzhou, China', 'China', 'https://gztrade.com', 'manufacturer', 4.5, 85, 150, 142, 12, 'NET 30', 100.0, 'USD', 'premium'),
        ('US Dropship Warehouse', 'American Supply Corp', 'John Smith', 'john@americansupply.com', '+1-555-0123', 
         'Los Angeles, CA', 'USA', 'https://americansupply.com', 'distributor', 4.2, 78, 89, 84, 3, 'NET 15', 50.0, 'USD', 'standard'),
        ('European Electronics', 'EuroTech GmbH', 'Hans Mueller', 'hans@eurotech.de', '+49-30-1234567', 
         'Berlin, Germany', 'Germany', 'https://eurotech.de', 'manufacturer', 4.7, 92, 67, 65, 7, 'NET 45', 200.0, 'EUR', 'premium'),
    ]
    
    for supplier in suppliers_data:
        cursor.execute('''
            INSERT OR IGNORE INTO suppliers 
            (name, company_name, contact_person, email, phone, address, country, website, business_type,
             performance_rating, reliability_score, total_orders, successful_orders, average_delivery_days,
             payment_terms, minimum_order_value, currency, discount_tier)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', supplier)
    
    # Sample products
    products_data = [
        ('SKU-001', 'Wireless Bluetooth Headphones', 'High-quality wireless headphones with noise cancellation', 
         'Electronics', 'Audio', 'TechBrand', 1, 2, 25.50, 49.99, 49.0, 79.99, 50, 10, 200, 'in_stock',
         0.3, '20x15x8', 'Black', 'One Size', 'Plastic/Metal', '112233', 'New', 5.99, 1),
        ('SKU-002', 'USB-C Fast Charging Cable', '3ft USB-C to USB-A fast charging cable',
         'Electronics', 'Accessories', 'CableCorp', 1, 3, 3.20, 12.99, 75.4, 19.99, 150, 25, 500, 'in_stock',
         0.1, '10x5x2', 'White', '3ft', 'TPE', '445566', 'New', 2.99, 1),
        ('SKU-003', 'Ergonomic Office Chair', 'Adjustable height office chair with lumbar support',
         'Furniture', 'Office', 'ComfortSeating', 2, 1, 89.00, 199.99, 55.5, 299.99, 25, 5, 100, 'in_stock',
         15.5, '65x65x110', 'Gray', 'Standard', 'Mesh/Plastic', '778899', 'New', 25.00, 2),
    ]
    
    for product in products_data:
        cursor.execute('''
            INSERT OR IGNORE INTO products 
            (sku, name, description, category, subcategory, brand, primary_supplier_id, backup_supplier_id,
             cost_price, selling_price, profit_margin_percent, retail_price, stock_level, reorder_point, 
             max_stock_level, stock_status, weight_kg, dimensions_cm, color, size, material, 
             ebay_category_id, ebay_condition, shipping_cost, handling_days)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', product)
    
    # Sample supplier-product relationships
    cursor.execute('''
        INSERT OR IGNORE INTO supplier_products 
        (supplier_id, product_id, supplier_sku, supplier_name, supplier_cost, lead_time_days, 
         minimum_quantity, quality_rating, is_preferred)
        VALUES 
        (1, 1, 'AE-WBH-001', 'Premium Wireless Headphones', 25.50, 10, 5, 5, TRUE),
        (2, 1, 'US-WBH-001', 'Wireless Headphones - US Stock', 28.00, 2, 1, 4, FALSE),
        (1, 2, 'AE-USBC-002', 'Fast Charge Cable 3ft', 3.20, 7, 10, 5, TRUE),
        (3, 3, 'EU-CHAIR-003', 'Ergonomic Office Chair Premium', 89.00, 14, 1, 5, TRUE)
    ''')
    
    print("✅ Sample data inserted successfully")

def verify_schema(cursor):
    """Verify that all tables and indexes were created correctly"""
    
    print("🔍 Verifying enhanced schema...")
    
    # Check tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    
    expected_tables = [
        'suppliers', 'products', 'supplier_products', 'price_history', 'order_items'
    ]
    
    for table in expected_tables:
        if table in tables:
            print(f"  ✅ Table '{table}' created successfully")
            # Count records
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"     📊 {count} records")
        else:
            print(f"  ❌ Table '{table}' missing!")
    
    # Check indexes
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")
    indexes = [row[0] for row in cursor.fetchall()]
    print(f"  🔍 Created {len(indexes)} performance indexes")
    
    print("✅ Schema verification completed")

def main():
    """Main migration execution"""
    print("🚀 Starting Enhanced Supplier & Product Management Migration")
    print("=" * 60)
    
    # Database connection
    db_path = os.path.join(os.path.dirname(__file__), '..', 'ebay_optimizer.db')
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Execute migration steps
        create_enhanced_tables(cursor)
        create_indexes(cursor)
        update_existing_orders_table(cursor)
        insert_sample_data(cursor)
        verify_schema(cursor)
        
        # Commit changes
        conn.commit()
        
        print("=" * 60)
        print("🎉 Migration completed successfully!")
        print(f"📁 Database: {db_path}")
        print("🔧 Enhanced Features:")
        print("   • Comprehensive supplier management")
        print("   • Product catalog with supplier mapping")
        print("   • Performance tracking and analytics")
        print("   • Pricing optimization and cost history")
        print("   • Advanced order item management")
        print("   • SOLID architecture ready")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        if conn:
            conn.rollback()
        sys.exit(1)
    
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()