#!/usr/bin/env python3
"""
Script import dữ liệu từ Google Sheets vào SQLite database

Sử dụng:
    python import_sheets.py <SPREADSHEET_ID>
    
Ví dụ:
    python import_sheets.py 1ABC123DEF456GHI
"""

import sys
import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.database import SessionLocal
from backend.app.models.models import Listing, Order, Source

# Google Sheets configuration
SCOPE = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
CREDS_PATH = os.path.join(os.path.dirname(__file__), '../credentials/google-service-account.json')

def get_google_client():
    """Kết nối với Google Sheets"""
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_PATH, SCOPE)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        print(f"❌ Lỗi kết nối Google Sheets: {e}")
        return None

def import_listings(sheet, db):
    """Import listings từ sheet 'Listings'"""
    try:
        print("\n📊 Import Listings...")
        worksheet = sheet.worksheet("Listings")
        records = worksheet.get_all_records()
        
        added = 0
        updated = 0
        
        for record in records:
            if not record.get('item_id'):
                continue
                
            existing = db.query(Listing).filter(Listing.item_id == record['item_id']).first()
            
            if existing:
                # Update existing
                existing.title = record.get('title', existing.title)
                existing.price = float(record.get('price', existing.price))
                existing.quantity = int(record.get('quantity', existing.quantity))
                existing.category = record.get('category', existing.category)
                existing.status = record.get('status', existing.status)
                existing.updated_at = datetime.utcnow()
                updated += 1
            else:
                # Add new
                new_listing = Listing(
                    item_id=record['item_id'],
                    title=record.get('title', ''),
                    price=float(record.get('price', 0)),
                    quantity=int(record.get('quantity', 0)),
                    category=record.get('category', 'Other'),
                    condition=record.get('condition', 'New'),
                    description=record.get('description', ''),
                    image_url=record.get('image_url', ''),
                    status=record.get('status', 'active'),
                    views=int(record.get('views', 0)),
                    watchers=int(record.get('watchers', 0))
                )
                db.add(new_listing)
                added += 1
        
        db.commit()
        print(f"✅ Listings: {added} thêm mới, {updated} cập nhật")
        return added, updated
        
    except Exception as e:
        print(f"❌ Lỗi import listings: {e}")
        db.rollback()
        return 0, 0

def import_orders(sheet, db):
    """Import orders từ sheet 'Orders'"""
    try:
        print("\n📦 Import Orders...")
        worksheet = sheet.worksheet("Orders")
        records = worksheet.get_all_records()
        
        added = 0
        updated = 0
        
        for record in records:
            if not record.get('order_id'):
                continue
                
            existing = db.query(Order).filter(Order.order_id == record['order_id']).first()
            
            if existing:
                # Update existing
                existing.status = record.get('status', existing.status)
                existing.tracking_number = record.get('tracking_number', existing.tracking_number)
                existing.updated_at = datetime.utcnow()
                updated += 1
            else:
                # Add new
                new_order = Order(
                    order_id=record['order_id'],
                    buyer_name=record.get('buyer_name', ''),
                    buyer_email=record.get('buyer_email', ''),
                    item_title=record.get('item_title', ''),
                    item_id=record.get('item_id', ''),
                    quantity=int(record.get('quantity', 1)),
                    price=float(record.get('price', 0)),
                    total=float(record.get('total', 0)),
                    status=record.get('status', 'pending'),
                    shipping_address=record.get('shipping_address', ''),
                    tracking_number=record.get('tracking_number', ''),
                    order_date=datetime.utcnow()
                )
                db.add(new_order)
                added += 1
        
        db.commit()
        print(f"✅ Orders: {added} thêm mới, {updated} cập nhật")
        return added, updated
        
    except Exception as e:
        print(f"❌ Lỗi import orders: {e}")
        db.rollback()
        return 0, 0

def import_sources(sheet, db):
    """Import sources từ sheet 'Sources'"""
    try:
        print("\n🏭 Import Sources...")
        worksheet = sheet.worksheet("Sources")
        records = worksheet.get_all_records()
        
        added = 0
        updated = 0
        
        for record in records:
            if not record.get('name'):
                continue
                
            existing = db.query(Source).filter(Source.name == record['name']).first()
            
            if existing:
                # Update existing
                existing.url = record.get('url', existing.url)
                existing.profit_margin = float(record.get('profit_margin', existing.profit_margin))
                existing.reliability_score = float(record.get('reliability_score', existing.reliability_score))
                existing.updated_at = datetime.utcnow()
                updated += 1
            else:
                # Add new
                new_source = Source(
                    name=record['name'],
                    type=record.get('type', 'Supplier'),
                    url=record.get('url', ''),
                    api_key=record.get('api_key', ''),
                    profit_margin=float(record.get('profit_margin', 30)),
                    shipping_cost=float(record.get('shipping_cost', 0)),
                    processing_time=int(record.get('processing_time', 3)),
                    reliability_score=float(record.get('reliability_score', 100)),
                    auto_order=str(record.get('auto_order', 'false')).lower() == 'true',
                    notes=record.get('notes', '')
                )
                db.add(new_source)
                added += 1
        
        db.commit()
        print(f"✅ Sources: {added} thêm mới, {updated} cập nhật")
        return added, updated
        
    except Exception as e:
        print(f"❌ Lỗi import sources: {e}")
        db.rollback()
        return 0, 0

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("❌ Vui lòng cung cấp SPREADSHEET_ID")
        print("Sử dụng: python import_sheets.py <SPREADSHEET_ID>")
        sys.exit(1)
    
    spreadsheet_id = sys.argv[1]
    
    print("🚀 Bắt đầu import từ Google Sheets...")
    print(f"📋 Spreadsheet ID: {spreadsheet_id}")
    
    # Connect to Google Sheets
    client = get_google_client()
    if not client:
        sys.exit(1)
    
    try:
        sheet = client.open_by_key(spreadsheet_id)
        print(f"✅ Kết nối thành công: {sheet.title}")
    except Exception as e:
        print(f"❌ Không thể mở spreadsheet: {e}")
        sys.exit(1)
    
    # Connect to database
    db = SessionLocal()
    
    try:
        # Import data
        results = {
            'listings': import_listings(sheet, db),
            'orders': import_orders(sheet, db),
            'sources': import_sources(sheet, db)
        }
        
        # Summary
        print("\n" + "="*50)
        print("📊 KẾT QUẢ IMPORT:")
        print("="*50)
        
        total_added = sum(r[0] for r in results.values())
        total_updated = sum(r[1] for r in results.values())
        
        print(f"➕ Tổng thêm mới: {total_added}")
        print(f"✏️  Tổng cập nhật: {total_updated}")
        print(f"📈 Tổng xử lý: {total_added + total_updated}")
        
        print("\n✅ Import hoàn tất!")
        
    except Exception as e:
        print(f"\n❌ Lỗi import: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()