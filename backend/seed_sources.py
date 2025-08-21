#!/usr/bin/env python3
"""
Script để seed sample sources vào database
"""

import sys
import os
from datetime import datetime, timedelta
import random

# Add backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.database import engine, SessionLocal
from app.models.database_models import Source, SourceProduct, SourceStatusEnum, User
from sqlalchemy.orm import Session


def seed_sources(db: Session, user_id: int):
    """Seed sample sources and their products for user"""
    
    # Sample source data
    sample_sources = [
        {
            "name": "AliExpress Premium Supplier",
            "website_url": "https://aliexpress.com/store/12345",
            "status": SourceStatusEnum.CONNECTED,
            "api_key": "AE_API_KEY_123456789",
            "last_sync": datetime.now() - timedelta(hours=2),
            "total_products": 0,  # Will be calculated
        },
        {
            "name": "DHgate Electronics Store",
            "website_url": "https://dhgate.com/store/tech-world",
            "status": SourceStatusEnum.CONNECTED,
            "api_key": "DH_API_KEY_987654321",
            "last_sync": datetime.now() - timedelta(hours=6),
            "total_products": 0
        },
        {
            "name": "1688.com Factory Direct",
            "website_url": "https://1688.com/factory/direct-electronics",
            "status": SourceStatusEnum.CONNECTED,
            "last_sync": datetime.now() - timedelta(days=1),
            "total_products": 0
        },
        {
            "name": "Amazon FBA Wholesale",
            "website_url": "https://amazon.com/wholesale/electronics",
            "status": SourceStatusEnum.CONNECTED,
            "api_key": "AMZ_API_KEY_456789123",
            "last_sync": datetime.now() - timedelta(hours=12),
            "total_products": 0
        },
        {
            "name": "CJ Dropshipping",
            "website_url": "https://cjdropshipping.com/supplier/tech-plus",
            "status": SourceStatusEnum.SYNCING,
            "last_sync": datetime.now() - timedelta(days=3),
            "total_products": 0
        }
    ]
    
    # Sample products for each source
    source_products = [
        # AliExpress products
        [
            {"name": "iPhone 15 Pro Max Case Clear", "source_price": 3.50, "source_sku": "AE-CASE-IP15PM", "category": "electronics"},
            {"name": "USB-C Fast Charger 65W", "source_price": 12.99, "source_sku": "AE-CHARGER-65W", "category": "electronics"},
            {"name": "Bluetooth Earbuds Pro", "source_price": 25.00, "source_sku": "AE-BUDS-PRO", "category": "electronics"},
            {"name": "Wireless Charging Pad", "source_price": 8.99, "source_sku": "AE-CHARGE-PAD", "category": "electronics"}
        ],
        # DHgate products  
        [
            {"name": "Samsung Galaxy S24 Screen Protector", "source_price": 2.50, "source_sku": "DH-SCREEN-S24", "category": "electronics"},
            {"name": "Phone Ring Holder Stand", "source_price": 1.99, "source_sku": "DH-RING-STAND", "category": "electronics"},
            {"name": "Car Phone Mount Magnetic", "source_price": 6.50, "source_sku": "DH-CAR-MOUNT", "category": "automotive"}
        ],
        # 1688 products
        [
            {"name": "Silicone Phone Cases Bulk 50pcs", "source_price": 45.00, "source_sku": "1688-CASE-BULK", "category": "electronics"},
            {"name": "USB Cables Mixed Types 100pcs", "source_price": 89.99, "source_sku": "1688-CABLE-MIX", "category": "electronics"}
        ],
        # Amazon products
        [
            {"name": "Apple AirPods Pro 2nd Gen", "source_price": 199.99, "source_sku": "AMZ-AIRPODS-PRO2", "category": "electronics"},
            {"name": "MacBook Pro 14 M3 256GB", "source_price": 1599.99, "source_sku": "AMZ-MBP14-M3", "category": "electronics"},
            {"name": "iPad Air 10.9 WiFi 64GB", "source_price": 449.99, "source_sku": "AMZ-IPAD-AIR", "category": "electronics"}
        ],
        # CJ Dropshipping products
        [
            {"name": "Gaming Mechanical Keyboard", "source_price": 35.00, "source_sku": "CJ-KB-GAMING", "category": "electronics"},
            {"name": "Wireless Gaming Mouse RGB", "source_price": 22.50, "source_sku": "CJ-MOUSE-RGB", "category": "electronics"}
        ]
    ]
    
    created_sources = []
    created_products = []
    
    # Create sources and their products
    for i, source_data in enumerate(sample_sources):
        # Check if source already exists
        existing_source = db.query(Source).filter(
            Source.name == source_data["name"],
            Source.user_id == user_id
        ).first()
        
        if not existing_source:
            source_data["user_id"] = user_id
            source_data["id"] = f"SOURCE_{user_id}_{i+1}"  # Generate unique ID
            source_data["created_at"] = datetime.now() - timedelta(days=random.randint(30, 180))
            source_data["updated_at"] = datetime.now() - timedelta(days=random.randint(1, 7))
            
            source = Source(**source_data)
            db.add(source)
            db.flush()  # Get the source ID
            created_sources.append(source)
            
            # Add products for this source
            if i < len(source_products):
                for product_data in source_products[i]:
                    # Check if product already exists
                    existing_product = db.query(SourceProduct).filter(
                        SourceProduct.sku == product_data["source_sku"],
                        SourceProduct.source_id == source.id
                    ).first()
                    
                    if not existing_product:
                        # Calculate suggested selling price (markup 40-80%)
                        markup_percent = random.uniform(0.4, 0.8)
                        suggested_price = product_data["source_price"] * (1 + markup_percent)
                        
                        # Calculate ROI
                        roi = (suggested_price - product_data["source_price"]) / product_data["source_price"] * 100
                        
                        product = SourceProduct(
                            id=f"PRODUCT_{source.id}_{len(created_products)+1}",
                            source_id=source.id,
                            name=product_data["name"],
                            source_price=product_data["source_price"],
                            suggested_price=suggested_price,
                            sku=product_data["source_sku"],
                            category=product_data["category"],
                            stock_quantity=random.randint(10, 500),
                            roi=roi,
                            in_stock=random.choice([True, True, True, False]),  # 75% available
                            last_synced=datetime.now() - timedelta(hours=random.randint(1, 48)),
                            created_at=datetime.now() - timedelta(days=random.randint(1, 60)),
                            updated_at=datetime.now() - timedelta(hours=random.randint(1, 24))
                        )
                        
                        db.add(product)
                        created_products.append(product)
                        
                        # Update source product count
                        source.total_products += 1
    
    db.commit()
    
    print(f"✅ Created {len(created_sources)} sources with {len(created_products)} products for user {user_id}")
    return created_sources, created_products


