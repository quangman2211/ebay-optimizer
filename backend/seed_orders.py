#!/usr/bin/env python3
"""
Script để seed sample orders vào database
"""

import sys
import os
from datetime import datetime, timedelta
import random

# Add backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.database import engine, SessionLocal
from app.models.database_models import Order, OrderStatusEnum, User
from sqlalchemy.orm import Session


def seed_orders(db: Session, user_id: int):
    """Seed sample orders for user"""
    
    # Sample order data
    sample_orders = [
        {
            "order_number": "ORD-2024-001",
            "customer_name": "Nguyễn Văn A",
            "customer_email": "nguyenvana@email.com",
            "customer_phone": "0901234567",
            "product_name": "iPhone 15 Pro Max 256GB",
            "price_ebay": 1299.99,
            "price_cost": 1150.00,
            "net_profit": 119.99,
            "fees": 30.00,
            "status": OrderStatusEnum.SHIPPED,
            "order_date": datetime.now() - timedelta(days=2),
            "expected_ship_date": datetime.now() - timedelta(days=1),
            "actual_ship_date": datetime.now() - timedelta(days=1),
            "tracking_number": "1Z999AA1234567890",
            "carrier": "UPS",
            "customer_type": "regular"
        },
        {
            "order_number": "ORD-2024-002", 
            "customer_name": "Trần Thị B",
            "customer_email": "tranthib@email.com",
            "customer_phone": "0907654321",
            "product_name": "MacBook Pro 14 M3 Chip",
            "price_ebay": 1899.99,
            "price_cost": 1750.00,
            "net_profit": 109.99,
            "fees": 40.00,
            "status": OrderStatusEnum.PROCESSING,
            "order_date": datetime.now() - timedelta(days=1),
            "expected_ship_date": datetime.now() + timedelta(days=1),
            "customer_type": "vip"
        },
        {
            "order_number": "ORD-2024-003",
            "customer_name": "Lê Minh C", 
            "customer_email": "leminhc@email.com",
            "customer_phone": "0912345678",
            "product_name": "AirPods Pro 2nd Gen",
            "price_ebay": 249.99,
            "price_cost": 220.00,
            "net_profit": 22.49,
            "fees": 7.50,
            "status": OrderStatusEnum.PENDING,
            "order_date": datetime.now(),
            "expected_ship_date": datetime.now() + timedelta(days=2),
            "customer_type": "regular"
        },
        {
            "order_number": "ORD-2024-004",
            "customer_name": "Phạm Thị D",
            "customer_email": "phamthid@email.com", 
            "customer_phone": "0919876543",
            "product_name": "Samsung Galaxy S24 Ultra",
            "price_ebay": 1299.99,
            "price_cost": 1180.00,
            "net_profit": 89.99,
            "fees": 30.00,
            "status": OrderStatusEnum.DELIVERED,
            "order_date": datetime.now() - timedelta(days=5),
            "expected_ship_date": datetime.now() - timedelta(days=4),
            "actual_ship_date": datetime.now() - timedelta(days=4),
            "delivery_date": datetime.now() - timedelta(days=1),
            "tracking_number": "1Z999AA1234567891",
            "carrier": "FedEx",
            "customer_type": "regular"
        },
        {
            "order_number": "ORD-2024-005",
            "customer_name": "Hoàng Văn E",
            "customer_email": "hoangvane@email.com",
            "customer_phone": "0923456789",
            "product_name": "Dell XPS 13 Plus",
            "price_ebay": 1099.99,
            "price_cost": 980.00,
            "net_profit": 89.99,
            "fees": 30.00,
            "status": OrderStatusEnum.SHIPPED,
            "order_date": datetime.now() - timedelta(days=3),
            "expected_ship_date": datetime.now() - timedelta(days=2),
            "actual_ship_date": datetime.now() - timedelta(days=2),
            "tracking_number": "1Z999AA1234567892",
            "carrier": "DHL",
            "customer_type": "vip"
        }
    ]
    
    # Add more orders for better demo data
    additional_orders = []
    for i in range(6, 21):  # Add orders 006-020
        order = {
            "order_number": f"ORD-2024-{i:03d}",
            "customer_name": f"Khách hàng {i}",
            "customer_email": f"customer{i}@email.com",
            "customer_phone": f"09{random.randint(10000000, 99999999)}",
            "product_name": random.choice([
                "iPhone 15 Pro 128GB", "MacBook Air M3", "iPad Pro 11-inch",
                "AirPods Pro", "Apple Watch Series 9", "Samsung Galaxy Tab S9",
                "Sony WH-1000XM5", "Nintendo Switch OLED"
            ]),
            "price_ebay": random.uniform(199.99, 1499.99),
            "price_cost": 0,  # Will calculate
            "net_profit": 0,    # Will calculate
            "fees": 0,          # Will calculate
            "status": random.choice(list(OrderStatusEnum)),
            "order_date": datetime.now() - timedelta(days=random.randint(1, 30)),
            "expected_ship_date": datetime.now() + timedelta(days=random.randint(1, 5)),
            "customer_type": random.choice(["regular", "vip", "new"])
        }
        
        # Calculate derived fields
        order["price_cost"] = order["price_ebay"] * 0.85  # 15% markup
        order["fees"] = order["price_ebay"] * 0.025         # 2.5% fees
        order["net_profit"] = order["price_ebay"] - order["price_cost"] - order["fees"]
        
        # Add tracking for shipped/delivered orders
        if order["status"] in [OrderStatusEnum.SHIPPED, OrderStatusEnum.DELIVERED]:
            order["tracking_number"] = f"1Z999AA123456789{i}"
            order["carrier"] = random.choice(["UPS", "FedEx", "DHL", "USPS"])
            order["actual_ship_date"] = order["expected_ship_date"]
            
        if order["status"] == OrderStatusEnum.DELIVERED:
            order["delivery_date"] = order["actual_ship_date"] + timedelta(days=random.randint(2, 7))
            
        additional_orders.append(order)
    
    # Combine all orders
    all_orders = sample_orders + additional_orders
    
    # Create order objects and add to database
    created_orders = []
    for order_data in all_orders:
        # Check if order already exists
        existing = db.query(Order).filter(
            Order.order_number == order_data["order_number"],
            Order.user_id == user_id
        ).first()
        
        if not existing:
            order_data["user_id"] = user_id
            order_data["id"] = f"ORDER_{user_id}_{order_data['order_number']}"  # Generate unique ID
            order = Order(**order_data)
            db.add(order)
            created_orders.append(order)
    
    db.commit()
    
    print(f"✅ Created {len(created_orders)} sample orders for user {user_id}")
    return created_orders


def main():
    """Main function to seed orders"""
    print("🌱 Seeding sample orders...")
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Get test user
        user = db.query(User).filter(User.email == "test@ebayoptimizer.com").first()
        if not user:
            print("❌ Test user not found. Please run create_test_users.py first")
            return
        
        # Seed orders
        orders = seed_orders(db, user.id)
        
        # Print summary
        total_orders = db.query(Order).filter(Order.user_id == user.id).count()
        print(f"📊 Total orders in database: {total_orders}")
        
        # Show order status breakdown
        print("\n📈 Order Status Breakdown:")
        for status in OrderStatusEnum:
            count = db.query(Order).filter(
                Order.user_id == user.id,
                Order.status == status
            ).count()
            print(f"  {status.value}: {count} orders")
        
        print("\n🎉 Order seeding completed successfully!")
        
    except Exception as e:
        print(f"❌ Error seeding orders: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()