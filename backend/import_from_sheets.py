#!/usr/bin/env python3
"""
Script để import data từ Google Sheets vào SQLite database
"""

import sys
import os
from datetime import datetime
import json

# Add backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.database import SessionLocal
from app.models.database_models import Listing, ListingStatusEnum, User
from app.services.google_sheets import GoogleSheetsService
from app.core.config import settings
from sqlalchemy.orm import Session


def import_listings_from_sheets(db: Session, user_id: int):
    """Import listings from Google Sheets into SQLite database"""
    
    print(f"📊 Starting Google Sheets import for user {user_id}...")
    
    # Initialize Google Sheets service
    sheets_service = GoogleSheetsService()
    
    # Get all listings from Google Sheets
    sheets_listings = sheets_service.get_all_listings()
    
    if not sheets_listings:
        print("⚠️ No listings found in Google Sheets")
        return []
    
    print(f"📋 Found {len(sheets_listings)} listings in Google Sheets")
    
    imported_listings = []
    updated_listings = []
    
    for sheet_listing in sheets_listings:
        try:
            # Check if listing already exists in SQLite
            existing_listing = db.query(Listing).filter(
                Listing.user_id == user_id,
                Listing.title == sheet_listing.get('title', '')
            ).first()
            
            # Prepare listing data for SQLite
            listing_data = {
                'user_id': user_id,
                'title': sheet_listing.get('title', '')[:80],  # Limit to 80 chars
                'description': sheet_listing.get('description', ''),
                'category': sheet_listing.get('category', 'uncategorized'),
                'price': float(sheet_listing.get('price', 0)) if sheet_listing.get('price') else None,
                'quantity': int(sheet_listing.get('quantity', 0)) if sheet_listing.get('quantity') else 0,
                'keywords': sheet_listing.get('keywords', []),
                'item_specifics': sheet_listing.get('item_specifics', {}),
                'sheet_row': sheet_listing.get('sheet_row'),
                'updated_at': datetime.now()
            }
            
            # Map status from sheets to database enum
            sheet_status = sheet_listing.get('status', 'draft').lower()
            if sheet_status in [e.value for e in ListingStatusEnum]:
                listing_data['status'] = ListingStatusEnum(sheet_status)
            else:
                listing_data['status'] = ListingStatusEnum.DRAFT
            
            if existing_listing:
                # Update existing listing
                for key, value in listing_data.items():
                    if key != 'user_id':  # Don't update user_id
                        setattr(existing_listing, key, value)
                
                db.add(existing_listing)
                updated_listings.append(existing_listing)
                print(f"🔄 Updated: {existing_listing.title}")
                
            else:
                # Create new listing
                listing_data['id'] = f"IMPORT_{user_id}_{len(imported_listings)+1}_{int(datetime.now().timestamp())}"
                listing_data['created_at'] = datetime.now()
                
                # Set some default performance values
                listing_data['views'] = 0
                listing_data['watchers'] = 0
                listing_data['sold'] = 0
                listing_data['performance_score'] = 0.0
                
                new_listing = Listing(**listing_data)
                db.add(new_listing)
                imported_listings.append(new_listing)
                print(f"✅ Imported: {new_listing.title}")
                
        except Exception as e:
            print(f"❌ Error processing listing '{sheet_listing.get('title', 'Unknown')}': {e}")
            continue
    
    # Commit all changes
    try:
        db.commit()
        print(f"💾 Successfully committed {len(imported_listings)} new + {len(updated_listings)} updated listings")
    except Exception as e:
        print(f"❌ Error committing to database: {e}")
        db.rollback()
        return []
    
    return imported_listings + updated_listings


