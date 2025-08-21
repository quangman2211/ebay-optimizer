"""
Initial Database Schema Migration
Creates all tables for eBay Optimizer application
"""

from sqlalchemy import text
from app.db.database import engine
from app.models.database_models import Base, User, Listing, Order, Source, SourceProduct, Account, SystemSetting, ActivityLog


def upgrade():
    """Create all tables"""
    print("🚀 Creating database tables...")
    
    # Create all tables defined in models
    Base.metadata.create_all(bind=engine)
    
    # Create additional indexes manually if needed
    with engine.begin() as conn:
        # Additional indexes for performance
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_listings_search 
            ON listings(title, category, keywords);
        """))
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_orders_customer 
            ON orders(customer_name, customer_email);
        """))
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_orders_dates 
            ON orders(order_date, expected_ship_date, actual_ship_date);
        """))
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_accounts_metrics 
            ON accounts(health_score, feedback_score, monthly_revenue);
        """))
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_source_products_search 
            ON source_products(name, brand, category, sku);
        """))
        
        print("✅ Database tables created successfully")


def downgrade():
    """Drop all tables"""
    print("⚠️  Dropping all database tables...")
    
    # Drop all tables
    Base.metadata.drop_all(bind=engine)
    
    print("✅ Database tables dropped successfully")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        downgrade()
    else:
        upgrade()