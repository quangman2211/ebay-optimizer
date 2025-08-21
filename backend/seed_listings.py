#!/usr/bin/env python3
"""
Script để seed sample listings vào database
"""

import sys
import os
from datetime import datetime, timedelta
import random

# Add backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.database import engine, SessionLocal
from app.models.database_models import Listing, ListingStatusEnum, User
from sqlalchemy.orm import Session


def seed_listings(db: Session, user_id: int):
    """Seed sample listings for user"""
    
    # Sample listing categories and products
    categories_products = {
        "electronics": [
            {
                "title": "Apple iPhone 15 Pro Max 256GB Natural Titanium Unlocked",
                "description": "Brand new Apple iPhone 15 Pro Max with 256GB storage in Natural Titanium. Factory unlocked, works with all carriers. Includes original box and accessories.",
                "price": 1299.99,
                "quantity": 5,
                "keywords": ["iphone", "apple", "smartphone", "unlocked", "new"],
                "item_specifics": {"brand": "Apple", "model": "iPhone 15 Pro Max", "storage": "256GB", "condition": "New"}
            },
            {
                "title": "MacBook Pro 14-inch M3 Chip 512GB SSD Silver",
                "description": "Powerful MacBook Pro with M3 chip, 14-inch Liquid Retina XDR display, 512GB SSD storage. Perfect for professionals and creators.",
                "price": 1899.99,
                "quantity": 3,
                "keywords": ["macbook", "apple", "laptop", "m3", "professional"],
                "item_specifics": {"brand": "Apple", "model": "MacBook Pro", "processor": "M3", "condition": "New"}
            },
            {
                "title": "Samsung Galaxy S24 Ultra 512GB Titanium Black",
                "description": "Latest Samsung Galaxy S24 Ultra with S Pen, 200MP camera, 512GB storage. Titanium Black color, factory unlocked.",
                "price": 1299.99,
                "quantity": 4,
                "keywords": ["samsung", "galaxy", "smartphone", "android", "camera"],
                "item_specifics": {"brand": "Samsung", "model": "Galaxy S24 Ultra", "storage": "512GB", "condition": "New"}
            }
        ],
        "clothing": [
            {
                "title": "Nike Air Jordan 1 Retro High OG Chicago 2015 Size 10",
                "description": "Authentic Nike Air Jordan 1 Retro High OG in Chicago colorway from 2015. Size 10 US, excellent condition with original box.",
                "price": 899.99,
                "quantity": 1,
                "keywords": ["jordan", "nike", "sneakers", "chicago", "retro"],
                "item_specifics": {"brand": "Nike", "model": "Air Jordan 1", "size": "10", "condition": "Used"}
            },
            {
                "title": "Supreme Box Logo Hoodie Black Medium FW23",
                "description": "Supreme Box Logo Hoodie in Black color, size Medium from Fall/Winter 2023 collection. Brand new with tags.",
                "price": 599.99,
                "quantity": 2,
                "keywords": ["supreme", "hoodie", "streetwear", "box logo", "fw23"],
                "item_specifics": {"brand": "Supreme", "size": "Medium", "season": "FW23", "condition": "New"}
            }
        ],
        "collectibles": [
            {
                "title": "Pokemon Cards Base Set Charizard Holo 4/102 PSA 9",
                "description": "Pokemon Base Set Charizard holographic card #4/102 graded PSA 9. Mint condition, perfect for collectors.",
                "price": 2499.99,
                "quantity": 1,
                "keywords": ["pokemon", "charizard", "psa", "collectible", "trading card"],
                "item_specifics": {"game": "Pokemon", "card": "Charizard", "grade": "PSA 9", "condition": "Mint"}
            },
            {
                "title": "Vintage Rolex Submariner Date 16610 Steel Black Dial",
                "description": "Vintage Rolex Submariner Date ref 16610 with black dial and bezel. Excellent condition, serviced recently. Comes with papers.",
                "price": 8999.99,
                "quantity": 1,
                "keywords": ["rolex", "submariner", "vintage", "luxury", "watch"],
                "item_specifics": {"brand": "Rolex", "model": "Submariner", "reference": "16610", "condition": "Excellent"}
            }
        ]
    }
    
    # Create listings from sample data
    created_listings = []
    
    for category, products in categories_products.items():
        for product in products:
            # Check if listing already exists
            existing = db.query(Listing).filter(
                Listing.title == product["title"],
                Listing.user_id == user_id
            ).first()
            
            if not existing:
                # Calculate performance metrics
                views = random.randint(50, 500)
                watchers = random.randint(5, 50)
                sold = random.randint(0, product["quantity"])
                
                # Calculate performance score based on views, watchers, sold
                performance_score = min(100, (watchers * 5) + (sold * 10) + (views * 0.1))
                
                listing = Listing(
                    id=f"LISTING_{user_id}_{len(created_listings)+1}",
                    user_id=user_id,
                    title=product["title"],
                    description=product["description"],
                    category=category,
                    price=product["price"],
                    quantity=product["quantity"],
                    keywords=product["keywords"],
                    item_specifics=product["item_specifics"],
                    status=random.choice(list(ListingStatusEnum)),
                    views=views,
                    watchers=watchers,
                    sold=sold,
                    performance_score=performance_score,
                    item_id=f"EBAY{random.randint(100000000, 999999999)}",
                    created_at=datetime.now() - timedelta(days=random.randint(1, 60)),
                    updated_at=datetime.now() - timedelta(days=random.randint(0, 10))
                )
                
                db.add(listing)
                created_listings.append(listing)
    
    # Add more random listings for demo purposes
    additional_products = [
        "PlayStation 5 Console Disc Version",
        "Nintendo Switch OLED White",
        "AirPods Pro 2nd Generation",
        "iPad Pro 12.9 M3 WiFi 256GB",
        "Canon EOS R6 Mark II Body",
        "Sony WH-1000XM5 Headphones",
        "Microsoft Surface Pro 9",
        "Dell XPS 13 Plus Laptop",
        "Apple Watch Series 9 45mm",
        "Bose QuietComfort Earbuds",
        "GoPro Hero 12 Black",
        "DJI Mini 4 Pro Drone",
        "Dyson V15 Detect Vacuum",
        "KitchenAid Stand Mixer",
        "Ninja Foodi Pressure Cooker"
    ]
    
    for i, product_name in enumerate(additional_products):
        title = f"{product_name} - Brand New in Box"
        
        # Check if listing already exists
        existing = db.query(Listing).filter(
            Listing.title == title,
            Listing.user_id == user_id
        ).first()
        
        if not existing:
            price = random.uniform(99.99, 1999.99)
            quantity = random.randint(1, 10)
            views = random.randint(10, 800)
            watchers = random.randint(0, 80) 
            sold = random.randint(0, quantity)
            
            # Calculate performance score
            performance_score = min(100, (watchers * 3) + (sold * 15) + (views * 0.05))
            
            listing = Listing(
                id=f"LISTING_{user_id}_{len(created_listings)+1}",
                user_id=user_id,
                title=title,
                description=f"Brand new {product_name} in original packaging. Fast shipping, excellent customer service.",
                category=random.choice(["electronics", "home", "sports", "automotive"]),
                price=price,
                quantity=quantity,
                keywords=[word.lower() for word in product_name.split()[:4]],
                item_specifics={"brand": "Various", "condition": "New"},
                status=random.choice(list(ListingStatusEnum)),
                views=views,
                watchers=watchers,
                sold=sold,
                performance_score=performance_score,
                item_id=f"EBAY{random.randint(100000000, 999999999)}",
                created_at=datetime.now() - timedelta(days=random.randint(1, 90)),
                updated_at=datetime.now() - timedelta(days=random.randint(0, 15))
            )
            
            db.add(listing)
            created_listings.append(listing)
    
    db.commit()
    
    print(f"✅ Created {len(created_listings)} sample listings for user {user_id}")
    return created_listings