def main():
    """Main function to seed sources"""
    print("🌱 Seeding sample sources and products...")
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Get test user
        user = db.query(User).filter(User.email == "test@ebayoptimizer.com").first()
        if not user:
            print("❌ Test user not found. Please run create_test_users.py first")
            return
        
        # Seed sources
        sources, products = seed_sources(db, user.id)
        
        # Print summary
        total_sources = db.query(Source).filter(Source.user_id == user.id).count()
        total_products = db.query(SourceProduct).join(Source).filter(Source.user_id == user.id).count()
        print(f"📊 Total sources: {total_sources}, Total products: {total_products}")
        
        # Show source status breakdown
        print("\n📈 Source Status Breakdown:")
        for status in SourceStatusEnum:
            count = db.query(Source).filter(
                Source.user_id == user.id,
                Source.status == status
            ).count()
            print(f"  {status.value}: {count} sources")
        
        # Show source type breakdown
        print("\n🏷️ Source Type Breakdown:")
        source_types = db.query(Source.type).filter(Source.user_id == user.id).distinct().all()
        for (source_type,) in source_types:
            count = db.query(Source).filter(
                Source.user_id == user.id,
                Source.type == source_type
            ).count()
            print(f"  {source_type}: {count} sources")
        
        # Show average ROI
        avg_roi = db.execute(
            """SELECT AVG(sp.roi) 
               FROM source_products sp 
               JOIN sources s ON sp.source_id = s.id 
               WHERE s.user_id = ?""", 
            (user.id,)
        ).scalar()
        if avg_roi:
            print(f"\n💰 Average ROI across all products: {avg_roi:.1f}%")
        
        # Show products by availability
        available_products = db.execute(
            """SELECT COUNT(*) 
               FROM source_products sp 
               JOIN sources s ON sp.source_id = s.id 
               WHERE s.user_id = ? AND sp.is_available = 1""", 
            (user.id,)
        ).scalar()
        print(f"📦 Available products: {available_products}/{total_products}")
        
        print("\n🎉 Source seeding completed successfully!")
        
    except Exception as e:
        print(f"❌ Error seeding sources: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()