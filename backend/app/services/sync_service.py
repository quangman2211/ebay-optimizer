"""
Sync Service - Bi-directional SQLite ↔ Google Sheets Synchronization
Hybrid architecture: SQLite as primary, Google Sheets as backup/collaboration
"""

import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.db.database import SessionLocal
from app.services.google_sheets import GoogleSheetsService
from app.core.config import settings
from app.repositories import listing_repo, order_repo, source_repo, account_repo
from app.models.database_models import (
    Listing, Order, Source, Account, ActivityLog,
    ListingStatusEnum, OrderStatusEnum, SourceStatusEnum, AccountStatusEnum
)


class SyncService:
    """
    Service để sync data giữa SQLite và Google Sheets với smart merge logic
    """
    
    def __init__(self):
        self.sheets_service = GoogleSheetsService()
        self.sync_config = {
            "enabled": True,
            "auto_sync_interval": 3600,  # 1 hour
            "conflict_resolution": "merge_all",  # merge_all, sqlite_wins, sheets_wins, manual
            "sync_entities": ["listings", "orders", "sources", "accounts"],
            "backup_before_sync": True,
            "dry_run_mode": False
        }
        self._backup_data = {}  # Store backup data
    
    def _create_backup(self, db: Session, user_id: int, entity_type: str) -> bool:
        """Create backup before sync operation"""
        try:
            if not self.sync_config["backup_before_sync"]:
                return True
            
            backup_key = f"{entity_type}_{user_id}_{datetime.now().isoformat()}"
            
            if entity_type == "listings":
                result = listing_repo.get_multi(db, skip=0, limit=10000, user_id=user_id)
                self._backup_data[backup_key] = {
                    "entity_type": entity_type,
                    "timestamp": datetime.now().isoformat(),
                    "count": len(result["items"]),
                    "data": [item.__dict__ for item in result["items"]]
                }
            
            return True
        except Exception as e:
            print(f"Backup failed for {entity_type}: {e}")
            return False
    
    def _detect_changes_since_last_sync(self, db: Session, user_id: int, entity_type: str) -> Tuple[List, datetime]:
        """Detect changes since last sync"""
        try:
            # Get last sync timestamp
            last_sync = db.query(ActivityLog).filter(
                and_(
                    ActivityLog.user_id == user_id,
                    ActivityLog.action.in_(["sync_export", "sync_import", "full_sync"]),
                    ActivityLog.entity_type == entity_type,
                    ActivityLog.success == True
                )
            ).order_by(ActivityLog.created_at.desc()).first()
            
            last_sync_time = last_sync.created_at if last_sync else datetime.min
            
            # Get changed records
            if entity_type == "listings":
                changed_items = db.query(Listing).filter(
                    and_(
                        Listing.user_id == user_id,
                        Listing.updated_at > last_sync_time
                    )
                ).all()
            else:
                changed_items = []
            
            return changed_items, last_sync_time
            
        except Exception as e:
            print(f"Error detecting changes: {e}")
            return [], datetime.min
    
    def _smart_merge_listings(self, sqlite_listings: List, sheets_listings: List, last_sync_time: datetime) -> Dict[str, Any]:
        """Smart merge logic for listings"""
        merge_result = {
            "sqlite_new": [],
            "sheets_new": [],
            "conflicts": [],
            "merged_data": []
        }
        
        # Create lookup dictionaries
        sqlite_dict = {str(item.id): item for item in sqlite_listings}
        sheets_dict = {str(item.get("id", item.get("ID"))): item for item in sheets_listings if item.get("id") or item.get("ID")}
        
        # Find new items from SQLite (not in Sheets)
        for sqlite_id, sqlite_item in sqlite_dict.items():
            if sqlite_id not in sheets_dict:
                # Handle None created_at by treating as very old date
                item_created_at = sqlite_item.created_at if sqlite_item.created_at else datetime.min
                if item_created_at > last_sync_time:
                    merge_result["sqlite_new"].append(sqlite_item)
        
        # Find new items from Sheets (not in SQLite)
        for sheets_id, sheets_item in sheets_dict.items():
            if sheets_id not in sqlite_dict:
                merge_result["sheets_new"].append(sheets_item)
        
        # Find conflicts (exist in both, modified after last sync)
        for item_id in sqlite_dict.keys():
            if item_id in sheets_dict:
                sqlite_item = sqlite_dict[item_id]
                sheets_item = sheets_dict[item_id]
                
                # Check if either was modified since last sync
                # Handle None updated_at by treating as very old date
                item_updated_at = sqlite_item.updated_at if sqlite_item.updated_at else datetime.min
                sqlite_modified = item_updated_at > last_sync_time
                sheets_updated = sheets_item.get("Last Updated") or sheets_item.get("updated_at")
                sheets_modified = False
                
                if sheets_updated:
                    try:
                        sheets_timestamp = datetime.fromisoformat(sheets_updated.replace('Z', '+00:00'))
                        sheets_modified = sheets_timestamp > last_sync_time
                    except:
                        pass
                
                if sqlite_modified or sheets_modified:
                    merge_result["conflicts"].append({
                        "id": item_id,
                        "sqlite_item": sqlite_item,
                        "sheets_item": sheets_item,
                        "sqlite_modified": sqlite_modified,
                        "sheets_modified": sheets_modified
                    })
        
        return merge_result
    
    def _resolve_conflicts(self, conflicts: List[Dict]) -> List[Dict]:
        """Resolve conflicts based on configured strategy"""
        resolved = []
        
        for conflict in conflicts:
            resolution = {"id": conflict["id"]}
            
            if self.sync_config["conflict_resolution"] == "merge_all":
                # Merge both - prefer newer timestamp
                sqlite_item = conflict["sqlite_item"]
                sheets_item = conflict["sheets_item"]
                
                # Use SQLite as base, overlay with Sheets changes
                resolution["action"] = "merge"
                resolution["winner"] = "merged"
                
            elif self.sync_config["conflict_resolution"] == "sqlite_wins":
                resolution["action"] = "keep_sqlite"
                resolution["winner"] = "sqlite"
                
            elif self.sync_config["conflict_resolution"] == "sheets_wins":
                resolution["action"] = "keep_sheets"
                resolution["winner"] = "sheets"
                
            else:  # manual
                resolution["action"] = "manual_review_required"
                resolution["winner"] = "none"
            
            resolved.append(resolution)
        
        return resolved
    
    def sync_listings_to_sheets(self, db: Session, user_id: int, sheet_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Export SQLite listings to Google Sheets với smart merge
        """
        try:
            # Create backup before sync
            if not self._create_backup(db, user_id, "listings"):
                return {"success": False, "message": "Backup failed, aborting sync"}
            
            # Get all listings from SQLite
            result = listing_repo.get_multi(db, skip=0, limit=1000, user_id=user_id)
            sqlite_listings = result["items"]
            
            if not sqlite_listings:
                return {"success": True, "message": "No listings to sync", "exported": 0}
            
            # Get existing sheets data using specified or configured sheet name
            target_sheet = sheet_name or getattr(settings, 'SHEET_NAME', 'Listings')
            sheets_listings = self.sheets_service.get_all_listings(target_sheet) or []
            
            # Detect changes since last sync
            changed_items, last_sync_time = self._detect_changes_since_last_sync(db, user_id, "listings")
            
            # Perform smart merge
            merge_result = self._smart_merge_listings(sqlite_listings, sheets_listings, last_sync_time)
            
            # Apply conflict resolution
            conflicts_resolved = self._resolve_conflicts(merge_result["conflicts"])
            
            if self.sync_config["dry_run_mode"]:
                return {
                    "success": True,
                    "message": "Dry run completed",
                    "dry_run": True,
                    "preview": {
                        "sqlite_new": len(merge_result["sqlite_new"]),
                        "sheets_new": len(merge_result["sheets_new"]),
                        "conflicts": len(merge_result["conflicts"]),
                        "conflicts_resolved": len(conflicts_resolved)
                    }
                }
            
            # Convert SQLite new items to Google Sheets format (20 columns optimized)
            new_sheets_data = []
            for listing in merge_result["sqlite_new"]:
                sheets_row = [
                    str(listing.id),                                             # Listing ID
                    listing.item_id or "",                                      # eBay Item ID
                    listing.sku or "",                                          # SKU
                    listing.title or "",                                        # Current Title
                    listing.optimized_title or "",                              # Optimized Title
                    listing.description or "",                                  # Description
                    listing.category or "",                                     # Category
                    str(listing.price) if listing.price else "",               # Price
                    str(listing.quantity) if listing.quantity else "0",        # Quantity
                    listing.condition or "",                                    # Condition
                    listing.status.value,                                       # Status
                    ",".join(listing.keywords) if listing.keywords else "",    # Keywords
                    json.dumps(listing.item_specifics) if listing.item_specifics else "{}", # Item Specifics
                    str(listing.views) if listing.views else "0",              # Views
                    str(listing.watchers) if listing.watchers else "0",        # Watchers
                    str(listing.sold) if listing.sold else "0",                # Sold
                    str(listing.performance_score) if listing.performance_score else "", # Performance Score
                    str(listing.seo_score) if listing.seo_score else "",       # SEO Score
                    listing.created_at.isoformat() if listing.created_at else "", # Created
                    listing.updated_at.isoformat() if listing.updated_at else ""  # Last Updated
                ]
                new_sheets_data.append(sheets_row)
            
            # Create or update sheet with listings type
            if not self.sheets_service.create_sheet_if_not_exists(target_sheet, "listings"):
                return {"success": False, "message": "Failed to create Google Sheet"}
            
            # Add new items to sheets using batch append
            success_count = 0
            if new_sheets_data:
                try:
                    # Use Google Sheets API to append data
                    if self.sheets_service.service and self.sheets_service.spreadsheet_id:
                        body = {
                            'values': new_sheets_data
                        }
                        
                        # Determine range based on 20 columns (A-T)
                        range_name = f"{target_sheet}!A:T"
                        
                        self.sheets_service.service.spreadsheets().values().append(
                            spreadsheetId=self.sheets_service.spreadsheet_id,
                            range=range_name,
                            valueInputOption='USER_ENTERED',
                            insertDataOption='INSERT_ROWS',
                            body=body
                        ).execute()
                        
                        success_count = len(new_sheets_data)
                except Exception as e:
                    print(f"Error appending listings: {e}")
                    # Fallback to individual adds
                    for sheet_row in new_sheets_data:
                        # Convert back to dict format for fallback
                        sheet_dict = {
                            "id": sheet_row[0],
                            "title": sheet_row[1],
                            "description": sheet_row[2],
                            "category": sheet_row[3],
                            "price": sheet_row[4],
                            "quantity": sheet_row[5]
                        }
                        if self.sheets_service.add_listing(sheet_dict):
                            success_count += 1
            
            # Log sync activity
            activity = ActivityLog(
                user_id=user_id,
                action="sync_export",
                entity_type="listings",
                description=f"Smart export: {success_count} new items to Sheets, {len(merge_result['conflicts'])} conflicts detected",
                success=True,
                new_values={
                    "exported_new": success_count,
                    "conflicts_detected": len(merge_result["conflicts"]),
                    "sheets_preserved": len(merge_result["sheets_new"]),
                    "merge_strategy": self.sync_config["conflict_resolution"]
                }
            )
            db.add(activity)
            db.commit()
            
            return {
                "success": True,
                "message": f"Smart sync completed: {success_count} new items exported",
                "exported_new": success_count,
                "conflicts_detected": len(merge_result["conflicts"]),
                "sheets_items_preserved": len(merge_result["sheets_new"]),
                "total_sqlite": len(sqlite_listings),
                "total_sheets_after": len(sheets_listings) + success_count
            }
            
        except Exception as e:
            # Log error
            activity = ActivityLog(
                user_id=user_id,
                action="sync_export",
                entity_type="listings",
                description=f"Failed to export listings to Google Sheets",
                success=False,
                error_message=str(e)
            )
            db.add(activity)
            db.commit()
            
            return {"success": False, "message": f"Sync failed: {str(e)}"}
    
    def sync_listings_from_sheets(self, db: Session, user_id: int, sheet_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Import Google Sheets listings to SQLite với smart merge
        """
        try:
            # Create backup before sync
            if not self._create_backup(db, user_id, "listings"):
                return {"success": False, "message": "Backup failed, aborting sync"}
            
            # Get all listings from Google Sheets using specified or configured sheet name
            target_sheet = sheet_name or getattr(settings, 'SHEET_NAME', 'Listings')
            sheets_listings = self.sheets_service.get_all_listings(target_sheet)
            
            if not sheets_listings:
                return {"success": True, "message": "No listings found in Google Sheets", "imported": 0}
            
            # Get all SQLite listings
            result = listing_repo.get_multi(db, skip=0, limit=1000, user_id=user_id)
            sqlite_listings = result["items"]
            
            # Detect changes since last sync
            changed_items, last_sync_time = self._detect_changes_since_last_sync(db, user_id, "listings")
            
            # Perform smart merge analysis
            merge_result = self._smart_merge_listings(sqlite_listings, sheets_listings, last_sync_time)
            
            # Apply conflict resolution
            conflicts_resolved = self._resolve_conflicts(merge_result["conflicts"])
            
            if self.sync_config["dry_run_mode"]:
                return {
                    "success": True,
                    "message": "Import dry run completed",
                    "dry_run": True,
                    "preview": {
                        "sheets_new": len(merge_result["sheets_new"]),
                        "sqlite_new": len(merge_result["sqlite_new"]),
                        "conflicts": len(merge_result["conflicts"]),
                        "conflicts_resolved": len(conflicts_resolved)
                    }
                }
            
            imported_count = 0
            updated_count = 0
            errors = []
            
            # Import new items from Sheets
            for sheet_listing in merge_result["sheets_new"]:
                try:
                    listing_id = sheet_listing.get("id") or sheet_listing.get("ID")
                    
                    if not listing_id:
                        continue
                    
                    # Convert from sheets format
                    listing_data = {
                        "title": sheet_listing.get("title") or sheet_listing.get("Title", ""),
                        "description": sheet_listing.get("description") or sheet_listing.get("Description", ""),
                        "category": sheet_listing.get("category") or sheet_listing.get("Category", ""),
                        "price": float(sheet_listing.get("price", sheet_listing.get("Price", 0))) if sheet_listing.get("price") or sheet_listing.get("Price") else None,
                        "quantity": int(sheet_listing.get("quantity", sheet_listing.get("Quantity", 0))) if sheet_listing.get("quantity") or sheet_listing.get("Quantity") else 0,
                        "keywords": sheet_listing.get("keywords", sheet_listing.get("Keywords", "")).split(",") if sheet_listing.get("keywords") or sheet_listing.get("Keywords") else [],
                        "item_specifics": sheet_listing.get("item_specifics", {}),
                        "status": ListingStatusEnum(sheet_listing.get("status", sheet_listing.get("Status", "draft")))
                    }
                    
                    # Create new listing
                    listing_data["id"] = listing_id
                    listing_repo.create(
                        db,
                        obj_in=listing_data,
                        user_id=user_id
                    )
                    imported_count += 1
                        
                except Exception as e:
                    errors.append(f"Error importing new listing {listing_id}: {str(e)}")
            
            # Handle conflicts based on resolution strategy
            for conflict, resolution in zip(merge_result["conflicts"], conflicts_resolved):
                try:
                    if resolution["action"] == "keep_sheets":
                        # Update SQLite with Sheets data
                        existing_listing = conflict["sqlite_item"]
                        sheets_data = conflict["sheets_item"]
                        
                        listing_data = {
                            "title": sheets_data.get("title", sheets_data.get("Title", "")),
                            "description": sheets_data.get("description", sheets_data.get("Description", "")),
                            "category": sheets_data.get("category", sheets_data.get("Category", "")),
                            "price": float(sheets_data.get("price", sheets_data.get("Price", 0))) if sheets_data.get("price") or sheets_data.get("Price") else None,
                            "quantity": int(sheets_data.get("quantity", sheets_data.get("Quantity", 0))) if sheets_data.get("quantity") or sheets_data.get("Quantity") else 0,
                        }
                        
                        listing_repo.update(
                            db,
                            db_obj=existing_listing,
                            obj_in=listing_data
                        )
                        updated_count += 1
                        
                except Exception as e:
                    errors.append(f"Error resolving conflict for {conflict['id']}: {str(e)}")
            
            # Log sync activity
            activity = ActivityLog(
                user_id=user_id,
                action="sync_import",
                entity_type="listings",
                description=f"Smart import: {imported_count} new from Sheets, {updated_count} conflicts resolved",
                success=len(errors) == 0,
                new_values={
                    "imported_new": imported_count,
                    "conflicts_resolved": updated_count,
                    "sqlite_preserved": len(merge_result["sqlite_new"]),
                    "errors_count": len(errors),
                    "merge_strategy": self.sync_config["conflict_resolution"]
                }
            )
            db.add(activity)
            db.commit()
            
            return {
                "success": True,
                "message": f"Smart import completed: {imported_count} new items, {updated_count} conflicts resolved",
                "imported_new": imported_count,
                "conflicts_resolved": updated_count,
                "sqlite_items_preserved": len(merge_result["sqlite_new"]),
                "errors": errors,
                "total_sqlite_after": len(sqlite_listings) + imported_count
            }
            
        except Exception as e:
            # Log error
            activity = ActivityLog(
                user_id=user_id,
                action="sync_import",
                entity_type="listings",
                description=f"Failed to import listings from Google Sheets",
                success=False,
                error_message=str(e)
            )
            db.add(activity)
            db.commit()
            
            return {"success": False, "message": f"Import failed: {str(e)}"}
    
    def should_update_from_sheets(self, sqlite_listing: Listing, sheets_listing: Dict[str, Any]) -> bool:
        """
        Determine if SQLite record should be updated from Sheets based on conflict resolution
        """
        if self.sync_config["conflict_resolution"] == "sheets_wins":
            return True
        elif self.sync_config["conflict_resolution"] == "sqlite_wins":
            return False
        else:
            # Compare timestamps (manual resolution needed if different)
            sheets_updated = sheets_listing.get("updated_at")
            if not sheets_updated:
                return False
            
            try:
                sheets_timestamp = datetime.fromisoformat(sheets_updated.replace('Z', '+00:00'))
                sqlite_timestamp = sqlite_listing.updated_at or sqlite_listing.created_at
                
                # Update if sheets is newer
                return sheets_timestamp > sqlite_timestamp
            except:
                return False
    
    def sync_orders_to_sheets(self, db: Session, user_id: int, sheet_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Export orders to dedicated orders sheet in Google Sheets
        """
        try:
            # Get target sheet name from config or parameter
            target_sheet = sheet_name or getattr(settings, 'ORDERS_SHEET_NAME', 'Orders')
            
            # Get recent orders (last 30 days to avoid huge exports)
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=30)
            
            orders = db.query(Order).filter(
                and_(
                    Order.user_id == user_id,
                    Order.created_at >= cutoff_date
                )
            ).all()
            
            if not orders:
                return {
                    "success": True,
                    "message": "No orders to export",
                    "exported_count": 0
                }
            
            # Create backup
            if not self._create_backup(db, user_id, "orders"):
                return {"success": False, "message": "Backup failed, aborting sync"}
            
            # Convert to export format for Google Sheets
            export_data = []
            for order in orders:
                export_row = [
                    str(order.id),
                    order.order_number or "",
                    order.customer_name or "",
                    order.customer_email or "",
                    order.product_name or "",
                    str(order.price_ebay) if order.price_ebay else "",
                    order.status.value,
                    order.order_date.isoformat() if order.order_date else "",
                    order.tracking_number or "",
                    order.carrier or "",
                    ",".join(order.alerts) if order.alerts else "",
                    order.created_at.isoformat()
                ]
                export_data.append(export_row)
            
            # Export to Google Sheets using the target sheet
            if self.sheets_service.use_fallback:
                return {
                    "success": True,
                    "message": f"Fallback mode: {len(export_data)} orders prepared for export to {target_sheet}",
                    "exported_count": len(export_data),
                    "target_sheet": target_sheet
                }
            
            # Create Orders sheet if not exists
            if not self.sheets_service.create_sheet_if_not_exists(target_sheet, "orders"):
                return {"success": False, "message": "Failed to create Orders sheet"}
            
            # Use Google Sheets API to export
            try:
                # Headers are already created by create_sheet_if_not_exists
                # Just prepare the data rows
                sheet_data = export_data
                
                # Clear existing data (except headers) and write new data
                if self.sheets_service.service and self.sheets_service.spreadsheet_id:
                    # Clear data rows only (keep headers)
                    if len(export_data) > 0:
                        clear_range = f"{target_sheet}!A2:L"
                        self.sheets_service.service.spreadsheets().values().clear(
                            spreadsheetId=self.sheets_service.spreadsheet_id,
                            range=clear_range
                        ).execute()
                        
                        # Write new data starting from row 2
                        body = {
                            'values': sheet_data
                        }
                        
                        self.sheets_service.service.spreadsheets().values().update(
                            spreadsheetId=self.sheets_service.spreadsheet_id,
                            range=f"{target_sheet}!A2:L{len(sheet_data) + 1}",
                            valueInputOption='USER_ENTERED',
                            body=body
                        ).execute()
                
                return {
                    "success": True,
                    "message": f"Successfully exported {len(export_data)} orders to {target_sheet} sheet",
                    "exported_count": len(export_data),
                    "target_sheet": target_sheet
                }
                
            except Exception as sheets_error:
                return {
                    "success": False,
                    "message": f"Google Sheets export failed: {str(sheets_error)}",
                    "target_sheet": target_sheet
                }
            
        except Exception as e:
            return {"success": False, "message": f"Orders export failed: {str(e)}"}
    
    def sync_sources_to_sheets(self, db: Session, user_id: int, sheet_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Export sources to dedicated sources sheet in Google Sheets
        """
        try:
            # Get target sheet name from config or parameter
            target_sheet = sheet_name or getattr(settings, 'SOURCES_SHEET_NAME', 'Sources')
            
            # Get all sources for the user
            sources = db.query(Source).filter(Source.user_id == user_id).all()
            
            if not sources:
                return {
                    "success": True,
                    "message": "No sources to export",
                    "exported_count": 0
                }
            
            # Create backup
            if not self._create_backup(db, user_id, "sources"):
                return {"success": False, "message": "Backup failed, aborting sync"}
            
            # Convert to export format for Google Sheets
            export_data = []
            for source in sources:
                export_row = [
                    str(source.id),
                    source.name or "",
                    source.website_url or "",
                    source.status.value if source.status else "disconnected",
                    str(source.total_products) if source.total_products else "0",
                    source.last_sync.isoformat() if source.last_sync else "",
                    source.created_at.isoformat()
                ]
                export_data.append(export_row)
            
            # Export to Google Sheets using the target sheet
            if self.sheets_service.use_fallback:
                return {
                    "success": True,
                    "message": f"Fallback mode: {len(export_data)} sources prepared for export to {target_sheet}",
                    "exported_count": len(export_data),
                    "target_sheet": target_sheet
                }
            
            # Create Sources sheet if not exists
            if not self.sheets_service.create_sheet_if_not_exists(target_sheet, "sources"):
                return {"success": False, "message": "Failed to create Sources sheet"}
            
            # Use Google Sheets API to export
            try:
                # Headers are already created by create_sheet_if_not_exists
                # Just prepare the data rows
                sheet_data = export_data
                
                # Clear existing data (except headers) and write new data
                if self.sheets_service.service and self.sheets_service.spreadsheet_id:
                    # Clear data rows only (keep headers)
                    if len(export_data) > 0:
                        clear_range = f"{target_sheet}!A2:G"
                        self.sheets_service.service.spreadsheets().values().clear(
                            spreadsheetId=self.sheets_service.spreadsheet_id,
                            range=clear_range
                        ).execute()
                        
                        # Write new data starting from row 2
                        body = {
                            'values': sheet_data
                        }
                        
                        self.sheets_service.service.spreadsheets().values().update(
                            spreadsheetId=self.sheets_service.spreadsheet_id,
                            range=f"{target_sheet}!A2:G{len(sheet_data) + 1}",
                            valueInputOption='USER_ENTERED',
                            body=body
                        ).execute()
                
                return {
                    "success": True,
                    "message": f"Successfully exported {len(export_data)} sources to {target_sheet} sheet",
                    "exported_count": len(export_data),
                    "target_sheet": target_sheet
                }
                
            except Exception as sheets_error:
                return {
                    "success": False,
                    "message": f"Google Sheets export failed: {str(sheets_error)}",
                    "target_sheet": target_sheet
                }
            
        except Exception as e:
            return {"success": False, "message": f"Sources export failed: {str(e)}"}
    
    def full_sync(self, db: Session, user_id: int, direction: str = "bidirectional") -> Dict[str, Any]:
        """
        Perform full synchronization with smart merge
        direction: "to_sheets", "from_sheets", "bidirectional"
        """
        results = {
            "success": True,
            "message": "Smart bidirectional sync completed",
            "details": {},
            "summary": {
                "total_new_items": 0,
                "total_conflicts_resolved": 0,
                "items_preserved": 0
            }
        }
        
        try:
            # Đặc biệt xử lý bidirectional để tránh mất dữ liệu
            if direction == "bidirectional":
                # Thực hiện smart sync thông minh
                
                # Bước 1: Phân tích trước khi sync
                sqlite_result = listing_repo.get_multi(db, skip=0, limit=1000, user_id=user_id)
                sqlite_listings = sqlite_result["items"]
                sheets_listings = self.sheets_service.get_all_listings() or []
                
                changed_items, last_sync_time = self._detect_changes_since_last_sync(db, user_id, "listings")
                merge_analysis = self._smart_merge_listings(sqlite_listings, sheets_listings, last_sync_time)
                
                # Bước 2: Export chỉ những items mới từ SQLite
                if merge_analysis["sqlite_new"]:
                    listings_export = self.sync_listings_to_sheets(db, user_id)
                    results["details"]["listings_export"] = listings_export
                    results["summary"]["total_new_items"] += listings_export.get("exported_new", 0)
                else:
                    results["details"]["listings_export"] = {"success": True, "message": "No new SQLite items to export", "exported_new": 0}
                
                # Bước 3: Import chỉ những items mới từ Sheets
                if merge_analysis["sheets_new"] or merge_analysis["conflicts"]:
                    listings_import = self.sync_listings_from_sheets(db, user_id)
                    results["details"]["listings_import"] = listings_import
                    results["summary"]["total_new_items"] += listings_import.get("imported_new", 0)
                    results["summary"]["total_conflicts_resolved"] += listings_import.get("conflicts_resolved", 0)
                else:
                    results["details"]["listings_import"] = {"success": True, "message": "No new Sheets items to import", "imported_new": 0}
                
                # Bước 4: Tính toán summary
                results["summary"]["items_preserved"] = len(merge_analysis["sqlite_new"]) + len(merge_analysis["sheets_new"])
                results["summary"]["conflicts_detected"] = len(merge_analysis["conflicts"])
                
                # Thông báo kết quả chi tiết
                if results["summary"]["total_new_items"] > 0:
                    results["message"] = f"Smart sync: {results['summary']['total_new_items']} new items merged, {results['summary']['total_conflicts_resolved']} conflicts resolved"
                else:
                    results["message"] = "All data already in sync - no changes needed"
                
            elif direction == "to_sheets":
                # Export to Google Sheets using configured sheet names
                listings_export = self.sync_listings_to_sheets(db, user_id)
                results["details"]["listings_export"] = listings_export
                
                orders_export = self.sync_orders_to_sheets(db, user_id)
                results["details"]["orders_export"] = orders_export
                
                sources_export = self.sync_sources_to_sheets(db, user_id)
                results["details"]["sources_export"] = sources_export
                
                results["summary"]["total_new_items"] = (
                    listings_export.get("exported_new", 0) + 
                    orders_export.get("exported_count", 0) + 
                    sources_export.get("exported_count", 0)
                )
                
            elif direction == "from_sheets":
                # Import from Google Sheets
                listings_import = self.sync_listings_from_sheets(db, user_id)
                results["details"]["listings_import"] = listings_import
                
                results["summary"]["total_new_items"] = listings_import.get("imported_new", 0)
                results["summary"]["total_conflicts_resolved"] = listings_import.get("conflicts_resolved", 0)
            
            # Update sync timestamp
            sync_activity = ActivityLog(
                user_id=user_id,
                action="full_sync",
                entity_type="system",
                description=f"Smart {direction} sync: {results['summary']['total_new_items']} new items, {results['summary']['total_conflicts_resolved']} conflicts resolved",
                success=True,
                new_values={
                    "sync_direction": direction,
                    "timestamp": datetime.now().isoformat(),
                    "summary": results["summary"],
                    "merge_strategy": self.sync_config["conflict_resolution"]
                }
            )
            db.add(sync_activity)
            db.commit()
            
            return results
            
        except Exception as e:
            results["success"] = False
            results["message"] = f"Full sync failed: {str(e)}"
            return results
    
    def get_sync_status(self, db: Session, user_id: int) -> Dict[str, Any]:
        """
        Get current sync status and statistics
        """
        try:
            # Get last sync activities
            last_export = db.query(ActivityLog).filter(
                and_(
                    ActivityLog.user_id == user_id,
                    ActivityLog.action.in_(["sync_export", "full_sync"])
                )
            ).order_by(ActivityLog.created_at.desc()).first()
            
            last_import = db.query(ActivityLog).filter(
                and_(
                    ActivityLog.user_id == user_id,
                    ActivityLog.action.in_(["sync_import", "full_sync"])
                )
            ).order_by(ActivityLog.created_at.desc()).first()
            
            # Count records in each system
            sqlite_counts = {
                "listings": listing_repo.count(db, user_id=user_id),
                "orders": order_repo.count(db, user_id=user_id),
                "sources": source_repo.count(db, user_id=user_id),
                "accounts": account_repo.count(db, user_id=user_id)
            }
            
            # Get Google Sheets count (if available)
            sheets_listings = self.sheets_service.get_all_listings()
            sheets_counts = {
                "listings": len(sheets_listings) if sheets_listings else 0
            }
            
            return {
                "success": True,
                "sqlite_counts": sqlite_counts,
                "sheets_counts": sheets_counts,
                "last_export": {
                    "timestamp": last_export.created_at.isoformat() if last_export else None,
                    "success": last_export.success if last_export else None,
                    "details": last_export.description if last_export else None
                },
                "last_import": {
                    "timestamp": last_import.created_at.isoformat() if last_import else None,
                    "success": last_import.success if last_import else None,
                    "details": last_import.description if last_import else None
                },
                "config": self.sync_config
            }
            
        except Exception as e:
            return {"success": False, "message": f"Error getting sync status: {str(e)}"}
    
    def schedule_auto_sync(self, user_id: int) -> bool:
        """
        Schedule automatic synchronization (to be called by background task)
        """
        if not self.sync_config["enabled"]:
            return False
        
        try:
            db = SessionLocal()
            
            # Perform bidirectional sync
            result = self.full_sync(db, user_id, "bidirectional")
            
            db.close()
            
            return result["success"]
            
        except Exception as e:
            print(f"Auto-sync failed for user {user_id}: {e}")
            return False


# Create service instance
sync_service = SyncService()