def main():
    """Main function to seed listings"""
    print("🌱 Seeding sample listings...")
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Get test user
        user = db.query(User).filter(User.email == "test@ebayoptimizer.com").first()
        if not user:
            print("❌ Test user not found. Please run create_test_users.py first")
            return
        
        # Seed listings
        listings = seed_listings(db, user.id)
        
        # Print summary
        total_listings = db.query(Listing).filter(Listing.user_id == user.id).count()
        print(f"📊 Total listings in database: {total_listings}")
        
        # Show listing status breakdown
        print("\n📈 Listing Status Breakdown:")
        for status in ListingStatusEnum:
            count = db.query(Listing).filter(
                Listing.user_id == user.id,
                Listing.status == status
            ).count()
            print(f"  {status.value}: {count} listings")
        
        # Show category breakdown
        print("\n🏷️ Category Breakdown:")
        categories = db.query(Listing.category).filter(Listing.user_id == user.id).distinct().all()
        for (category,) in categories:
            count = db.query(Listing).filter(
                Listing.user_id == user.id,
                Listing.category == category
            ).count()
            print(f"  {category}: {count} listings")
        
        # Show performance summary
        avg_performance = db.execute(
            "SELECT AVG(performance_score) FROM listings WHERE user_id = ?", 
            (user.id,)
        ).scalar()
        print(f"\n⭐ Average Performance Score: {avg_performance:.1f}")
        
        print("\n🎉 Listing seeding completed successfully!")
        
    except Exception as e:
        print(f"❌ Error seeding listings: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()