def export_listings_to_sheets(db: Session, user_id: int):
    """Export listings from SQLite to Google Sheets"""
    
    print(f"📤 Starting export to Google Sheets for user {user_id}...")
    
    # Initialize Google Sheets service
    sheets_service = GoogleSheetsService()
    
    # Get all user listings from SQLite
    sqlite_listings = db.query(Listing).filter(Listing.user_id == user_id).all()
    
    if not sqlite_listings:
        print("⚠️ No listings found in SQLite database")
        return 0
    
    print(f"📋 Found {len(sqlite_listings)} listings in SQLite")
    
    # Convert to sheets format
    sheets_data = []
    for listing in sqlite_listings:
        sheet_data = {
            'id': listing.id,
            'title': listing.title,
            'description': listing.description,
            'category': listing.category,
            'price': listing.price,
            'quantity': listing.quantity,
            'keywords': listing.keywords or [],
            'status': listing.status.value if listing.status else 'draft',
            'item_specifics': listing.item_specifics or {},
            'sheet_row': listing.sheet_row
        }
        sheets_data.append(sheet_data)
    
    # Export to Google Sheets
    success_count = 0
    for data in sheets_data:
        if sheets_service.add_listing(data):
            success_count += 1
            print(f"📤 Exported: {data['title']}")
        else:
            print(f"❌ Failed to export: {data['title']}")
    
    print(f"✅ Successfully exported {success_count}/{len(sheets_data)} listings")
    return success_count


def sync_bidirectional(db: Session, user_id: int):
    """Sync data bidirectionally between SQLite and Google Sheets"""
    
    print("🔄 Starting bidirectional sync between SQLite ↔ Google Sheets...")
    
    # Import from Sheets to SQLite first
    imported = import_listings_from_sheets(db, user_id)
    
    # Then export any SQLite-only data to Sheets
    exported_count = export_listings_to_sheets(db, user_id)
    
    print(f"🎉 Sync complete! Imported: {len(imported)}, Exported: {exported_count}")
    return len(imported), exported_count


def main():
    """Main function to handle Google Sheets import/export"""
    
    # Check command line arguments
    if len(sys.argv) < 2:
        print("Usage: python3 import_from_sheets.py [import|export|sync]")
        print("  import - Import from Google Sheets to SQLite")
        print("  export - Export from SQLite to Google Sheets") 
        print("  sync   - Bidirectional sync")
        return
    
    operation = sys.argv[1].lower()
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Get test user
        user = db.query(User).filter(User.email == "test@ebayoptimizer.com").first()
        if not user:
            print("❌ Test user not found. Please run create_test_users.py first")
            return
        
        print(f"👤 Using user: {user.email} (ID: {user.id})")
        print(f"📊 Spreadsheet ID: {settings.SPREADSHEET_ID}")
        print(f"📄 Sheet Name: {settings.SHEET_NAME}")
        
        if operation == "import":
            # Import from Google Sheets
            imported = import_listings_from_sheets(db, user.id)
            print(f"\n📈 Import Summary:")
            print(f"  - Processed: {len(imported)} listings")
            
            # Show updated totals
            total_listings = db.query(Listing).filter(Listing.user_id == user.id).count()
            print(f"  - Total in database: {total_listings} listings")
            
        elif operation == "export":
            # Export to Google Sheets
            exported_count = export_listings_to_sheets(db, user.id)
            print(f"\n📤 Export Summary:")
            print(f"  - Exported: {exported_count} listings")
            
        elif operation == "sync":
            # Bidirectional sync
            imported_count, exported_count = sync_bidirectional(db, user.id)
            print(f"\n🔄 Sync Summary:")
            print(f"  - Imported from Sheets: {imported_count}")
            print(f"  - Exported to Sheets: {exported_count}")
            
            # Show final totals
            total_listings = db.query(Listing).filter(Listing.user_id == user.id).count()
            print(f"  - Total in database: {total_listings} listings")
            
        else:
            print(f"❌ Unknown operation: {operation}")
            print("Valid operations: import, export, sync")
            
    except Exception as e:
        print(f"❌ Error during {operation}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()